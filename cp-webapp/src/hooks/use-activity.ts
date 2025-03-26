import { useCallback, useEffect } from 'react';

interface UseActivityOptions {
  /**
   * Callback function to be executed when activity is detected
   */
  onActivity: () => void;
  /**
   * Whether the activity monitoring is enabled
   */
  enabled?: boolean;
  /**
   * List of events to listen for on the main window
   */
  events?: string[];
  /**
   * Whether to listen for messages from iframes with type 'activity'
   */
  listenToIframeMessages?: boolean;
}

/**
 * Hook that monitors user activity and calls a callback function when activity is detected
 */
export function useActivity({
  onActivity,
  enabled = true,
  events = ['mousedown', 'keydown', 'scroll', 'mousemove'],
  listenToIframeMessages = true,
}: UseActivityOptions) {
  // Handler for main window activity
  const handleMainActivity = useCallback(() => {
    onActivity();
  }, [onActivity]);

  // Handler for iframe messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      if (event.data.type === 'activity') {
        onActivity();
      }
    },
    [onActivity]
  );

  // Set up activity monitoring
  useEffect(() => {
    if (!enabled) return;

    // Add event listeners for the main window
    events.forEach(event => {
      window.addEventListener(event, handleMainActivity);
    });

    // Add message listener for iframe events if enabled
    if (listenToIframeMessages) {
      window.addEventListener('message', handleMessage);
    }

    return () => {
      // Clean up main window events
      events.forEach(event => {
        window.removeEventListener(event, handleMainActivity);
      });

      // Clean up message listener
      if (listenToIframeMessages) {
        window.removeEventListener('message', handleMessage);
      }
    };
  }, [enabled, events, handleMainActivity, handleMessage, listenToIframeMessages]);

  // Return the trigger function that can be called manually
  return {
    triggerActivity: onActivity,
  };
}
