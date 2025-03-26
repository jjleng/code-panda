'use client';

import { ProjectCard } from '@/components/project-card';
import { Button } from '@/components/ui/button';
import { LocalProjectStore } from '@/lib/local-project-store';
import { Project } from '@/types/project-store';
import { Clock, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

export default function NewProject() {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isSubmitting) return;

    setIsSubmitting(true);
    // Create unique identifier for the new project
    const projectId = uuidv4();

    // Store initial message in session storage for later retrieval
    sessionStorage.setItem(`project_initial_message_${projectId}`, message);

    // Navigate to the project page with flag indicating this is an initial prompt
    router.push(`/projects/${projectId}?initial_prompt=true`);
  };

  // Dynamically adjust textarea height based on content
  useEffect(() => {
    if (!textareaRef.current) return;

    const textarea = textareaRef.current;
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }, [message]);

  // Fetch the most recent projects to display in the UI
  useEffect(() => {
    async function loadRecentProjects() {
      try {
        setIsLoading(true);
        const projectStore = new LocalProjectStore();
        await projectStore.initialize();

        try {
          const result = await projectStore.listProjects({ limit: 5 });
          setRecentProjects(result.projects);
        } catch (error) {
          console.error('Error loading recent projects:', error);
          setRecentProjects([]);
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadRecentProjects();
  }, []);

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center p-4">
      <div className="mb-8 text-center">
        <h1 className="mb-4 text-4xl font-bold">CodePanda</h1>
        <p className="text-xl text-muted-foreground">
          Full-stack AI agent ready to build your next big idea.
        </p>
      </div>

      <div className="mb-8 w-full min-w-[450px]">
        <form onSubmit={handleSubmit} className="flex flex-col">
          <div className="border-1 flex w-full flex-col rounded-md border bg-card p-1 focus-within:border-background focus-within:ring-1 focus-within:ring-ring">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              disabled={isSubmitting}
              placeholder="Describe your project or ask a question..."
              className="custom-scrollbar min-h-[100px] w-full resize-none overflow-y-auto rounded-md bg-card p-2 text-base text-foreground placeholder:text-muted-foreground/50 focus-visible:outline-none"
              style={{ maxHeight: '450px' }}
            />
            <div className="mt-2 flex w-full justify-end">
              <Button
                type="submit"
                size="icon"
                variant="ghost"
                disabled={isSubmitting || !message.trim()}
                className={`flex items-center justify-center rounded-lg p-1.5 ${
                  !isSubmitting && message.trim() ? 'hover:bg-muted' : ''
                }`}
              >
                <Send
                  size={16}
                  className={
                    !isSubmitting && message.trim() ? 'text-primary' : 'text-muted-foreground'
                  }
                />
              </Button>
            </div>
          </div>
        </form>
      </div>

      {/* Recent Projects Section */}
      <div className="mt-6 w-full min-w-[450px]">
        {recentProjects.length > 0 && (
          <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
            <Clock size={18} className="text-muted-foreground" />
            Recent Projects
          </h2>
        )}

        {isLoading ? (
          <div className="py-4 text-center text-muted-foreground"></div>
        ) : recentProjects.length > 0 ? (
          <div className="custom-scrollbar max-h-[300px] overflow-y-auto pr-1">
            <ul className="space-y-2">
              {recentProjects.map(project => (
                <li key={project.projectId}>
                  <ProjectCard project={project} />
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="py-4 text-center text-muted-foreground"></div>
        )}
      </div>

      <div className="text-center text-sm text-muted-foreground"></div>
    </div>
  );
}
