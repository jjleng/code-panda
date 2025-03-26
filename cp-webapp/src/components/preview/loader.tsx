'use client';

import { Cpu, HardDrive, Loader2, Sparkles, Globe } from 'lucide-react';
import { BsRobot } from 'react-icons/bs';
import { useEffect, useState } from 'react';

const loadingMessages = [
  'Warming up the quantum processors...',
  'Teaching robots to dance...',
  'Debugging the space-time continuum...',
  'Reticulating digital splines...',
  'Charging the flux capacitor...',
  'Teaching AI to make coffee...',
  'Downloading more RAM...',
  'Feeding the code hamsters...',
  'Untangling the binary spaghetti...',
  'Consulting the robot oracle...',
];

interface LoaderProps {
  isLoading?: boolean;
}

export function Loader({ isLoading = true }: LoaderProps) {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (isLoading) {
      const interval = setInterval(() => {
        setMessageIndex(prev => (prev + 1) % loadingMessages.length);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isLoading]);

  return (
    <div className="flex h-full w-full items-center justify-center p-6">
      {isLoading && (
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="relative h-24 w-24">
            {/* Spinning outer ring */}
            <Loader2 className="absolute h-24 w-24 animate-spin text-muted-foreground opacity-20" />
            {/* Pulsing CPU */}
            <Cpu className="absolute inset-0 m-auto h-16 w-16 animate-pulse text-primary" />
            {/* Orbiting elements */}
            <div className="absolute inset-0 animate-spin-slow">
              <BsRobot className="absolute -top-6 left-1/2 h-10 w-10 -translate-x-1/2 text-primary/80" />
              <HardDrive className="absolute -right-6 top-1/2 h-10 w-10 -translate-y-1/2 text-primary/80" />
              <Globe className="absolute -bottom-6 left-1/2 h-10 w-10 -translate-x-1/2 text-primary/80" />
              <Sparkles className="absolute -left-6 top-1/2 h-10 w-10 -translate-y-1/2 text-primary/80" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-lg font-medium">Unleashing AI Superpowers</p>
            <p className="min-w-[200px] text-sm text-muted-foreground">
              {loadingMessages[messageIndex]}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
