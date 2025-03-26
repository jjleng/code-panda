import {
  PaginationParams,
  Project,
  ProjectPaginationParams,
  ProjectPaginationResult,
  ProjectStore,
  StoredMessage,
} from '@/types/project-store';
import { v4 as uuidv4 } from 'uuid';

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined' && window.indexedDB;

// IndexedDB database name and version
const DB_NAME = 'codepanda-projects';
const DB_VERSION = 3; // Increased version for schema update

// Object store names
const MESSAGES_STORE = 'messages';
const PROJECTS_STORE = 'projects';

export class LocalProjectStore implements ProjectStore {
  private db: IDBDatabase | null = null;

  constructor() {
    this.initialize();
  }

  async initialize(): Promise<void> {
    if (this.db) {
      return;
    }

    // Skip initialization if not in browser
    if (!isBrowser) {
      console.warn('IndexedDB not available - not in browser context');
      return;
    }

    return new Promise((resolve, reject) => {
      const request = window.indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = event => {
        console.error('Error opening IndexedDB', event);
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = event => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve();
      };

      request.onupgradeneeded = event => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create messages store
        if (!db.objectStoreNames.contains(MESSAGES_STORE)) {
          const messagesStore = db.createObjectStore(MESSAGES_STORE, {
            keyPath: 'id',
          });
          messagesStore.createIndex('projectId', 'projectId', {
            unique: false,
          });
          messagesStore.createIndex('createdAt', 'createdAt', {
            unique: false,
          });
          messagesStore.createIndex('projectId_createdAt', ['projectId', 'createdAt'], {
            unique: false,
          });
        }

        if (!db.objectStoreNames.contains(PROJECTS_STORE)) {
          const projectsStore = db.createObjectStore(PROJECTS_STORE, {
            keyPath: 'projectId',
          });
          projectsStore.createIndex('updatedAt', 'updatedAt', {
            unique: false,
          });
        }
      };
    });
  }

  private getStore(storeName: string, mode: IDBTransactionMode = 'readonly'): IDBObjectStore {
    if (!this.db) {
      throw new Error('Database not initialized');
    }

    const transaction = this.db.transaction(storeName, mode);
    return transaction.objectStore(storeName);
  }

  async addMessage(message: Omit<StoredMessage, 'id' | 'createdAt'>): Promise<string> {
    await this.initialize();

    // If not in browser environment, return a fake ID
    if (!isBrowser) {
      return uuidv4();
    }

    const now = new Date();
    const id = uuidv4();

    const storedMessage: StoredMessage = {
      ...message,
      id,
      createdAt: now,
      updatedAt: now,
    };

    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(MESSAGES_STORE, 'readwrite');
        const request = store.add(storedMessage);

        request.onsuccess = () => {
          resolve(id);
        };
        request.onerror = event => {
          const error = (event.target as IDBRequest).error;
          console.error('Failed to add message to IndexedDB:', error);
          reject(new Error(`Failed to add message: ${error?.message || event}`));
        };
      } catch (error) {
        console.error('Exception in addMessage:', error);
        reject(error);
      }
    });
  }

  async updateMessage(messageId: string, updates: Partial<StoredMessage>): Promise<void> {
    await this.initialize();

    // Skip if not in browser environment
    if (!isBrowser) {
      return;
    }

    return new Promise((resolve, reject) => {
      const store = this.getStore(MESSAGES_STORE, 'readwrite');
      const request = store.get(messageId);

      request.onsuccess = () => {
        const message = request.result as StoredMessage;
        if (!message) {
          reject(new Error(`Message not found: ${messageId}`));
          return;
        }

        const updatedMessage = {
          ...message,
          ...updates,
          id: messageId, // Ensure ID doesn't change
          updatedAt: new Date(),
        };

        const updateRequest = store.put(updatedMessage);
        updateRequest.onsuccess = () => resolve();
        updateRequest.onerror = event => reject(new Error(`Failed to update message: ${event}`));
      };

      request.onerror = event => reject(new Error(`Failed to get message for update: ${event}`));
    });
  }

  async getMessages({ projectId, limit, cursor }: PaginationParams): Promise<StoredMessage[]> {
    await this.initialize();

    // Return empty array if not in browser environment
    if (!isBrowser) {
      return [];
    }

    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(MESSAGES_STORE);
        const projectIdCreatedAtIndex = store.index('projectId_createdAt');

        // Create key range based on cursor if provided
        const endDate = cursor ? new Date(cursor) : new Date(8640000000000000);
        const range = IDBKeyRange.bound(
          [projectId, new Date(0)],
          [projectId, endDate],
          false,
          false
        );

        const request = projectIdCreatedAtIndex.openCursor(range, 'prev');
        const allMessages: StoredMessage[] = [];
        let count = 0;

        request.onsuccess = event => {
          const cursorObj = (event.target as IDBRequest).result as IDBCursorWithValue | null;
          if (cursorObj && count < limit) {
            allMessages.push(cursorObj.value as StoredMessage);
            count++;
            cursorObj.continue();
          } else {
            resolve(allMessages);
          }
        };

        request.onerror = event => {
          reject(new Error(`Failed to retrieve messages: ${event}`));
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  async getMessageCount(projectId: string): Promise<number> {
    await this.initialize();

    // Return 0 if not in browser environment
    if (!isBrowser) {
      return 0;
    }

    return new Promise((resolve, reject) => {
      const store = this.getStore(MESSAGES_STORE);
      const index = store.index('projectId');
      const request = index.count(projectId);

      request.onsuccess = () => resolve(request.result);
      request.onerror = event => reject(new Error(`Failed to get message count: ${event}`));
    });
  }

  async addMessages(messages: Omit<StoredMessage, 'id' | 'createdAt'>[]): Promise<string[]> {
    if (!messages.length) return [];

    // If not in browser environment, return fake IDs
    if (!isBrowser) {
      return messages.map(() => uuidv4());
    }

    const messageIds: string[] = [];
    for (const message of messages) {
      const id = await this.addMessage(message);
      messageIds.push(id);
    }

    return messageIds;
  }

  async createProject(
    projectId: string,
    name: string = 'Unnamed Project',
    description: string = ''
  ): Promise<void> {
    await this.initialize();

    // Skip if not in browser environment
    if (!isBrowser) {
      return;
    }

    try {
      const projectData = await this.getProjectData(projectId);
      if (projectData) {
        // Project exists, update its name and description
        return this.updateProject(projectId, name, description);
      } else {
        // Project doesn't exist, create minimal record with name and description
        const now = new Date();
        const project = {
          projectId,
          name,
          description,
          createdAt: now,
          updatedAt: now,
        };

        const store = this.getStore(PROJECTS_STORE, 'readwrite');
        await new Promise<void>((resolve, reject) => {
          const request = store.add(project);
          request.onsuccess = () => resolve();
          request.onerror = event => reject(new Error(`Failed to create project: ${event}`));
        });
      }
    } catch (error) {
      console.error('Exception in createProject:', error);
      throw error;
    }
  }

  async updateProject(projectId: string, name: string, description: string): Promise<void> {
    await this.initialize();

    // Skip if not in browser environment
    if (!isBrowser) {
      return;
    }

    return new Promise((resolve, reject) => {
      const store = this.getStore(PROJECTS_STORE, 'readwrite');
      const request = store.get(projectId);

      request.onsuccess = () => {
        const project = request.result;

        const updatedProject = project
          ? {
              ...project,
              name,
              description,
              updatedAt: new Date(),
            }
          : {
              projectId,
              name,
              description,
              createdAt: new Date(),
              updatedAt: new Date(),
            };

        const updateRequest = store.put(updatedProject);
        updateRequest.onsuccess = () => resolve();
        updateRequest.onerror = event => reject(new Error(`Failed to update project: ${event}`));
      };

      request.onerror = event => reject(new Error(`Failed to get project for update: ${event}`));
    });
  }

  async getProject(projectId: string): Promise<Project | null> {
    await this.initialize();

    // Return null if not in browser environment
    if (!isBrowser) {
      return null;
    }

    return this.getProjectData(projectId);
  }

  // Helper method to get project data
  private async getProjectData(projectId: string): Promise<Project | null> {
    return new Promise((resolve, reject) => {
      const store = this.getStore(PROJECTS_STORE);
      const request = store.get(projectId);

      request.onsuccess = () => {
        resolve(request.result || null);
      };
      request.onerror = event => reject(new Error(`Failed to get project data: ${event}`));
    });
  }

  async listProjects(params: ProjectPaginationParams): Promise<ProjectPaginationResult> {
    await this.initialize();

    // Return empty result if not in browser environment
    if (!isBrowser) {
      return { projects: [], nextCursor: undefined };
    }

    const { limit, cursor } = params;
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(PROJECTS_STORE);
        const index = store.index('updatedAt');

        // Create key range based on cursor if provided
        const range = cursor ? IDBKeyRange.upperBound(new Date(cursor).getTime(), true) : undefined;

        const request = index.openCursor(range, 'prev');
        const projects: Project[] = [];
        let count = 0;
        let nextCursor: string | undefined = undefined;

        request.onsuccess = event => {
          const cursor = (event.target as IDBRequest).result as IDBCursorWithValue | null;

          if (cursor && count < limit) {
            const project = cursor.value as Project;
            projects.push(project);
            count++;
            cursor.continue();
          } else if (cursor) {
            // There are more results available, set the next cursor
            const project = cursor.value as Project;
            nextCursor = project.updatedAt.toISOString();
            resolve({ projects, nextCursor });
          } else {
            // No more results
            resolve({ projects, nextCursor: undefined });
          }
        };

        request.onerror = event => {
          console.error('Error listing projects:', event);
          reject(new Error(`Failed to list projects: ${event}`));
        };
      } catch (error) {
        console.error('Exception in listProjects:', error);
        resolve({ projects: [], nextCursor: undefined });
      }
    });
  }
}
