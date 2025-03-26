'use client';

import { CodeMergeView } from '@/components/code-view/code-renderer';
import { Spinner } from '@/components/spinner';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { ProvisioningState, useProject } from '@/context';
import {
  getCommitDiffOptions,
  getCommitsInfiniteOptions,
  getFileDiffOptions,
} from '@/generated/runner/@tanstack/react-query.gen';
import { useDirection } from '@radix-ui/react-direction';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Resizable } from 're-resizable';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { CommitsList } from './commits-list';
import { useSnapshotContext } from './context';

export function SnapshotView() {
  const [explorerWidth, setExplorerWidth] = useState<string>('300px');
  const [foldedFiles, setFoldedFiles] = useState<Set<number>>(new Set());
  const parentRef = useRef<HTMLDivElement>(null);
  const dir = useDirection();
  const { projectId, provisioningState } = useProject();
  const {
    selectedCommit,
    setSelectedCommit,
    selectedFile,
    setSelectedFile,
    isLoading,
    refreshTrigger,
  } = useSnapshotContext();

  const {
    data: commitsData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery({
    ...getCommitsInfiniteOptions({
      query: {
        project_id: projectId!,
        limit: 20,
      },
    }),
    getNextPageParam: lastPage => {
      const commits = lastPage.commits;
      return lastPage.has_next_page
        ? commits && commits.length > 0
          ? commits[commits.length - 1].hash
          : null
        : null;
    },
    initialPageParam: '',
    enabled: projectId !== null && provisioningState === ProvisioningState.PROVISIONED,
  });

  const { data: commitDiffData, refetch: refetchCommitDiff } = useQuery({
    ...getCommitDiffOptions({
      query: {
        project_id: projectId!,
        commit_hash: selectedCommit || '',
      },
    }),
    enabled:
      !!selectedCommit &&
      !selectedFile &&
      !!projectId &&
      provisioningState === ProvisioningState.PROVISIONED,
  });

  const { data: fileDiffData, refetch: refetchFileDiff } = useQuery({
    ...getFileDiffOptions({
      query: {
        project_id: projectId!,
        commit_hash: selectedCommit || '',
        file_path: selectedFile || '',
      },
    }),
    enabled:
      !!selectedCommit &&
      !!selectedFile &&
      !!projectId &&
      provisioningState === ProvisioningState.PROVISIONED,
  });

  // Flatten commits from all pages
  const commits = commitsData?.pages.flatMap(page => page.commits || []) || [];

  const handleCommitSelect = useCallback(
    async (hash: string) => {
      setSelectedFile(null);
      setSelectedCommit(hash);
      await refetchCommitDiff();
    },
    [setSelectedFile, setSelectedCommit, refetchCommitDiff]
  );

  // Handle loading more commits when scrolling
  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Refetch when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger > 0) {
      refetch().then(result => {
        // Add safe checks to prevent accessing properties of undefined
        const commits = result?.data?.pages?.[0]?.commits;
        if (commits && commits.length > 0) {
          handleCommitSelect(commits[0].hash);
        }
      });
    }
  }, [refreshTrigger, refetch, handleCommitSelect]);

  // Select first commit on initial data load
  useEffect(() => {
    const commits = commitsData?.pages[0]?.commits;
    if (commits && commits.length > 0 && !selectedCommit && refreshTrigger === 0) {
      handleCommitSelect(commits[0].hash);
    }
  }, [commitsData, handleCommitSelect, selectedCommit, refreshTrigger]);

  const handleFileSelect = async (hash: string, file: string) => {
    setSelectedFile(file);
    await refetchFileDiff();
  };

  const toggleFold = (index: number) => {
    setFoldedFiles(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  // Get the appropriate diff content based on whether a file is selected
  const diffContents = selectedFile ? [fileDiffData?.diff] : commitDiffData?.changes || [];

  // Show message if no files were changed
  const noFilesChanged =
    !selectedFile && diffContents.length === 0 && (commitDiffData?.changes?.length || 0) > 0;

  // Set up virtualizer for the diff list
  const virtualizer = useVirtualizer({
    count: diffContents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 500,
    overscan: 5, // Increased overscan
    measureElement: element => {
      // Return initial measurement
      const height = element.getBoundingClientRect().height;
      return Math.max(height, 100); // Ensure minimum height
    },
  });

  return (
    <ErrorBoundary fallback={<div>Something went wrong</div>}>
      <div className="grid h-full grid-cols-[auto_1fr] overflow-hidden">
        <Resizable
          className="overflow-hidden"
          onResize={(_event, _direction, ref) => {
            setExplorerWidth(`${ref.offsetWidth}px`);
          }}
          size={{
            width: explorerWidth,
            height: '100%',
          }}
          minWidth="200px"
          maxWidth="400px"
          enable={{ right: dir === 'ltr', left: dir === 'rtl' }}
          defaultSize={{
            width: explorerWidth,
            height: '100%',
          }}
        >
          <div className="h-full border-e border-border px-1">
            <ScrollArea className="h-full">
              <div className="min-w-[200px]">
                {!commitsData ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="flex items-center">
                      <Spinner />
                    </div>
                  </div>
                ) : (
                  <CommitsList
                    commits={commits}
                    onCommitSelect={handleCommitSelect}
                    onFileSelect={handleFileSelect}
                    isLoadingMore={isFetchingNextPage}
                    onLoadMore={hasNextPage ? handleLoadMore : undefined}
                  />
                )}
              </div>
              <ScrollBar orientation="vertical" />
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          </div>
        </Resizable>

        <div className="relative grid h-full grid-rows-[auto_1fr] overflow-hidden">
          {selectedCommit && (
            <div className="border-b">
              <div className="p-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {selectedFile ? selectedFile : `Changes in ${selectedCommit}`}
                </h3>
              </div>
            </div>
          )}
          <div className="min-h-0 overflow-auto">
            {isLoading ? (
              <div className="flex h-full items-center justify-center">
                <Spinner />
              </div>
            ) : !selectedCommit ? (
              <div className="p-4">Select a commit to view changes</div>
            ) : noFilesChanged ? (
              <div className="p-4">No files were changed in this commit</div>
            ) : (
              <div className="h-full p-4">
                <div ref={parentRef} className="relative h-full overflow-auto">
                  <div
                    className="w-full"
                    style={{
                      height: `${virtualizer.getTotalSize()}px`,
                      position: 'relative',
                    }}
                  >
                    {virtualizer.getVirtualItems().map(virtualItem => {
                      const diffContent = diffContents[virtualItem.index];
                      const isFolded = foldedFiles.has(virtualItem.index);
                      return (
                        <div
                          key={virtualItem.key}
                          ref={virtualizer.measureElement}
                          data-index={virtualItem.index}
                          className="absolute left-0 w-full rounded-lg bg-white shadow"
                          style={{
                            transform: `translateY(${virtualItem.start}px)`,
                            marginBottom: '1rem',
                            display: 'flex',
                            flexDirection: 'column',
                          }}
                        >
                          {/* File header with toggle functionality */}
                          <div
                            className="flex cursor-pointer items-center justify-between border-b px-4 py-2 hover:bg-gray-50"
                            onClick={() => toggleFold(virtualItem.index)}
                          >
                            <h4 className="text-sm font-medium">
                              {diffContent?.path || 'unknown'}
                            </h4>
                            <span className="text-xs text-gray-500">
                              {isFolded ? 'Show' : 'Hide'}
                            </span>
                          </div>

                          {/* Render the diff only when not folded */}
                          {!isFolded && (
                            <div className="flex-grow">
                              <CodeMergeView
                                fileName={diffContent?.path || 'unknown'}
                                oldText={diffContent?.old_text || ''}
                                newText={diffContent?.new_text || ''}
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
