import { Message } from './chat';

export type StoredMessage = Message & {
  id: string; // Unique ID for each message
  projectId: string; // Project this message belongs to
  createdAt: Date; // When the message was created
  updatedAt?: Date; // When the message was last updated
};

export interface PaginationParams {
  limit: number;
  projectId: string;
  cursor?: string;
}

export interface Project {
  projectId: string;
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectPaginationParams {
  limit: number;
  cursor?: string; // Optional cursor for pagination
}

export interface ProjectPaginationResult {
  projects: Project[];
  nextCursor?: string; // Optional cursor for the next page
}

export interface ProjectStore {
  initialize(): Promise<void>;

  // Message-related methods
  addMessage(message: Omit<StoredMessage, 'id' | 'createdAt'>): Promise<string>;
  updateMessage(messageId: string, updates: Partial<StoredMessage>): Promise<void>;
  getMessages(params: PaginationParams): Promise<StoredMessage[]>;
  getMessageCount(projectId: string): Promise<number>;
  addMessages(messages: Omit<StoredMessage, 'id' | 'createdAt'>[]): Promise<string[]>;

  // Project methods
  createProject(projectId: string, name?: string, description?: string): Promise<void>;
  updateProject(projectId: string, name: string, description: string): Promise<void>;
  getProject(projectId: string): Promise<Project | null>;

  listProjects(params: ProjectPaginationParams): Promise<ProjectPaginationResult>;
}
