import { SqlBlockStatus } from '@/components/markdown-renderer/sql-block';
import React, { createContext, useCallback, useContext } from 'react';

interface SqlBlockContextType {
  updateSqlBlockStatus: (id: string, status: SqlBlockStatus) => void;
  isStreaming: boolean;
  requestFixMessage: (message: string) => void;
}

const SqlBlockContext = createContext<SqlBlockContextType | undefined>(undefined);

interface SqlBlockProviderProps {
  children: React.ReactNode;
  onStatusChange?: (id: string, status: SqlBlockStatus) => void;
  isStreaming?: boolean;
  requestFixMessage?: (message: string) => void;
}

export const SqlBlockProvider = ({
  children,
  onStatusChange,
  isStreaming = false,
  requestFixMessage = () => {},
}: SqlBlockProviderProps) => {
  const updateSqlBlockStatus = useCallback(
    (id: string, status: SqlBlockStatus) => {
      if (onStatusChange) {
        onStatusChange(id, status);
      }
    },
    [onStatusChange]
  );

  return (
    <SqlBlockContext.Provider value={{ updateSqlBlockStatus, isStreaming, requestFixMessage }}>
      {children}
    </SqlBlockContext.Provider>
  );
};

export const useSqlBlock = (): SqlBlockContextType => {
  const context = useContext(SqlBlockContext);
  if (!context) {
    throw new Error('useSqlBlock must be used within a SqlBlockProvider');
  }
  return context;
};
