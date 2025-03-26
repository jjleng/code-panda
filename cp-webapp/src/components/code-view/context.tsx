'use client';

import { ProvisioningState, useProject } from '@/context';
import { getFileContentOptions } from '@/generated/runner/@tanstack/react-query.gen';
import { useToast } from '@/hooks/use-toast';
import { useQuery } from '@tanstack/react-query';
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

interface CodeViewContextType {
  selectedFile: string | null;
  setSelectedFile: (file: string | null) => void;
  fileContent: string | null;
  fileContentError: Error | null;
  isLoading: boolean;
  mimeType: string | null;
  refreshTrigger: number;
  triggerRefresh: () => void;
}

const CodeViewContext = createContext<CodeViewContextType | undefined>(undefined);

// Utility function to get relative path
const getRelativePath = (fullPath: string | null): string | null => {
  if (!fullPath) return null;
  const parts = fullPath.split('/');
  return parts.slice(1).join('/');
};

export function useCodeViewContext() {
  const context = useContext(CodeViewContext);
  if (context === undefined) {
    throw new Error('useCodeViewContext must be used within a CodeViewProvider');
  }
  return context;
}

export function CodeViewProvider({ children }: { children?: React.ReactNode }) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const { toast } = useToast();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const triggerRefresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, [setRefreshTrigger]);
  const { projectId, provisioningState } = useProject();

  const {
    data: fileContent,
    error: fileContentError,
    isLoading,
    refetch: refetchFileContent,
  } = useQuery({
    ...getFileContentOptions({
      query: {
        project_id: projectId!,
        file_path: getRelativePath(selectedFile)!,
      },
    }),
    enabled: !!selectedFile && !!projectId && provisioningState === ProvisioningState.PROVISIONED,
  });

  useEffect(() => {
    if (refreshTrigger > 0 && selectedFile) {
      refetchFileContent();
    }
  }, [refreshTrigger, selectedFile, refetchFileContent]);

  // Show toast on error
  useEffect(() => {
    if (fileContentError) {
      toast({
        variant: 'destructive',
        title: 'Error loading file content',
        description:
          fileContentError instanceof Error
            ? fileContentError.message
            : 'Failed to load file content',
      });
    }
  }, [fileContentError, toast]);

  return (
    <CodeViewContext.Provider
      value={{
        selectedFile,
        setSelectedFile,
        fileContent: fileContent?.content ?? null,
        fileContentError,
        isLoading,
        mimeType: fileContent?.mime_type ?? null,
        refreshTrigger,
        triggerRefresh,
      }}
    >
      {children}
    </CodeViewContext.Provider>
  );
}
