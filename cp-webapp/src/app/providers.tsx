'use client';

import { SidebarProvider } from '@/components/ui/sidebar';
import { DirectionProvider } from '@radix-ui/react-direction';
import { isServer, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { useEffect, useState } from 'react';

import { client as agentClient } from '@/generated/agent/sdk.gen';
import { client as runnerClient } from '@/generated/runner/sdk.gen';

agentClient.setConfig({
  baseUrl: process.env.NEXT_PUBLIC_AGENT_URL,
});

runnerClient.setConfig({
  baseUrl: process.env.NEXT_PUBLIC_RUNNER_URL,
});

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // With SSR, we usually want to set some default staleTime
        // above 0 to avoid refetching immediately on the client
        staleTime: 365 * 24 * 60 * 60 * 1000,
        // Disable refetches as we want to control them manually
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        refetchOnMount: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (isServer) {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    // This is very important, so we don't re-make a new client if React
    // suspends during the initial render. This may not be needed if we
    // have a suspense boundary BELOW the creation of the query client
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

function detectDirection() {
  // Move this inside useEffect to avoid SSR mismatch
  if (typeof window === 'undefined') return 'ltr';

  const rtlLanguages = ['ar', 'he', 'fa', 'ur', 'yi', 'ckb', 'dv', 'ps', 'sd', 'syr'];
  const userLang = navigator.language || navigator.languages?.[0] || 'unknown';

  return rtlLanguages.some(lang => userLang.startsWith(lang)) ? 'rtl' : 'ltr';
}

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();
  const [direction, setDirection] = useState<'ltr' | 'rtl'>('ltr');

  useEffect(() => {
    // Initialize direction on client-side
    setDirection(detectDirection());
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <DirectionProvider dir={direction}>
        <SidebarProvider open={false}>
          <div
            dir={direction}
            style={{
              display: 'contents',
            }}
          >
            {children}
          </div>
        </SidebarProvider>
      </DirectionProvider>
    </QueryClientProvider>
  );
}
