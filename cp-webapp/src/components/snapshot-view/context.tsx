'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useMutation } from '@tanstack/react-query';
import { switchCommitApiV1ProjectsProjectIdSwitchCommitPostMutation } from '@/generated/agent/@tanstack/react-query.gen';
import { useToast } from '@/hooks/use-toast';
import { useProject } from '@/context';

interface SnapshotContextType {
  selectedCommit: string | null;
  setSelectedCommit: (commit: string | null) => void;
  selectedFile: string | null;
  setSelectedFile: (file: string | null) => void;
  commitDiff: string | null;
  setCommitDiff: (diff: string | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  refreshTrigger: number;
  triggerRefresh: () => void;
  switchingCommit: boolean;
  setSwitchingCommit: (inProgress: boolean) => void;
  switchToCommit: (hash: string) => Promise<void>;
}

const SnapshotContext = createContext<SnapshotContextType | undefined>(undefined);

export function SnapshotProvider({ children }: { children?: ReactNode }) {
  const [selectedCommit, setSelectedCommit] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [commitDiff, setCommitDiff] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [switchingCommit, setSwitchingCommit] = useState(false);
  const { projectId } = useProject();

  const { toast } = useToast();

  const switchCommitMutate = useMutation(
    switchCommitApiV1ProjectsProjectIdSwitchCommitPostMutation()
  );

  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const switchToCommit = async (hash: string) => {
    if (!projectId) return;

    try {
      setSwitchingCommit(true);
      await switchCommitMutate.mutateAsync({
        path: {
          project_id: projectId,
        },
        body: {
          commit_hash: hash,
        },
      });
      triggerRefresh();
    } catch (error) {
      console.error('Failed to switch to commit:', error);
      toast({
        variant: 'destructive',
        title: 'Error switching commit',
        description: error instanceof Error ? error.message : 'Failed to switch commit',
      });
      throw error;
    } finally {
      setSwitchingCommit(false);
    }
  };

  return (
    <SnapshotContext.Provider
      value={{
        selectedCommit,
        setSelectedCommit,
        selectedFile,
        setSelectedFile,
        commitDiff,
        setCommitDiff,
        isLoading,
        setIsLoading,
        refreshTrigger,
        triggerRefresh,
        switchingCommit,
        setSwitchingCommit,
        switchToCommit,
      }}
    >
      {children}
    </SnapshotContext.Provider>
  );
}

export function useSnapshotContext() {
  const context = useContext(SnapshotContext);
  if (context === undefined) {
    throw new Error('useSnapshotContext must be used within a SnapshotProvider');
  }
  return context;
}
