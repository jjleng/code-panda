interface Model {
  name: string;
  value: string;
  section: string;
  capabilities: {
    vision: boolean;
  };
}

export const models: Model[] = [
  {
    name: 'GPT-4o mini',
    value: 'gpt-4o-mini',
    section: 'default',
    capabilities: {
      vision: true,
    },
  },
  {
    name: 'Gemini 2.0 Flash Experimental',
    value: 'gemini-2.0-flash-exp',
    section: 'default',
    capabilities: {
      vision: true,
    },
  },
  {
    name: 'Claude 3 Haiku',
    value: 'claude-3-haiku',
    section: 'default',
    capabilities: {
      vision: true,
    },
  },
];
