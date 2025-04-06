import { Button } from '@/components/ui/button';
import { useProject } from '@/context';
import { useSqlBlock } from '@/context/sql-block-context';
import { executeMigrationApiV1ProjectsProjectIdMigrationsPostMutation } from '@/generated/agent/@tanstack/react-query.gen';
import { useToast } from '@/hooks/use-toast';
import { useMutation } from '@tanstack/react-query';
import { AlertCircle, CheckCircle2, Play } from 'lucide-react';
import React, { memo, useCallback } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

export type SqlBlockStatus = 'not_started' | 'success' | 'error';

export interface SqlBlockProps {
  children: React.ReactNode;
  status?: string; // Will be "success", "error", or undefined/"not_started"
  id?: string; // Unique identifier for the SQL block
}

// Helper function to extract SQL text from React nodes recursively
const extractSqlText = (node: React.ReactNode): string => {
  if (typeof node === 'string') {
    // Replace HTML encoded newlines with actual newlines
    return node.replace(/&#10;/g, '\n').replace(/&amp;#10;/g, '\n');
  }
  if (typeof node === 'number' || typeof node === 'boolean') return String(node);
  if (node == null) return '';

  if (Array.isArray(node)) {
    return node.map(extractSqlText).join('');
  }

  if (React.isValidElement(node)) {
    const props = node.props as { children?: React.ReactNode };
    return extractSqlText(props.children);
  }

  return '';
};

const SqlBlock = memo(({ children, status = 'not_started', id }: SqlBlockProps) => {
  // Extract the SQL code as a string from children using our helper function
  const rawSqlCode = extractSqlText(children);

  const sqlCode = rawSqlCode.replace(/−−/g, '--'); // Replace Unicode minus-minus with standard dashes

  // Get context for handling migrations, streaming state, and requesting fixes
  const { updateSqlBlockStatus, isStreaming, requestFixMessage } = useSqlBlock();
  const { projectId } = useProject();
  const { toast } = useToast();

  // Set up the mutation for executing SQL migrations
  const migrationMutation = useMutation(
    executeMigrationApiV1ProjectsProjectIdMigrationsPostMutation()
  );

  const handleMigrate = useCallback(async () => {
    if (!id || !projectId) {
      console.error('Cannot migrate SQL block: missing ID or project ID');
      return;
    }

    // Update status to indicate processing
    updateSqlBlockStatus(id, 'not_started');

    try {
      // Execute the SQL migration via API
      const result = await migrationMutation.mutateAsync({
        headers: {
          'X-CP-Project-ID': projectId,
        },
        path: {
          project_id: projectId,
        },
        body: {
          sql: sqlCode,
          name: `Migration from SQL block <sql-block>${sqlCode}</sql-block>`,
        },
      });

      if (result.success) {
        // Update status to success
        updateSqlBlockStatus(id, 'success');

        toast({
          title: 'SQL Migration Successful',
          description: 'The SQL migration was executed successfully.',
        });
      } else {
        // Update status to error
        updateSqlBlockStatus(id, 'error');

        toast({
          title: 'SQL Migration Failed',
          description: result.error || 'The SQL migration failed to execute.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error executing SQL migration:', error);

      // Update status to error
      updateSqlBlockStatus(id, 'error');

      toast({
        title: 'SQL Migration Failed',
        // @ts-expect-error ignore
        description: error?.detail ?? 'An unknown error occurred',
        variant: 'destructive',
      });
    }
  }, [id, projectId, sqlCode, updateSqlBlockStatus, migrationMutation, toast]);

  const requestMigrationFix = useCallback(async () => {
    if (!id || !projectId) {
      console.error('Cannot request migration fix: missing ID or project ID');
      return;
    }

    const messageContent = `The previous migration attempt failed. Please review the error message and provide a corrected sql block`;

    try {
      requestFixMessage(messageContent);

      toast({
        title: 'Request Sent',
        description: 'Asked the assistant to fix the failed SQL migration.',
      });
    } catch (error) {
      console.error('Error sending message to agent:', error);
      toast({
        title: 'Error Sending Request',
        description: 'Could not ask the assistant for a fix.',
        variant: 'destructive',
      });
    }
  }, [id, projectId, requestFixMessage, toast]);

  // Render the appropriate button based on status
  const renderButton = () => {
    switch (status) {
      case 'success':
        return (
          <Button
            variant="outline"
            size="sm"
            className="flex w-full items-center justify-center gap-2 opacity-70"
            disabled={true}
          >
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-xs">Migrated</span>
          </Button>
        );
      case 'error':
        return (
          <Button
            onClick={requestMigrationFix}
            variant="outline"
            size="sm"
            className="flex w-full items-center justify-center gap-2 bg-red-50"
            disabled={!id || isStreaming || migrationMutation.isPending}
          >
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="text-xs">
              {migrationMutation.isPending ? 'Migrating...' : 'Retry Migration'}
            </span>
          </Button>
        );
      default: // not_started
        return (
          <Button
            onClick={handleMigrate}
            variant="outline"
            size="sm"
            className="flex w-full items-center justify-center gap-2"
            disabled={!id || isStreaming || migrationMutation.isPending}
          >
            <Play className="h-4 w-4" />
            <span className="text-xs">
              {migrationMutation.isPending ? 'Migrating...' : 'Migrate'}
            </span>
          </Button>
        );
    }
  };

  return (
    <div className="my-4">
      <div className="overflow-hidden rounded-md">
        <SyntaxHighlighter
          language="sql"
          style={oneDark}
          customStyle={{ borderRadius: '0.375rem', margin: '0' }}
          wrapLongLines={true}
        >
          {sqlCode}
        </SyntaxHighlighter>
      </div>

      <div className="mt-2 flex justify-between">
        <div className="flex w-full flex-col">
          {renderButton()}
          {status === 'not_started' && !migrationMutation.isPending && (
            <span className="mt-1 text-xs text-muted-foreground">
              <b>Click</b> to apply these changes to your database. Please exercise caution as
              database changes are critical.
            </span>
          )}
          {status === 'error' && migrationMutation.error && (
            <div className="ml-2 mt-1 max-w-sm truncate text-xs text-red-500">
              {/* @ts-expect-error ignore */}
              {migrationMutation.error?.detail ?? 'Unknown error occurred'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

SqlBlock.displayName = 'SqlBlock';

export { SqlBlock };
