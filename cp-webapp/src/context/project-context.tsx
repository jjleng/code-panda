'use client';

import { createContext, ReactNode, useContext, useState } from 'react';

// Define an enum for project provisioning states
export enum ProvisioningState {
  NOT_STARTED = 'NOT_STARTED',
  PROVISIONING = 'PROVISIONING',
  PROVISIONED = 'PROVISIONED',
  ERROR = 'ERROR',
}

interface ProjectContextType {
  projectId: string | null;
  setProjectId: (id: string | null) => void;
  provisioningState: ProvisioningState;
  setProvisioningState: (state: ProvisioningState) => void;
  provisioningMessage: string;
  setProvisioningMessage: (message: string) => void;
  startProvisioning: () => void;
  stopProvisioning: () => void;
  isPreviewServerReady: boolean;
  setPreviewServerReady: (state: boolean) => void;
  isInitializingPreview: boolean;
  setInitializingPreview: (state: boolean) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

const DEFAULT_PROVISIONING_MESSAGE = 'Bringing up your workspace...';

export function ProjectProvider({ children }: { children?: ReactNode }) {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [provisioningState, setProvisioningState] = useState<ProvisioningState>(
    ProvisioningState.PROVISIONED
  );
  const [provisioningMessage, setProvisioningMessage] = useState(DEFAULT_PROVISIONING_MESSAGE);
  const [isPreviewServerReady, setPreviewServerReady] = useState(false);
  const [isInitializingPreview, setInitializingPreview] = useState(true);

  const startProvisioning = () => {
    setProvisioningState(ProvisioningState.PROVISIONING);
    setProvisioningMessage(DEFAULT_PROVISIONING_MESSAGE);
  };

  const stopProvisioning = () => {
    setProvisioningState(ProvisioningState.PROVISIONED);
    setProvisioningMessage('');
  };

  return (
    <ProjectContext.Provider
      value={{
        projectId,
        setProjectId,
        provisioningState,
        setProvisioningState,
        provisioningMessage,
        setProvisioningMessage,
        startProvisioning,
        stopProvisioning,
        isPreviewServerReady,
        setPreviewServerReady,
        isInitializingPreview,
        setInitializingPreview,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
