import { Prompt, KnowledgeBaseItem, ChatMessage, SystemStatus, AuthResponse, User } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Mock Data for fallback
const MOCK_PROMPTS: Prompt[] = [
  { id: '1', name: 'Support Agent V1', description: 'Standard customer support responses', content: 'You are a helpful support agent...', version: 3, lastUpdated: '2023-10-25T10:00:00Z' },
  { id: '2', name: 'Billing Specialist', description: 'Handles refunds and invoicing', content: 'You are an expert in finance...', version: 1, lastUpdated: '2023-10-24T14:30:00Z' },
  { id: '3', name: 'Technical Diagnostics', description: 'Deep dive into error logs', content: 'Analyze the following stack trace...', version: 5, lastUpdated: '2023-10-26T09:15:00Z' },
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
const shouldMock = true; // Set to false to try actual API first in production

const getHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

export const apiService = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    if (shouldMock) {
      await delay(1200);
      if (email === 'admin@demo.com' && password === 'password') {
        const response: AuthResponse = {
          access_token: 'mock_jwt_token_xyz_123',
          token_type: 'bearer',
          user: MOCK_USER
        };
        localStorage.setItem('auth_token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        return response;
      }
      throw new Error('Invalid credentials');
    }
    
    // Real implementation would look like:
    /*
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const res = await fetch(`${API_BASE_URL}/auth/token`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
       body: formData
    });
    */
    throw new Error('Real API not connected');
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

  getPrompts: async (): Promise<Prompt[]> => {
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
    if (shouldMock) {
      await delay(1500);
      return {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Here is a draft response based on your policy:\n\n"Thank you for contacting us regarding '${text.substring(0, 15)}...'. We understand your concern and would be happy to assist you..."\n\nIs there anything else I can help with?`,
        confidence: 0.92,
        timestamp: Date.now(),
      };
    }
    try {
      const res = await fetch(`${API_BASE_URL}/replies/generate`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error('Network response was not ok');
      return await res.json();
    } catch (e) {
      console.error(e);
      throw e;
    }
  }
};
