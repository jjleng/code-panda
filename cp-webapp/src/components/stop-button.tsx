import { CircleStop } from 'lucide-react';
import React from 'react';

interface StopButtonProps {
  onClick: () => void;
}

export default function StopButton({ onClick }: StopButtonProps) {
  return (
    <button
      className="inline-flex cursor-pointer items-center justify-center gap-1 rounded-l-full rounded-r-full border border-primary bg-background p-1 px-4 leading-none text-primary hover:bg-primary hover:text-primary-foreground"
      onClick={onClick}
      type="button"
      aria-label="Stop assistant response"
    >
      <CircleStop size={14} />
      Stop
    </button>
  );
}
