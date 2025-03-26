'use client';

import { ProjectCard } from '@/components/project-card';
import { Spinner } from '@/components/spinner';
import { Button } from '@/components/ui/button';
import { LocalProjectStore } from '@/lib/local-project-store';
import { Project } from '@/types/project-store';
import { FolderOpen } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';

// Number of projects to load per batch
const PAGE_SIZE = 12;

export default function ProjectsList() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Load initial projects
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const projectStore = new LocalProjectStore();
      await projectStore.initialize();

      const result = (await projectStore.listProjects({
        limit: PAGE_SIZE,
      })) as { projects: Project[]; nextCursor?: string };

      setProjects(result.projects);
      setNextCursor(result.nextCursor);
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMoreProjects = useCallback(async () => {
    if (isLoadingMore || !nextCursor) return;

    try {
      setIsLoadingMore(true);
      const projectStore = new LocalProjectStore();
      await projectStore.initialize();

      const result = (await projectStore.listProjects({
        limit: PAGE_SIZE,
        cursor: nextCursor,
      })) as { projects: Project[]; nextCursor?: string };

      // Append new projects to existing ones
      setProjects(prev => [...prev, ...result.projects]);
      setNextCursor(result.nextCursor);
    } catch (error) {
      console.error('Error loading more projects:', error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [nextCursor, isLoadingMore]);

  // Set up intersection observer for infinite scrolling
  useEffect(() => {
    if (!nextCursor || !loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && !isLoadingMore && nextCursor) {
          loadMoreProjects();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [isLoadingMore, nextCursor, loadMoreProjects]);

  return (
    <div className="container mx-auto max-w-4xl p-4">
      <div className="mb-6 flex items-center">
        <h1 className="text-2xl font-bold">Your Projects</h1>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner />
        </div>
      ) : projects.length === 0 ? (
        <div className="py-16 text-center">
          <div className="mb-4 flex justify-center">
            <FolderOpen size={64} className="text-muted-foreground/50" />
          </div>
          <h2 className="mb-2 text-xl font-semibold">No projects yet</h2>
          <p className="mb-6 text-muted-foreground">Create your first project to get started</p>
          <Button onClick={() => router.push('/projects/new')}>Create New Project</Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4">
            {projects.map(project => (
              <ProjectCard key={project.projectId} project={project} />
            ))}
          </div>

          <div ref={loadMoreRef} className="mt-8 py-4 text-center">
            {isLoadingMore ? (
              <div className="flex justify-center">
                <Spinner />
              </div>
            ) : nextCursor ? (
              <p className="text-sm text-muted-foreground">Scroll to load more projects</p>
            ) : (
              <p className="text-sm text-muted-foreground"></p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
