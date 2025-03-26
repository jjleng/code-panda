import { MarkdownRenderer } from '@/components/markdown-renderer';
import { PulsingDot } from '@/components/pulsing-dot';
import { cn } from '@/lib/utils';
import { AssistantMessage } from '@/types/chat';
import Image from 'next/image';

function AssistantChatBubble({
  message,
  streaming,
}: {
  message: AssistantMessage;
  streaming: boolean;
}) {
  return (
    <>
      <div className="flex items-center">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-transparent text-white">
          <Image src="/code-panda.svg" alt="CodePanda" width={24} height={24} className="h-6 w-6" />
        </div>
        <div className="text-sm text-foreground/70 ltr:ml-2 rtl:mr-2">CodePanda</div>
      </div>
      <div className={cn('w-full', streaming || message.content ? 'my-3' : '')}>
        {!message.content && streaming ? (
          <p>
            <PulsingDot
              style={{
                backgroundColor: 'var(--tw-prose-body)',
              }}
            />
          </p>
        ) : (
          <MarkdownRenderer text={message.content} streaming={streaming} />
        )}
      </div>
      <div className={cn(!message.content ? 'my-4' : '')}>
        {message.error && <div className="text-sm text-destructive">{message.error}</div>}
        {message.cancelled && (
          <div className="text-sm text-destructive">Generation is canceled</div>
        )}
      </div>
    </>
  );
}

export { AssistantChatBubble };
