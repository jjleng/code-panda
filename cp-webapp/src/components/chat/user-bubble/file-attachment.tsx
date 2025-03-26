import React from 'react';
import { defaultStyles, FileIcon } from 'react-file-icon';

function FileAttachmentPreview({
  fileAttachment,
}: {
  fileAttachment: { type: string; name: string };
}) {
  return (
    <div className="not-prose flex w-full items-center rounded-lg border bg-muted p-2 shadow-sm">
      <div className="w-6 flex-shrink-0">
        <FileIcon
          extension={fileAttachment.type}
          {...(fileAttachment.type in defaultStyles
            ? defaultStyles[fileAttachment.type as keyof typeof defaultStyles]
            : {})}
        />
      </div>
      <div className="ml-3 overflow-hidden">
        <p className="truncate text-sm font-medium">{fileAttachment.name}</p>
        <p className="truncate text-sm text-gray-500">{fileAttachment.type}</p>
      </div>
    </div>
  );
}

export { FileAttachmentPreview };
