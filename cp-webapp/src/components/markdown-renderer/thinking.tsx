import React, { memo } from 'react';
import { cn } from '@/lib/utils';
import styles from './markdown-renderer.module.css';

interface ThinkingProps {
  children: React.ReactNode;
  content?: string;
}

const Thinking = memo(({ children }: ThinkingProps) => {
  return (
    <div className="my-2 rounded border-l-4 border-muted-foreground bg-muted/30 p-3">
      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground/70">
        thinking
      </div>

      <div className={cn('text-muted-foreground', styles.nestedMarkdown)}>
        {React.Children.map(children, child => {
          return child;
        })}
      </div>
    </div>
  );
});

Thinking.displayName = 'Thinking';

export { Thinking, type ThinkingProps };
