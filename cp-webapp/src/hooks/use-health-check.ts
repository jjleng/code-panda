'use client';

import { useCallback, useEffect, useState } from 'react';

// Export standalone health check function
export async function checkHealth(projectId: string | null): Promise<boolean> {
  if (!projectId) return false;

  return true;
}

interface UseHealthCheckOptions {
  projectId: string | null;
  enabled: boolean;
  interval?: number;
  onHealthy?: () => void;
}

export function useHealthCheck({
  projectId,
  enabled,
  interval = 3000,
  onHealthy,
}: UseHealthCheckOptions) {
  const [isPolling, setIsPolling] = useState(false);

  const checkHealthCallback = useCallback(async () => {
    return checkHealth(projectId);
  }, [projectId]);

  useEffect(() => {
    if (!enabled || !projectId) {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    let timeoutId: NodeJS.Timeout;

    const poll = async () => {
      const isHealthy = await checkHealthCallback();

      if (isHealthy) {
        setIsPolling(false);
        onHealthy?.();
      } else {
        timeoutId = setTimeout(poll, interval);
      }
    };

    poll();

    return () => {
      clearTimeout(timeoutId);
      setIsPolling(false);
    };
  }, [enabled, projectId, interval, checkHealthCallback, onHealthy]);

  return { isPolling };
}
