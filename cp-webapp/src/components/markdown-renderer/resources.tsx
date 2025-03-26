import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';
import React, { memo } from 'react';

interface ResourceLinkProps {
  url: string;
  children: React.ReactNode;
}

const ResourceLink = memo(({ url, children }: ResourceLinkProps) => {
  return (
    <Button variant="outline" className="inline-flex items-center gap-2" asChild>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2"
      >
        <ExternalLink className="h-4 w-4" />
        {children}
      </a>
    </Button>
  );
});

ResourceLink.displayName = 'ResourceLink';

interface ResourcesProps {
  children: React.ReactNode;
}

const Resources = memo(({ children }: ResourcesProps) => {
  return <div className="my-4 flex flex-wrap gap-2">{children}</div>;
});

Resources.displayName = 'Resources';

export { ResourceLink, Resources, type ResourceLinkProps, type ResourcesProps };
