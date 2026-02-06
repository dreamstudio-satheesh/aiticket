import { PromptVersion, PromptVersionCreate, PromptVersionUpdate, KnowledgeBaseItem, ChatMessage, SystemStatus, AuthResponse, User } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

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
    try {
      const res = await fetch(`${API_BASE_URL}/health`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Network response was not ok');
      return await res.json();
    } catch (e) {
      console.warn('Health check failed', e);
      return { status: 'down', uptime: '-', latency: 0, activeAgents: 0 };
    }
  },

  getPrompts: async (): Promise<PromptVersion[]> => {
    const res = await fetch(`${API_BASE_URL}/prompts`, { headers: getHeaders() });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch prompts');
    }
    return await res.json();
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
    const res = await fetch(`${API_BASE_URL}/kb`, { headers: getHeaders() });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch knowledge base');
    }
    return await res.json();
  },

  generateReply: async (
    text: string,
    promptId?: number | null,
    temperature?: number,
    model?: string
  ): Promise<ChatMessage> => {
    const res = await fetch(`${API_BASE_URL}/playground/generate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        subject: 'Playground Query',
        content: text,
        use_reranking: true,
        prompt_id: promptId || undefined,
        temperature: temperature !== undefined ? temperature : undefined,
        model: model || undefined,
      }),
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
