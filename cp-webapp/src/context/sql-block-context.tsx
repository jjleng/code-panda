import { SqlBlockStatus } from '@/components/markdown-renderer/sql-block';
import React, { createContext, useCallback, useContext } from 'react';

interface SqlBlockContextType {
  updateSqlBlockStatus: (id: string, status: SqlBlockStatus) => void;
  isStreaming: boolean;
}

const SqlBlockContext = createContext<SqlBlockContextType | undefined>(undefined);

interface SqlBlockProviderProps {
  children: React.ReactNode;
  onStatusChange?: (id: string, status: SqlBlockStatus) => void;
  isStreaming?: boolean;
}

export const SqlBlockProvider = ({
  children,
  onStatusChange,
  isStreaming = false,
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
    <SqlBlockContext.Provider value={{ updateSqlBlockStatus, isStreaming }}>
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
