import { cn } from '@/lib/utils';
import React from 'react';

interface PulsingDotProps {
  className?: string;
  style?: React.CSSProperties;
}

const PulsingDot: React.FC<PulsingDotProps> = ({ className = '', style = {} }) => {
  return (
    <span
      role="status"
      aria-label="Loading indicator"
      className={cn(
        'inline-block h-2 w-2 animate-pulse-radius rounded-full ltr:ml-2 rtl:mr-2',
        className
      )}
      style={style}
    />
  );
};

export { PulsingDot };
