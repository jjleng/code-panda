'use client';

import { Spinner } from '@/components/spinner';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { ProvisioningState, useProject } from '@/context';
import { FileNode } from '@/generated/runner';
import { getFileTreeOptions } from '@/generated/runner/@tanstack/react-query.gen';
import { useToast } from '@/hooks/use-toast';
import { useDirection } from '@radix-ui/react-direction';
import { useQuery } from '@tanstack/react-query';
import { EditorView } from '@uiw/react-codemirror';
import { Resizable } from 're-resizable';
import React, { Component, PropsWithChildren, useEffect, useMemo, useRef, useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { CodeRenderer } from './code-renderer';
import { useCodeViewContext } from './context';
import { FileExplorer, FileSystemNode } from './file-explorer';

interface RenderContentProps {
  isLoading: boolean;
  fileContent: string | null;
  selectedFile: string | null;
  mimeType: string | null;
  editorRef: React.RefObject<EditorView | null>;
}

const transformFileTree = (node: FileNode): FileSystemNode => ({
  name: node.name,
  type: node.type === 'folder' ? 'folder' : 'file',
  children: node.children?.map(transformFileTree),
});

interface ImageRendererProps {
  content: string;
}

const ImageRenderer = React.memo(({ content }: ImageRendererProps) => {
  return (
    <ScrollArea className="flex h-full items-center justify-center p-4">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`data:image/*;base64,${content}`}
        className="max-h-full max-w-full object-contain"
        alt="File preview"
      />
      <ScrollBar orientation="vertical" />
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );
});

ImageRenderer.displayName = 'ImageRenderer';

interface DownloadableFileProps {
  filename: string;
  content: string;
}

const DownloadableFile = React.memo(({ filename, content }: DownloadableFileProps) => {
  const handleDownload = () => {
    try {
      const blob = new Blob([Buffer.from(content, 'base64')]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename.split('/').pop() || 'download';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      // Handle error appropriately
    }
  };

  return (
    <div className="flex items-center justify-center p-8">
      <button
        onClick={handleDownload}
        className="flex items-center space-x-2 rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
      >
        <span>Download {filename.split('/').pop()}</span>
      </button>
    </div>
  );
});

DownloadableFile.displayName = 'DownloadableFile';

const RenderContent: React.FC<RenderContentProps> = ({
  isLoading,
  fileContent,
  selectedFile,
  mimeType,
  editorRef,
}) => {
  if (isLoading) {
    return (
      <div role="status" aria-label="Loading content">
        Loading...
      </div>
    );
  }

  if (!fileContent || !selectedFile) {
    return (
      <div className="p-4" role="status">
        Select a file to view
      </div>
    );
  }

  if (
    mimeType?.startsWith('text/') ||
    mimeType?.includes('javascript') ||
    mimeType?.includes('json')
  ) {
    return <CodeRenderer editorRef={editorRef} />;
  }

  if (mimeType?.startsWith('image/')) {
    return <ImageRenderer content={fileContent} />;
  }

  return <DownloadableFile filename={selectedFile} content={fileContent} />;
};

function CodeViewNoContext() {
  const { toast } = useToast();
  const editorRef = useRef<EditorView | null>(null);
  const [explorerWidth, setExplorerWidth] = useState<string>('300px');
  const { selectedFile, setSelectedFile, fileContent, isLoading, mimeType, refreshTrigger } =
    useCodeViewContext();
  const { projectId, provisioningState } = useProject();

  const dir = useDirection();

  const {
    data: fileTreeData,
    error: fileTreeError,
    refetch,
  } = useQuery({
    ...getFileTreeOptions({
      query: {
        project_id: projectId!,
      },
    }),
    enabled: projectId != null && provisioningState === ProvisioningState.PROVISIONED,
  });

  useEffect(() => {
    if (fileTreeError) {
      toast({
        variant: 'destructive',
        title: 'Error loading file tree',
        description:
          fileTreeError instanceof Error ? fileTreeError.message : 'Failed to load file tree',
      });
    }
  }, [fileTreeError, toast]);

  // refetch when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger > 0) {
      refetch();
    }
  }, [refreshTrigger, refetch]);

  const fileTree = useMemo(
    () => (fileTreeData?.root ? transformFileTree(fileTreeData.root) : null),
    [fileTreeData]
  );

  const isFileTreeLoading = !fileTree && !fileTreeError;

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
          <div className="h-full border-e border-border pe-1">
            <ScrollArea className="h-full">
              <div className="min-w-[200px]">
                {isFileTreeLoading ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="flex items-center">
                      <Spinner />
                    </div>
                  </div>
                ) : fileTree ? (
                  <FileExplorer
                    data={fileTree}
                    onFileSelect={path => {
                      setSelectedFile(path);
                    }}
                  />
                ) : null}
              </div>
              <ScrollBar orientation="vertical" />
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          </div>
        </Resizable>

        <div className="relative grid h-full grid-rows-[auto_1fr] overflow-hidden">
          {selectedFile && (
            <div className="border-b">
              <div className="p-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {selectedFile}
                </h3>
              </div>
            </div>
          )}
          <div className="min-h-0 overflow-hidden">
            <RenderContent
              isLoading={isLoading || isFileTreeLoading}
              fileContent={fileContent}
              selectedFile={selectedFile}
              mimeType={mimeType}
              editorRef={editorRef}
            />
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

interface CodeViewErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class CodeViewErrorBoundary extends Component<PropsWithChildren, CodeViewErrorBoundaryState> {
  state: CodeViewErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: unknown): CodeViewErrorBoundaryState {
    return {
      hasError: true,
      error: error instanceof Error ? error : new Error(String(error)),
    };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-red-600 dark:text-red-400">
          <h3 className="font-semibold">Error loading content</h3>
          <p className="text-sm">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-2 text-sm underline"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export function CodeView() {
  return (
    <CodeViewErrorBoundary>
      <CodeViewNoContext />
    </CodeViewErrorBoundary>
  );
}
