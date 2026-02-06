'use client';

import { useState, useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import {
  AlertCircle, CheckCircle2, Clock, TrendingUp,
  Send, Sparkles, RefreshCw, Plus, X,
  Mail, Bot, Star,
} from 'lucide-react';

import type { DashboardData, CommandHistoryItem } from '@/lib/types';

// Components
import Sidebar from '@/components/Sidebar';
import SummaryCard from '@/components/SummaryCard';
import { SkeletonDashboard } from '@/components/SkeletonLoader';
import FinanceTab from '@/components/FinanceTab';
import SocialTab from '@/components/SocialTab';
import ApprovalsTab from '@/components/ApprovalsTab';
import TasksTab from '@/components/TasksTab';
import CEOBriefing from '@/components/CEOBriefing';

// ==================== AI AGENTS ====================
const AI_AGENTS = [
  { id: 'email', name: 'Email Agent', icon: '📧', color: 'from-blue-500 to-cyan-500', status: 'online' },
  { id: 'social', name: 'Social Agent', icon: '📱', color: 'from-purple-500 to-pink-500', status: 'online' },
  { id: 'task', name: 'Task Agent', icon: '📋', color: 'from-orange-500 to-yellow-500', status: 'online' },
  { id: 'crm', name: 'CRM Agent', icon: '👥', color: 'from-teal-500 to-cyan-500', status: 'online' },
  { id: 'finance', name: 'Finance Agent', icon: '💰', color: 'from-emerald-500 to-green-500', status: 'online' },
  { id: 'approval', name: 'Approval Agent', icon: '✅', color: 'from-green-500 to-emerald-500', status: 'online' },
];

// ==================== SAMPLE CHART DATA ====================
const WEEKLY_ACTIVITY = [
  { day: 'Mon', emails: 12, tasks: 8, approvals: 3 },
  { day: 'Tue', emails: 18, tasks: 5, approvals: 7 },
  { day: 'Wed', emails: 9, tasks: 12, approvals: 2 },
  { day: 'Thu', emails: 22, tasks: 6, approvals: 5 },
  { day: 'Fri', emails: 15, tasks: 10, approvals: 4 },
  { day: 'Sat', emails: 4, tasks: 2, approvals: 1 },
  { day: 'Sun', emails: 2, tasks: 1, approvals: 0 },
];

const REVENUE_TREND = [
  { month: 'Aug', revenue: 12400 },
  { month: 'Sep', revenue: 15800 },
  { month: 'Oct', revenue: 14200 },
  { month: 'Nov', revenue: 18600 },
  { month: 'Dec', revenue: 21000 },
  { month: 'Jan', revenue: 19500 },
];

// ==================== TOAST HELPER ====================
function showToast(message: string, type: 'success' | 'error') {
  if (type === 'success') {
    toast.success(message, {
      style: { background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border-primary)' },
    });
  } else {
    toast.error(message, {
      style: { background: 'var(--bg-card)', color: 'var(--accent-red)', border: '1px solid var(--border-primary)' },
    });
  }
}

// ==================== MAIN DASHBOARD COMPONENT ====================
export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('command');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Command Center State
  const [commandInput, setCommandInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<CommandHistoryItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Email Composer State
  const [emailTo, setEmailTo] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [emailTone, setEmailTone] = useState('professional');

  // Settings State
  const [connections, setConnections] = useState({
    gmail: false, linkedin: false, twitter: false, whatsapp: false, slack: false, calendar: false,
  });
  const [automationRules, setAutomationRules] = useState({
    autoEmail: true, vipDrafts: true, invoiceProcess: true, socialSchedule: false, ceoBriefing: true,
  });

  // Modal States
  const [showAddContactModal, setShowAddContactModal] = useState(false);
  const [newContact, setNewContact] = useState({ name: '', email: '', company: '', type: 'lead' });

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchDashboardData() {
    try {
      const response = await fetch('/api/dashboard');
      const json = await response.json();
      if (json.error) {
        showToast('Failed to fetch dashboard data', 'error');
        return;
      }
      setData(json);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch:', error);
      showToast('Connection error: Unable to reach dashboard API', 'error');
    } finally {
      setLoading(false);
    }
  }

  // ==================== COMMAND PROCESSING ====================
  async function processCommand(command: string) {
    const newCommand: CommandHistoryItem = {
      id: Date.now().toString(), command, response: '', timestamp: new Date(), status: 'pending',
    };
    setCommandHistory(prev => [newCommand, ...prev]);
    setIsProcessing(true);
    setCommandInput('');

    await new Promise(resolve => setTimeout(resolve, 1500));

    let response = '';
    const lowerCommand = command.toLowerCase();

    if (lowerCommand.includes('linkedin') && lowerCommand.includes('post')) {
      const topic = command.replace(/.*post about|.*post on|.*write about/gi, '').trim();
      response = `LinkedIn Post Draft Created\n\nTopic: "${topic}"\n\nDraft saved to Approvals queue. Review it in Social Media tab.`;
      setActiveTab('social');
    } else if (lowerCommand.includes('email') && (lowerCommand.includes('send') || lowerCommand.includes('draft') || lowerCommand.includes('write'))) {
      response = `Email Draft Started\n\nSwitching to Email tab...`;
      setActiveTab('email');
    } else if (lowerCommand.includes('invoice') || lowerCommand.includes('pdf')) {
      response = `Invoice Processing\n\nUpload PDFs in the Financial tab for auto-extraction.\n\nSwitching to Financial tab...`;
      setActiveTab('financial');
    } else if (lowerCommand.includes('contact') || lowerCommand.includes('client') || lowerCommand.includes('lead')) {
      response = `CRM Update\n\nSwitching to CRM tab...`;
      setActiveTab('crm');
    } else if (lowerCommand.includes('task') || lowerCommand.includes('todo') || lowerCommand.includes('project')) {
      response = `Task Management\n\nSwitching to Tasks tab...`;
      setActiveTab('tasks');
    } else if (lowerCommand.includes('status') || lowerCommand.includes('summary') || lowerCommand.includes('briefing')) {
      const stats = data?.stats;
      response = `Daily Status Summary\n\nAwaiting Action: ${stats?.needsAction || 0}\nIn Progress: ${stats?.inProgress || 0}\nPending Approval: ${stats?.pendingApproval || 0}\nCompleted Today: ${stats?.completedToday || 0}\n\nAll ${AI_AGENTS.length} agents are online.`;
    } else {
      response = `Command Received: "${command}"\n\nTry:\n- "Write a LinkedIn post about AI automation"\n- "Draft email to client"\n- "Show me today\'s status summary"`;
    }

    setCommandHistory(prev =>
      prev.map(item => item.id === newCommand.id ? { ...item, response, status: 'completed' } : item)
    );
    setIsProcessing(false);
  }

  // ==================== AI GENERATION FUNCTIONS ====================
  async function generateEmailDraft() {
    if (!emailTo || !emailSubject) return;
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));

    const toneStyles: Record<string, string> = {
      professional: `Dear ${emailTo.split('@')[0]},\n\nI hope this email finds you well.\n\nRegarding ${emailSubject}, I wanted to reach out to discuss the details and next steps.\n\nPlease let me know your availability for a brief call.\n\nBest regards`,
      friendly: `Hey ${emailTo.split('@')[0]}!\n\nHope you're doing great!\n\nJust wanted to touch base about ${emailSubject}.\n\nLet me know what you think!\n\nCheers`,
      formal: `Dear Sir/Madam,\n\nI am writing to formally address the matter of ${emailSubject}.\n\nI would appreciate your prompt attention to this matter.\n\nYours faithfully`,
    };

    setEmailBody(toneStyles[emailTone] || toneStyles.professional);
    setIsProcessing(false);
  }

  async function submitEmailForApproval() {
    if (!emailTo || !emailSubject || !emailBody) return;
    setIsProcessing(true);
    try {
      const response = await fetch('/api/drafts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'email_draft', data: { to: emailTo, subject: emailSubject, body: emailBody, tone: emailTone } }),
      });
      const result = await response.json();
      if (result.success) {
        showToast('Email draft saved for approval', 'success');
        setEmailTo(''); setEmailSubject(''); setEmailBody('');
        await fetchDashboardData();
        setActiveTab('approvals');
      } else {
        showToast(result.error || 'Failed to save draft', 'error');
      }
    } catch {
      showToast('Error saving email draft', 'error');
    }
    setIsProcessing(false);
  }

  async function generateCeoBriefing() {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/briefing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'ceo_briefing' }),
      });
      const result = await response.json();
      if (result.success) {
        showToast('CEO Briefing generated', 'success');
        const newCommand: CommandHistoryItem = {
          id: Date.now().toString(),
          command: 'Generate CEO Briefing',
          response: `CEO Briefing Generated\n\n${result.briefing || 'Saved to Business/CEO_Briefings/'}`,
          timestamp: new Date(),
          status: 'completed',
        };
        setCommandHistory(prev => [newCommand, ...prev]);
      } else {
        showToast(result.error || 'Failed to generate briefing', 'error');
      }
    } catch {
      showToast('Error generating CEO briefing', 'error');
    }
    setIsProcessing(false);
  }

  // ==================== ADD CONTACT HANDLER ====================
  async function handleAddContact() {
    if (!newContact.name || !newContact.email) return;
    setIsProcessing(true);
    try {
      const response = await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newContact),
      });
      const result = await response.json();
      if (result.success) {
        showToast(`Contact added: ${newContact.name}`, 'success');
        setNewContact({ name: '', email: '', company: '', type: 'lead' });
        setShowAddContactModal(false);
        await fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to add contact', 'error');
      }
    } catch {
      showToast('Error adding contact', 'error');
    }
    setIsProcessing(false);
  }

  function toggleAutomationRule(ruleKey: keyof typeof automationRules) {
    setAutomationRules(prev => ({ ...prev, [ruleKey]: !prev[ruleKey] }));
  }

  // ==================== RECHARTS CUSTOM TOOLTIP ====================
  function ChartTooltip({ active, payload, label }: any) {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-lg p-3 text-xs border border-[var(--border-primary)] bg-[var(--bg-card)] shadow-lg">
        <p className="font-semibold text-[var(--text-primary)] mb-1">{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={i} style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' && entry.name === 'revenue' ? `$${entry.value.toLocaleString()}` : entry.value}
          </p>
        ))}
      </div>
    );
  }

  // ==================== RENDER ====================
  return (
    <div className="flex h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border-primary)' },
        }}
      />

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        approvalCount={data?.pendingApprovals?.length || 0}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 flex items-center justify-between px-6 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] flex-shrink-0">
          {/* Spacer for mobile hamburger */}
          <div className="md:hidden w-10" />
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              {activeTab === 'command' ? 'Command Center' : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchDashboardData}
              className="p-2 rounded-lg hover:bg-[var(--bg-tertiary)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
              aria-label="Refresh data"
            >
              <RefreshCw size={16} />
            </button>
            <span className="text-xs text-[var(--text-tertiary)] font-mono hidden sm:inline" suppressHydrationWarning>
              {lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--:--'}
            </span>
          </div>
        </header>

        {/* Scrollable content area */}
        <main id="main-content" className="flex-1 overflow-y-auto p-6 bg-[var(--bg-secondary)] bg-grid">
          {loading ? (
            <SkeletonDashboard />
          ) : (
            <>
              {/* ==================== COMMAND CENTER TAB ==================== */}
              {activeTab === 'command' && (
                <div className="space-y-6 animate-fade-in">
                  {/* CEO Briefing */}
                  <CEOBriefing data={data} onToast={showToast} />

                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <SummaryCard
                      label="Awaiting Action"
                      value={data?.stats.needsAction || 0}
                      icon={<AlertCircle size={20} />}
                      gradient="orange"
                      trend={{ value: -12, label: 'vs last week' }}
                    />
                    <SummaryCard
                      label="In Progress"
                      value={data?.stats.inProgress || 0}
                      icon={<Clock size={20} />}
                      gradient="blue"
                      trend={{ value: 8, label: 'vs last week' }}
                    />
                    <SummaryCard
                      label="Pending Approval"
                      value={data?.stats.pendingApproval || 0}
                      icon={<CheckCircle2 size={20} />}
                      gradient="purple"
                    />
                    <SummaryCard
                      label="Completed Today"
                      value={data?.stats.completedToday || 0}
                      icon={<TrendingUp size={20} />}
                      gradient="green"
                      trend={{ value: 24, label: 'vs yesterday' }}
                    />
                  </div>

                  {/* Charts Row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Weekly Activity Chart */}
                    <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]">
                      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Weekly Activity</h3>
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={WEEKLY_ACTIVITY} barGap={2}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-secondary)" />
                          <XAxis dataKey="day" tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }} axisLine={false} tickLine={false} />
                          <YAxis tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }} axisLine={false} tickLine={false} />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar dataKey="emails" name="Emails" fill="#0070f3" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="tasks" name="Tasks" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="approvals" name="Approvals" fill="#00c853" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Revenue Trend Chart */}
                    <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]">
                      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Revenue Trend</h3>
                      <ResponsiveContainer width="100%" height={220}>
                        <LineChart data={REVENUE_TREND}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-secondary)" />
                          <XAxis dataKey="month" tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }} axisLine={false} tickLine={false} />
                          <YAxis tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                          <Tooltip content={<ChartTooltip />} />
                          <Line type="monotone" dataKey="revenue" name="revenue" stroke="#0070f3" strokeWidth={2.5} dot={{ fill: '#0070f3', r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Command Input */}
                  <div className="rounded-2xl p-6 border-2 border-brand-500/30 bg-[var(--bg-card)]" role="region" aria-label="Command Center input">
                    <h2 className="text-base font-semibold text-[var(--text-primary)] mb-1 flex items-center gap-2">
                      <Sparkles size={18} className="text-brand-500" />
                      Command Center
                    </h2>
                    <p className="text-[var(--text-tertiary)] text-sm mb-4">
                      Tell me what you need. I can draft emails, create social posts, manage tasks, and more.
                    </p>
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={commandInput}
                        onChange={(e) => setCommandInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && commandInput && processCommand(commandInput)}
                        placeholder="Try: 'Write a LinkedIn post about AI automation'"
                        disabled={isProcessing}
                        className="flex-1 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)]"
                        aria-label="Command input"
                      />
                      <button
                        onClick={() => commandInput && processCommand(commandInput)}
                        disabled={!commandInput || isProcessing}
                        className="btn-neon flex items-center gap-2 disabled:opacity-50"
                        aria-label="Send command"
                      >
                        <Send size={14} />
                        {isProcessing ? '...' : 'Send'}
                      </button>
                    </div>

                    {/* Quick Actions */}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {[
                        { label: 'Draft Email', cmd: 'Draft an email' },
                        { label: 'LinkedIn Post', cmd: 'Write a LinkedIn post about my business' },
                        { label: 'CEO Briefing', cmd: 'Generate CEO briefing', action: generateCeoBriefing },
                        { label: 'Upload Invoice', cmd: 'Upload invoice for processing' },
                        { label: 'Create Task', cmd: 'Create a new task' },
                      ].map((qa, i) => (
                        <button
                          key={i}
                          onClick={() => qa.action ? qa.action() : processCommand(qa.cmd)}
                          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                        >
                          {qa.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Command History */}
                  <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]" role="log" aria-label="Activity log">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Activity Log</h3>
                    <div className="space-y-3 max-h-[400px] overflow-y-auto">
                      {commandHistory.length === 0 ? (
                        <p className="text-[var(--text-tertiary)] text-center py-8 text-sm">No commands yet. Try asking me something!</p>
                      ) : (
                        commandHistory.map((item) => (
                          <div key={item.id} className="rounded-xl p-4 border border-[var(--border-secondary)] bg-[var(--bg-secondary)]">
                            <div className="flex items-start gap-3">
                              <span className="text-xs font-bold text-brand-500">[YOU]</span>
                              <div className="flex-1">
                                <p className="text-sm text-[var(--text-primary)]">{item.command}</p>
                                <p className="text-[10px] text-[var(--text-tertiary)] mt-1">{item.timestamp.toLocaleTimeString()}</p>
                              </div>
                            </div>
                            {item.response && (
                              <div className="mt-3 pl-8 border-l-2 border-brand-500/30">
                                <div className="flex items-start gap-3">
                                  <span className="text-xs font-bold text-emerald-500">[AI]</span>
                                  <pre className="text-[var(--text-secondary)] text-sm whitespace-pre-wrap font-sans flex-1">{item.response}</pre>
                                </div>
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Active Agents */}
                  <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]" role="region" aria-label="Active AI agents">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Active AI Agents</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                      {AI_AGENTS.map((agent) => (
                        <div key={agent.id} className="rounded-xl p-3 border border-[var(--border-secondary)] bg-[var(--bg-secondary)] text-center card-hover">
                          <div className={`w-10 h-10 mx-auto rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center text-lg mb-2`}>
                            {agent.icon}
                          </div>
                          <p className="text-xs font-medium text-[var(--text-primary)]">{agent.name}</p>
                          <div className="flex items-center justify-center gap-1 mt-1">
                            <span className="w-1.5 h-1.5 rounded-full status-online" />
                            <span className="text-[10px] text-emerald-500">Online</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ==================== EMAIL TAB ==================== */}
              {activeTab === 'email' && (
                <div className="space-y-6 animate-fade-in">
                  {/* Email Inbox */}
                  <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]" role="region" aria-label="Email inbox">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
                        <Mail size={18} className="text-brand-500" />
                        Inbox
                      </h2>
                      <button onClick={fetchDashboardData} className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]">
                        <RefreshCw size={12} className="inline mr-1" />
                        Refresh
                      </button>
                    </div>
                    <div className="space-y-2 max-h-[300px] overflow-y-auto">
                      {data?.emails && data.emails.length > 0 ? (
                        data.emails.slice(0, 10).map((email) => (
                          <div key={email.id} className="flex items-start gap-3 p-3 rounded-xl border border-[var(--border-secondary)] bg-[var(--bg-secondary)] hover:border-[var(--border-focus)] cursor-pointer transition-colors">
                            <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${email.priority === 'high' ? 'bg-red-500' : 'bg-emerald-500'}`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex justify-between items-start gap-2">
                                <p className="text-sm font-medium text-[var(--text-primary)] truncate">{email.from}</p>
                                <span className="text-[10px] text-[var(--text-tertiary)] whitespace-nowrap">{new Date(email.received).toLocaleDateString()}</span>
                              </div>
                              <p className="text-sm text-[var(--text-secondary)] truncate">{email.subject}</p>
                              <p className="text-xs text-[var(--text-tertiary)] truncate">{email.snippet}</p>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8">
                          <Mail size={32} className="mx-auto text-[var(--text-tertiary)] mb-2" />
                          <p className="text-[var(--text-tertiary)] text-sm">No emails in inbox.</p>
                          <p className="text-[var(--text-tertiary)] text-xs mt-1">Run the Gmail watcher to fetch new emails.</p>
                        </div>
                      )}
                    </div>
                    {data?.emails && data.emails.length > 10 && (
                      <p className="text-xs text-[var(--text-tertiary)] mt-2 text-center">Showing 10 of {data.emails.length} emails</p>
                    )}
                  </div>

                  {/* Email Composer */}
                  <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]" role="region" aria-label="Compose email">
                    <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-1">
                      <Send size={18} className="text-brand-500" />
                      Compose Email
                    </h2>
                    <p className="text-[var(--text-tertiary)] text-sm mb-6">Drafts require your approval before sending.</p>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm text-[var(--text-secondary)] mb-2">To (Email Address)</label>
                        <input type="email" value={emailTo} onChange={(e) => setEmailTo(e.target.value)} placeholder="recipient@example.com"
                          className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]" />
                        {data?.contacts && data.contacts.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            <span className="text-xs text-[var(--text-tertiary)]">Quick select:</span>
                            {data.contacts.slice(0, 5).map((contact) => (
                              <button key={contact.id} onClick={() => setEmailTo(contact.email)} className="text-xs px-2 py-1 rounded-lg border border-[var(--border-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]">
                                {contact.name}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm text-[var(--text-secondary)] mb-2">Subject</label>
                        <input type="text" value={emailSubject} onChange={(e) => setEmailSubject(e.target.value)} placeholder="Enter email subject"
                          className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]" />
                      </div>

                      <div>
                        <label className="block text-sm text-[var(--text-secondary)] mb-2">Tone</label>
                        <div className="flex gap-2">
                          {['professional', 'friendly', 'formal'].map((tone) => (
                            <button key={tone} onClick={() => setEmailTone(tone)}
                              className={`px-4 py-2 rounded-xl text-sm capitalize transition-colors ${
                                emailTone === tone
                                  ? 'bg-brand-500/15 border border-brand-500/40 text-brand-500 font-medium'
                                  : 'border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
                              }`}>
                              {tone}
                            </button>
                          ))}
                        </div>
                      </div>

                      <button onClick={generateEmailDraft} disabled={!emailTo || !emailSubject || isProcessing} className="btn-neon w-full disabled:opacity-50 flex items-center justify-center gap-2">
                        <Sparkles size={14} />
                        {isProcessing ? 'Generating...' : 'Generate AI Draft'}
                      </button>

                      <div>
                        <label className="block text-sm text-[var(--text-secondary)] mb-2">Message Body</label>
                        <textarea value={emailBody} onChange={(e) => setEmailBody(e.target.value)} placeholder="Your email content will appear here..." rows={8}
                          className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]" />
                      </div>

                      <div className="flex gap-3">
                        <button onClick={submitEmailForApproval} disabled={!emailTo || !emailSubject || !emailBody || isProcessing} className="btn-neon flex-1 disabled:opacity-50">
                          Save Draft for Approval
                        </button>
                        <button onClick={() => { setEmailTo(''); setEmailSubject(''); setEmailBody(''); }}
                          className="px-4 py-2 rounded-xl border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]">
                          Clear
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ==================== SOCIAL MEDIA TAB ==================== */}
              {activeTab === 'social' && (
                <div className="animate-fade-in">
                  <SocialTab data={data} isProcessing={isProcessing} onRefresh={fetchDashboardData} onToast={showToast} onSwitchTab={setActiveTab} />
                </div>
              )}

              {/* ==================== CRM TAB ==================== */}
              {activeTab === 'crm' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <SummaryCard label="Total Contacts" value={data?.contactStats?.total || 0} icon={<Bot size={20} />} gradient="blue" />
                    <SummaryCard label="Clients" value={data?.contactStats?.clients || 0} icon={<CheckCircle2 size={20} />} gradient="green" />
                    <SummaryCard label="Leads" value={data?.contactStats?.leads || 0} icon={<TrendingUp size={20} />} gradient="orange" />
                    <SummaryCard label="VIPs" value={data?.contactStats?.vips || 0} icon={<Star size={20} />} gradient="purple" />
                  </div>

                  <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]" role="region" aria-label="Contacts list">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-base font-semibold text-[var(--text-primary)]">Contacts</h3>
                      <button onClick={() => setShowAddContactModal(true)} className="btn-neon text-xs flex items-center gap-1">
                        <Plus size={14} /> Add Contact
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full" role="table">
                        <thead>
                          <tr className="border-b border-[var(--border-primary)]">
                            <th className="text-left py-3 px-4 text-xs text-[var(--text-tertiary)] uppercase font-medium">Name</th>
                            <th className="text-left py-3 px-4 text-xs text-[var(--text-tertiary)] uppercase font-medium">Company</th>
                            <th className="text-left py-3 px-4 text-xs text-[var(--text-tertiary)] uppercase font-medium">Type</th>
                            <th className="text-left py-3 px-4 text-xs text-[var(--text-tertiary)] uppercase font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(data?.contacts || []).map((contact) => (
                            <tr key={contact.id} className="border-b border-[var(--border-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors">
                              <td className="py-3 px-4">
                                <div className="flex items-center gap-2">
                                  {contact.is_vip && <Star size={12} className="text-yellow-500" />}
                                  <div>
                                    <div className="text-sm text-[var(--text-primary)]">{contact.name}</div>
                                    <div className="text-xs text-[var(--text-tertiary)]">{contact.email}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="py-3 px-4 text-sm text-[var(--text-secondary)]">{contact.company}</td>
                              <td className="py-3 px-4">
                                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                  contact.type === 'client' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-orange-500/15 text-orange-600 dark:text-orange-400'
                                }`}>{contact.type}</span>
                              </td>
                              <td className="py-3 px-4 text-sm text-[var(--text-secondary)]">{contact.status}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* ==================== FINANCIAL TAB ==================== */}
              {activeTab === 'financial' && (
                <div className="animate-fade-in">
                  <FinanceTab data={data} isProcessing={isProcessing} onRefresh={fetchDashboardData} onToast={showToast} />
                </div>
              )}

              {/* ==================== TASKS TAB ==================== */}
              {activeTab === 'tasks' && (
                <div className="animate-fade-in">
                  <TasksTab data={data} isProcessing={isProcessing} onRefresh={fetchDashboardData} onToast={showToast} />
                </div>
              )}

              {/* ==================== APPROVALS TAB ==================== */}
              {activeTab === 'approvals' && (
                <div className="animate-fade-in">
                  <ApprovalsTab data={data} isProcessing={isProcessing} onRefresh={fetchDashboardData} onToast={showToast} onSwitchTab={setActiveTab} />
                </div>
              )}

              {/* ==================== SETTINGS TAB ==================== */}
              {activeTab === 'settings' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="rounded-2xl p-6 border border-[var(--border-primary)] bg-[var(--bg-card)]" role="region" aria-label="Settings">
                    <h2 className="text-base font-semibold text-[var(--text-primary)] mb-6">Settings & Connections</h2>

                    <div className="space-y-8">
                      {/* Account Connections */}
                      <div>
                        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Connect Your Accounts</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {[
                            { id: 'gmail', name: 'Gmail', desc: 'Read and send emails' },
                            { id: 'linkedin', name: 'LinkedIn', desc: 'Post updates and messages' },
                            { id: 'twitter', name: 'Twitter/X', desc: 'Post tweets and read mentions' },
                            { id: 'whatsapp', name: 'WhatsApp', desc: 'Monitor business messages' },
                            { id: 'slack', name: 'Slack', desc: 'Team communication' },
                            { id: 'calendar', name: 'Google Calendar', desc: 'Manage meetings and events' },
                          ].map((service) => (
                            <div key={service.id} className="rounded-xl p-4 border border-[var(--border-secondary)] bg-[var(--bg-secondary)]">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-medium text-[var(--text-primary)]">{service.name}</p>
                                  <p className="text-xs text-[var(--text-tertiary)]">{service.desc}</p>
                                </div>
                                <button
                                  onClick={() => setConnections(prev => ({ ...prev, [service.id]: !prev[service.id as keyof typeof prev] }))}
                                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                    connections[service.id as keyof typeof connections]
                                      ? 'bg-brand-500/15 text-brand-500 border border-brand-500/40'
                                      : 'border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
                                  }`}
                                >
                                  {connections[service.id as keyof typeof connections] ? 'Connected' : 'Connect'}
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* API Keys */}
                      <div>
                        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">API Configuration</h3>
                        <div className="rounded-xl p-4 border border-[var(--border-secondary)] bg-[var(--bg-secondary)]">
                          <p className="text-sm text-[var(--text-tertiary)] mb-3">API keys are stored locally. Configure in:</p>
                          <code className="block rounded-lg p-3 text-sm text-brand-500 font-mono bg-[var(--bg-primary)] border border-[var(--border-secondary)]">
                            /config/credentials/.env
                          </code>
                          <div className="mt-3 text-xs text-[var(--text-tertiary)]">
                            <p>Required: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN, TWITTER_API_KEY</p>
                          </div>
                        </div>
                      </div>

                      {/* Automation Rules */}
                      <div>
                        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Automation Rules</h3>
                        <div className="space-y-2">
                          {[
                            { key: 'autoEmail', label: 'Auto-categorize incoming emails' },
                            { key: 'vipDrafts', label: 'Draft replies for VIP contacts' },
                            { key: 'invoiceProcess', label: 'Auto-process invoice PDFs' },
                            { key: 'socialSchedule', label: 'Schedule social posts' },
                            { key: 'ceoBriefing', label: 'Weekly CEO briefing' },
                          ].map((rule) => (
                            <div key={rule.key} className="flex items-center justify-between rounded-xl p-4 border border-[var(--border-secondary)] bg-[var(--bg-secondary)]">
                              <span className="text-sm text-[var(--text-primary)]">{rule.label}</span>
                              <button
                                onClick={() => toggleAutomationRule(rule.key as keyof typeof automationRules)}
                                role="switch"
                                aria-checked={automationRules[rule.key as keyof typeof automationRules]}
                                aria-label={rule.label}
                                className={`w-11 h-6 rounded-full relative transition-colors ${
                                  automationRules[rule.key as keyof typeof automationRules] ? 'bg-brand-500' : 'bg-[var(--text-tertiary)]'
                                }`}
                              >
                                <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-transform ${
                                  automationRules[rule.key as keyof typeof automationRules] ? 'translate-x-[22px]' : 'translate-x-0.5'
                                }`} />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* CEO Briefing */}
                      <div>
                        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">Manual Actions</h3>
                        <button onClick={generateCeoBriefing} disabled={isProcessing} className="btn-neon w-full disabled:opacity-50 flex items-center justify-center gap-2">
                          <Sparkles size={14} />
                          Generate CEO Briefing Now
                        </button>
                        <p className="text-xs text-[var(--text-tertiary)] mt-2">
                          Generates a comprehensive business summary including revenue, tasks, and recommendations.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Add Contact Modal */}
      {showAddContactModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-label="Add new contact">
          <div className="rounded-2xl p-6 w-full max-w-md mx-4 border border-[var(--border-primary)] bg-[var(--bg-card)] shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-base font-semibold text-[var(--text-primary)]">Add New Contact</h2>
              <button onClick={() => setShowAddContactModal(false)} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] p-1" aria-label="Close dialog">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-2">Name *</label>
                <input type="text" value={newContact.name} onChange={(e) => setNewContact(prev => ({ ...prev, name: e.target.value }))} placeholder="Enter contact name"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-2">Email *</label>
                <input type="email" value={newContact.email} onChange={(e) => setNewContact(prev => ({ ...prev, email: e.target.value }))} placeholder="email@example.com"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-2">Company</label>
                <input type="text" value={newContact.company} onChange={(e) => setNewContact(prev => ({ ...prev, company: e.target.value }))} placeholder="Company name"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-2">Type</label>
                <select value={newContact.type} onChange={(e) => setNewContact(prev => ({ ...prev, type: e.target.value }))}
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)]">
                  <option value="lead">Lead</option>
                  <option value="client">Client</option>
                  <option value="vendor">Vendor</option>
                  <option value="partner">Partner</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button onClick={handleAddContact} disabled={!newContact.name || !newContact.email || isProcessing} className="btn-neon flex-1 disabled:opacity-50">
                  {isProcessing ? 'Adding...' : 'Add Contact'}
                </button>
                <button onClick={() => setShowAddContactModal(false)} className="px-4 py-2 rounded-xl border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
