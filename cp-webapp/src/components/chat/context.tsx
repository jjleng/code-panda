import { useCodeViewContext } from '@/components/code-view/context';
import { useProject } from '@/context';
import { uploadAssetsApiV1ProjectsProjectIdUploadPost } from '@/generated/agent/sdk.gen';
import { useToast } from '@/hooks/use-toast';
import { models } from '@/model-list';

import { extension } from 'mime-types';
import React, { createContext, Dispatch, SetStateAction, useContext, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

export interface FileAttachment {
  file: File;
  type: string;
  name: string;
  id: string;
}

interface ChatContextType {
  files: FileAttachment[];
  cid: string | undefined;
  isStreaming: boolean;
  addFile: (file: File) => void;
  uploadAssets: (files: File[]) => Promise<void>;
  deleteFile: (id: string) => void;
  removeAllFiles: () => void;
  model: string | null;
  setModel: (model: string) => void;
  setCid: Dispatch<SetStateAction<string | undefined>>;
  setIsStreaming: Dispatch<SetStateAction<boolean>>;
  isUploading: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}
export default function ChatProvider({ children }: { children: React.ReactNode }) {
  const [files, setFiles] = useState<FileAttachment[]>([]);
  const [model, updateModel] = useState<string | null>(null);
  const [cid, setCid] = useState<string | undefined>();
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();
  const { projectId } = useProject();
  const { triggerRefresh } = useCodeViewContext();

  const addFile = (file: File) => {
    setFiles(prevFiles => [
      ...prevFiles,
      {
        file,
        name: file.name,
        type: extension(file.type) || 'unknown',
        id: uuidv4(),
      },
    ]);
  };

  const uploadAssets = async (files: File[]): Promise<void> => {
    if (!files.length) return;

    setIsUploading(true);

    try {
      await uploadAssetsApiV1ProjectsProjectIdUploadPost({
        path: { project_id: projectId! },
        body: {
          files,
        },
      });

      toast({
        title: 'Upload successful',
        description: `${files.length} file${files.length > 1 ? 's' : ''} uploaded to project`,
      });

      // Refresh code view to show the newly uploaded files
      triggerRefresh();
    } catch (error) {
      console.error('Error uploading files:', error);
      toast({
        title: 'Upload failed',
        description: 'Failed to upload files to project',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const deleteFile = (id: string) => {
    setFiles(prevFiles => prevFiles.filter(file => file.id !== id));
  };

  const setModel = (model: string) => {
    updateModel(model);
    const modelObj = models.find(m => m.value === model);
    if (modelObj && !modelObj.capabilities.vision) {
      setFiles(prevFiles => prevFiles.filter(file => !file.file.type.startsWith('image/')));
    }
  };

  return (
    <ChatContext.Provider
      value={{
        files,
        cid,
        model,
        isStreaming,
        isUploading,
        setCid,
        addFile,
        uploadAssets,
        deleteFile,
        removeAllFiles: () => setFiles([]),
        setModel,
        setIsStreaming,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}
