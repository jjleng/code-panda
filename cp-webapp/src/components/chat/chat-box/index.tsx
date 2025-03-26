import FileList from '@/components/chat/chat-box/attachments/file-list';
import { useChatContext } from '@/components/chat/context';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { ImageUp, Loader2, Send } from 'lucide-react';
import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';

const MAX_TEXTAREA_HEIGHT = 450;

interface ChatBoxProps {
  placeholder?: string;
  onSend: (
    query: string,
    attachments?: Array<{
      url: string;
      type: string;
      filename: string;
      mime_type: string;
      size: number;
    }>
  ) => void;
  disabled?: boolean;
}

const ChatBox = forwardRef<HTMLTextAreaElement, ChatBoxProps>(
  ({ placeholder, onSend, disabled = false }: ChatBoxProps, ref) => {
    const [value, setValue] = useState('');
    const [cursorPosition, setCursorPosition] = useState<number | null>(null);
    const maxHeight = MAX_TEXTAREA_HEIGHT; // Max height for the textarea
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const { files, removeAllFiles, uploadAssets, isUploading } = useChatContext();
    const fileInputRef = useRef<HTMLInputElement>(null);

    useImperativeHandle(ref, () => textareaRef.current as HTMLTextAreaElement);

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setValue(e.target.value);
      setCursorPosition(e.target.selectionStart || 0);
    };

    const triggerSend = async () => {
      if (!value && !files.length) return;

      const attachments = await Promise.all(
        files.map(async ({ file }) => {
          const url = URL.createObjectURL(file);
          return {
            url,
            type: file.type,
            filename: file.name,
            mime_type: file.type,
            size: file.size,
          };
        })
      );

      onSend(value, attachments);
      setValue('');
      setCursorPosition(null);
      removeAllFiles();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        triggerSend();
      }
    };

    const handleFileButtonClick = () => {
      fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        const selectedFiles = Array.from(e.target.files);

        uploadAssets(selectedFiles);

        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    };

    useEffect(() => {
      if (!textareaRef.current) return;

      const textarea = textareaRef.current;
      textarea.style.height = 'auto'; // Reset height to auto to recalculate
      textarea.style.height = `${textarea.scrollHeight}px`; // Set height based on scroll height
      // Check if there is a text selection, if not, focus on the textarea
      const textSelection = window.getSelection();
      if (!textSelection || textSelection.toString().trim() === '') {
        textarea.focus();
      }

      if (cursorPosition !== null) {
        textarea.setSelectionRange(cursorPosition, cursorPosition);
      }
    }, [value, cursorPosition]);

    const isSubmitDisabled = disabled || !value;

    return (
      <div className="border-1 group flex w-full flex-col items-center rounded-md border bg-card p-1 focus-within:border-background focus-within:ring-1 focus-within:ring-ring">
        <FileList />
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          style={{ maxHeight: maxHeight }}
          data-enable-grammarly="false"
          aria-label="Chat message input"
          className={`custom-scrollbar w-full resize-none overflow-y-auto rounded-md bg-card p-2 text-base text-foreground placeholder:text-muted-foreground/50 focus-visible:outline-none`}
          placeholder={placeholder || 'Type a message...'}
        />
        <div className="mt-2 flex w-full justify-between">
          <div></div>
          <div className="flex items-center space-x-[1px] rtl:space-x-reverse">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              multiple
              accept="image/*,video/*,audio/*,application/pdf,text/plain,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={handleFileButtonClick}
                    aria-label="Add attachment"
                    className="flex items-center justify-center rounded-lg p-1.5 hover:bg-muted"
                    disabled={isUploading}
                  >
                    {isUploading ? (
                      <Loader2 size={16} className="animate-spin text-muted-foreground" />
                    ) : (
                      <ImageUp size={16} className="text-muted-foreground" />
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{isUploading ? 'Uploading files...' : 'Upload assets for the project'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <button
              onClick={triggerSend}
              aria-label="Send message"
              className={`flex items-center justify-center rounded-lg p-1.5 ${
                !isSubmitDisabled ? 'hover:bg-muted' : ''
              }`}
              disabled={isSubmitDisabled}
            >
              <Send
                size={16}
                className={cn(!isSubmitDisabled ? 'text-primary' : 'text-muted-foreground')}
              />
            </button>
          </div>
        </div>
      </div>
    );
  }
);

ChatBox.displayName = 'ChatBox';

export { ChatBox };
