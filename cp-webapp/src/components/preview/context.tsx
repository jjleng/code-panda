'use client';

import React, { createContext, useCallback, useContext, useState } from 'react';

interface PreviewContextType {
  previewPath: string;
  setPreviewPath: (path: string) => void;
  refreshCounter: number;
  triggerRefresh: () => void;
  pathsRefreshCounter: number;
  triggerPathsRefresh: () => void;
}

// Initialize with undefined like code-view context
const PreviewContext = createContext<PreviewContextType | undefined>(undefined);

export function usePreviewContext() {
  const context = useContext(PreviewContext);
  if (context === undefined) {
    throw new Error('usePreviewContext must be used within a PreviewProvider');
  }
  return context;
}

export const PreviewProvider = ({ children }: { children?: React.ReactNode }) => {
  const [previewPath, setPreviewPath] = useState('/');
  const [refreshCounter, setRefreshCounter] = useState(0);
  const [pathsRefreshCounter, setPathsRefreshCounter] = useState(0);

  const triggerRefresh = useCallback(() => {
    setRefreshCounter(prev => prev + 1);
  }, []);

  const triggerPathsRefresh = useCallback(() => {
    setPathsRefreshCounter(prev => prev + 1);
  }, []);

  return (
    <PreviewContext.Provider
      value={{
        previewPath,
        setPreviewPath,
        refreshCounter,
        triggerRefresh,
        pathsRefreshCounter,
        triggerPathsRefresh,
      }}
    >
      {children}
    </PreviewContext.Provider>
  );
};
