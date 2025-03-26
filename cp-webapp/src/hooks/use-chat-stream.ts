import { useCodeViewContext } from '@/components/code-view/context';
import { usePreviewContext } from '@/components/preview/context';
import { useSnapshotContext } from '@/components/snapshot-view/context';
import { useProject } from '@/context';
import { useChatHistory } from '@/context/chat-history';
import { stringToBase64 } from '@/lib/base64';
import { Message, UserMessage } from '@/types/chat';
import { ProjectStore, StoredMessage } from '@/types/project-store';
import { events } from 'fetch-event-stream';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { v4 as uuidv4 } from 'uuid';

// Types definition section
type TextBlock = {
  type: 'text';
  text: string;
};

type ImageBlock = {
  type: 'image_url';
  image_url: {
    url: string;
  };
};

type MessagePart = TextBlock | ImageBlock;

export type StreamEvent = {
  type: 'text' | 'tool' | 'usage' | 'thinking';
  content?: string;
  tool_name?: string;
  tool_id?: string;
  status?: 'started' | 'completed' | 'failed' | 'partial' | 'executing';
  params?: {
    path?: string;
    content?: string;
    diff?: string;
    regex?: string;
    file_pattern?: string;
    recursive?: boolean;
    name?: string;
    source?: string;
    destination?: string;
  };
  result?: string;
  error?: string;
  input_tokens?: number;
  output_tokens?: number;
  extra?: {
    old_content?: string;
    new_content?: string;
  };
};

const FASTAPI_URL = process.env.NEXT_PUBLIC_AGENT_URL;

// Utility functions
const getMessageIdentifier = (message: Message) => {
  // Use a combination of role, timestamp, and first few chars of content as identifier
  const timestamp =
    message.timestamp instanceof Date
      ? message.timestamp.getTime()
      : new Date(message.timestamp || 0).getTime();

  // Get first 10 chars of content (or full content if shorter)
  const contentPreview = message.content?.slice(0, 10) || '';

  return `${message.role}-${timestamp}-${contentPreview}`;
};

/**
 * Content block handlers for different types of special blocks in messages
 */
const contentBlockHandlers = {
  /**
   * Handle SQL block operations like adding IDs and updating status
   */
  sqlBlock: {
    addIdIfMissing: (content: string): string => {
      return content.replace(/<sql-block(?!\s+[^>]*?id=)([^>]*?)>/g, (match, attributes) => {
        const uuid = uuidv4();
        return `<sql-block${attributes} id="${uuid}">`;
      });
    },

    updateBlockStatus: (content: string, id: string, status: string): string => {
      const escapedId = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

      return content.replace(
        new RegExp(`<sql-block([^>]*?)id=["']${escapedId}["']([^>]*?)>`, 'i'),
        (match, before, after) => {
          if (/\bstatus=["'][^"']*["']/.test(match)) {
            return match.replace(/\bstatus=["'][^"']*["']/, `status="${status}"`);
          } else {
            return `<sql-block${before}id="${escapedId}"${after} status="${status}">`;
          }
        }
      );
    },

    findBlockRegex: (id: string): RegExp => {
      // Escape special characters in the ID for regex safety
      const escapedId = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp(`<sql-block[^>]*?\\bid=["']${escapedId}["'][^>]*?>`, 'i');
    },
  },
};

/**
 * Process message content with transformations like adding IDs to blocks
 */
const processMessageContent = (content: string): string => {
  let processedContent = content;

  // Use the existing SQL block handler to add IDs where missing
  processedContent = contentBlockHandlers.sqlBlock.addIdIfMissing(processedContent);

  return processedContent;
};

/**
 * Prepare message content with text and images
 */
const prepareMessageContent = async (
  content: string,
  attachments?: UserMessage['attachments']
): Promise<MessagePart[]> => {
  const contentParts: MessagePart[] = [];

  // Add text content if present
  if (content) {
    contentParts.push({ type: 'text', text: content });
  }

  // Add image attachments if present
  if (attachments?.length) {
    for (const attachment of attachments) {
      if (attachment.type.startsWith('image/')) {
        const response = await fetch(attachment.url);
        const blob = await response.blob();
        const base64 = await new Promise<string>(resolve => {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64 = (reader.result as string).split(',')[1];
            resolve(base64);
          };
          reader.readAsDataURL(blob);
        });
        contentParts.push({
          type: 'image_url',
          image_url: {
            url: `data:${attachment.type};base64,${base64}`,
          },
        });
      }
    }
  }

  return contentParts;
};

/**
 * Synchronize and merge messages from stored history with current messages
 */
const syncMessagesFromHistory = (
  prevMessages: Message[],
  storedMessages: Array<StoredMessage>
): Message[] => {
  // Create a map of existing messages by unique identifier
  const existingMessagesMap = new Map(prevMessages.map(msg => [getMessageIdentifier(msg), msg]));

  // Map stored messages to the format expected by this component
  // Use chronological order (oldest first) for display
  const orderedMessages = [...storedMessages]
    .sort((a, b) => {
      const dateA =
        a.createdAt instanceof Date ? a.createdAt.getTime() : new Date(a.createdAt).getTime();
      const dateB =
        b.createdAt instanceof Date ? b.createdAt.getTime() : new Date(b.createdAt).getTime();
      return dateA - dateB;
    })
    .map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.createdAt,
      attachments: 'attachments' in msg ? msg.attachments : undefined,
    }));

  // Merge existing and new messages using the improved identifier
  orderedMessages.forEach(msg => {
    const identifier = getMessageIdentifier(msg);
    existingMessagesMap.set(identifier, msg);
  });

  // Convert back to array and sort chronologically
  return Array.from(existingMessagesMap.values()).sort((a, b) => {
    const dateA =
      a.timestamp instanceof Date ? a.timestamp.getTime() : new Date(a.timestamp || 0).getTime();
    const dateB =
      b.timestamp instanceof Date ? b.timestamp.getTime() : new Date(b.timestamp || 0).getTime();
    return dateA - dateB;
  });
};

/**
 * Check project status and ensure project has a summary
 */
const ensureProjectHasSummary = async (
  projectId: string | undefined,
  projectStore: ProjectStore,
  ensureProjectWithSummary: (projectId: string, initialMessage: string) => Promise<void>,
  content: string
): Promise<void> => {
  if (!projectId) return;

  try {
    // First check if project exists and has a description
    const project = await projectStore.getProject(projectId);

    if (!project || !project.description || project.description.trim() === '') {
      // Project needs summary generation
      await ensureProjectWithSummary(projectId, content);
    }
  } catch (err) {
    console.error('Error checking project status:', err);
    // Continue even on error - ensure we try to create project
    await ensureProjectWithSummary(projectId, content);
  }
};

// Main hook
export function useChatStream() {
  // State variables
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  // Remove hasMoreMessages state since it just mirrors the context value

  // Refs
  const currentMessageRef = useRef<string>('');
  const currentThinkingBlockRef = useRef<string | null>(null);
  const projectCheckedRef = useRef<boolean>(false);
  const currentAssistantMessageIdRef = useRef<string | null>(null);

  // Context hooks
  const { triggerRefresh: triggerCodeViewRefresh } = useCodeViewContext();
  const { triggerRefresh: triggerSnapshotRefresh } = useSnapshotContext();
  const { previewPath, triggerPathsRefresh: triggerPreviewPathsRefresh } = usePreviewContext();
  const { projectId } = useProject();

  // Chat history integration
  const {
    addMessage: addMessageToHistory,
    updateMessage: updateMessageInHistoryOriginal,
    messages: storedMessages,
    store: projectStore,
    ensureProjectWithSummary,
  } = useChatHistory();

  // Create a debounced version of the update function using currentMessageRef
  const updateMessageInHistory = useDebouncedCallback(
    (messageId: string) => {
      if (messageId) {
        updateMessageInHistoryOriginal(messageId, {
          content: currentMessageRef.current,
        });
      }
    },
    2000 // 2 second debounce time
  );

  // Message handling functions
  const updateAssistantMessage = useCallback(
    (newMessage: string) => {
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage?.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: newMessage,
            },
          ];
        }
        return prev.concat({
          role: 'assistant',
          content: newMessage,
          timestamp: new Date(),
        });
      });

      // Update message in history store if we have an ID (debounced)
      if (currentAssistantMessageIdRef.current) {
        updateMessageInHistory(currentAssistantMessageIdRef.current);
      }
    },
    [updateMessageInHistory]
  );

  const cleanupThinking = useCallback(() => {
    if (currentThinkingBlockRef.current !== null) {
      const newMessage =
        currentMessageRef.current + `<thinking>${currentThinkingBlockRef.current}</thinking>`;
      currentMessageRef.current = newMessage;
      updateAssistantMessage(newMessage);
      currentThinkingBlockRef.current = null;
    }
  }, [updateAssistantMessage]);

  const markPendingToolsAsFailed = useCallback(() => {
    const toolRegex =
      /<(write-to-file|apply-diff)(?=.*?\bid="([^"]+)")(?=.*?\bpath="([^"]+)")(?=.*?\bstatus="started")[^>]*>/g;

    let match;
    let updatedMessage = currentMessageRef.current;

    // For each match, replace with a failed status
    while ((match = toolRegex.exec(updatedMessage)) !== null) {
      const [fullTag, toolName, toolId, path] = match;
      const newTag = `<${toolName} path="${path}" id="${toolId}" status="failed" old_content="" new_content="" />`;
      updatedMessage = updatedMessage.replace(fullTag, newTag);
    }

    if (updatedMessage !== currentMessageRef.current) {
      currentMessageRef.current = updatedMessage;
      updateAssistantMessage(updatedMessage);
    }
  }, [updateAssistantMessage]);

  // Tool event handling
  const handleToolEvent = useCallback(
    (data: StreamEvent) => {
      if (!data.tool_name || !data.tool_id) return;

      if (['write-to-file', 'apply-diff'].includes(data.tool_name)) {
        if (data.status === 'partial' && data.params?.path) {
          // Check if the tool with this ID already exists in the message
          const toolIdRegex = new RegExp(`id="${data.tool_id}"`);

          // Only add the tool tag if it doesn't already exist
          if (!toolIdRegex.test(currentMessageRef.current)) {
            const toolTag = `<${data.tool_name} path="${data.params.path}" id="${data.tool_id}" status="started" />\n\n`;
            currentMessageRef.current += toolTag;
            updateAssistantMessage(currentMessageRef.current);
          }
        } else if (data.status === 'completed' || data.status === 'failed') {
          const regex = new RegExp(`<${data.tool_name}[^>]*?id="${data.tool_id}"[^>]*?>`);
          const newTag = `<${data.tool_name} path="${data.params?.path}" id="${
            data.tool_id
          }" status="${data.status}" old_content="${
            data.extra?.old_content ? stringToBase64(data.extra.old_content) : ''
          }" new_content="${data.extra?.new_content ? stringToBase64(data.extra.new_content) : ''}" />`;
          currentMessageRef.current = currentMessageRef.current.replace(regex, newTag);
          updateAssistantMessage(currentMessageRef.current);
        }
      }

      if (
        ['write-to-file', 'apply-diff', 'delete-file', 'rename-file', 'add-dependency'].includes(
          data.tool_name
        )
      ) {
        // Trigger refresh when file operations completed
        if (data.status === 'completed' || data.status === 'failed') {
          triggerCodeViewRefresh();
          triggerSnapshotRefresh();
          triggerPreviewPathsRefresh();
        }
      }
    },
    [
      updateAssistantMessage,
      triggerCodeViewRefresh,
      triggerSnapshotRefresh,
      triggerPreviewPathsRefresh,
    ]
  );

  // Stream event processing
  const processSSEChunk = useCallback(
    (chunk: string) => {
      try {
        const data: StreamEvent = JSON.parse(chunk);
        switch (data.type) {
          case 'thinking':
            if (data.content) {
              if (currentThinkingBlockRef.current === null) {
                currentThinkingBlockRef.current = data.content;
              } else {
                currentThinkingBlockRef.current += data.content;
              }
              // Don't update currentMessageRef here, only show thinking tags in display
              updateAssistantMessage(
                currentMessageRef.current +
                  `<thinking>${currentThinkingBlockRef.current}</thinking>`
              );
            }
            break;

          case 'text':
            cleanupThinking();
            if (data.content) {
              // Process the incoming content with our utility
              const newContent = processMessageContent(data.content);

              const newMessage = currentMessageRef.current + newContent;
              currentMessageRef.current = newMessage;
              updateAssistantMessage(newMessage);
            }
            break;

          case 'tool':
            cleanupThinking();
            handleToolEvent(data);
            break;
        }
      } catch (e) {
        console.error('Error parsing event data:', e);
      }
    },
    [updateAssistantMessage, handleToolEvent, cleanupThinking]
  );

  // Stop streaming
  const stop = useCallback(() => {
    if (abortController) {
      cleanupThinking();
      markPendingToolsAsFailed();
      abortController.abort();
      setAbortController(null);
      setIsStreaming(false);
    }
  }, [abortController, cleanupThinking, markPendingToolsAsFailed]);

  // SQL Block status handling
  const handleSqlBlockStatusChange = useCallback(
    async (id: string, status: string) => {
      // Get regex to find SQL block with this ID
      const sqlBlockRegex = contentBlockHandlers.sqlBlock.findBlockRegex(id);

      try {
        // Look for the message containing this SQL block
        for (const message of storedMessages) {
          if (message.content && sqlBlockRegex.test(message.content)) {
            // Found the message containing this SQL block
            const newContent = contentBlockHandlers.sqlBlock.updateBlockStatus(
              message.content,
              id,
              status
            );

            // Update the message in history store
            await updateMessageInHistoryOriginal(message.id, {
              content: newContent,
            });

            break;
          }
        }

        // Update local state to reflect changes (moved outside the loop)
        setMessages(prevMessages =>
          prevMessages.map(m => {
            // Use the same regex pattern to find matching messages in our state
            if (m.content && sqlBlockRegex.test(m.content)) {
              return {
                ...m,
                content: contentBlockHandlers.sqlBlock.updateBlockStatus(m.content, id, status),
              };
            }
            return m;
          })
        );
      } catch (error) {
        console.error('Error updating SQL block status:', error);
      }
    },
    [updateMessageInHistoryOriginal, storedMessages]
  );

  // Message sending function
  const sendMessage = useCallback(
    async (content: string, attachments: UserMessage['attachments']) => {
      currentThinkingBlockRef.current = null;
      const userMessage: UserMessage = {
        role: 'user',
        content,
        attachments,
        timestamp: new Date(),
      };

      // Check project status only if we haven't before
      if (projectId && !projectCheckedRef.current) {
        projectCheckedRef.current = true; // Mark as checked to avoid future checks
        await ensureProjectHasSummary(projectId, projectStore, ensureProjectWithSummary, content);
      }

      // Save user message to history store
      await addMessageToHistory({
        ...userMessage,
      });

      stop();

      const controller = new AbortController();
      setAbortController(controller);
      setIsStreaming(true);

      try {
        // Create a placeholder for the assistant's response
        currentAssistantMessageIdRef.current = await addMessageToHistory({
          role: 'assistant',
          content: '',
        });

        // Reset current message content
        currentMessageRef.current = '';

        const response = await fetch(`${FASTAPI_URL}/api/v1/chat`, {
          method: 'POST',
          headers: new Headers({
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          }),
          body: JSON.stringify({
            project_id: projectId,
            message: await prepareMessageContent(content, attachments),
            context: {
              previewPath: previewPath || '/',
            },
          }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Failed to send message: ${response.status}`);
        }

        const eventStream = events(response, controller.signal);

        for await (const event of eventStream) {
          if (controller.signal.aborted) break;
          if (!event.data) continue;
          processSSEChunk(event.data);
        }
      } catch (error) {
        if (error instanceof Error) {
          if (error.name !== 'AbortError') {
            console.error('Error:', error.message);
            markPendingToolsAsFailed();
            throw error;
          }
          console.log('Stream aborted');
        }
      } finally {
        cleanupThinking();
        setIsStreaming(false);
        setAbortController(null);

        // Update final content - force immediate update without waiting for debounce
        if (currentAssistantMessageIdRef.current) {
          // Use the original non-debounced function for the final update
          updateMessageInHistoryOriginal(currentAssistantMessageIdRef.current, {
            content: currentMessageRef.current,
          });
          currentAssistantMessageIdRef.current = null;
        }
      }
    },
    [
      stop,
      processSSEChunk,
      cleanupThinking,
      previewPath,
      projectId,
      addMessageToHistory,
      updateMessageInHistoryOriginal,
      markPendingToolsAsFailed,
      ensureProjectWithSummary,
      projectStore,
    ]
  );

  // Sync messages from stored history
  useEffect(() => {
    if (storedMessages.length > 0) {
      // Log for debugging pagination issues
      console.log(`Syncing ${storedMessages.length} messages from history`);

      setMessages(prevMessages => {
        const newMessages = syncMessagesFromHistory(prevMessages, storedMessages);
        console.log(`Updated to ${newMessages.length} total messages`);
        return newMessages;
      });
    }
  }, [storedMessages]);

  return {
    messages,
    isStreaming,
    sendMessage,
    stop,
    handleSqlBlockStatusChange,
  };
}
