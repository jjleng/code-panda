import { cn } from '@/lib/utils';
import { javascript } from '@codemirror/lang-javascript';
import { loadLanguage } from '@uiw/codemirror-extensions-langs';
import { githubLight } from '@uiw/codemirror-theme-github';
import CodeMirror, { basicSetup, EditorState, EditorView, Extension } from '@uiw/react-codemirror';
import React, { useEffect, useMemo, useRef } from 'react';
import { MergeView } from '@codemirror/merge';
import styles from './code-renderer.module.css';
import { useCodeViewContext } from './context';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';

export interface CodeRendererProps {
  editorRef: React.RefObject<EditorView | null>;
}

export const getLanguageFromFileExtension = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase() || '';

  switch (ext) {
    case 'js':
      return 'javascript';
    case 'jsx':
      return 'javascript';
    case 'ts':
    case 'tsx':
      return 'typescript';
    case 'css':
      return 'css';
    case 'cpp':
    case 'cc':
    case 'h':
    case 'hpp':
      return 'cpp';
    case 'go':
      return 'go';
    case 'java':
      return 'java';
    case 'php':
      return 'php';
    case 'py':
      return 'python';
    case 'html':
    case 'htm':
      return 'html';
    case 'sql':
      return 'sql';
    case 'json':
      return 'json';
    case 'rs':
      return 'rust';
    case 'xml':
      return 'xml';
    case 'yml':
    case 'yaml':
      return 'yaml';
    case 'clj':
    case 'cljs':
      return 'clojure';
    case 'cs':
      return 'csharp';
    case 'sh':
    case 'bash':
    case 'zsh':
      return 'shell';
    case 'rb':
      return 'ruby';
    case 'swift':
      return 'swift';
    case 'kt':
      return 'kotlin';
    case 'm':
      return 'objectiveC';
    case 'hs':
      return 'haskell';
    case 'scala':
      return 'scala';
    case 'lisp':
    case 'cl':
      return 'commonLisp';
    case 'r':
      return 'r';
    case 'lua':
      return 'lua';
    case 'dart':
      return 'dart';
    case 'pl':
      return 'perl';
    case 'ps1':
      return 'powershell';
    case 'v':
    case 'vh':
      return 'verilog';
    case 'dockerfile':
      return 'dockerfile';
    case 'vue':
      return 'vue';
    default:
      return '';
  }
};

const getLanguageExtension = (language: string) => {
  switch (language) {
    case 'javascript':
      return javascript({ jsx: true, typescript: false });
    case 'typescript':
      return javascript({ jsx: true, typescript: true });
    case 'css':
      return loadLanguage('css');
    case 'cpp':
      return loadLanguage('cpp');
    case 'go':
      return loadLanguage('go');
    case 'java':
      return loadLanguage('java');
    case 'php':
      return loadLanguage('php');
    case 'python':
      return loadLanguage('python');
    case 'html':
      return loadLanguage('html');
    case 'sql':
      return loadLanguage('sql');
    case 'json':
      return loadLanguage('json');
    case 'rust':
      return loadLanguage('rust');
    case 'xml':
      return loadLanguage('xml');
    case 'yaml':
      return loadLanguage('yaml');
    case 'clojure':
      return loadLanguage('clojure');
    case 'csharp':
      return loadLanguage('csharp');
    case 'bash':
    case 'zsh':
      return loadLanguage('shell');
    case 'ruby':
      return loadLanguage('ruby');
    case 'swift':
      return loadLanguage('swift');
    case 'kotlin':
      return loadLanguage('kotlin');
    case 'objectiveC':
      return loadLanguage('objectiveC');
    case 'haskell':
      return loadLanguage('haskell');
    case 'scala':
      return loadLanguage('scala');
    case 'commonLisp':
      return loadLanguage('commonLisp');
    case 'r':
      return loadLanguage('r');
    case 'lua':
      return loadLanguage('lua');
    case 'dart':
      return loadLanguage('dart');
    case 'perl':
      return loadLanguage('perl');
    case 'powershell':
      return loadLanguage('powershell');
    case 'verilog':
      return loadLanguage('verilog');
    case 'dockerfile':
      return loadLanguage('dockerfile');
    case 'vue':
      return loadLanguage('vue');
    default:
      return undefined;
  }
};

// Shared utility function for extensions
function useLanguageExtensions(fileName: string | null) {
  return useMemo(() => {
    if (!fileName) {
      return [];
    }

    const extensionArray: Extension[] = [];
    const extension = getLanguageExtension(getLanguageFromFileExtension(fileName));
    if (extension) {
      extensionArray.push(extension);
    }
    return extensionArray;
  }, [fileName]);
}

// Add this function before the CodeRendererComponent
const decodeBase64Content = (content: string | null): string => {
  if (!content) return '';
  try {
    return Buffer.from(content, 'base64').toString('utf-8');
  } catch (e) {
    console.error('Failed to decode base64 content:', e);
    return '';
  }
};

// Normal View Component
export function CodeRendererComponent({ editorRef }: Readonly<CodeRendererProps>) {
  const { selectedFile, fileContent } = useCodeViewContext();
  const extensions = useLanguageExtensions(selectedFile);

  if (!fileContent) {
    return null;
  }

  return (
    <div className="h-full overflow-hidden">
      <ScrollArea className="h-full">
        <CodeMirror
          theme={githubLight}
          editable={false}
          className={cn('h-full w-full', styles.codeMirrorCustom)}
          value={decodeBase64Content(fileContent)}
          height="100%"
          extensions={extensions}
          onCreateEditor={view => {
            editorRef.current = view;
          }}
        />
        <ScrollBar orientation="vertical" />
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}

export const CodeRenderer = React.memo(CodeRendererComponent);

export function CodeMergeView({
  fileName,
  oldText,
  newText,
}: {
  fileName: string;
  oldText: string;
  newText: string;
}) {
  const extensions = useLanguageExtensions(fileName);
  const diffRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!diffRef.current) return;

    const extendedExtensions = [...basicSetup(), ...extensions, EditorState.readOnly.of(true)];

    const config = (text: string) => ({
      doc: text,
      extensions: extendedExtensions,
    });

    const view = new MergeView({
      a: config(oldText),
      b: config(newText),
      parent: diffRef.current,
      highlightChanges: true,
      gutter: true,
      collapseUnchanged: {
        margin: 3,
        minSize: 4,
      },
    });

    return () => view.destroy();
  }, [oldText, newText, extensions]);

  return (
    <>
      <style jsx global>{`
        .diff-add {
          background-color: rgba(0, 255, 0, 0.1);
        }
        .diff-remove {
          background-color: rgba(255, 0, 0, 0.1);
        }
      `}</style>
      <div
        ref={diffRef}
        className={cn(
          'custom-scrollbar-thick h-full w-full overflow-x-auto',
          styles.mergeViewWrapper
        )}
      />
    </>
  );
}
