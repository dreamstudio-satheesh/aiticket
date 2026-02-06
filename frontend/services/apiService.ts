import { PromptVersion, PromptVersionCreate, PromptVersionUpdate, KnowledgeBaseItem, ChatMessage, SystemStatus, AuthResponse, User } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Mock Data for fallback
const MOCK_PROMPTS: PromptVersion[] = [
  { id: 1, tenant_id: null, version: '1.0.0', name: 'Support Agent V1', description: 'Standard customer support responses', system_prompt: 'You are a helpful support agent...', context_template: 'Use the following context:\n{context}', task_template: 'Answer the following ticket:\n{ticket}', model: 'gpt-4o-mini', temperature: 3, max_tokens: 1000, is_active: false, is_default: true, performance_metrics: null, created_at: '2023-10-25T10:00:00Z', updated_at: '2023-10-25T10:00:00Z' },
  { id: 2, tenant_id: null, version: '1.0.0', name: 'Billing Specialist', description: 'Handles refunds and invoicing', system_prompt: 'You are an expert in finance...', context_template: 'Use the following context:\n{context}', task_template: 'Handle the billing query:\n{ticket}', model: 'gpt-4o-mini', temperature: 3, max_tokens: 1000, is_active: false, is_default: false, performance_metrics: null, created_at: '2023-10-24T14:30:00Z', updated_at: '2023-10-24T14:30:00Z' },
  { id: 3, tenant_id: null, version: '2.0.0', name: 'Technical Diagnostics', description: 'Deep dive into error logs', system_prompt: 'Analyze the following stack trace...', context_template: 'Use the following context:\n{context}', task_template: 'Diagnose the issue:\n{ticket}', model: 'gpt-4o', temperature: 5, max_tokens: 2000, is_active: false, is_default: false, performance_metrics: null, created_at: '2023-10-26T09:15:00Z', updated_at: '2023-10-26T09:15:00Z' },
];

const MOCK_KB: KnowledgeBaseItem[] = [
  { id: '101', name: 'Product_Manual_v2.pdf', type: 'pdf', size: '2.4 MB', status: 'indexed', lastModified: '2023-10-01' },
  { id: '102', name: 'Return_Policy.docx', type: 'docx', size: '450 KB', status: 'indexed', lastModified: '2023-09-15' },
  { id: '103', name: 'Troubleshooting_Guide.txt', type: 'txt', size: '12 KB', status: 'indexing', lastModified: '2023-10-26' },
];

const MOCK_STATUS: SystemStatus = {
  status: 'healthy',
  uptime: '99.98%',
  latency: 45,
  activeAgents: 12
};

const MOCK_USER: User = {
  id: 'u_123',
  email: 'admin@demo.com',
  name: 'Admin User',
  tenant_id: 't_host_01',
  role: 'admin'
};

// Helper to simulate delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Helper to determine if we should use mock
const shouldMock = false;

const getHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

export const apiService = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    // Step 1: POST form-encoded credentials to /auth/login
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const tokenRes = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!tokenRes.ok) {
      const err = await tokenRes.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid credentials');
    }

    const tokenData = await tokenRes.json();
    const accessToken: string = tokenData.access_token;

    // Step 2: GET /auth/me to fetch user profile
    const meRes = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    });

    if (!meRes.ok) {
      throw new Error('Failed to fetch user profile');
    }

    const profile = await meRes.json();

    // Step 3: Map backend shape to frontend User
    const user: User = {
      id: String(profile.id),
      email: profile.email,
      name: profile.full_name || profile.email,
      tenant_id: String(profile.tenant_id),
      role: profile.role,
    };

    const response: AuthResponse = {
      access_token: accessToken,
      token_type: 'bearer',
      user,
    };

    localStorage.setItem('auth_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    return response;
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },

  getCurrentUser: (): User | null => {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  },

  getHealth: async (): Promise<SystemStatus> => {
    if (shouldMock) {
      await delay(500);
      return MOCK_STATUS;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/health`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Network response was not ok');
      return await res.json();
    } catch (e) {
      console.warn('API fetch failed, returning mock data', e);
      return MOCK_STATUS;
    }
  },

  getPrompts: async (): Promise<PromptVersion[]> => {
    if (shouldMock) {
      await delay(600);
      return MOCK_PROMPTS;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/prompts`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Network response was not ok');
      return await res.json();
    } catch (e) {
      return MOCK_PROMPTS;
    }
  },

  getPrompt: async (id: number): Promise<PromptVersion> => {
    const res = await fetch(`${API_BASE_URL}/prompts/${id}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch prompt');
    return await res.json();
  },

  getActivePrompt: async (): Promise<PromptVersion> => {
    const res = await fetch(`${API_BASE_URL}/prompts/active`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch active prompt');
    return await res.json();
  },

  setActivePrompt: async (promptId: number): Promise<PromptVersion> => {
    const res = await fetch(`${API_BASE_URL}/prompts/active`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ prompt_id: promptId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to set active prompt');
    }
    return await res.json();
  },

  createPrompt: async (data: PromptVersionCreate): Promise<PromptVersion> => {
    const res = await fetch(`${API_BASE_URL}/prompts`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create prompt');
    }
    return await res.json();
  },

  updatePrompt: async (id: number, data: PromptVersionUpdate): Promise<PromptVersion> => {
    const res = await fetch(`${API_BASE_URL}/prompts/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update prompt');
    }
    return await res.json();
  },

  deletePrompt: async (id: number): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/prompts/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete prompt');
    }
  },

  duplicatePrompt: async (promptId: number, newName: string): Promise<PromptVersion> => {
    const res = await fetch(`${API_BASE_URL}/prompts/duplicate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ prompt_id: promptId, new_name: newName }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to duplicate prompt');
    }
    return await res.json();
  },

  getKnowledgeBase: async (): Promise<KnowledgeBaseItem[]> => {
    if (shouldMock) {
      await delay(700);
      return MOCK_KB;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/kb`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Network response was not ok');
      return await res.json();
    } catch (e) {
      return MOCK_KB;
    }
  },

  generateReply: async (text: string): Promise<ChatMessage> => {
    const res = await fetch(`${API_BASE_URL}/playground/generate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ subject: 'Playground Query', content: text, use_reranking: true }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to generate reply');
    }

    const data = await res.json();
    return {
      id: data.id,
      role: data.role,
      content: data.content,
      confidence: data.confidence,
      timestamp: data.timestamp,
    };
  }
};
