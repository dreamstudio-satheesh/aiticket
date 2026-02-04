import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { GlassCard } from './components/GlassCard';
import { LoginScreen } from './components/LoginScreen';
import { apiService } from './services/apiService';
import { SystemStatus, Prompt, KnowledgeBaseItem, ChatMessage, User } from './types';
import { 
  Activity, 
  Server, 
  Zap, 
  Clock, 
  Plus, 
  Edit3, 
  Trash2, 
  FileText, 
  Globe, 
  Search, 
  Send, 
  Bot, 
  User as UserIcon,
  MoreHorizontal,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Settings,
  Database,
  LogOut,
  ChevronRight
} from 'lucide-react';
import { HashRouter } from 'react-router-dom';

// -- Sub-Components --

// 1. Dashboard View
const DashboardView: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      const data = await apiService.getHealth();
      setStatus(data);
    };
    fetchStatus();
  }, []);

  const stats = [
    { label: 'Uptime', value: status?.uptime || 'Loading...', icon: Clock, color: 'text-green-400', bg: 'bg-green-500/10' },
    { label: 'Latency', value: status ? `${status.latency}ms` : '...', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
    { label: 'Active Agents', value: status?.activeAgents || 0, icon: Server, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Total Requests', value: '1.2M', icon: Activity, color: 'text-neon-purple', bg: 'bg-neon-purple/10' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-white tracking-tight">System Overview</h2>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          System Operational
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => (
          <GlassCard key={idx} hoverEffect className="p-6 group">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400 group-hover:text-gray-300 transition-colors">{stat.label}</p>
                <h3 className="text-3xl font-bold text-white mt-2 tracking-tight">{stat.value}</h3>
              </div>
              <div className={`p-3 rounded-xl ${stat.bg} ${stat.color} transition-transform group-hover:scale-110`}>
                <stat.icon className="w-6 h-6" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-xs font-medium">
              <span className="text-green-400 flex items-center gap-1 bg-green-400/10 px-2 py-0.5 rounded">
                <Plus className="w-3 h-3" /> 2.5%
              </span>
              <span className="ml-2 text-gray-500">vs last hour</span>
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="lg:col-span-2 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Live Traffic</h3>
            <div className="flex gap-2">
                <span className="w-3 h-3 rounded-full bg-neon-blue animate-pulse"></span>
                <span className="text-xs text-gray-400">Real-time</span>
            </div>
          </div>
          <div className="h-64 flex items-end justify-between gap-2 px-2">
             {/* Enhanced CSS Bar Chart Visualization */}
            {[45, 60, 30, 80, 55, 70, 45, 90, 65, 50, 75, 60, 40, 55, 85, 95, 60, 40, 70, 50].map((h, i) => (
              <div key={i} className="w-full bg-space-700/50 rounded-t-sm relative group" style={{ height: '100%' }}>
                 <div 
                    className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-neon-blue to-neon-purple rounded-t-sm transition-all duration-500 ease-out group-hover:brightness-125" 
                    style={{ height: `${h}%`, opacity: 0.8 }}
                 ></div>
                 {/* Glow effect on hover */}
                 <div className="absolute inset-0 bg-neon-purple/20 opacity-0 group-hover:opacity-100 transition-opacity blur-md"></div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-6">
           <div className="flex items-center justify-between mb-6">
               <h3 className="text-lg font-semibold text-white">Recent Alerts</h3>
               <button className="text-xs text-neon-purple hover:text-white transition-colors">View All</button>
           </div>
           <div className="space-y-3">
              {[
                { text: 'High latency detected in us-east-1', time: '2m ago', type: 'warning' },
                { text: 'Knowledge base index updated', time: '15m ago', type: 'success' },
                { text: 'New prompt version deployed', time: '1h ago', type: 'info' },
                { text: 'Tenant #402 onboarding complete', time: '2h ago', type: 'success' },
              ].map((alert, i) => (
                <div key={i} className="flex gap-4 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-transparent hover:border-white/5 cursor-default">
                  {alert.type === 'warning' && <AlertCircle className="w-5 h-5 text-yellow-500 shrink-0" />}
                  {alert.type === 'success' && <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />}
                  {alert.type === 'info' && <Activity className="w-5 h-5 text-blue-500 shrink-0" />}
                  <div>
                    <p className="text-sm text-gray-200 font-medium">{alert.text}</p>
                    <p className="text-xs text-gray-500 mt-1">{alert.time}</p>
                  </div>
                </div>
              ))}
           </div>
        </GlassCard>
      </div>
    </div>
  );
};

// 2. Prompt Engineering View
const PromptsView: React.FC = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);

  useEffect(() => {
    apiService.getPrompts().then(setPrompts);
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">System Prompts</h2>
          <p className="text-gray-400 mt-1">Manage the persona and instructions for your agents.</p>
        </div>
        <button className="flex items-center gap-2 px-5 py-2.5 bg-neon-purple hover:bg-purple-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-neon-purple/20 hover:scale-105 active:scale-95">
          <Plus className="w-4 h-4" /> New Prompt
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {prompts.map((prompt) => (
          <GlassCard key={prompt.id} className="p-6 flex flex-col h-full group cursor-pointer" hoverEffect>
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/20">
                <Terminal className="w-6 h-6" />
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                 <button className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"><Edit3 className="w-4 h-4" /></button>
                 <button className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-red-400 transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
            
            <h3 className="text-xl font-bold text-white mb-2 group-hover:text-neon-purple transition-colors">{prompt.name}</h3>
            <p className="text-sm text-gray-400 line-clamp-2 mb-6 flex-1 leading-relaxed">{prompt.description}</p>
            
            <div className="flex items-center justify-between pt-4 border-t border-white/10">
              <span className="px-2.5 py-1 rounded-md text-xs font-mono bg-white/5 text-gray-300 border border-white/10">v{prompt.version}.0</span>
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(prompt.lastUpdated).toLocaleDateString()}
              </span>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
};

// 3. Knowledge Base View
const KnowledgeBaseView: React.FC = () => {
  const [items, setItems] = useState<KnowledgeBaseItem[]>([]);

  useEffect(() => {
    apiService.getKnowledgeBase().then(setItems);
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Knowledge Base</h2>
          <p className="text-gray-400 mt-1">RAG indexes and source documents for weighted merging.</p>
        </div>
        <div className="flex gap-3">
          <div className="relative group">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-neon-blue transition-colors" />
            <input 
              type="text" 
              placeholder="Search documents..." 
              className="pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-neon-blue/50 focus:bg-space-800 transition-all w-64"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl font-medium transition-all border border-white/10 hover:border-white/20">
            <Plus className="w-4 h-4" /> Upload
          </button>
        </div>
      </div>

      <GlassCard className="overflow-hidden">
        <div className="w-full text-left text-sm">
          <div className="bg-white/5 text-gray-400 font-medium border-b border-white/10 grid grid-cols-12 gap-4 px-6 py-4 uppercase text-xs tracking-wider">
             <div className="col-span-5">Name</div>
             <div className="col-span-2">Type</div>
             <div className="col-span-2">Size</div>
             <div className="col-span-2">Status</div>
             <div className="col-span-1 text-right">Actions</div>
          </div>
          <div className="divide-y divide-white/5">
            {items.map((item) => (
              <div key={item.id} className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-white/[0.02] transition-colors group">
                <div className="col-span-5 flex items-center gap-4">
                  <div className={`p-2.5 rounded-lg bg-white/5 ring-1 ring-white/10 ${item.type === 'pdf' ? 'text-red-400' : 'text-blue-400'}`}>
                    {item.type === 'web' ? <Globe className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                  </div>
                  <span className="text-gray-200 font-medium group-hover:text-white transition-colors">{item.name}</span>
                </div>
                <div className="col-span-2 text-gray-500 font-mono text-xs uppercase">{item.type}</div>
                <div className="col-span-2 text-gray-500 font-mono text-xs">{item.size}</div>
                <div className="col-span-2">
                   <span className={`
                     px-2.5 py-1 rounded-full text-xs font-medium border inline-flex items-center gap-1.5
                     ${item.status === 'indexed' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 
                       item.status === 'indexing' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}
                   `}>
                     <span className={`w-1.5 h-1.5 rounded-full ${item.status === 'indexed' ? 'bg-green-500' : item.status === 'indexing' ? 'bg-blue-500 animate-pulse' : 'bg-red-500'}`}></span>
                     {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                   </span>
                </div>
                <div className="col-span-1 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="text-gray-500 hover:text-white transition-colors p-1 hover:bg-white/10 rounded">
                    <MoreHorizontal className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

// 4. Chat Playground View
const ChatPlaygroundView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiService.generateReply(userMsg.content);
      setMessages(prev => [...prev, response]);
    } catch (e) {
      // Error handling
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6 animate-fade-in">
      <div className="flex-1 flex flex-col h-full">
         <GlassCard className="flex-1 flex flex-col overflow-hidden border border-white/10">
            {/* Header */}
            <div className="p-4 border-b border-white/10 bg-white/5 flex items-center justify-between">
               <div className="flex items-center gap-3">
                 <div className="relative">
                   <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse absolute -right-0.5 -bottom-0.5 border-2 border-space-900"></div>
                   <div className="w-8 h-8 rounded-lg bg-neon-purple/20 flex items-center justify-center border border-neon-purple/30">
                      <Bot className="w-4 h-4 text-neon-purple" />
                   </div>
                 </div>
                 <div>
                    <h3 className="font-semibold text-white text-sm">Support Agent</h3>
                    <p className="text-xs text-gray-400">Model: v3.0 • Confidence > 85%</p>
                 </div>
               </div>
               <button className="text-xs text-neon-purple hover:text-white transition-colors" onClick={() => setMessages([])}>Clear Context</button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6" ref={scrollRef}>
               {messages.length === 0 && (
                 <div className="h-full flex flex-col items-center justify-center text-gray-500">
                    <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6 animate-pulse-slow">
                        <Bot className="w-10 h-10 text-gray-600" />
                    </div>
                    <p className="text-lg font-medium text-gray-300">AI Playground</p>
                    <p className="text-sm mt-2 max-w-sm text-center">Test your prompts and RAG retrieval against real support ticket scenarios.</p>
                 </div>
               )}
               {messages.map((msg) => (
                 <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''} animate-fade-in`}>
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-neon-purple/20 flex items-center justify-center border border-neon-purple/30 shrink-0 mt-1">
                        <Bot className="w-4 h-4 text-neon-purple" />
                      </div>
                    )}
                    
                    <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-1' : 'order-2'}`}>
                      <div className={`
                        p-4 rounded-2xl
                        ${msg.role === 'user' 
                          ? 'bg-neon-blue/20 border border-neon-blue/30 text-white rounded-br-none' 
                          : 'bg-white/10 border border-white/10 text-gray-200 rounded-bl-none'}
                      `}>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                      </div>
                      {msg.confidence && (
                         <div className="flex items-center gap-2 mt-2 ml-1">
                            <div className="h-1.5 w-24 bg-gray-800 rounded-full overflow-hidden border border-white/5">
                               <div className="h-full bg-gradient-to-r from-neon-blue to-green-400" style={{ width: `${msg.confidence * 100}%` }} />
                            </div>
                            <span className="text-xs font-mono text-gray-400">{(msg.confidence * 100).toFixed(0)}% Score</span>
                         </div>
                      )}
                    </div>

                    {msg.role === 'user' && (
                       <div className="w-8 h-8 rounded-full bg-gray-700/50 border border-white/10 flex items-center justify-center shrink-0 order-2 mt-1">
                         <UserIcon className="w-4 h-4 text-gray-300" />
                       </div>
                    )}
                 </div>
               ))}
               {loading && (
                 <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-neon-purple/20 flex items-center justify-center border border-neon-purple/30 shrink-0">
                        <Bot className="w-4 h-4 text-neon-purple" />
                    </div>
                    <div className="bg-white/10 border border-white/10 rounded-2xl p-4 flex gap-1">
                       <span className="w-2 h-2 rounded-full bg-neon-purple animate-bounce" style={{ animationDelay: '0ms' }}></span>
                       <span className="w-2 h-2 rounded-full bg-neon-purple animate-bounce" style={{ animationDelay: '150ms' }}></span>
                       <span className="w-2 h-2 rounded-full bg-neon-purple animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                 </div>
               )}
            </div>

            {/* Input */}
            <div className="p-4 bg-white/5 border-t border-white/10 backdrop-blur-md">
               <div className="relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Paste a support ticket or type a query..."
                    className="w-full bg-space-900/50 border border-white/10 rounded-xl pl-4 pr-12 py-4 text-white focus:outline-none focus:border-neon-purple/50 focus:ring-1 focus:ring-neon-purple/50 transition-all placeholder:text-gray-600 shadow-inner"
                  />
                  <button 
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-neon-purple hover:bg-purple-600 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
                  >
                    <Send className="w-4 h-4" />
                  </button>
               </div>
            </div>
         </GlassCard>
      </div>
      
      {/* Context Panel (Sidebar for Playgound) */}
      <div className="w-80 hidden xl:flex flex-col gap-6">
         <GlassCard className="p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Settings className="w-4 h-4 text-neon-blue" />
              Controls
            </h3>
            <div className="space-y-6">
               <div>
                 <div className="flex justify-between mb-2">
                    <label className="text-xs text-gray-400 font-medium">Temperature</label>
                    <span className="text-xs text-neon-blue">0.7</span>
                 </div>
                 <input type="range" className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-neon-purple" />
                 <div className="flex justify-between text-[10px] text-gray-600 mt-1 uppercase tracking-wider">
                   <span>Precise</span>
                   <span>Creative</span>
                 </div>
               </div>
               <div>
                  <label className="text-xs text-gray-400 block mb-2 font-medium">Active Prompt</label>
                  <div className="relative">
                    <select className="w-full bg-space-900 border border-white/10 rounded-lg p-2.5 text-sm text-gray-300 outline-none appearance-none focus:border-neon-purple/50">
                        <option>Support Agent V1</option>
                        <option>Billing Specialist</option>
                    </select>
                    <ChevronRight className="w-4 h-4 text-gray-500 absolute right-3 top-3 rotate-90 pointer-events-none" />
                  </div>
               </div>
            </div>
         </GlassCard>
         
         <GlassCard className="p-6 flex-1 flex flex-col">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
               <Database className="w-4 h-4 text-neon-pink" />
               RAG Context
            </h3>
            <div className="flex-1 rounded-xl bg-space-900/50 border border-white/5 p-4 flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
                    <Search className="w-5 h-5 text-gray-600" />
                </div>
               <p className="text-sm text-gray-400 italic px-4">
                   Knowledge sources retrieved for the conversation will appear here.
               </p>
            </div>
         </GlassCard>
      </div>
    </div>
  );
};

// -- Main App Component --

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  useEffect(() => {
    // Check for existing token
    const isAuth = apiService.isAuthenticated();
    setIsAuthenticated(isAuth);
    if (isAuth) {
        setCurrentUser(apiService.getCurrentUser());
    }
    setIsAuthChecking(false);
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setCurrentUser(apiService.getCurrentUser());
  };

  const handleLogout = () => {
    apiService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardView />;
      case 'prompts': return <PromptsView />;
      case 'kb': return <KnowledgeBaseView />;
      case 'playground': return <ChatPlaygroundView />;
      default: return <DashboardView />;
    }
  };

  if (isAuthChecking) {
    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-neon-purple border-t-transparent rounded-full animate-spin"></div>
        </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <HashRouter>
      <div className="min-h-screen font-sans selection:bg-neon-purple/30 selection:text-white">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="pl-64 transition-all duration-300">
          <header className="h-16 flex items-center justify-between px-8 border-b border-white/5 bg-space-900/50 backdrop-blur-xl sticky top-0 z-40">
            <div className="flex items-center text-sm text-gray-400">
               <span className="hover:text-white cursor-pointer transition-colors" onClick={() => setActiveTab('dashboard')}>Home</span>
               <span className="mx-2 text-gray-600">/</span>
               <span className="text-white capitalize">{activeTab.replace('-', ' ')}</span>
            </div>
            <div className="flex items-center gap-6">
                {currentUser && (
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-medium text-white">{currentUser.name}</p>
                        <p className="text-xs text-neon-purple uppercase tracking-wider">{currentUser.role}</p>
                    </div>
                )}
               <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-neon-blue to-purple-600 border border-white/20 shadow-lg shadow-purple-500/20 flex items-center justify-center text-white font-bold cursor-pointer hover:scale-105 transition-transform">
                    {currentUser?.name?.charAt(0) || 'A'}
               </div>
               <button onClick={handleLogout} className="text-gray-400 hover:text-white transition-colors">
                   <LogOut className="w-5 h-5" />
               </button>
            </div>
          </header>
          <div className="p-8 max-w-[1600px] mx-auto pb-20">
            {renderContent()}
          </div>
        </main>
      </div>
    </HashRouter>
  );
};

export default App;
