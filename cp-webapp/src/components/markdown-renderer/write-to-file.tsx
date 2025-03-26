import { useMergeViewContext } from '@/components/merge-view/context';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { base64ToString } from '@/lib/base64';
import { Check, Loader2, X } from 'lucide-react';
import { memo, useEffect, useState } from 'react';

interface WriteToFileProps {
  path: string;
  id: string;
  status: string;
  toolName: 'write-to-file' | 'apply-diff';
  old_content?: string;
  new_content?: string;
}

const WriteToFile = memo(
  ({ path, id, status, toolName, old_content, new_content }: WriteToFileProps) => {
    const [oldContent, setOldContent] = useState<string | undefined>(old_content);
    const [newContent, setNewContent] = useState<string | undefined>(new_content);
    const { setShowMergeView, setMergeViewProps } = useMergeViewContext();

    useEffect(() => {
      setOldContent(old_content ? base64ToString(old_content) : undefined);
      setNewContent(new_content ? base64ToString(new_content) : undefined);
    }, [old_content, new_content]);

    const canShowDiff = status === 'completed';

    const handleClick = () => {
      if (canShowDiff) {
        setMergeViewProps({
          fileName: path,
          oldText: oldContent || '',
          newText: newContent || '',
        });
        setShowMergeView(true);
      }
    };

    // We show the same title for both write-to-file and apply-diff
    const title = toolName === 'write-to-file' ? 'Writing File' : 'Writing File';

    return (
      <Card
        className={`my-0.5 ${canShowDiff ? 'cursor-pointer hover:bg-accent' : ''}`}
        key={id}
        onClick={canShowDiff ? handleClick : undefined}
      >
        <CardHeader className="flex flex-row items-center space-y-0 py-2">
          <div className="flex min-w-0 flex-1 flex-col space-y-0">
            <CardTitle className="text-sm">{title}</CardTitle>
            <p className="truncate text-xs text-muted-foreground">{path}</p>
          </div>
          <div className="ml-3 flex-shrink-0">
            {status === 'started' && <Loader2 className="h-4 w-4 animate-spin" />}
            {status === 'completed' && <Check className="h-4 w-4" />}
            {status === 'failed' && <X className="h-4 w-4 text-destructive" />}
          </div>
        </CardHeader>
      </Card>
    );
  }
);

WriteToFile.displayName = 'WriteToFile';

export { WriteToFile, type WriteToFileProps };
