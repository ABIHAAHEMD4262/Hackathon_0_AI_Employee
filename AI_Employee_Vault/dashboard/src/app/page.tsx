'use client';

import { useState, useEffect, useRef } from 'react';

// ==================== TYPE DEFINITIONS ====================
interface Contact {
  id: string;
  name: string;
  email: string;
  company: string;
  type: string;
  status: string;
  is_vip: boolean;
  lead_stage?: string;
  lead_value?: number;
}

interface Invoice {
  id: string;
  type: string;
  client_name?: string;
  vendor_name?: string;
  status: string;
  due_date: string;
  line_items: Array<{ quantity: number; unit_price: number }>;
  discount?: number;
}

interface Task {
  id: string;
  title: string;
  project_id: string;
  status: string;
  priority: string;
  due_date?: string;
}

interface Project {
  id: string;
  name: string;
  client: string;
  status: string;
  budget: number;
  budget_spent: number;
  deadline: string;
}

interface Email {
  id: string;
  from: string;
  subject: string;
  received: string;
  priority: string;
  status: string;
  snippet: string;
}

interface DashboardData {
  stats: { needsAction: number; inProgress: number; pendingApproval: number; completedToday: number };
  pendingApprovals: Array<{ id: string; type: string; title: string; created: string; preview: string }>;
  activities: Array<{ id: string; action: string; timestamp: string; status: string }>;
  contacts?: Contact[];
  contactStats?: { total: number; clients: number; leads: number; vips: number };
  invoices?: Invoice[];
  expenses?: Array<{ id: string; description: string; amount: number; category: string; date: string }>;
  financialStats?: { outstandingAR: number; outstandingAP: number; totalExpenses: number; pipelineValue: number };
  projects?: Project[];
  tasks?: Task[];
  taskStats?: { total: number; todo: number; in_progress: number; completed: number; blocked: number; overdue: number };
  emails?: Email[];
}

interface CommandHistoryItem {
  id: string;
  command: string;
  response: string;
  timestamp: Date;
  status: 'pending' | 'completed' | 'error';
}

// ==================== AI AGENTS ====================
const AI_AGENTS = [
  { id: 'email', name: 'Email Agent', icon: '📧', color: 'from-blue-500 to-cyan-500', status: 'online' },
  { id: 'social', name: 'Social Agent', icon: '📱', color: 'from-purple-500 to-pink-500', status: 'online' },
  { id: 'task', name: 'Task Agent', icon: '⚡', color: 'from-orange-500 to-yellow-500', status: 'online' },
  { id: 'crm', name: 'CRM Agent', icon: '👥', color: 'from-teal-500 to-cyan-500', status: 'online' },
  { id: 'finance', name: 'Finance Agent', icon: '💰', color: 'from-emerald-500 to-green-500', status: 'online' },
  { id: 'approval', name: 'Approval Agent', icon: '🛡️', color: 'from-green-500 to-emerald-500', status: 'online' },
];

// ==================== TAB DEFINITIONS ====================
const TABS = [
  { id: 'command', label: 'Command Center', icon: '🎮' },
  { id: 'email', label: 'Email', icon: '📧' },
  { id: 'social', label: 'Social Media', icon: '📱' },
  { id: 'crm', label: 'CRM', icon: '👥' },
  { id: 'financial', label: 'Financial', icon: '💰' },
  { id: 'tasks', label: 'Tasks', icon: '✅' },
  { id: 'approvals', label: 'Approvals', icon: '🔐' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

// ==================== MAIN DASHBOARD COMPONENT ====================
export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('command');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Command Center State
  const [commandInput, setCommandInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<CommandHistoryItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Email Composer State
  const [emailTo, setEmailTo] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [emailTone, setEmailTone] = useState('professional');

  // Social Media State
  const [socialPlatform, setSocialPlatform] = useState('linkedin');
  const [socialContent, setSocialContent] = useState('');
  const [socialTopic, setSocialTopic] = useState('');

  // Upload State
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Settings State
  const [connections, setConnections] = useState({
    gmail: false,
    linkedin: false,
    twitter: false,
    whatsapp: false,
    slack: false,
    calendar: false,
  });

  // Automation Rules State
  const [automationRules, setAutomationRules] = useState({
    autoEmail: true,
    vipDrafts: true,
    invoiceProcess: true,
    socialSchedule: false,
    ceoBriefing: true,
  });

  // Modal States
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const [showAddContactModal, setShowAddContactModal] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', priority: 'medium', due_date: '' });
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
      setData(json);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch:', error);
    } finally {
      setLoading(false);
    }
  }

  // ==================== COMMAND PROCESSING ====================
  async function processCommand(command: string) {
    const newCommand: CommandHistoryItem = {
      id: Date.now().toString(),
      command,
      response: '',
      timestamp: new Date(),
      status: 'pending',
    };
    setCommandHistory(prev => [newCommand, ...prev]);
    setIsProcessing(true);
    setCommandInput('');

    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 1500));

    let response = '';
    const lowerCommand = command.toLowerCase();

    if (lowerCommand.includes('linkedin') && lowerCommand.includes('post')) {
      const topic = command.replace(/.*post about|.*post on|.*write about/gi, '').trim();
      response = `📝 **LinkedIn Post Draft Created**\n\nTopic: "${topic}"\n\n---\n\nI've drafted a LinkedIn post for you. Please review it in the **Social Media** tab and approve before posting.\n\n✅ Draft saved to Approvals queue.`;
      setSocialPlatform('linkedin');
      setSocialTopic(topic);
      setActiveTab('social');
    } else if (lowerCommand.includes('email') && (lowerCommand.includes('send') || lowerCommand.includes('draft') || lowerCommand.includes('write'))) {
      response = `📧 **Email Draft Started**\n\nI've opened the Email Composer for you. Please fill in the recipient and I'll help draft the message.\n\n➡️ Switching to Email tab...`;
      setActiveTab('email');
    } else if (lowerCommand.includes('invoice') || lowerCommand.includes('pdf')) {
      response = `📄 **Invoice Processing**\n\nYou can upload invoice PDFs in the **Financial** tab. I'll automatically:\n- Extract vendor/client info\n- Categorize the expense\n- Add to your financial tracking\n\n➡️ Switching to Financial tab...`;
      setActiveTab('financial');
    } else if (lowerCommand.includes('contact') || lowerCommand.includes('client') || lowerCommand.includes('lead')) {
      response = `👥 **CRM Update**\n\nI can help you:\n- Add new contacts\n- Update client information\n- Track lead status\n\n➡️ Switching to CRM tab...`;
      setActiveTab('crm');
    } else if (lowerCommand.includes('task') || lowerCommand.includes('todo') || lowerCommand.includes('project')) {
      response = `✅ **Task Management**\n\nI can help you:\n- Create new tasks\n- Update project status\n- Set deadlines\n\n➡️ Switching to Tasks tab...`;
      setActiveTab('tasks');
    } else if (lowerCommand.includes('status') || lowerCommand.includes('summary') || lowerCommand.includes('briefing')) {
      const stats = data?.stats;
      response = `📊 **Daily Status Summary**\n\n` +
        `• **Awaiting Action:** ${stats?.needsAction || 0} items\n` +
        `• **In Progress:** ${stats?.inProgress || 0} tasks\n` +
        `• **Pending Approval:** ${stats?.pendingApproval || 0} items\n` +
        `• **Completed Today:** ${stats?.completedToday || 0} tasks\n\n` +
        `**Financial:**\n` +
        `• Outstanding AR: $${(data?.financialStats?.outstandingAR || 0).toLocaleString()}\n` +
        `• Pipeline Value: $${(data?.financialStats?.pipelineValue || 0).toLocaleString()}\n\n` +
        `All ${AI_AGENTS.length} agents are online and operational.`;
    } else {
      response = `🤖 **Command Received**\n\n"${command}"\n\nI understand you want me to: ${command}\n\n` +
        `I'll process this request. Here are some example commands:\n` +
        `• "Write a LinkedIn post about AI automation"\n` +
        `• "Draft an email to John about the project"\n` +
        `• "Show me today's status summary"\n` +
        `• "Upload invoice for processing"\n` +
        `• "Add new contact"\n` +
        `• "Create task for tomorrow"`;
    }

    setCommandHistory(prev =>
      prev.map(item =>
        item.id === newCommand.id
          ? { ...item, response, status: 'completed' }
          : item
      )
    );
    setIsProcessing(false);
  }

  // ==================== AI GENERATION FUNCTIONS ====================
  async function generateEmailDraft() {
    if (!emailTo || !emailSubject) return;
    setIsProcessing(true);

    await new Promise(resolve => setTimeout(resolve, 1000));

    const toneStyles: Record<string, string> = {
      professional: `Dear ${emailTo.split('@')[0]},\n\nI hope this email finds you well.\n\nRegarding ${emailSubject}, I wanted to reach out to discuss the details and next steps.\n\nPlease let me know your availability for a brief call to discuss further.\n\nBest regards`,
      friendly: `Hey ${emailTo.split('@')[0]}!\n\nHope you're doing great! 😊\n\nJust wanted to touch base about ${emailSubject}.\n\nLet me know what you think!\n\nCheers`,
      formal: `Dear Sir/Madam,\n\nI am writing to formally address the matter of ${emailSubject}.\n\nI would appreciate your prompt attention to this matter.\n\nYours faithfully`,
    };

    setEmailBody(toneStyles[emailTone] || toneStyles.professional);
    setIsProcessing(false);
  }

  async function generateSocialPost() {
    if (!socialTopic) return;
    setIsProcessing(true);

    await new Promise(resolve => setTimeout(resolve, 1500));

    const posts: Record<string, string> = {
      linkedin: `🚀 ${socialTopic}\n\nIn today's rapidly evolving landscape, staying ahead means embracing innovation.\n\nHere are 3 key insights:\n\n1️⃣ Automation is the future\n2️⃣ AI enhances human capabilities\n3️⃣ Early adopters win\n\nWhat's your take on ${socialTopic.toLowerCase()}?\n\n#Innovation #AI #FutureOfWork #Automation`,
      twitter: `🧵 Thread on ${socialTopic}:\n\n1/ The future is here, and it's automated.\n\n2/ Key insight: AI doesn't replace humans—it amplifies them.\n\n3/ Early adopters are seeing 10x productivity gains.\n\nWhat's your experience? 👇\n\n#AI #Automation`,
      facebook: `📢 Exciting thoughts on ${socialTopic}!\n\nI've been exploring how AI and automation are transforming the way we work. The results? Mind-blowing. 🤯\n\nWould love to hear your thoughts in the comments!\n\n#Innovation #Technology`,
      instagram: `✨ ${socialTopic}\n\n📍 The future of work is here\n🎯 AI + Humans = Unstoppable\n💡 Innovation drives success\n\nDouble tap if you agree! 💪\n\n#AIRevolution #FutureOfWork #Innovation #TechTrends`,
    };

    setSocialContent(posts[socialPlatform] || posts.linkedin);
    setIsProcessing(false);
  }

  // ==================== FILE UPLOAD ====================
  function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (files) {
      setUploadedFiles(prev => [...prev, ...Array.from(files)]);
    }
  }

  async function processUploadedFile(file: File) {
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Add to command history
    const newCommand: CommandHistoryItem = {
      id: Date.now().toString(),
      command: `Upload: ${file.name}`,
      response: `📄 **File Processed: ${file.name}**\n\n` +
        `• Type: ${file.type || 'Unknown'}\n` +
        `• Size: ${(file.size / 1024).toFixed(2)} KB\n\n` +
        `✅ File has been processed and added to your records.\n` +
        `📋 If this is an invoice, it's been added to the Financial tab.`,
      timestamp: new Date(),
      status: 'completed',
    };
    setCommandHistory(prev => [newCommand, ...prev]);
    setUploadedFiles(prev => prev.filter(f => f !== file));
    setIsProcessing(false);
  }

  // ==================== APPROVAL ACTIONS ====================
  async function handleApproval(id: string, approved: boolean) {
    setIsProcessing(true);

    try {
      const response = await fetch('/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, action: approved ? 'approve' : 'reject' }),
      });

      const result = await response.json();

      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `${approved ? 'Approve' : 'Reject'} item ${id}`,
        response: result.success
          ? (approved
            ? `✅ **Approved!** Item ${id} has been approved and will be executed.`
            : `❌ **Rejected.** Item ${id} has been rejected and archived.`)
          : `⚠️ Error: ${result.error || 'Unknown error'}`,
        timestamp: new Date(),
        status: result.success ? 'completed' : 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);

      // Refresh data to update approvals list
      await fetchDashboardData();
    } catch (error) {
      console.error('Approval error:', error);
      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `${approved ? 'Approve' : 'Reject'} item ${id}`,
        response: `⚠️ Error processing approval. Please try again.`,
        timestamp: new Date(),
        status: 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);
    }

    setIsProcessing(false);
  }

  // ==================== SUBMIT HANDLERS ====================
  async function submitEmailForApproval() {
    if (!emailTo || !emailSubject || !emailBody) return;
    setIsProcessing(true);

    try {
      const response = await fetch('/api/drafts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'email_draft',
          data: {
            to: emailTo,
            subject: emailSubject,
            body: emailBody,
            tone: emailTone,
          },
        }),
      });

      const result = await response.json();

      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `Email draft to ${emailTo}`,
        response: result.success
          ? `📧 **Email Draft Saved for Approval**\n\n` +
            `• To: ${emailTo}\n` +
            `• Subject: ${emailSubject}\n\n` +
            `✅ Check the **Approvals** tab to review and send.`
          : `⚠️ Error: ${result.error || 'Failed to save draft'}`,
        timestamp: new Date(),
        status: result.success ? 'completed' : 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);

      if (result.success) {
        setEmailTo('');
        setEmailSubject('');
        setEmailBody('');
        await fetchDashboardData();
        setActiveTab('approvals');
      }
    } catch (error) {
      console.error('Submit email error:', error);
    }

    setIsProcessing(false);
  }

  async function submitSocialForApproval() {
    if (!socialContent) return;
    setIsProcessing(true);

    try {
      const response = await fetch('/api/drafts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'social_post',
          data: {
            platform: socialPlatform,
            topic: socialTopic,
            content: socialContent,
          },
        }),
      });

      const result = await response.json();

      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `${socialPlatform} post draft`,
        response: result.success
          ? `📱 **${socialPlatform.charAt(0).toUpperCase() + socialPlatform.slice(1)} Post Saved for Approval**\n\n` +
            `✅ Check the **Approvals** tab to review and post.`
          : `⚠️ Error: ${result.error || 'Failed to save draft'}`,
        timestamp: new Date(),
        status: result.success ? 'completed' : 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);

      if (result.success) {
        setSocialContent('');
        setSocialTopic('');
        await fetchDashboardData();
        setActiveTab('approvals');
      }
    } catch (error) {
      console.error('Submit social error:', error);
    }

    setIsProcessing(false);
  }

  // ==================== ADD TASK HANDLER ====================
  async function handleAddTask() {
    if (!newTask.title) return;
    setIsProcessing(true);

    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTask),
      });

      const result = await response.json();

      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `Create task: ${newTask.title}`,
        response: result.success
          ? `✅ **Task Created**\n\n• Title: ${newTask.title}\n• Priority: ${newTask.priority}\n• Due: ${newTask.due_date || 'Not set'}`
          : `⚠️ Error: ${result.error || 'Failed to create task'}`,
        timestamp: new Date(),
        status: result.success ? 'completed' : 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);

      if (result.success) {
        setNewTask({ title: '', priority: 'medium', due_date: '' });
        setShowAddTaskModal(false);
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Add task error:', error);
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

      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `Add contact: ${newContact.name}`,
        response: result.success
          ? `✅ **Contact Added**\n\n• Name: ${newContact.name}\n• Email: ${newContact.email}\n• Company: ${newContact.company || 'Not set'}\n• Type: ${newContact.type}`
          : `⚠️ Error: ${result.error || 'Failed to add contact'}`,
        timestamp: new Date(),
        status: result.success ? 'completed' : 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);

      if (result.success) {
        setNewContact({ name: '', email: '', company: '', type: 'lead' });
        setShowAddContactModal(false);
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Add contact error:', error);
    }

    setIsProcessing(false);
  }

  // ==================== GENERATE CEO BRIEFING ====================
  async function generateCeoBriefing() {
    setIsProcessing(true);

    const newCommand: CommandHistoryItem = {
      id: Date.now().toString(),
      command: 'Generate CEO Briefing',
      response: '',
      timestamp: new Date(),
      status: 'pending',
    };
    setCommandHistory(prev => [newCommand, ...prev]);

    try {
      const response = await fetch('/api/briefing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'ceo_briefing' }),
      });

      const result = await response.json();

      setCommandHistory(prev =>
        prev.map(item =>
          item.id === newCommand.id
            ? {
                ...item,
                response: result.success
                  ? `📊 **CEO Briefing Generated**\n\n${result.briefing || 'Briefing saved to Business/CEO_Briefings/'}\n\n✅ View in the Obsidian vault.`
                  : `⚠️ Error: ${result.error || 'Failed to generate briefing'}`,
                status: result.success ? 'completed' : 'error',
              }
            : item
        )
      );
    } catch (error) {
      console.error('CEO Briefing error:', error);
      setCommandHistory(prev =>
        prev.map(item =>
          item.id === newCommand.id
            ? { ...item, response: '⚠️ Error generating briefing', status: 'error' }
            : item
        )
      );
    }

    setIsProcessing(false);
  }

  // ==================== TOGGLE AUTOMATION RULE ====================
  function toggleAutomationRule(ruleKey: keyof typeof automationRules) {
    setAutomationRules(prev => ({ ...prev, [ruleKey]: !prev[ruleKey] }));
  }

  // ==================== AUTO REPLY TO EMAIL ====================
  async function handleAutoReply(email: Email) {
    setIsProcessing(true);

    const newCommand: CommandHistoryItem = {
      id: Date.now().toString(),
      command: `Auto-reply to: ${email.from}`,
      response: '',
      timestamp: new Date(),
      status: 'pending',
    };
    setCommandHistory(prev => [newCommand, ...prev]);

    try {
      const response = await fetch('/api/auto-reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          emailId: email.id,
          from: email.from,
          subject: email.subject,
          snippet: email.snippet,
        }),
      });

      const result = await response.json();

      setCommandHistory(prev =>
        prev.map(item =>
          item.id === newCommand.id
            ? {
                ...item,
                response: result.success
                  ? `✅ **Auto-Reply Sent!**\n\n• To: ${email.from}\n• Subject: Re: ${email.subject}\n\n${result.message || 'Email sent successfully.'}`
                  : `⚠️ Error: ${result.error || 'Failed to send auto-reply'}`,
                status: result.success ? 'completed' : 'error',
              }
            : item
        )
      );

      if (result.success) {
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Auto-reply error:', error);
      setCommandHistory(prev =>
        prev.map(item =>
          item.id === newCommand.id
            ? { ...item, response: '⚠️ Error sending auto-reply', status: 'error' }
            : item
        )
      );
    }

    setIsProcessing(false);
  }

  // ==================== ARCHIVE EMAIL ====================
  async function handleArchiveEmail(emailId: string) {
    setIsProcessing(true);

    try {
      const response = await fetch('/api/emails', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: emailId, action: 'archive' }),
      });

      const result = await response.json();

      const newCommand: CommandHistoryItem = {
        id: Date.now().toString(),
        command: `Archive email: ${emailId}`,
        response: result.success
          ? '✅ Email archived successfully'
          : `⚠️ Error: ${result.error || 'Failed to archive'}`,
        timestamp: new Date(),
        status: result.success ? 'completed' : 'error',
      };
      setCommandHistory(prev => [newCommand, ...prev]);

      if (result.success) {
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Archive error:', error);
    }

    setIsProcessing(false);
  }

  // ==================== RENDER LOADING ====================
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] bg-grid flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-[#00ff88]/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[#00ff88] animate-spin"></div>
            <div className="absolute inset-4 rounded-full bg-[#00ff88]/10 flex items-center justify-center">
              <span className="text-3xl">🤖</span>
            </div>
          </div>
          <h2 className="text-[#00ff88] text-xl font-bold glow-text">INITIALIZING</h2>
          <p className="text-gray-500 mt-2">Loading AI Employee...</p>
        </div>
      </div>
    );
  }

  // ==================== MAIN RENDER ====================
  return (
    <div className="min-h-screen bg-[#0a0a0f] bg-grid hex-pattern text-gray-100">
      {/* Header */}
      <header className="border-b border-[#00ff88]/20 backdrop-blur-sm bg-[#0a0a0f]/80 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="agent-avatar w-12 h-12 rounded-full bg-gradient-to-br from-[#00ff88] to-[#00d4ff] flex items-center justify-center text-2xl">
                🤖
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">AI EMPLOYEE</h1>
                <p className="text-sm text-gray-500 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full status-online"></span>
                  {AI_AGENTS.length} Agents Online • Ready to assist
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500 uppercase">Last Sync</p>
              <p className="text-[#00ff88] font-mono">{lastUpdated.toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="border-b border-gray-800 bg-[#0a0a0f]/90 sticky top-[73px] z-40">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto py-2">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-[#00ff88]/20 border border-[#00ff88]/50 text-[#00ff88]'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.id === 'approvals' && (data?.pendingApprovals?.length || 0) > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-[#ff9f43]/20 text-[#ff9f43]">
                    {data?.pendingApprovals?.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* ==================== COMMAND CENTER TAB ==================== */}
        {activeTab === 'command' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'AWAITING ACTION', value: data?.stats.needsAction || 0, icon: '⚠️', color: '#ff9f43' },
                { label: 'PROCESSING', value: data?.stats.inProgress || 0, icon: '⚡', color: '#00d4ff' },
                { label: 'PENDING APPROVAL', value: data?.stats.pendingApproval || 0, icon: '🔒', color: '#b347ff' },
                { label: 'COMPLETED TODAY', value: data?.stats.completedToday || 0, icon: '✅', color: '#00ff88' },
              ].map((stat, i) => (
                <div key={i} className="glass-card p-4 card-hover">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{stat.icon}</span>
                    <span className="text-3xl font-bold font-mono" style={{ color: stat.color }}>{stat.value}</span>
                  </div>
                  <p className="text-xs text-gray-500 uppercase">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Command Input */}
            <div style={{
              background: 'rgba(20, 20, 35, 0.9)',
              border: '2px solid #00ff88',
              borderRadius: '16px',
              padding: '24px',
              marginBottom: '24px'
            }}>
              <h2 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                <span>🎮</span> Command Center
              </h2>
              <p className="text-gray-500 text-sm mb-4">
                Tell me what you need. I can draft emails, create social posts, manage tasks, process invoices, and more.
              </p>
              <div style={{ display: 'flex', gap: '12px' }}>
                <input
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && commandInput && processCommand(commandInput)}
                  placeholder="Try: 'Write a LinkedIn post about AI automation' or 'Draft email to client'"
                  disabled={isProcessing}
                  style={{
                    flex: 1,
                    background: '#0a0a0f',
                    border: '1px solid #444',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    color: '#e0e0e0',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={() => commandInput && processCommand(commandInput)}
                  disabled={!commandInput || isProcessing}
                  style={{
                    background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 212, 255, 0.2))',
                    border: '1px solid #00ff88',
                    color: '#00ff88',
                    padding: '12px 24px',
                    borderRadius: '8px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    opacity: (!commandInput || isProcessing) ? 0.5 : 1
                  }}
                >
                  {isProcessing ? '...' : 'Send'}
                </button>
              </div>

              {/* Quick Actions */}
              <div className="mt-4 flex flex-wrap gap-2">
                {[
                  { label: '📧 Draft Email', cmd: 'Draft an email' },
                  { label: '💼 LinkedIn Post', cmd: 'Write a LinkedIn post about my business' },
                  { label: '📊 CEO Briefing', cmd: 'Generate CEO briefing', action: generateCeoBriefing },
                  { label: '📄 Upload Invoice', cmd: 'Upload invoice for processing' },
                  { label: '✅ Create Task', cmd: 'Create a new task' },
                ].map((quickAction, i) => (
                  <button
                    key={i}
                    onClick={() => quickAction.action ? quickAction.action() : processCommand(quickAction.cmd)}
                    className="text-xs px-3 py-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-all"
                  >
                    {quickAction.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Command History */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold gradient-text mb-4">Activity Log</h3>
              <div className="space-y-4 max-h-[400px] overflow-y-auto">
                {commandHistory.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No commands yet. Try asking me something!</p>
                ) : (
                  commandHistory.map((item) => (
                    <div key={item.id} className="bg-[#0a0a0f]/50 rounded-lg p-4 border border-gray-800">
                      <div className="flex items-start gap-3">
                        <span className="text-xl">👤</span>
                        <div className="flex-1">
                          <p className="text-gray-200 font-medium">{item.command}</p>
                          <p className="text-xs text-gray-600 mt-1">{item.timestamp.toLocaleTimeString()}</p>
                        </div>
                      </div>
                      {item.response && (
                        <div className="mt-3 pl-8 border-l-2 border-[#00ff88]/30">
                          <div className="flex items-start gap-3">
                            <span className="text-xl">🤖</span>
                            <div className="flex-1">
                              <pre className="text-gray-400 text-sm whitespace-pre-wrap font-sans">{item.response}</pre>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Active Agents */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold gradient-text mb-4">Active AI Agents</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {AI_AGENTS.map((agent) => (
                  <div key={agent.id} className="bg-[#0a0a0f]/50 rounded-lg p-3 border border-gray-800 text-center">
                    <div className={`w-10 h-10 mx-auto rounded-lg bg-gradient-to-br ${agent.color} flex items-center justify-center text-xl mb-2`}>
                      {agent.icon}
                    </div>
                    <p className="text-sm font-medium text-gray-300">{agent.name}</p>
                    <div className="flex items-center justify-center gap-1 mt-1">
                      <span className="w-2 h-2 rounded-full bg-[#00ff88]"></span>
                      <span className="text-[10px] text-[#00ff88]">Online</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ==================== EMAIL TAB ==================== */}
        {activeTab === 'email' && (
          <div className="space-y-6">
            {/* Email Inbox */}
            <div className="glass-card p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold gradient-text flex items-center gap-2">
                  <span>📥</span> Inbox
                </h2>
                <button
                  onClick={fetchDashboardData}
                  className="text-xs px-3 py-1 rounded bg-white/5 text-gray-400 hover:bg-white/10"
                >
                  🔄 Refresh
                </button>
              </div>
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {data?.emails && data.emails.length > 0 ? (
                  data.emails.slice(0, 10).map((email) => (
                    <div key={email.id} className="flex items-start gap-3 p-3 rounded-lg bg-[#0a0a0f]/50 border border-gray-800 hover:border-gray-700 cursor-pointer">
                      <div className={`w-2 h-2 rounded-full mt-2 ${email.priority === 'high' ? 'bg-[#ff4757]' : 'bg-[#00ff88]'}`}></div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start gap-2">
                          <p className="text-sm font-medium text-gray-200 truncate">{email.from}</p>
                          <span className="text-[10px] text-gray-500 whitespace-nowrap">
                            {new Date(email.received).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300 truncate">{email.subject}</p>
                        <p className="text-xs text-gray-500 truncate">{email.snippet}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <span className="text-4xl block mb-2 opacity-50">📭</span>
                    <p className="text-gray-500 text-sm">No emails in inbox.</p>
                    <p className="text-gray-600 text-xs mt-1">Run the Gmail watcher to fetch new emails.</p>
                  </div>
                )}
              </div>
              {data?.emails && data.emails.length > 10 && (
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Showing 10 of {data.emails.length} emails
                </p>
              )}
            </div>

            {/* Email Composer */}
            <div className="glass-card p-6">
              <h2 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                <span>📧</span> Compose Email
              </h2>
              <p className="text-gray-500 text-sm mb-6">
                Compose emails with AI assistance. Drafts require your approval before sending.
              </p>

              <div className="space-y-4">
                {/* Recipient */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">To (Email Address)</label>
                  <input
                    type="email"
                    value={emailTo}
                    onChange={(e) => setEmailTo(e.target.value)}
                    placeholder="recipient@example.com"
                    className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                  />
                  {data?.contacts && data.contacts.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="text-xs text-gray-500">Quick select:</span>
                      {data.contacts.slice(0, 5).map((contact) => (
                        <button
                          key={contact.id}
                          onClick={() => setEmailTo(contact.email)}
                          className="text-xs px-2 py-1 rounded bg-white/5 text-gray-400 hover:bg-white/10"
                        >
                          {contact.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Subject */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Subject</label>
                  <input
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    placeholder="Enter email subject"
                    className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                  />
                </div>

                {/* Tone Selector */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Tone</label>
                  <div className="flex gap-2">
                    {['professional', 'friendly', 'formal'].map((tone) => (
                      <button
                        key={tone}
                        onClick={() => setEmailTone(tone)}
                        className={`px-4 py-2 rounded-lg text-sm capitalize ${
                          emailTone === tone
                            ? 'bg-[#00ff88]/20 border border-[#00ff88]/50 text-[#00ff88]'
                            : 'bg-white/5 text-gray-400 hover:bg-white/10'
                        }`}
                      >
                        {tone}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  onClick={generateEmailDraft}
                  disabled={!emailTo || !emailSubject || isProcessing}
                  className="btn-neon w-full disabled:opacity-50"
                >
                  {isProcessing ? 'Generating...' : '✨ Generate AI Draft'}
                </button>

                {/* Body */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Message Body</label>
                  <textarea
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    placeholder="Your email content will appear here..."
                    rows={8}
                    className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                  />
                </div>

                {/* Submit */}
                <div className="flex gap-3">
                  <button
                    onClick={submitEmailForApproval}
                    disabled={!emailTo || !emailSubject || !emailBody || isProcessing}
                    className="btn-neon flex-1 disabled:opacity-50"
                  >
                    📝 Save Draft for Approval
                  </button>
                  <button
                    onClick={() => { setEmailTo(''); setEmailSubject(''); setEmailBody(''); }}
                    className="px-4 py-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================== SOCIAL MEDIA TAB ==================== */}
        {activeTab === 'social' && (
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h2 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                <span>📱</span> Social Media Composer
              </h2>
              <p className="text-gray-500 text-sm mb-6">
                Create engaging social media posts with AI. All posts require approval before publishing.
              </p>

              <div className="space-y-4">
                {/* Platform Selector */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Platform</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: '#0077b5' },
                      { id: 'twitter', name: 'Twitter/X', icon: '🐦', color: '#1da1f2' },
                      { id: 'facebook', name: 'Facebook', icon: '📘', color: '#1877f2' },
                      { id: 'instagram', name: 'Instagram', icon: '📸', color: '#e4405f' },
                    ].map((platform) => (
                      <button
                        key={platform.id}
                        onClick={() => setSocialPlatform(platform.id)}
                        className={`p-4 rounded-lg border text-center transition-all ${
                          socialPlatform === platform.id
                            ? 'border-[#00ff88]/50 bg-[#00ff88]/10'
                            : 'border-gray-700 bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <span className="text-2xl block mb-1">{platform.icon}</span>
                        <span className="text-sm text-gray-300">{platform.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Topic Input */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">What should I write about?</label>
                  <input
                    type="text"
                    value={socialTopic}
                    onChange={(e) => setSocialTopic(e.target.value)}
                    placeholder="e.g., AI automation, productivity tips, business growth..."
                    className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                  />
                </div>

                {/* Generate Button */}
                <button
                  onClick={generateSocialPost}
                  disabled={!socialTopic || isProcessing}
                  className="btn-neon w-full disabled:opacity-50"
                >
                  {isProcessing ? 'Generating...' : `✨ Generate ${socialPlatform.charAt(0).toUpperCase() + socialPlatform.slice(1)} Post`}
                </button>

                {/* Content */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Post Content</label>
                  <textarea
                    value={socialContent}
                    onChange={(e) => setSocialContent(e.target.value)}
                    placeholder="Your post content will appear here..."
                    rows={8}
                    className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                  />
                  <div className="mt-2 flex justify-between text-xs text-gray-500">
                    <span>Characters: {socialContent.length}</span>
                    <span>{socialPlatform === 'twitter' ? 'Max: 280' : socialPlatform === 'linkedin' ? 'Max: 3,000' : 'No limit'}</span>
                  </div>
                </div>

                {/* Submit */}
                <div className="flex gap-3">
                  <button
                    onClick={submitSocialForApproval}
                    disabled={!socialContent || isProcessing}
                    className="btn-neon flex-1 disabled:opacity-50"
                  >
                    📝 Save for Approval
                  </button>
                  <button
                    onClick={() => { setSocialContent(''); setSocialTopic(''); }}
                    className="px-4 py-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>

            {/* Connection Status */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold gradient-text mb-4">Connection Status</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { name: 'LinkedIn', connected: connections.linkedin },
                  { name: 'Twitter/X', connected: connections.twitter },
                  { name: 'Facebook', connected: false },
                  { name: 'Instagram', connected: false },
                ].map((platform, i) => (
                  <div key={i} className="bg-[#0a0a0f]/50 rounded-lg p-4 border border-gray-800">
                    <p className="text-gray-300 font-medium mb-2">{platform.name}</p>
                    {platform.connected ? (
                      <span className="text-xs text-[#00ff88] flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-[#00ff88]"></span> Connected
                      </span>
                    ) : (
                      <button
                        onClick={() => setActiveTab('settings')}
                        className="text-xs text-[#ff9f43] hover:underline"
                      >
                        Connect →
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ==================== CRM TAB ==================== */}
        {activeTab === 'crm' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Total Contacts', value: data?.contactStats?.total || 0, color: '#00d4ff' },
                { label: 'Clients', value: data?.contactStats?.clients || 0, color: '#00ff88' },
                { label: 'Leads', value: data?.contactStats?.leads || 0, color: '#ff9f43' },
                { label: 'VIPs', value: data?.contactStats?.vips || 0, color: '#b347ff' },
              ].map((stat, i) => (
                <div key={i} className="glass-card p-4 text-center">
                  <div className="text-3xl font-bold font-mono" style={{ color: stat.color }}>{stat.value}</div>
                  <p className="text-xs text-gray-500 uppercase mt-1">{stat.label}</p>
                </div>
              ))}
            </div>

            <div className="glass-card p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold gradient-text">Contacts</h3>
                <button onClick={() => setShowAddContactModal(true)} className="btn-neon text-xs">+ Add Contact</button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Name</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Company</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Type</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.contacts || []).map((contact) => (
                      <tr key={contact.id} className="border-b border-gray-800/50 hover:bg-white/5">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {contact.is_vip && <span className="text-yellow-400">⭐</span>}
                            <div>
                              <div className="text-gray-200">{contact.name}</div>
                              <div className="text-xs text-gray-500">{contact.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-400">{contact.company}</td>
                        <td className="py-3 px-4">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            contact.type === 'client' ? 'bg-[#00ff88]/20 text-[#00ff88]' : 'bg-[#ff9f43]/20 text-[#ff9f43]'
                          }`}>{contact.type}</span>
                        </td>
                        <td className="py-3 px-4 text-gray-400">{contact.status}</td>
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
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Outstanding AR', value: `$${(data?.financialStats?.outstandingAR || 0).toLocaleString()}`, color: '#00ff88' },
                { label: 'Outstanding AP', value: `$${(data?.financialStats?.outstandingAP || 0).toLocaleString()}`, color: '#ff9f43' },
                { label: 'Expenses', value: `$${(data?.financialStats?.totalExpenses || 0).toLocaleString()}`, color: '#ff4757' },
                { label: 'Pipeline', value: `$${(data?.financialStats?.pipelineValue || 0).toLocaleString()}`, color: '#00d4ff' },
              ].map((stat, i) => (
                <div key={i} className="glass-card p-4 text-center">
                  <div className="text-2xl font-bold font-mono" style={{ color: stat.color }}>{stat.value}</div>
                  <p className="text-xs text-gray-500 uppercase mt-1">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Upload Section */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold gradient-text mb-4">📄 Upload Invoice/Receipt</h3>
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center cursor-pointer hover:border-[#00ff88]/50 transition-all"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".pdf,.png,.jpg,.jpeg"
                  multiple
                  className="hidden"
                />
                <span className="text-4xl block mb-3">📁</span>
                <p className="text-gray-400">Click or drag files to upload</p>
                <p className="text-xs text-gray-500 mt-2">Supports PDF, PNG, JPG</p>
              </div>

              {uploadedFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                  {uploadedFiles.map((file, i) => (
                    <div key={i} className="flex items-center justify-between bg-[#0a0a0f]/50 rounded-lg p-3 border border-gray-800">
                      <div className="flex items-center gap-3">
                        <span className="text-xl">📄</span>
                        <div>
                          <p className="text-gray-200">{file.name}</p>
                          <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                        </div>
                      </div>
                      <button
                        onClick={() => processUploadedFile(file)}
                        disabled={isProcessing}
                        className="btn-neon text-xs disabled:opacity-50"
                      >
                        Process
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Invoices Table */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold gradient-text mb-4">Invoices</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">ID</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Client/Vendor</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Type</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Amount</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Due</th>
                      <th className="text-left py-3 px-4 text-xs text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.invoices || []).map((inv) => (
                      <tr key={inv.id} className="border-b border-gray-800/50 hover:bg-white/5">
                        <td className="py-3 px-4 font-mono text-sm text-gray-300">{inv.id}</td>
                        <td className="py-3 px-4 text-gray-400">{inv.client_name || inv.vendor_name}</td>
                        <td className="py-3 px-4">
                          <span className={`text-xs px-2 py-1 rounded-full ${inv.type === 'sent' ? 'bg-[#00ff88]/20 text-[#00ff88]' : 'bg-[#ff9f43]/20 text-[#ff9f43]'}`}>
                            {inv.type === 'sent' ? 'AR' : 'AP'}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-gray-200">
                          ${(inv.line_items || []).reduce((sum, item) => sum + item.quantity * item.unit_price, 0).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-gray-400">{new Date(inv.due_date).toLocaleDateString()}</td>
                        <td className="py-3 px-4">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            inv.status === 'paid' ? 'bg-[#00ff88]/20 text-[#00ff88]' :
                            inv.status === 'overdue' ? 'bg-[#ff4757]/20 text-[#ff4757]' : 'bg-[#ff9f43]/20 text-[#ff9f43]'
                          }`}>{inv.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ==================== TASKS TAB ==================== */}
        {activeTab === 'tasks' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              {[
                { label: 'Total', value: data?.taskStats?.total || 0, color: '#00d4ff' },
                { label: 'To Do', value: data?.taskStats?.todo || 0, color: '#ff9f43' },
                { label: 'In Progress', value: data?.taskStats?.in_progress || 0, color: '#00d4ff' },
                { label: 'Completed', value: data?.taskStats?.completed || 0, color: '#00ff88' },
                { label: 'Blocked', value: data?.taskStats?.blocked || 0, color: '#ff4757' },
                { label: 'Overdue', value: data?.taskStats?.overdue || 0, color: '#ff4757' },
              ].map((stat, i) => (
                <div key={i} className="glass-card p-3 text-center">
                  <div className="text-xl font-bold font-mono" style={{ color: stat.color }}>{stat.value}</div>
                  <p className="text-[10px] text-gray-500 uppercase">{stat.label}</p>
                </div>
              ))}
            </div>

            <div className="glass-card p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold gradient-text">Tasks</h3>
                <button onClick={() => setShowAddTaskModal(true)} className="btn-neon text-xs">+ Add Task</button>
              </div>
              <div className="space-y-3">
                {(data?.tasks || []).map((task) => (
                  <div key={task.id} className="flex items-center gap-4 p-3 rounded-lg bg-[#0a0a0f]/50 border border-gray-800">
                    <div className={`w-3 h-3 rounded-full ${
                      task.status === 'completed' ? 'bg-[#00ff88]' :
                      task.status === 'in_progress' ? 'bg-[#00d4ff]' :
                      task.status === 'blocked' ? 'bg-[#ff4757]' : 'bg-[#ff9f43]'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-gray-200">{task.title}</p>
                      <p className="text-xs text-gray-500">{task.due_date && `Due: ${new Date(task.due_date).toLocaleDateString()}`}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      task.priority === 'high' ? 'bg-[#ff4757]/20 text-[#ff4757]' : 'bg-gray-700 text-gray-400'
                    }`}>{task.priority}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ==================== APPROVALS TAB ==================== */}
        {activeTab === 'approvals' && (
          <div className="glass-card p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold gradient-text flex items-center gap-2">
                <span>🔐</span> Approval Queue
                {(data?.pendingApprovals?.length || 0) > 0 && (
                  <span className="px-2 py-1 text-xs rounded-full bg-[#ff9f43]/20 text-[#ff9f43]">
                    {data?.pendingApprovals?.length} pending
                  </span>
                )}
              </h2>
              <button
                onClick={fetchDashboardData}
                disabled={isProcessing}
                className="text-xs px-3 py-1 rounded bg-white/5 text-gray-400 hover:bg-white/10"
              >
                🔄 Refresh
              </button>
            </div>

            {/* Outgoing Drafts Awaiting Approval */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                <span>📤</span> Outgoing Drafts
                <span className="text-xs text-gray-500">({data?.pendingApprovals?.length || 0})</span>
              </h3>
              {!data?.pendingApprovals?.length ? (
                <div className="text-center py-6 bg-[#0a0a0f]/30 rounded-lg border border-gray-800/50">
                  <p className="text-gray-500 text-sm">No outgoing drafts pending.</p>
                  <button
                    onClick={() => setActiveTab('email')}
                    className="mt-2 text-xs px-3 py-1 rounded bg-[#00ff88]/20 text-[#00ff88] hover:bg-[#00ff88]/30"
                  >
                    📧 Compose Email
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.pendingApprovals.map((item) => (
                    <div key={item.id} className="bg-[#0a0a0f]/50 rounded-lg border border-gray-800 p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">
                              {item.type === 'email_draft' ? '📧' : item.type === 'linkedin_post' || item.type === 'social_post' ? '💼' : '📋'}
                            </span>
                            <span className="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-400">
                              {item.type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className="text-xs text-gray-600">{new Date(item.created).toLocaleString()}</span>
                          </div>
                          <h3 className="font-medium text-gray-200 mb-2">{item.title}</h3>
                          <p className="text-sm text-gray-500">{item.preview}</p>
                        </div>
                        <div className="flex flex-col gap-2">
                          <button onClick={() => handleApproval(item.id, true)} disabled={isProcessing} className="btn-neon text-xs px-4 py-2 disabled:opacity-50">
                            ✓ Approve & Send
                          </button>
                          <button onClick={() => handleApproval(item.id, false)} disabled={isProcessing} className="btn-danger text-xs px-4 py-2 disabled:opacity-50">
                            ✕ Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Incoming Emails Needing Attention */}
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                <span>📥</span> Incoming Emails
                <span className="text-xs text-gray-500">({data?.emails?.length || 0} in inbox)</span>
              </h3>
              <p className="text-xs text-gray-600 mb-3">
                Approve = AI auto-replies and sends | Reject = Archive email
              </p>
              {!data?.emails?.length ? (
                <div className="text-center py-6 bg-[#0a0a0f]/30 rounded-lg border border-gray-800/50">
                  <p className="text-gray-500 text-sm">No incoming emails to review.</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {data.emails.slice(0, 15).map((email) => (
                    <div key={email.id} className="bg-[#0a0a0f]/50 rounded-lg border border-gray-800 p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">📧</span>
                            <div className={`w-2 h-2 rounded-full ${email.priority === 'high' ? 'bg-[#ff4757]' : 'bg-[#00ff88]'}`}></div>
                            <span className="text-xs text-gray-600">{new Date(email.received).toLocaleString()}</span>
                          </div>
                          <p className="text-sm font-medium text-gray-200 mb-1">{email.from}</p>
                          <p className="text-sm text-gray-300 mb-1">{email.subject}</p>
                          <p className="text-xs text-gray-500">{email.snippet}</p>
                        </div>
                        <div className="flex flex-col gap-2">
                          <button
                            onClick={() => handleAutoReply(email)}
                            disabled={isProcessing}
                            className="btn-neon text-xs px-4 py-2 disabled:opacity-50"
                          >
                            ✓ Approve & Reply
                          </button>
                          <button
                            onClick={() => handleArchiveEmail(email.id)}
                            disabled={isProcessing}
                            className="btn-danger text-xs px-4 py-2 disabled:opacity-50"
                          >
                            ✕ Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== SETTINGS TAB ==================== */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h2 className="text-lg font-bold gradient-text mb-4 flex items-center gap-2">
                <span>⚙️</span> Settings & Connections
              </h2>

              <div className="space-y-6">
                {/* Account Connections */}
                <div>
                  <h3 className="font-medium text-gray-300 mb-4">Connect Your Accounts</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { id: 'gmail', name: 'Gmail', icon: '📧', desc: 'Read and send emails' },
                      { id: 'linkedin', name: 'LinkedIn', icon: '💼', desc: 'Post updates and messages' },
                      { id: 'twitter', name: 'Twitter/X', icon: '🐦', desc: 'Post tweets and read mentions' },
                      { id: 'whatsapp', name: 'WhatsApp', icon: '💬', desc: 'Monitor business messages' },
                      { id: 'slack', name: 'Slack', icon: '💼', desc: 'Team communication' },
                      { id: 'calendar', name: 'Google Calendar', icon: '📅', desc: 'Manage meetings and events' },
                    ].map((service) => (
                      <div key={service.id} className="bg-[#0a0a0f]/50 rounded-lg p-4 border border-gray-800">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{service.icon}</span>
                            <div>
                              <p className="font-medium text-gray-200">{service.name}</p>
                              <p className="text-xs text-gray-500">{service.desc}</p>
                            </div>
                          </div>
                          <button
                            onClick={() => setConnections(prev => ({ ...prev, [service.id]: !prev[service.id as keyof typeof prev] }))}
                            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                              connections[service.id as keyof typeof connections]
                                ? 'bg-[#00ff88]/20 text-[#00ff88] border border-[#00ff88]/50'
                                : 'bg-white/5 text-gray-400 hover:bg-white/10'
                            }`}
                          >
                            {connections[service.id as keyof typeof connections] ? '✓ Connected' : 'Connect'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* API Keys Section */}
                <div>
                  <h3 className="font-medium text-gray-300 mb-4">API Configuration</h3>
                  <div className="bg-[#0a0a0f]/50 rounded-lg p-4 border border-gray-800">
                    <p className="text-sm text-gray-500 mb-4">
                      API keys are stored securely in your local environment. Configure them in:
                    </p>
                    <code className="block bg-black/50 rounded p-3 text-sm text-[#00ff88] font-mono">
                      /config/credentials/.env
                    </code>
                    <div className="mt-4 text-xs text-gray-500">
                      <p>Required variables:</p>
                      <ul className="list-disc list-inside mt-2 space-y-1">
                        <li>GMAIL_CLIENT_ID</li>
                        <li>GMAIL_CLIENT_SECRET</li>
                        <li>LINKEDIN_ACCESS_TOKEN</li>
                        <li>TWITTER_API_KEY</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Automation Rules */}
                <div>
                  <h3 className="font-medium text-gray-300 mb-4">Automation Rules</h3>
                  <div className="space-y-3">
                    {[
                      { key: 'autoEmail', label: 'Auto-categorize incoming emails' },
                      { key: 'vipDrafts', label: 'Draft replies for VIP contacts' },
                      { key: 'invoiceProcess', label: 'Auto-process invoice PDFs' },
                      { key: 'socialSchedule', label: 'Schedule social posts' },
                      { key: 'ceoBriefing', label: 'Weekly CEO briefing' },
                    ].map((rule) => (
                      <div key={rule.key} className="flex items-center justify-between bg-[#0a0a0f]/50 rounded-lg p-4 border border-gray-800">
                        <span className="text-gray-300">{rule.label}</span>
                        <div
                          onClick={() => toggleAutomationRule(rule.key as keyof typeof automationRules)}
                          className={`w-12 h-6 rounded-full relative cursor-pointer transition-all ${
                            automationRules[rule.key as keyof typeof automationRules] ? 'bg-[#00ff88]/30' : 'bg-gray-700'
                          }`}
                        >
                          <div className={`w-5 h-5 rounded-full absolute top-0.5 transition-all ${
                            automationRules[rule.key as keyof typeof automationRules] ? 'right-0.5 bg-[#00ff88]' : 'left-0.5 bg-gray-500'
                          }`}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* CEO Briefing Button */}
                <div>
                  <h3 className="font-medium text-gray-300 mb-4">Manual Actions</h3>
                  <button
                    onClick={generateCeoBriefing}
                    disabled={isProcessing}
                    className="btn-neon w-full disabled:opacity-50"
                  >
                    📊 Generate CEO Briefing Now
                  </button>
                  <p className="text-xs text-gray-500 mt-2">
                    Generates a comprehensive business summary including revenue, tasks, and recommendations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Add Task Modal */}
      {showAddTaskModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="glass-card p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold gradient-text">Add New Task</h2>
              <button onClick={() => setShowAddTaskModal(false)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Task Title *</label>
                <input
                  type="text"
                  value={newTask.title}
                  onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter task title"
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Priority</label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask(prev => ({ ...prev, priority: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Due Date</label>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask(prev => ({ ...prev, due_date: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleAddTask}
                  disabled={!newTask.title || isProcessing}
                  className="btn-neon flex-1 disabled:opacity-50"
                >
                  {isProcessing ? 'Creating...' : '✓ Create Task'}
                </button>
                <button
                  onClick={() => setShowAddTaskModal(false)}
                  className="px-4 py-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Contact Modal */}
      {showAddContactModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="glass-card p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold gradient-text">Add New Contact</h2>
              <button onClick={() => setShowAddContactModal(false)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Name *</label>
                <input
                  type="text"
                  value={newContact.name}
                  onChange={(e) => setNewContact(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter contact name"
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Email *</label>
                <input
                  type="email"
                  value={newContact.email}
                  onChange={(e) => setNewContact(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="email@example.com"
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Company</label>
                <input
                  type="text"
                  value={newContact.company}
                  onChange={(e) => setNewContact(prev => ({ ...prev, company: e.target.value }))}
                  placeholder="Company name"
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Type</label>
                <select
                  value={newContact.type}
                  onChange={(e) => setNewContact(prev => ({ ...prev, type: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:border-[#00ff88]/50"
                >
                  <option value="lead">Lead</option>
                  <option value="client">Client</option>
                  <option value="vendor">Vendor</option>
                  <option value="partner">Partner</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleAddContact}
                  disabled={!newContact.name || !newContact.email || isProcessing}
                  className="btn-neon flex-1 disabled:opacity-50"
                >
                  {isProcessing ? 'Adding...' : '✓ Add Contact'}
                </button>
                <button
                  onClick={() => setShowAddContactModal(false)}
                  className="px-4 py-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-[#00ff88]/10 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🤖</span>
              <div>
                <p className="text-sm font-bold gradient-text">AI EMPLOYEE v2.0</p>
                <p className="text-xs text-gray-600">Hackathon 2026 • Built with Claude Code</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span className="w-2 h-2 rounded-full status-online"></span>
              All Systems Operational
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
