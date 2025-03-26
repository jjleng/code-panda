'use client';

import { ChatPanel } from '@/components/chat';
import { CodeView } from '@/components/code-view';
import { CodeViewProvider } from '@/components/code-view/context';
import { MergeViewProvider } from '@/components/merge-view/context';
import { MergeViewOverlay } from '@/components/merge-view/overlay';
import { Preview } from '@/components/preview';
import { PreviewProvider } from '@/components/preview/context';
import { SnapshotView } from '@/components/snapshot-view';
import { SnapshotProvider } from '@/components/snapshot-view/context';
import { Button } from '@/components/ui/button';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { WorkspaceProvisioningOverlay } from '@/components/workspace-provisioning-overlay';
import { ProjectProvider, ProvisioningState, useProject } from '@/context';
import { useHeartbeat } from '@/hooks/use-heartbeat';
import { useToast } from '@/hooks/use-toast';
import { compose } from '@/lib/compose';
import { cn } from '@/lib/utils';
import { useDirection } from '@radix-ui/react-direction';
import { Chrome, Code, Download, GitBranch } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import { Resizable } from 're-resizable';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { validate as validateUuid } from 'uuid';

const DownloadButton = () => {
  const { projectId } = useProject();
  const [tooltipOpen, setTooltipOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const { toast } = useToast();

  const handleDownload = async () => {
    try {
      setIsDownloading(true);

      const agentBaseUrl = process.env.NEXT_PUBLIC_AGENT_URL;
      if (!agentBaseUrl) {
        throw new Error('Agent API URL is not configured');
      }

      const downloadUrl = `${agentBaseUrl}/api/v1/projects/${projectId}/download`;

      const response = await fetch(downloadUrl, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      // Get the blob from the response
      const blob = await response.blob();

      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Create and trigger a download link
      const a = document.createElement('a');
      a.href = url;
      a.download = `project-${projectId}.zip`;
      document.body.appendChild(a);
      a.click();

      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading source code:', error);
      toast({
        title: 'Download failed',
        description: error instanceof Error ? error.message : 'Failed to download source code',
        variant: 'destructive',
      });
    } finally {
      setIsDownloading(false);
    }
  };

  // Listen for activity messages to close tooltip
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'activity') {
        setTooltipOpen(false);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  return (
    <TooltipProvider>
      <Tooltip open={tooltipOpen} onOpenChange={setTooltipOpen}>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDownload}
            className="ml-2 h-8 w-8"
            disabled={isDownloading}
          >
            <Download className={`h-4 w-4 ${isDownloading ? 'animate-pulse' : ''}`} />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Download source code</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const AppProviders = compose(
  PreviewProvider,
  MergeViewProvider,
  CodeViewProvider,
  SnapshotProvider
);

const AppContent = () => {
  const [activeTab, setActiveTab] = useState('preview');
  const [chatPanelWidth, setChatPanelWidth] = useState('400px');
  const dir = useDirection();
  const params = useParams();
  const router = useRouter();

  const {
    projectId,
    setProjectId,
    provisioningState,
    provisioningMessage,
    startProvisioning,
    stopProvisioning,
  } = useProject();

  // Set the projectId from URL params with validation
  useEffect(() => {
    if (params.projectId && typeof params.projectId === 'string') {
      // Validate if the projectId is a valid UUID
      if (validateUuid(params.projectId)) {
        setProjectId(params.projectId);
      } else {
        // If not valid, redirect to the new project page
        console.error('Invalid project ID format');
        router.push('/projects/new');
      }
    }
  }, [params.projectId, setProjectId, router]);

  useHeartbeat({
    projectId,
    onProvisioning: useCallback(() => {
      startProvisioning();
    }, [startProvisioning]),
    onProvisioned: useCallback(() => {
      stopProvisioning();
    }, [stopProvisioning]),
  });

  const previewComponent = useMemo(() => <Preview />, []);
  const codeComponent = useMemo(() => <CodeView />, []);
  const snapshotComponent = useMemo(() => <SnapshotView />, []);

  // Calculate if the workspace is in a provisioning state
  const isProvisioning =
    provisioningState === ProvisioningState.PROVISIONING ||
    provisioningState === ProvisioningState.NOT_STARTED;

  return (
    <AppProviders>
      <div className="flex h-screen flex-1 overflow-hidden">
        <Resizable
          className="!max-w-none overflow-hidden"
          onResize={(_event, _direction, ref) => {
            const width = ref.offsetWidth;
            setChatPanelWidth(`${width}px`);
          }}
          size={{
            width: chatPanelWidth,
            height: '100%',
          }}
          minWidth="400px"
          maxWidth={'55%'}
          enable={{ right: dir === 'ltr', left: dir === 'rtl' }}
          defaultSize={{
            width: chatPanelWidth,
            height: '100%',
          }}
        >
          <aside className="relative flex h-full w-full flex-col border-e bg-gray-50/50 dark:bg-gray-900/50">
            <ChatPanel disabled={isProvisioning} requireAuth={false} />
          </aside>
        </Resizable>

        <main className="relative flex flex-1 flex-col">
          {isProvisioning && <WorkspaceProvisioningOverlay message={provisioningMessage} />}
          <header className="flex items-center border-b bg-gray-50/50 px-6 py-2 shadow-sm dark:bg-gray-900/50">
            <div className="flex flex-1 items-center justify-between">
              <ToggleGroup
                type="single"
                defaultValue="preview"
                onValueChange={value => {
                  if (value) setActiveTab(value);
                }}
              >
                <ToggleGroupItem value="preview" aria-label="Toggle preview">
                  <Chrome className="h-4 w-4" />
                  Preview
                </ToggleGroupItem>
                <ToggleGroupItem value="code" aria-label="Toggle code editor">
                  <Code className="h-4 w-4" />
                  Code
                </ToggleGroupItem>
                <ToggleGroupItem value="snapshots" aria-label="Toggle snapshots">
                  <GitBranch className="h-4 w-4" />
                  Snapshots
                </ToggleGroupItem>
              </ToggleGroup>
              <div className="flex items-center">
                <DownloadButton />
              </div>
            </div>
          </header>

          <div
            className={cn('flex-1 overflow-hidden', {
              hidden: activeTab !== 'code',
            })}
          >
            {codeComponent}
          </div>
          <div
            className={cn('flex-1', {
              hidden: activeTab !== 'preview',
            })}
          >
            {previewComponent}
          </div>
          <div
            className={cn('flex-1 overflow-hidden', {
              hidden: activeTab !== 'snapshots',
            })}
          >
            {snapshotComponent}
          </div>
        </main>
      </div>
      <MergeViewOverlay />
    </AppProviders>
  );
};

const ProjectPage = () => (
  <ProjectProvider>
    <AppContent />
  </ProjectProvider>
);

export default ProjectPage;
