import { CopyButton } from '@/components/copy-button';
import { cn } from '@/lib/utils';
import React, { memo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeProps {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  fullHeight?: boolean;
}

const Code = memo(({ inline, className, children, fullHeight, ...props }: CodeProps) => {
  const match = /language-(\w+)/.exec(className || '');

  if (inline || !match) {
    return <code className={cn(className)}>{children}</code>;
  }

  const codeString = String(children).replace(/\n$/, '');
  const language = match[1];

  return (
    <div
      className={cn('relative flex flex-1 flex-col overflow-hidden', {
        'h-full': fullHeight,
      })}
    >
      <div className="flex flex-shrink-0 items-center justify-between p-1 px-3">
        <div aria-label="Language">{language}</div>
        <CopyButton code={codeString} />
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
        className={cn('custom-scrollbar min-w-full flex-1 overflow-auto')}
        customStyle={
          fullHeight
            ? {
                margin: 0,
                height: '100%',
                maxHeight: '100%',
              }
            : {}
        }
        {...props}
      >
        {codeString}
      </SyntaxHighlighter>
    </div>
  );
});

Code.displayName = 'Code';

export { Code, type CodeProps };
