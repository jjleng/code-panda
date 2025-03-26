'use client';

import React, { createContext, useContext, useState } from 'react';

export interface MergeViewProps {
  fileName: string;
  oldText: string;
  newText: string;
}

interface MergeViewContextType {
  showMergeView: boolean;
  setShowMergeView: (show: boolean) => void;
  mergeViewProps: MergeViewProps | null;
  setMergeViewProps: (props: MergeViewProps | null) => void;
}

const MergeViewContext = createContext<MergeViewContextType | undefined>(undefined);

export function useMergeViewContext() {
  const context = useContext(MergeViewContext);
  if (context === undefined) {
    throw new Error('useMergeViewContext must be used within a MergeViewProvider');
  }
  return context;
}

export function MergeViewProvider({ children }: { children?: React.ReactNode }) {
  const [showMergeView, setShowMergeView] = useState(false);
  const [mergeViewProps, setMergeViewProps] = useState<MergeViewProps | null>(null);

  return (
    <MergeViewContext.Provider
      value={{
        showMergeView,
        setShowMergeView,
        mergeViewProps,
        setMergeViewProps,
      }}
    >
      {children}
    </MergeViewContext.Provider>
  );
}
