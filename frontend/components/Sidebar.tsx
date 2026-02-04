import React from 'react';
import { LayoutDashboard, Terminal, Database, MessageSquareText, Settings, Activity } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'prompts', label: 'Prompt Engineering', icon: Terminal },
    { id: 'kb', label: 'Knowledge Base', icon: Database },
    { id: 'playground', label: 'Chat Playground', icon: MessageSquareText },
  ];

  return (
    <div className="w-64 h-screen fixed left-0 top-0 flex flex-col border-r border-white/10 bg-space-900/50 backdrop-blur-md z-50">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center shadow-lg shadow-neon-purple/20">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
          AI Studio
        </span>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`
                w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                ${isActive 
                  ? 'bg-white/10 text-white shadow-lg border border-white/5' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                }
              `}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-neon-purple' : ''}`} />
              <span className="font-medium">{item.label}</span>
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-neon-purple shadow-[0_0_8px_rgba(168,85,247,0.8)]" />
              )}
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/10">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white transition-colors">
          <Settings className="w-5 h-5" />
          <span className="font-medium">Settings</span>
        </button>
        <div className="mt-4 px-4 py-3 rounded-xl bg-gradient-to-br from-neon-blue/10 to-neon-purple/10 border border-white/5">
          <p className="text-xs text-gray-400 uppercase font-bold tracking-wider mb-1">API Status</p>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-sm text-green-400 font-mono">ONLINE</span>
          </div>
        </div>
      </div>
    </div>
  );
};
