'use client';

import { AssistantChatBubble } from '@/components/chat/assistant-bubble';
import { UserChatBubble } from '@/components/chat/user-bubble';
import StopButton from '@/components/stop-button';
import { ProvisioningState, useProject } from '@/context';
import { ChatHistoryProvider, useChatHistory } from '@/context/chat-history';
import { SqlBlockProvider } from '@/context/sql-block-context';
import { useChatStream } from '@/hooks/use-chat-stream';
import { isAssistantMessage } from '@/types/chat';
import { useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ChatBox } from './chat-box';
import ChatProvider from './context';

interface ChatViewProps {
  disabled?: boolean;
  messages: ReturnType<typeof useChatStream>['messages'];
  isStreaming: boolean;
  sendMessage: ReturnType<typeof useChatStream>['sendMessage'];
  stop: ReturnType<typeof useChatStream>['stop'];
}

const ChatView = ({ disabled, messages, isStreaming, sendMessage, stop }: ChatViewProps) => {
  const [wasCanceled, setWasCanceled] = useState(false);
  const [userScrolled, setUserScrolled] = useState(false);
  const [initialPromptProcessed, setInitialPromptProcessed] = useState(false);
  const { projectId, provisioningState } = useProject();
  const { loadMoreMessages, hasMoreMessages } = useChatHistory();
  const searchParams = useSearchParams();
  const hasInitialPrompt = searchParams.get('initial_prompt') === 'true';
  const initialPromptRef = useRef<string | null>(null);

  // Process the initial message from sessionStorage - split into two parts:
  // 1. First, capture the initial message when component mounts
  useEffect(() => {
    if (
      hasInitialPrompt &&
      !initialPromptProcessed &&
      projectId &&
      messages.length === 0 &&
      initialPromptRef.current === null
    ) {
      const storedMessage = sessionStorage.getItem(`project_initial_message_${projectId}`);

      if (storedMessage) {
        // Store the message in ref for later use
        initialPromptRef.current = storedMessage;
      }
    }
  }, [hasInitialPrompt, initialPromptProcessed, projectId, messages.length]);

  // 2. Then, send the message only after project is provisioned
  useEffect(() => {
    // Only attempt to send the message when:
    // - We have a stored message
    // - Project is fully provisioned
    // - We're not already streaming
    // - The initial prompt hasn't been processed yet
    if (
      initialPromptRef.current &&
      provisioningState === ProvisioningState.PROVISIONED &&
      !isStreaming &&
      !initialPromptProcessed
    ) {
      // Now it's safe to send the message
      sendMessage(initialPromptRef.current, []);

      // Clean up after using
      sessionStorage.removeItem(`project_initial_message_${projectId}`);
      initialPromptRef.current = null;
      setInitialPromptProcessed(true);
    }
  }, [provisioningState, isStreaming, initialPromptProcessed, projectId, sendMessage]);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isLoadingMoreRef = useRef(false);
  const initialLoadComplete = useRef(false);

  // Scroll to bottom of chat container
  const scrollToBottom = useCallback(() => {
    const container = chatContainerRef.current;
    if (!container) return;

    // Use requestAnimationFrame for smoother scrolling and to ensure DOM is ready
    requestAnimationFrame(() => {
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    });
  }, []);

  // Handles loading older messages when scrolling up
  const handleLoadMore = useCallback(async () => {
    if (isLoadingMoreRef.current || !hasMoreMessages) return;

    isLoadingMoreRef.current = true;

    // Record scroll position metrics before loading more
    const container = chatContainerRef.current;
    if (!container) {
      isLoadingMoreRef.current = false;
      return;
    }

    const scrollTopBefore = container.scrollTop;
    const oldScrollHeight = container.scrollHeight;

    // Calculate how many messages to load
    const minBatchSize = Math.max(
      10, // Minimum of 10 items
      Math.ceil((container.clientHeight || 300) / 60) * 2 // Or 2x viewport height
    );

    await loadMoreMessages(undefined, minBatchSize);

    // Use requestAnimationFrame to ensure DOM is fully updated before adjusting scroll
    requestAnimationFrame(() => {
      if (container) {
        // Maintain scroll position relative to content already loaded
        const newScrollHeight = container.scrollHeight;
        const heightDiff = newScrollHeight - oldScrollHeight;
        container.scrollTop = scrollTopBefore + heightDiff;
      }
      isLoadingMoreRef.current = false;
    });
  }, [hasMoreMessages, loadMoreMessages]);

  // Manages scroll detection for infinite loading and auto-scrolling behavior
  const handleScroll = useCallback(() => {
    if (!chatContainerRef.current || isLoadingMoreRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;

    // Trigger infinite loading when user scrolls near the top (200px threshold)
    if (scrollTop < 200 && hasMoreMessages && !isLoadingMoreRef.current) {
      handleLoadMore();
    }

    // Calculate how far the user has scrolled from the bottom
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    // Dynamic threshold for auto-scrolling:
    // - Larger threshold during streaming to maintain visibility of new content
    // - Smaller threshold otherwise for more precise control
    const autoScrollThreshold = isStreaming ? 300 : 100;
    const isAtBottom = distanceFromBottom < autoScrollThreshold;

    // Track if user has manually scrolled away from bottom
    setUserScrolled(!isAtBottom);
  }, [hasMoreMessages, handleLoadMore, isStreaming]);

  // Set up scroll event listener
  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // Auto-scroll to bottom for new messages
  useEffect(() => {
    // Don't auto-scroll if:
    // 1. There are no messages and we're not streaming
    // 2. User has explicitly scrolled up/away from bottom
    if ((!isStreaming && !messages.length) || userScrolled) return;

    scrollToBottom();
  }, [messages, isStreaming, userScrolled, scrollToBottom]);

  // Reset userScrolled when streaming starts to ensure auto-scrolling
  useEffect(() => {
    if (isStreaming && chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

      // If we're reasonably close to the bottom when streaming starts, reset userScrolled
      if (distanceFromBottom < 500) {
        setUserScrolled(false);
      }
    }
  }, [isStreaming]);

  // Initial load: ensure we have enough messages to make the scrollbar appear
  useEffect(() => {
    const container = chatContainerRef.current;
    if (!initialLoadComplete.current && messages.length > 0 && container) {
      // If content doesn't fill the container and we have more messages, load more
      if (
        container.scrollHeight <= container.clientHeight &&
        hasMoreMessages &&
        !isLoadingMoreRef.current
      ) {
        handleLoadMore().then(() => {
          // After loading more messages, scroll to bottom
          scrollToBottom();
        });
      } else {
        // We have enough messages or no more to load, scroll to bottom and mark as complete
        scrollToBottom();
        initialLoadComplete.current = true;
      }
    }
  }, [messages.length, hasMoreMessages, handleLoadMore, scrollToBottom]);

  // Reset canceled state when a new message starts streaming
  useEffect(() => {
    if (isStreaming) {
      setWasCanceled(false);
    }
  }, [isStreaming]);

  const handleStop = () => {
    setWasCanceled(true);
    stop();
  };

  return (
    <div className="flex h-full flex-col">
      <div
        ref={chatContainerRef}
        className="custom-scrollbar-thick prose mr-1 min-h-0 !max-w-none flex-1 overflow-y-auto dark:prose-invert"
      >
        {/* Loading indicator at the top - simplified to just show loading state */}
        {hasMoreMessages && isLoadingMoreRef.current && (
          <div className="sticky top-0 z-10 flex h-8 items-center justify-center bg-background">
            <div className="text-sm text-muted-foreground">Loading...</div>
          </div>
        )}

        {/* Render all messages directly */}
        {messages.map((message, index) => (
          <div key={`message-${index}`} className="p-4">
            {isAssistantMessage(message) ? (
              <AssistantChatBubble
                message={{
                  ...message,
                  timestamp: new Date(message.timestamp || Date.now()),
                }}
                streaming={isStreaming && index === messages.length - 1}
              />
            ) : (
              <UserChatBubble
                message={{
                  ...message,
                  role: 'user',
                  timestamp: new Date(message.timestamp || Date.now()),
                }}
              />
            )}
          </div>
        ))}

        {/* Show streaming indicator or canceled message when appropriate */}
        {(isStreaming || wasCanceled) &&
          // Only show the streaming/canceled bubble if:
          // 1. There are no messages, OR
          // 2. The last message is not from assistant, OR
          // 3. The last message is from assistant but has no content
          // 4. AND we're not currently streaming to the last message (which would mean it already exists)
          (!messages.length ||
            messages[messages.length - 1].role !== 'assistant' ||
            !messages[messages.length - 1].content) &&
          !(
            isStreaming &&
            messages.length &&
            messages[messages.length - 1].role === 'assistant'
          ) && (
            <div className="p-4">
              <AssistantChatBubble
                message={{
                  role: 'assistant',
                  content: wasCanceled ? 'Stream canceled' : '',
                  timestamp: new Date(),
                }}
                streaming={isStreaming}
              />
            </div>
          )}
      </div>

      <div className="mt-auto p-3">
        <div className="flex flex-col gap-2">
          {isStreaming && (
            <div className="flex justify-center">
              <StopButton onClick={handleStop} />
            </div>
          )}
          <ChatBox
            onSend={sendMessage}
            disabled={isStreaming || disabled}
            placeholder={
              isStreaming
                ? 'Assistant is thinking...'
                : disabled
                  ? 'Workspace is being provisioned...'
                  : 'Type a message...'
            }
          />
        </div>
      </div>
    </div>
  );
};

const ChatStreamController = ({ disabled }: { disabled?: boolean }) => {
  const { messages, isStreaming, sendMessage, stop, handleSqlBlockStatusChange } = useChatStream();

  const handleRequestFixMessage = useCallback(
    (message: string) => {
      sendMessage(message, []);
    },
    [sendMessage]
  );

  return (
    <SqlBlockProvider
      onStatusChange={handleSqlBlockStatusChange}
      isStreaming={isStreaming}
      requestFixMessage={handleRequestFixMessage}
    >
      <ChatView
        disabled={disabled}
        messages={messages}
        isStreaming={isStreaming}
        sendMessage={sendMessage}
        stop={stop}
      />
    </SqlBlockProvider>
  );
};

export const ChatPanel = ({
  disabled,
  requireAuth = false,
}: {
  disabled?: boolean;
  requireAuth?: boolean;
} = {}) => {
  return (
    <ChatHistoryProvider requireAuth={requireAuth}>
      <ChatProvider>
        <ChatStreamController disabled={disabled} />
      </ChatProvider>
    </ChatHistoryProvider>
  );
};
