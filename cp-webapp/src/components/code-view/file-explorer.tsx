import { FC, useState } from 'react';
import { FiFolder, FiFile, FiChevronRight, FiChevronDown } from 'react-icons/fi';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

export interface FileSystemNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileSystemNode[];
}

interface FileExplorerProps {
  data: FileSystemNode;
  level?: number;
  currentPath?: string;
  onFileSelect?: (path: string) => void;
}

const FileExplorer: FC<FileExplorerProps> = ({
  data,
  level = 0,
  currentPath = '',
  onFileSelect,
}) => {
  const path = currentPath ? `${currentPath}/${data.name}` : data.name;
  const [isOpen, setIsOpen] = useState(level === 0);

  return (
    <div className="w-full whitespace-nowrap">
      {data.type === 'folder' ? (
        <Collapsible defaultOpen={level === 0} onOpenChange={setIsOpen}>
          <CollapsibleTrigger className="flex w-full items-center rounded p-1 hover:bg-secondary/50">
            <div style={{ marginLeft: `${level * 12}px` }} className="flex items-center gap-2">
              {data.children?.length ? (
                isOpen ? (
                  <FiChevronDown className="h-4 w-4 flex-none text-muted-foreground" />
                ) : (
                  <FiChevronRight className="h-4 w-4 flex-none text-muted-foreground" />
                )
              ) : (
                <span className="w-4 flex-none" />
              )}
              <FiFolder className="h-4 w-4 flex-none text-yellow-500" />
              <span>{data.name}</span>
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent>
            {data.children?.map((child, index) => (
              <FileExplorer
                key={`${child.name}-${index}`}
                data={child}
                level={level + 1}
                currentPath={path}
                onFileSelect={onFileSelect}
              />
            ))}
          </CollapsibleContent>
        </Collapsible>
      ) : (
        <div
          className="flex cursor-pointer items-center rounded p-1 hover:bg-secondary/50"
          style={{ marginLeft: `${(level + 1) * 12}px` }}
          onClick={() => onFileSelect?.(path)}
        >
          <FiFile className="mr-2 h-4 w-4 flex-none text-muted-foreground" />
          <span>{data.name}</span>
        </div>
      )}
    </div>
  );
};

export { FileExplorer };
