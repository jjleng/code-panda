import { MarkdownRenderer } from '@/components/markdown-renderer';
import React from 'react';
import { FileAttachmentPreview } from './file-attachment';
import { UserMessage } from '@/types/chat';

function UserChatBubble({ message }: { message: UserMessage }) {
  return (
    <>
      <div className="my-4 flex flex-col items-end">
        <span className="inline-block whitespace-pre-wrap rounded-md bg-muted p-2 px-3">
          <MarkdownRenderer text={message.content} streaming={false} />
        </span>
        {message.attachments?.map((attachment, index) => {
          return (
            <div className="mt-2 w-full" key={index}>
              <FileAttachmentPreview
                fileAttachment={{
                  type: attachment.type,
                  name: attachment.filename,
                }}
              />
            </div>
          );
        })}
      </div>
    </>
  );
}

export { UserChatBubble };
