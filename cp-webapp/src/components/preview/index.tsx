'use client';

import { Loader } from '@/components/preview/loader';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useProject } from '@/context';
import { listProjectPathsApiV1ProjectsProjectIdPathsGetOptions } from '@/generated/agent/@tanstack/react-query.gen';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, ChevronDown, RefreshCw, Smartphone } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { usePreviewContext } from './context';
import { restartPreviewServer } from '@/hooks/use-heartbeat';

function getProxyUrl(projectId: string | null): string {
  const baseUrl = process.env.NEXT_PUBLIC_PROXY_URL;
  if (!baseUrl) {
    throw new Error('NEXT_PUBLIC_PROXY_URL is not defined in the environment.');
  }
  if (!projectId) {
    return '';
  }
  return baseUrl.replace('PROJECT_ID', projectId);
}

function AddressBar({
  baseUrl,
  onRefresh,
  isMobileView,
  onToggleMobileView,
  projectId,
}: {
  baseUrl: string;
  onRefresh: () => void;
  isMobileView: boolean;
  onToggleMobileView: () => void;
  projectId: string | null;
}) {
  const { previewPath, setPreviewPath, pathsRefreshCounter } = usePreviewContext();
  const [path, setPath] = useState(previewPath);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [tooltipOpen, setTooltipOpen] = useState(false);
  const [backTooltipOpen, setBackTooltipOpen] = useState(false);
  const [forwardTooltipOpen, setForwardTooltipOpen] = useState(false);
  const [refreshTooltipOpen, setRefreshTooltipOpen] = useState(false);
  const [history, setHistory] = useState<string[]>([previewPath]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [isUserEditing, setIsUserEditing] = useState(false);
  const [pathsDropdownOpen, setPathsDropdownOpen] = useState(false);

  useEffect(() => {
    // Only update the input field when not actively being edited by user
    if (!isUserEditing) {
      setPath(previewPath);
    }
  }, [previewPath, isUserEditing]);

  const {
    data: pathsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    ...listProjectPathsApiV1ProjectsProjectIdPathsGetOptions({
      headers: {
        'X-CP-Project-ID': projectId,
      },
      path: {
        project_id: projectId!,
      },
    }),
    enabled: projectId != null,
  });

  useEffect(() => {
    if (pathsRefreshCounter > 0) {
      refetch();
    }
  }, [pathsRefreshCounter, refetch]);

  const availablePaths = useMemo(() => {
    return pathsData?.paths || [];
  }, [pathsData]);

  useEffect(() => {
    if (error) {
      console.error('Error fetching project paths:', error);
    }
  }, [error]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    onRefresh();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleBack = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      const previousPath = history[newIndex];
      setPath(previousPath);
      setPreviewPath(previousPath);
      setIsUserEditing(false);

      // Navigate the iframe
      if (window.frames[0]) {
        window.frames[0].location.href = `${baseUrl}${previousPath}`;
      }
    }
  };

  const handleForward = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      const nextPath = history[newIndex];
      setPath(nextPath);
      setPreviewPath(nextPath);
      setIsUserEditing(false);

      // Navigate the iframe
      if (window.frames[0]) {
        window.frames[0].location.href = `${baseUrl}${nextPath}`;
      }
    }
  };

  const navigateToPath = (selectedPath: string) => {
    setPath(selectedPath);
    setPreviewPath(selectedPath);
    setIsUserEditing(false);
    setPathsDropdownOpen(false);

    // Add to history
    addToHistory(selectedPath);

    // Navigate the iframe
    if (window.frames[0]) {
      window.frames[0].location.href = `${baseUrl}${selectedPath}`;
    }
  };

  const addToHistory = useCallback(
    (newPath: string) => {
      // Only add if it's different from the current path
      if (newPath !== history[historyIndex]) {
        // Remove any forward history when navigating to a new path
        setHistory(prev => [...prev.slice(0, historyIndex + 1), newPath]);
        setHistoryIndex(prev => prev + 1);
      }
    },
    [history, historyIndex]
  );

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin === baseUrl && event.data.type === 'navigation') {
        console.log('Received navigation event:', event.data);
        const newPath = event.data.path;
        setPreviewPath(newPath);
        setPath(newPath);
        setIsUserEditing(false);

        // Add to history when navigation happens
        addToHistory(newPath);
      }

      if (event.data?.type === 'activity') {
        setTooltipOpen(false);
        setBackTooltipOpen(false);
        setForwardTooltipOpen(false);
        setRefreshTooltipOpen(false);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [setPreviewPath, baseUrl, history, historyIndex, addToHistory]);

  return (
    <div className="flex items-center gap-2 border-b bg-white p-2">
      <TooltipProvider delayDuration={1400}>
        <Tooltip open={backTooltipOpen} onOpenChange={setBackTooltipOpen}>
          <TooltipTrigger asChild>
            <button
              onClick={handleBack}
              disabled={historyIndex <= 0}
              className={`rounded p-1 ${
                historyIndex > 0
                  ? 'text-gray-700 hover:bg-gray-100'
                  : 'cursor-not-allowed text-gray-300'
              }`}
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">Go back</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider delayDuration={1400}>
        <Tooltip open={forwardTooltipOpen} onOpenChange={setForwardTooltipOpen}>
          <TooltipTrigger asChild>
            <button
              onClick={handleForward}
              disabled={historyIndex >= history.length - 1}
              className={`rounded p-1 ${
                historyIndex < history.length - 1
                  ? 'text-gray-700 hover:bg-gray-100'
                  : 'cursor-not-allowed text-gray-300'
              }`}
            >
              <ArrowRight className="h-4 w-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">Go forward</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider delayDuration={1400}>
        <Tooltip open={refreshTooltipOpen} onOpenChange={setRefreshTooltipOpen}>
          <TooltipTrigger asChild>
            <button
              onClick={handleRefresh}
              className={`rounded p-1 hover:bg-gray-100 ${isRefreshing ? 'animate-spin' : ''}`}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">Refresh page</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <div className="flex flex-1 items-center overflow-hidden rounded border">
        <span className="flex h-8 items-center truncate border-r bg-muted/30 px-2 text-sm text-muted-foreground">
          {baseUrl}
        </span>
        <Input
          type="text"
          value={path}
          onChange={e => {
            setPath(e.target.value);
            setIsUserEditing(true);
            setPreviewPath(e.target.value);
          }}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              const newPath = path;
              setIsUserEditing(false);

              // Add to history when user presses Enter
              addToHistory(newPath);

              // Navigate the iframe
              if (window.frames[0]) {
                window.frames[0].location.href = `${baseUrl}${newPath}`;
              }
            }
          }}
          className="h-8 min-w-[140px] flex-1 shrink-0 rounded-none border-0 px-2 text-sm focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0"
          placeholder="Enter path..."
        />

        {/* Paths dropdown */}
        <DropdownMenu open={pathsDropdownOpen} onOpenChange={setPathsDropdownOpen}>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 rounded-none border-l focus:ring-0 focus-visible:ring-0"
            >
              <ChevronDown className="h-4 w-4" />
              <span className="sr-only">Select path</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="max-h-80 w-56 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-2">
                <RefreshCw className="me-2 h-4 w-4 animate-spin" />
                <span>Loading paths...</span>
              </div>
            ) : availablePaths.length > 0 ? (
              availablePaths.map(availablePath => (
                <DropdownMenuItem
                  key={availablePath}
                  onClick={() => navigateToPath(availablePath)}
                  className="cursor-pointer truncate"
                >
                  {availablePath}
                </DropdownMenuItem>
              ))
            ) : (
              <div className="px-3 py-2 text-sm text-muted-foreground">
                {error ? 'Failed to load paths' : 'No paths available'}
              </div>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <TooltipProvider>
        <Tooltip open={tooltipOpen} onOpenChange={setTooltipOpen}>
          <TooltipTrigger asChild>
            <button onClick={onToggleMobileView} className="rounded p-1 hover:bg-gray-100">
              <Smartphone className={`h-4 w-4 ${isMobileView ? 'text-blue-500' : ''}`} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            {isMobileView ? 'Switch to desktop view' : 'Switch to mobile view'}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}

function Preview() {
  const {
    isInitializingPreview,
    isPreviewServerReady,
    projectId,
    setInitializingPreview,
    setPreviewServerReady,
  } = useProject();
  const [key, setKey] = useState(0);
  const { setPreviewPath, refreshCounter } = usePreviewContext();
  const [isMobileView, setIsMobileView] = useState(false);

  const handleRefresh = useCallback(async () => {
    if (projectId) {
      setInitializingPreview(true);

      try {
        const success = await restartPreviewServer(projectId);
        setPreviewServerReady(success);

        // Increment key to force iframe refresh
        setKey(prev => prev + 1);
      } catch (error) {
        console.error('Error during refresh/restart:', error);
        setPreviewServerReady(false);
      } finally {
        setInitializingPreview(false);
      }
    } else {
      setKey(prev => prev + 1);
    }
  }, [projectId, setInitializingPreview, setPreviewServerReady]);

  // Listen for refresh triggers from the context
  useEffect(() => {
    if (refreshCounter > 0) {
      setKey(prev => prev + 1);
    }
  }, [refreshCounter]);

  const toggleMobileView = () => {
    setIsMobileView(prev => !prev);
  };

  // Handle only navigation events from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin === getProxyUrl(projectId) && event.data.type === 'navigation') {
        console.log('Received navigation event:', event.data);
        setPreviewPath(event.data.path);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [setPreviewPath, projectId]);

  const previewIframe = useMemo(
    () =>
      !projectId ? (
        <></>
      ) : (
        <>
          <div className="flex h-full w-full flex-col">
            <AddressBar
              baseUrl={getProxyUrl(projectId)}
              onRefresh={handleRefresh}
              isMobileView={isMobileView}
              onToggleMobileView={toggleMobileView}
              projectId={projectId}
            />
            <div className="flex flex-1 justify-center overflow-auto bg-gray-100">
              <iframe
                key={key}
                src={getProxyUrl(projectId)}
                className={`h-full border-none ${
                  isMobileView ? 'w-[375px] border-x border-gray-300 shadow-md' : 'w-full'
                }`}
                title="Preview"
              />
            </div>
          </div>
        </>
      ),
    [key, isMobileView, projectId, handleRefresh]
  );

  if (isInitializingPreview) {
    return <Loader isLoading={true} />;
  }

  if (!isPreviewServerReady) {
    return <div>Failed to start preview server</div>;
  }

  return previewIframe;
}

export { Preview };
