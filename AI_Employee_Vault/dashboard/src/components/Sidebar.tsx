'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Mail,
  Share2,
  Users,
  DollarSign,
  CheckSquare,
  ShieldCheck,
  Settings,
  Sun,
  Moon,
  Monitor,
  Menu,
  X,
  Bot,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  approvalCount?: number;
}

const NAV_ITEMS = [
  { id: 'command', label: 'Command Center', icon: LayoutDashboard },
  { id: 'email', label: 'Email', icon: Mail },
  { id: 'social', label: 'Social Media', icon: Share2 },
  { id: 'crm', label: 'CRM', icon: Users },
  { id: 'financial', label: 'Financial', icon: DollarSign },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare },
  { id: 'approvals', label: 'Approvals', icon: ShieldCheck },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ activeTab, onTabChange, approvalCount = 0 }: SidebarProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => setMounted(true), []);

  function cycleTheme() {
    if (theme === 'dark') setTheme('light');
    else if (theme === 'light') setTheme('system');
    else setTheme('dark');
  }

  function handleNav(tabId: string) {
    onTabChange(tabId);
    setMobileOpen(false);
  }

  const themeIcon = mounted
    ? theme === 'dark' ? <Moon size={16} /> : theme === 'light' ? <Sun size={16} /> : <Monitor size={16} />
    : <Moon size={16} />;

  const themeLabel = mounted
    ? theme === 'dark' ? 'Dark' : theme === 'light' ? 'Light' : 'System'
    : 'Dark';

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-primary)] text-[var(--text-primary)]"
        aria-label="Open navigation menu"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      <div
        className={`sidebar-overlay ${mobileOpen ? 'open' : ''}`}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        className={`sidebar sidebar-mobile ${mobileOpen ? 'open' : ''} md:relative md:transform-none w-[260px] h-screen flex flex-col`}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* Logo */}
        <div className="p-5 flex items-center justify-between border-b border-[var(--border-primary)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
              <Bot size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-[var(--text-primary)]">AI Employee</h1>
              <p className="text-[11px] text-[var(--text-tertiary)]">Dashboard v2.0</p>
            </div>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
            aria-label="Close navigation menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`sidebar-item w-full ${isActive ? 'active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={18} />
                <span className="flex-1 text-left">{item.label}</span>
                {item.id === 'approvals' && approvalCount > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-orange-500/15 text-orange-500">
                    {approvalCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-[var(--border-primary)] space-y-2">
          {/* Theme toggle */}
          <button
            onClick={cycleTheme}
            className="sidebar-item w-full"
            aria-label={`Current theme: ${themeLabel}. Click to change.`}
          >
            {themeIcon}
            <span className="flex-1 text-left">{themeLabel} Mode</span>
          </button>

          {/* Status */}
          <div className="flex items-center gap-2 px-4 py-2 text-[11px] text-[var(--text-tertiary)]">
            <span className="w-2 h-2 rounded-full status-online flex-shrink-0" />
            All Systems Online
          </div>
        </div>
      </aside>
    </>
  );
}
