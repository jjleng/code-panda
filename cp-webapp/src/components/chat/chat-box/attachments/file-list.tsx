import { useChatContext, type FileAttachment } from '@/components/chat/context';
import { formatBytes } from '@/lib/utils';
import { X } from 'lucide-react';
import { extension } from 'mime-types';
import React from 'react';
import { defaultStyles, FileIcon } from 'react-file-icon';

type FileCardProps = {
  fileAttachment: FileAttachment;
  onDelete: (id: string) => void;
};

const FileCard: React.FC<FileCardProps> = ({ fileAttachment, onDelete }) => {
  const { file, id: fileId } = fileAttachment;
  const fileExtension = extension(file.type) || 'unknown';

  return (
    <div className="group/file-card relative flex max-w-[160px] items-center rounded-md bg-accent p-2">
      <div className="w-8 flex-shrink-0">
        <FileIcon
          extension={fileExtension}
          {...(fileExtension in defaultStyles
            ? defaultStyles[fileExtension as keyof typeof defaultStyles]
            : {})}
        />
      </div>

      <div className="min-w-0 flex-1 ltr:ml-2 rtl:mr-2">
        <p className="w-full truncate text-sm font-medium text-foreground/70">{file.name}</p>
        <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
      </div>

      <button
        onClick={() => onDelete(fileId)}
        aria-label={`Remove ${file.name}`}
        className="absolute -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-gray-600 text-white opacity-0 shadow-md transition-opacity group-hover/file-card:opacity-100 hover:bg-gray-700 ltr:-right-1 rtl:-left-1"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export default function FileList() {
  const { files, deleteFile } = useChatContext();

  const handleDelete = React.useCallback(
    (fileId: string) => {
      try {
        deleteFile(fileId);
      } catch (error) {
        console.error('Failed to delete file:', error);
        // Here you could add a toast notification for error feedback
      }
    },
    [deleteFile]
  );

  if (!files?.length) return null;

  return (
    <div className="w-full px-2">
      <div className="flex flex-wrap gap-2 border-b py-2">
        {files.map(f => (
          <FileCard key={f.id} fileAttachment={f} onDelete={handleDelete} />
        ))}
      </div>
    </div>
  );
}
