import { useCallback, useEffect, useRef, useState } from 'react';

interface UseInfiniteScrollOptions {
  loadMoreFn: () => Promise<void>;
  hasMore: boolean;
  threshold?: number;
  cooldownMs?: number;
}

interface UseInfiniteScrollResult {
  loadMoreTriggerRef: React.RefObject<HTMLDivElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  isLoading: boolean;
}

export function useInfiniteScroll({
  loadMoreFn,
  hasMore,
  threshold = 0.5,
  cooldownMs = 500,
}: UseInfiniteScrollOptions): UseInfiniteScrollResult {
  const [isLoading, setIsLoading] = useState(false);
  const isLoadingRef = useRef(false);
  const loadMoreTriggerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleLoadMore = useCallback(async () => {
    if (isLoadingRef.current || !hasMore) return;

    isLoadingRef.current = true;
    setIsLoading(true);

    const container = containerRef.current;
    if (!container) {
      isLoadingRef.current = false;
      setIsLoading(false);
      return;
    }

    const scrollHeight = container.scrollHeight;

    try {
      await loadMoreFn();

      // Restore scroll position after new items are loaded
      requestAnimationFrame(() => {
        if (container) {
          const heightDiff = container.scrollHeight - scrollHeight;
          container.scrollTop = heightDiff;
        }
        isLoadingRef.current = false;
        setIsLoading(false);
      });
    } catch (error) {
      isLoadingRef.current = false;
      setIsLoading(false);
      console.error('Error loading more items:', error);
    }
  }, [hasMore, loadMoreFn]);

  useEffect(() => {
    const loadMoreTrigger = loadMoreTriggerRef.current;
    const container = containerRef.current;

    if (!loadMoreTrigger || !container || !hasMore) return;

    let timeoutId: NodeJS.Timeout | null = null;

    const observer = new IntersectionObserver(
      entries => {
        const target = entries[0];
        if (target.isIntersecting && !isLoadingRef.current && hasMore) {
          // Clear any pending timeouts to prevent duplicate loads
          if (timeoutId) clearTimeout(timeoutId);

          // Set a timeout to prevent rapid consecutive loads
          timeoutId = setTimeout(() => {
            handleLoadMore();
            timeoutId = null;
          }, cooldownMs);
        }
      },
      {
        root: container,
        threshold,
      }
    );

    observer.observe(loadMoreTrigger);
    return () => {
      observer.disconnect();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [hasMore, handleLoadMore, threshold, cooldownMs]);

  return {
    loadMoreTriggerRef,
    containerRef,
    isLoading,
  };
}
