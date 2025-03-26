import { useProject } from '@/context';
import { generateSummaryApiV1ProjectsProjectIdGenerateSummaryPostMutation } from '@/generated/agent/@tanstack/react-query.gen';
import { useToast } from '@/hooks/use-toast';
import { LocalProjectStore } from '@/lib/local-project-store';
import { Message } from '@/types/chat';
import { ProjectStore, StoredMessage } from '@/types/project-store';
import { useMutation } from '@tanstack/react-query';
import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

// Default pagination values
const DEFAULT_LIMIT = 30;

interface ChatHistoryContextType {
  store: ProjectStore;
  messages: StoredMessage[];
  hasMoreMessages: boolean;
  loading: boolean;
  oldestMessageDate: Date | null;
  // Actions
  addMessage: (message: Omit<Message, 'id'>) => Promise<string>;
  updateMessage: (messageId: string, updates: Partial<Message>) => Promise<void>;
  loadMoreMessages: (cursor?: string, limit?: number) => Promise<void>;
  refresh: () => Promise<void>;
  ensureProjectWithSummary: (projectId: string, firstMessage: string) => Promise<void>;
}

const ChatHistoryContext = createContext<ChatHistoryContextType | undefined>(undefined);

interface ChatHistoryProviderProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export function ChatHistoryProvider({ children, requireAuth = false }: ChatHistoryProviderProps) {
  const [store] = useState<ProjectStore>(new LocalProjectStore());

  const { toast } = useToast();
  const { projectId } = useProject();
  const [messages, setMessages] = useState<StoredMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(false);
  const [oldestMessageDate, setOldestMessageDate] = useState<Date | null>(null);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Add a loading ref to prevent double loads
  const isLoadingRef = useRef(false);

  const generateSummaryMutation = useMutation(
    generateSummaryApiV1ProjectsProjectIdGenerateSummaryPostMutation()
  );

  useEffect(() => {
    if (error) {
      toast({
        variant: 'destructive',
        title: 'Chat History Error',
        description: error.message || 'An error occurred with the chat history',
      });
      setError(null);
    }
  }, [error, toast]);

  const loadMessages = useCallback(
    async (cursor?: string, limit: number = DEFAULT_LIMIT) => {
      if (!projectId || isLoadingRef.current) return;
      try {
        isLoadingRef.current = true;
        if (!cursor) {
          const count = await store.getMessageCount(projectId);
          if (count === 0) {
            setMessages([]);
            setHasMoreMessages(false);
            setOldestMessageDate(null);
            return;
          }
        }

        const loadedMessages = await store.getMessages({
          projectId,
          limit,
          cursor,
        });

        // If no cursor, replace existing; otherwise append
        if (!cursor) {
          setMessages(loadedMessages);
        } else {
          setMessages(prev => [...prev, ...loadedMessages]);
        }

        // Since messages are in descending order, the last item is the oldest
        if (loadedMessages.length > 0) {
          const newOldest = loadedMessages[loadedMessages.length - 1].createdAt;
          setOldestMessageDate(prevDate =>
            prevDate ? new Date(Math.min(prevDate.getTime(), newOldest.getTime())) : newOldest
          );
        }

        setHasMoreMessages(loadedMessages.length >= limit);
      } catch (error) {
        console.error('Failed to load messages:', error);
        setError(error instanceof Error ? error : new Error('Failed to load messages'));
      } finally {
        isLoadingRef.current = false;
      }
    },
    [projectId, store]
  );

  const ensureProjectWithSummary = useCallback(
    async (projectId: string, firstMessage: string): Promise<void> => {
      if (!projectId) return;

      try {
        // 1. Initial project creation with default values
        if (!requireAuth) {
          // We need to create a project in the local store
          await store.createProject(projectId);
        }

        // 2. Generate and apply summary in the background (don't block)
        generateSummaryMutation.mutate(
          {
            headers: {
              'X-CP-Project-ID': projectId,
            },
            path: {
              project_id: projectId,
            },
            body: {
              message: firstMessage,
            },
          },
          {
            onSuccess: summary => {
              // Update project with better name/description when available
              store.updateProject(projectId, summary.name, summary.description).catch(err => {
                console.error('Failed to update project with summary:', err);
              });
            },
            onError: error => {
              console.error('Failed to generate project summary:', error);
              // Non-critical error - project still exists with default values
            },
          }
        );
      } catch (error) {
        console.error('Error in ensureProjectWithSummary:', error);
        // Don't throw - this is a background enhancement that shouldn't block messages
      }
    },
    [store, generateSummaryMutation, requireAuth]
  );

  // Initialize store and load messages
  useEffect(() => {
    if (!projectId || initialLoadDone) return;

    const initializeStore = async () => {
      setLoading(true);
      try {
        await store.initialize();
        await loadMessages(); // Initial load
        setInitialLoadDone(true);
      } catch (error) {
        console.error('Failed to initialize chat history:', error);
        setError(error instanceof Error ? error : new Error('Failed to initialize chat history'));
      } finally {
        setLoading(false);
      }
    };

    initializeStore();
  }, [projectId, store, loadMessages, initialLoadDone]);

  const addMessage = async (message: Omit<Message, 'id'>): Promise<string> => {
    if (!projectId) {
      throw new Error('No project selected');
    }

    try {
      // Create a properly structured StoredMessage object
      const messageToAdd: StoredMessage = {
        ...message,
        id: uuidv4(),
        projectId,
        createdAt: new Date(),
      };

      // Add the message using the store's method
      const messageId = await store.addMessage(messageToAdd);
      // Refresh messages to include the new one
      await loadMessages(); // Reset to first page to see the new message

      return messageId;
    } catch (error) {
      console.error('Failed to add message:', error);
      setError(error instanceof Error ? error : new Error('Failed to add message'));
      throw error;
    }
  };

  const updateMessage = async (messageId: string, updates: Partial<Message>): Promise<void> => {
    try {
      await store.updateMessage(messageId, updates);

      setMessages(prev => prev.map(msg => (msg.id === messageId ? { ...msg, ...updates } : msg)));
    } catch (error) {
      console.error('Failed to update message:', error);
      setError(error instanceof Error ? error : new Error('Failed to update message'));
      throw error;
    }
  };

  // Load more messages using cursor-based pagination
  const loadMoreMessages = async (cursor?: string, limit?: number): Promise<void> => {
    if (!projectId || !hasMoreMessages) return;

    setLoading(true);
    try {
      // Use provided cursor or the oldest message date as cursor
      const paginationCursor = cursor || oldestMessageDate?.toISOString();
      if (!paginationCursor) return;

      await loadMessages(paginationCursor, limit);
    } catch (error) {
      console.error('Failed to load more messages:', error);
      setError(error instanceof Error ? error : new Error('Failed to load more messages'));
    } finally {
      setLoading(false);
    }
  };

  const refresh = async (): Promise<void> => {
    if (!projectId) return;

    setLoading(true);
    try {
      // Reset pagination state
      setOldestMessageDate(null);
      await loadMessages();
    } catch (error) {
      console.error('Failed to refresh chat history:', error);
      setError(error instanceof Error ? error : new Error('Failed to refresh chat history'));
    } finally {
      setLoading(false);
    }
  };

  const value = {
    store,
    messages,
    hasMoreMessages,
    loading,
    oldestMessageDate,
    addMessage,
    updateMessage,
    loadMoreMessages,
    refresh,
    ensureProjectWithSummary,
  };

  return <ChatHistoryContext.Provider value={value}>{children}</ChatHistoryContext.Provider>;
}

export function useChatHistory() {
  const context = useContext(ChatHistoryContext);
  if (!context) {
    throw new Error('useChatHistory must be used within a ChatHistoryProvider');
  }
  return context;
}
