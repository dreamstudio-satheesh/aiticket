export interface User {
  id: string;
  email: string;
  name: string;
  tenant_id: string;
  role: 'admin' | 'support' | 'manager';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Prompt {
  id: string;
  name: string;
  description: string;
  content: string;
  version: number;
  lastUpdated: string;
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
