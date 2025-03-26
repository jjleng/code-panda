type Attachment = {
  url: string;
  type: string;
  filename: string;
  mime_type: string;
  size: number;
};

interface BaseMessage {
  content: string;
  timestamp?: Date;
  role: 'user' | 'assistant';
}

export interface UserMessage extends BaseMessage {
  role: 'user';
  attachments?: Attachment[];
}

export interface AssistantMessage extends BaseMessage {
  role: 'assistant';
  model?: string;
  cancelled?: boolean;
  error?: string;
}

export type Message = UserMessage | AssistantMessage;

export function isAssistantMessage(message: Message): message is AssistantMessage {
  return message.role === 'assistant';
}

export function isUserMessage(message: Message): message is UserMessage {
  return message.role === 'user';
}
