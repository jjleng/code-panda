import { Project } from '@/types/project-store';
import { Clock } from 'lucide-react';
import Link from 'next/link';

interface ProjectCardProps {
  project: Project;
  className?: string;
}

export function ProjectCard({ project, className = '' }: ProjectCardProps) {
  // Format date for display
  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const diffDays = Math.floor(diff / (1000 * 3600 * 24));

    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <Link
      href={`/projects/${project.projectId}`}
      className={`block rounded-md border border-border p-3 transition-colors hover:bg-muted ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="truncate font-medium">{project.name || 'Unnamed Project'}</span>
        <div className="flex items-center text-xs text-muted-foreground">
          <Clock size={14} className="mr-1" />
          {formatDate(project.updatedAt)}
        </div>
      </div>
      {project.description ? (
        <p className="mt-1 truncate text-sm text-muted-foreground">{project.description}</p>
      ) : (
        <p className="mt-1 text-sm italic text-muted-foreground/50">No description</p>
      )}
    </Link>
  );
}
