import { ProvisioningState, useProject } from '@/context';
import { createProjectApiV1ProjectsPostMutation } from '@/generated/agent/@tanstack/react-query.gen';
import { startProject } from '@/generated/runner';
import { checkPreviewOptions } from '@/generated/runner/@tanstack/react-query.gen';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { useHealthCheck } from './use-health-check';
import { useActivity } from './use-activity';

const DEBOUNCE_WAIT = 30 * 1000; // 30 seconds

interface UseHeartbeatProps {
  projectId: string | null;
  onProvisioned?: () => void;
  onProvisioning?: () => void;
}

export async function restartPreviewServer(projectId: string): Promise<boolean> {
  try {
    const { error } = await startProject({
      body: {
        project_id: projectId,
      },
    });
    return !error;
  } catch {
    return false;
  }
}

export function useHeartbeat({ projectId, onProvisioned, onProvisioning }: UseHeartbeatProps) {
  const initialCallMadeRef = useRef(false);
  // Track if we should be actively polling for health status
  const [healthCheckEnabled, setHealthCheckEnabled] = useState(false);

  const createProject = useMutation(createProjectApiV1ProjectsPostMutation());
  const { setPreviewServerReady, setInitializingPreview, setProvisioningState, provisioningState } =
    useProject();

  // Preview server health check
  const { refetch: refetchPreview } = useQuery({
    ...checkPreviewOptions({
      query: {
        project_id: projectId!,
      },
    }),
    enabled: !!projectId && provisioningState === ProvisioningState.PROVISIONED,
  });

  // Check and manage preview server
  const managePreviewServer = useCallback(async () => {
    if (!projectId) return;

    try {
      // Check server status - use the returned data directly instead of stale state
      const { data: freshStatus } = await refetchPreview();
      const isHealthy = freshStatus?.healthy ?? false;

      if (!isHealthy) {
        // Only show loading and attempt restart if server is down
        setInitializingPreview(true);
        console.log('Preview server is down, attempting to restart...');
        const started = await restartPreviewServer(projectId);
        setPreviewServerReady(started);
        setInitializingPreview(false);
      } else {
        setPreviewServerReady(true);
        setInitializingPreview(false);
      }
    } catch (error) {
      console.error('Error managing preview server:', error);
      setPreviewServerReady(false);
      setInitializingPreview(false);
    }
  }, [projectId, setPreviewServerReady, setInitializingPreview, refetchPreview]);

  // Use the existing health check hook, leveraging its built-in polling capability
  const { isPolling } = useHealthCheck({
    projectId,
    enabled: healthCheckEnabled,
    onHealthy: useCallback(() => {
      setHealthCheckEnabled(false); // Stop polling once healthy
      setProvisioningState(ProvisioningState.PROVISIONED);
      onProvisioned?.();
      // Check preview server after workspace is healthy
      managePreviewServer();
    }, [onProvisioned, setProvisioningState, managePreviewServer]),
  });

  // Handle workspace access - attempt to access the workspace directly
  const accessWorkspace = useCallback(async () => {
    if (!projectId) return;

    try {
      await createProject.mutateAsync({
        body: {
          project_id: projectId,
          name: `Project ${projectId.slice(0, 8)}`,
        },
      });

      // Success! Workspace is ready
      setProvisioningState(ProvisioningState.PROVISIONED);
      onProvisioned?.();
      setHealthCheckEnabled(false); // Stop any health check polling
      await managePreviewServer();
    } catch {
      console.log('Project access failed, starting health check polling');

      // Set provisioning state if needed
      if (provisioningState !== ProvisioningState.PROVISIONING) {
        setProvisioningState(ProvisioningState.PROVISIONING);
        onProvisioning?.();
      }

      // Start health check polling (useHealthCheck will handle the repeated checks)
      setHealthCheckEnabled(true);
    }
  }, [
    projectId,
    provisioningState,
    createProject,
    setProvisioningState,
    onProvisioning,
    onProvisioned,
    managePreviewServer,
  ]);

  // Create debounced activity handler that will trigger workspace access
  // This prevents multiple rapid calls when user is actively interacting
  const debouncedActivityHandler = useDebouncedCallback(
    () => {
      accessWorkspace();
    },
    DEBOUNCE_WAIT,
    { maxWait: DEBOUNCE_WAIT, leading: true } // Leading ensures immediate first call
  );

  // Initialize workspace access when projectId is available
  useEffect(() => {
    if (projectId && !initialCallMadeRef.current) {
      initialCallMadeRef.current = true;
      debouncedActivityHandler();
    }
  }, [projectId, debouncedActivityHandler]);

  // The activity handler that external components will call
  const handleActivity = useCallback(() => {
    // If workspace might be idle/dead, try to access it again
    if (!initialCallMadeRef.current) {
      initialCallMadeRef.current = true;
      debouncedActivityHandler();
    }
  }, [debouncedActivityHandler]);

  // Use the activity hook to monitor user activity
  useActivity({
    onActivity: handleActivity,
    enabled: !!projectId,
  });

  return {
    handleActivity,
    isPolling,
  };
}
