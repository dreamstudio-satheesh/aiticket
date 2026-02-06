export interface User {
  id: string;
  email: string;
  name: string;
  tenant_id: string;
  role: 'admin' | 'support_agent' | 'manager';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PromptVersion {
  id: number;
  tenant_id: number | null;
  version: string;
  name: string;
  description: string | null;
  system_prompt: string;
  context_template: string;
  task_template: string;
  model: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  is_default: boolean;
  performance_metrics: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface PromptVersionCreate {
  name: string;
  version?: string;
  description?: string;
  system_prompt: string;
  context_template: string;
  task_template: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface PromptVersionUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  context_template?: string;
  task_template?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface KnowledgeBaseItem {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'txt' | 'web';
  size: string;
  status: 'indexed' | 'indexing' | 'error';
  lastModified: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  timestamp: number;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  uptime: string;
  latency: number;
  activeAgents: number;
}
