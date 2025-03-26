'use client';

import { X } from 'lucide-react';
import { useEffect } from 'react';
import { CodeMergeView } from '../code-view/code-renderer';
import { useMergeViewContext } from './context';

export function MergeViewOverlay() {
  const { showMergeView, setShowMergeView, mergeViewProps } = useMergeViewContext();

  // Add event listener for ESC key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowMergeView(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [setShowMergeView]);

  if (!showMergeView || !mergeViewProps) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
      onClick={() => setShowMergeView(false)}
    >
      <div
        className="fixed inset-16 z-50 flex flex-col overflow-hidden rounded-lg border bg-background shadow-lg"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">File Changes: {mergeViewProps.fileName}</h2>
          <button
            onClick={() => setShowMergeView(false)}
            className="rounded-full p-2 transition-colors hover:bg-accent"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-6">
          <CodeMergeView {...mergeViewProps} />
        </div>
      </div>
    </div>
  );
}
