'use client';

import { cn } from '@/lib/utils';
import { Spinner } from './spinner';

interface WorkspaceProvisioningOverlayProps {
  message: string;
  className?: string;
}

export function WorkspaceProvisioningOverlay({
  message,
  className,
}: WorkspaceProvisioningOverlayProps) {
  return (
    <div
      className={cn(
        'absolute inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background/80 backdrop-blur-sm',
        className
      )}
    >
      <Spinner className="h-8 w-8" />
      <p className="text-lg font-medium text-muted-foreground">{message}</p>
    </div>
  );
}
