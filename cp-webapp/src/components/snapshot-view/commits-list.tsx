'use client';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Commit } from '@/generated/runner/types.gen';
import { GitCommit } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useSnapshotContext } from './context';
import { convertToISO8601 } from '@/lib/utils';

interface CommitsListProps {
  commits: Commit[];
  onCommitSelect: (hash: string) => void;
  onFileSelect: (hash: string, file: string) => void;
  isLoadingMore?: boolean;
  onLoadMore?: () => void;
}

export const CommitsList: React.FC<CommitsListProps> = ({
  commits,
  onCommitSelect,
  onFileSelect,
  isLoadingMore = false,
  onLoadMore,
}) => {
  const { selectedCommit, selectedFile, switchToCommit, setSelectedCommit } = useSnapshotContext();
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [pendingCommitHash, setPendingCommitHash] = useState<string | null>(null);
  const loaderRef = React.useRef<HTMLDivElement>(null);

  // Radio selection only changes when explicitly clicked
  const [radioSelection, setRadioSelection] = useState<string>('');

  // Update radio selection only when commits array changes
  useEffect(() => {
    if (commits.length > 0) {
      setRadioSelection(commits[0].hash);
    }
  }, [commits]);

  // Intersection observer for infinite scroll
  useEffect(() => {
    if (!onLoadMore) return;

    const observer = new IntersectionObserver(
      entries => {
        const first = entries[0];
        if (first.isIntersecting && !isLoadingMore) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    const currentLoaderRef = loaderRef.current;
    if (currentLoaderRef) {
      observer.observe(currentLoaderRef);
    }

    return () => {
      if (currentLoaderRef) {
        observer.unobserve(currentLoaderRef);
      }
    };
  }, [onLoadMore, isLoadingMore]);

  const handleRadioClick = (e: React.MouseEvent, hash: string) => {
    e.preventDefault();
    e.stopPropagation();
    setPendingCommitHash(hash);
    setIsAlertOpen(true);
  };

  const handleConfirm = async () => {
    if (pendingCommitHash) {
      await switchToCommit(pendingCommitHash);
      setSelectedCommit(pendingCommitHash);
      setRadioSelection(pendingCommitHash);
      onCommitSelect(pendingCommitHash);
    }
    setPendingCommitHash(null);
    setIsAlertOpen(false);
  };

  return (
    <>
      <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Switch Commit</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to switch to this commit? This will update your working
              directory.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPendingCommitHash(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm}>Continue</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="w-full">
        <RadioGroup value={radioSelection} className="w-full">
          <Accordion type="single" collapsible className="w-full">
            {commits.map(commit => (
              <AccordionItem key={commit.hash} value={commit.hash}>
                <div className="relative">
                  <AccordionTrigger
                    onClick={() => {
                      // Only handle accordion toggle, not radio selection
                      onCommitSelect(commit.hash);
                    }}
                    className={`w-full px-2 hover:bg-gray-100 hover:no-underline dark:hover:bg-gray-800 ${
                      selectedCommit === commit.hash ? 'bg-gray-50 dark:bg-gray-900' : ''
                    }`}
                  >
                    <div className="flex w-full items-center gap-2">
                      <TooltipProvider>
                        <Tooltip delayDuration={0}>
                          <TooltipTrigger asChild>
                            <div onClick={e => e.stopPropagation()}>
                              <RadioGroupItem
                                value={commit.hash}
                                id={commit.hash}
                                onClick={e => handleRadioClick(e, commit.hash)}
                              />
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Switch to this commit</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      <div className="min-w-0 flex-1 text-left">
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1 font-mono text-sm text-gray-500 dark:text-gray-400">
                            <GitCommit className="h-3.5 w-3.5" />
                            {commit.hash.slice(0, 7)}
                          </div>
                        </div>
                        <div className="line-clamp-2 break-words text-sm">{commit.message}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(convertToISO8601(commit.date)).toLocaleString(undefined, {
                            year: 'numeric',
                            month: 'numeric',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="flex flex-col gap-2 py-2 pl-6">
                      <div className="space-y-1">
                        {commit.files?.map(file => (
                          <div
                            key={file.path}
                            onClick={() => onFileSelect(commit.hash, file.path)}
                            className={`cursor-pointer rounded p-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 ${
                              selectedFile === file.path ? 'bg-gray-100 dark:bg-gray-800' : ''
                            }`}
                          >
                            {file.path}
                          </div>
                        ))}
                      </div>
                    </div>
                  </AccordionContent>
                </div>
              </AccordionItem>
            ))}
          </Accordion>
        </RadioGroup>

        {onLoadMore && (
          <div ref={loaderRef} className="py-4 text-center">
            {isLoadingMore && (
              <div className="flex justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-500 border-t-transparent"></div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};
