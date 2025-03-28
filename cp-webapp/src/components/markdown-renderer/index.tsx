import { cn } from '@/lib/utils';
import React, { memo, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import type { Plugin } from 'unified';
import { Code } from './code';
import { Mermaid } from './mermaid';
import { ResourceLink, Resources, type ResourceLinkProps, type ResourcesProps } from './resources';
import { SecretInput, type SecretInputProps } from './secret-input';
import { SqlBlock, type SqlBlockProps } from './sql-block';
import { Thinking, type ThinkingProps } from './thinking';
import { WriteToFile, type WriteToFileProps } from './write-to-file';

import 'katex/dist/katex.min.css';
import styles from './markdown-renderer.module.css';

const remarkPlugins: Array<[Plugin, object]> = [
  [remarkGfm, {}],
  [remarkMath, { singleDollarTextMath: false }],
];

interface Props {
  text: string;
  streaming: boolean;
  fullHeight?: boolean;
}
type Components = import('react-markdown').Components & {
  resources: React.ComponentType<ResourcesProps>;
  'resource-link': React.ComponentType<ResourceLinkProps>;
  'write-to-file': React.ComponentType<WriteToFileProps>;
  'apply-diff': React.ComponentType<WriteToFileProps>;
  thinking: React.ComponentType<ThinkingProps>;
  'secret-input': React.ComponentType<SecretInputProps>;
  'sql-block': React.ComponentType<SqlBlockProps>;
};

function processContent(content: string): string {
  return content
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '  ')
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\\\/g, '\\')
    .replace(/(\d+\.)([^\s])/g, '$1 $2')
    .replace(/([^\n])(\n+)(\d+\.)/g, '$1\n\n$3')
    .replace(/^(?=- )/gm, '\n')
    .replace(/([^\n])(\n\d+\.)/g, '$1\n\n$2')
    .replace(/(\n\d+\.\s+[^\n]+)(\n\d+\.)/g, '$1\n$2')
    .replace(/(\n\d+\.\s+[^\n]+)(\n{3,})(\d+\.)/g, '$1\n\n$3');
}

const MarkdownRenderer: React.FC<Props> = memo(({ text: rawText, streaming, fullHeight }) => {
  // Pre-process text to wrap custom elements in special markers that won't break markdown parsing
  const text = useMemo(() => {
    // Replace custom elements with properly formatted HTML comments that won't break parsing
    // but can be restored later via the components prop
    // Handle self-closing tags like <apply-diff/>
    let processedText = rawText.replace(
      /<(apply-diff|write-to-file|secret-input)([^>]*?)\/>/g,
      (match, tag, attributes) => {
        // Wrap in div to ensure markdown continues parsing after the element
        return `<div class='my-1'>\n<${tag}${attributes}/>\n</div>`;
      }
    );

    // Handle thinking tags with content
    processedText = processedText.replace(/<thinking>([\s\S]*?)<\/thinking>/g, (match, content) => {
      // Wrap thinking tags with their content in a div
      return `<div>\n<thinking>${processContent(content)}</thinking>\n</div>`;
    });

    // Handle SQL block tags with content
    processedText = processedText.replace(
      /<sql-block(?:\s+([^>]*))>([\s\S]*?)<\/sql-block>/g,
      (match, attributes, content) => {
        // Preserve all attributes
        let attrs = attributes ? ` ${attributes}` : '';
        // Set default status if not specified
        if (!attrs.includes('status=')) {
          attrs += ' status="not_started"';
        }
        // Format SQL content to preserve newlines
        const formattedContent = content.replace(/\n/g, '&#10;');
        return `<div>\n<sql-block${attrs}>${formattedContent}</sql-block>\n</div>`;
      }
    );

    return processedText;
  }, [rawText]);
  const components: Components = {
    pre: (props: React.HTMLAttributes<HTMLPreElement>) => {
      const isMermaid = React.Children.toArray(props.children).some(
        child =>
          React.isValidElement(child) &&
          'props' in child &&
          (child.props as { className?: string })?.className === 'language-mermaid'
      );
      return (
        <pre className={cn({ 'h-full': fullHeight, 'not-prose': isMermaid })}>{props.children}</pre>
      );
    },
    code: props => {
      if (props.className === 'language-mermaid') {
        return <Mermaid chart={props.children as string} />;
      }
      return <Code {...props} fullHeight={fullHeight} />;
    },
    resources: Resources,
    'resource-link': ResourceLink,
    'write-to-file': props => <WriteToFile {...props} toolName="write-to-file" />,
    'apply-diff': props => <WriteToFile {...props} toolName="apply-diff" />,
    thinking: Thinking,
    'secret-input': SecretInput,
    'sql-block': SqlBlock,
  };

  return (
    <div
      className={cn(styles.markdownRenderer, 'flex max-w-full flex-col', {
        'h-full': fullHeight,
        [styles.resultStreaming]: streaming,
      })}
    >
      <ReactMarkdown
        className={cn('flex flex-col', { 'h-full': fullHeight })}
        remarkPlugins={remarkPlugins}
        rehypePlugins={[
          rehypeRaw,
          [
            rehypeKatex,
            {
              strict: false,
            },
          ],
        ]}
        components={components}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
});

MarkdownRenderer.displayName = 'MarkdownRenderer';

export { MarkdownRenderer };
