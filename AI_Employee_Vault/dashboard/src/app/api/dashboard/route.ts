import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

// Get the vault path - use parent directory of dashboard
const VAULT_PATH = process.env.VAULT_PATH || path.resolve(process.cwd(), '..');
const NERVE_CENTER = path.resolve(process.cwd(), '..', '..', 'nerve_center');

// Log paths for debugging
console.log('Dashboard API - VAULT_PATH:', VAULT_PATH);
console.log('Dashboard API - NERVE_CENTER:', NERVE_CENTER);

interface ApprovalItem {
  id: string;
  type: string;
  title: string;
  created: string;
  preview: string;
  filePath: string;
}

interface Activity {
  id: string;
  action: string;
  timestamp: string;
  status: string;
}

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
  last_contact?: string;
}

interface Invoice {
  id: string;
  type: string;
  client_name?: string;
  vendor_name?: string;
  status: string;
  due_date: string;
  line_items: Array<{ quantity: number; unit_price: number; description: string }>;
  discount?: number;
}

interface Expense {
  id: string;
  description: string;
  amount: number;
  category: string;
  date: string;
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

interface Task {
  id: string;
  title: string;
  project_id: string;
  status: string;
  priority: string;
  due_date?: string;
  assignee?: string;
}

function loadJson<T>(filePath: string): T[] {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.error(`Error loading ${filePath}:`, error);
  }
  return [];
}

function readApprovalsFolder(): ApprovalItem[] {
  const approvalsPath = path.join(VAULT_PATH, 'Approvals');
  const items: ApprovalItem[] = [];

  console.log('Reading approvals from:', approvalsPath);

  try {
    if (!fs.existsSync(approvalsPath)) {
      console.log('Approvals folder does not exist');
      return items;
    }

    const files = fs.readdirSync(approvalsPath);
    console.log('Found files:', files);

    for (const file of files) {
      if (file.endsWith('.md')) {
        const filePath = path.join(approvalsPath, file);
        const content = fs.readFileSync(filePath, 'utf-8');

        // Parse frontmatter
        const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
        if (frontmatterMatch) {
          const frontmatter = frontmatterMatch[1];
          const statusMatch = frontmatter.match(/status:\s*(\w+)/);

          // Only include pending items
          if (statusMatch && statusMatch[1] === 'pending') {
            const typeMatch = frontmatter.match(/type:\s*(\w+)/);
            const titleMatch = frontmatter.match(/title:\s*(.+)/);
            const createdMatch = frontmatter.match(/created:\s*(.+)/);

            // Get preview from content (after frontmatter)
            const bodyContent = content.replace(/^---\n[\s\S]*?\n---\n?/, '');
            const preview = bodyContent.slice(0, 200).replace(/[#*`]/g, '').trim();

            const item = {
              id: file.replace('.md', ''),
              type: typeMatch ? typeMatch[1] : 'unknown',
              title: titleMatch ? titleMatch[1] : file.replace('.md', ''),
              created: createdMatch ? createdMatch[1] : new Date().toISOString(),
              preview: preview || 'No preview available',
              filePath: filePath,
            };
            console.log('Found pending item:', item.id, item.title);
            items.push(item);
          } else {
            console.log('Skipping file (status:', statusMatch ? statusMatch[1] : 'no match', '):', file);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error reading approvals folder:', error);
  }

  console.log('Total pending approvals:', items.length);
  return items;
}

function readActivityLog(): Activity[] {
  const logsPath = path.join(VAULT_PATH, 'Logs');
  const activities: Activity[] = [];

  try {
    if (!fs.existsSync(logsPath)) {
      return activities;
    }

    // Get today's log file
    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(logsPath, `daily_${today}.log`);

    if (fs.existsSync(logFile)) {
      const content = fs.readFileSync(logFile, 'utf-8');
      const lines = content.split('\n').filter(line => line.trim());

      // Parse last 10 log entries
      const recentLines = lines.slice(-10).reverse();

      for (let i = 0; i < recentLines.length; i++) {
        const line = recentLines[i];
        // Parse log format: [timestamp] [level] message
        const match = line.match(/\[([^\]]+)\]\s*\[(\w+)\]\s*(.+)/);
        if (match) {
          activities.push({
            id: `log-${i}`,
            action: match[3],
            timestamp: match[1],
            status: match[2].toLowerCase() === 'error' ? 'error' :
                   match[2].toLowerCase() === 'warning' ? 'pending' : 'completed',
          });
        }
      }
    }
  } catch (error) {
    console.error('Error reading activity log:', error);
  }

  return activities;
}

function getSystemHealth() {
  // Check for .running files or process indicators
  const health = {
    gmail: 'stopped',
    linkedin: 'stopped',
    orchestrator: 'stopped',
    approvals: 'stopped',
  };

  try {
    const statusPath = path.join(VAULT_PATH, '.status');

    if (fs.existsSync(statusPath)) {
      const statusFiles = fs.readdirSync(statusPath);

      for (const file of statusFiles) {
        const filePath = path.join(statusPath, file);
        const stat = fs.statSync(filePath);
        const ageMs = Date.now() - stat.mtimeMs;

        // Consider running if status file updated in last 5 minutes
        const isRunning = ageMs < 5 * 60 * 1000;

        if (file.includes('gmail')) health.gmail = isRunning ? 'running' : 'stopped';
        if (file.includes('linkedin')) health.linkedin = isRunning ? 'running' : 'stopped';
        if (file.includes('orchestrator')) health.orchestrator = isRunning ? 'running' : 'stopped';
        if (file.includes('approval')) health.approvals = isRunning ? 'running' : 'stopped';
      }
    }
  } catch (error) {
    console.error('Error checking system health:', error);
  }

  return health;
}

function getStats(approvals: ApprovalItem[], activities: Activity[]) {
  const completedToday = activities.filter(a => a.status === 'completed').length;
  const pendingApproval = approvals.length;

  // Count tasks from Tasks folder
  let needsAction = 0;
  let inProgress = 0;

  try {
    const tasksPath = path.join(VAULT_PATH, 'Tasks');
    if (fs.existsSync(tasksPath)) {
      const files = fs.readdirSync(tasksPath);
      for (const file of files) {
        if (file.endsWith('.md')) {
          const content = fs.readFileSync(path.join(tasksPath, file), 'utf-8');
          if (content.includes('status: needs_action') || content.includes('status: new')) {
            needsAction++;
          } else if (content.includes('status: in_progress')) {
            inProgress++;
          }
        }
      }
    }
  } catch (error) {
    console.error('Error reading tasks:', error);
  }

  return {
    needsAction,
    inProgress,
    pendingApproval,
    completedToday,
  };
}

// Load data from nerve_center
function getContacts(): Contact[] {
  return loadJson<Contact>(path.join(NERVE_CENTER, 'crm', 'contacts.json'));
}

function getInvoices(): Invoice[] {
  return loadJson<Invoice>(path.join(NERVE_CENTER, 'finances', 'invoices.json'));
}

function getExpenses(): Expense[] {
  return loadJson<Expense>(path.join(NERVE_CENTER, 'finances', 'expenses.json'));
}

function getProjects(): Project[] {
  return loadJson<Project>(path.join(NERVE_CENTER, 'projects', 'projects.json'));
}

function getTasks(): Task[] {
  return loadJson<Task>(path.join(NERVE_CENTER, 'projects', 'tasks.json'));
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

function getEmails(): Email[] {
  const emailsPath = path.join(VAULT_PATH, 'Needs_Action', 'Emails');
  const emails: Email[] = [];

  try {
    if (fs.existsSync(emailsPath)) {
      const files = fs.readdirSync(emailsPath)
        .filter(f => f.endsWith('.md'))
        .sort((a, b) => b.localeCompare(a))
        .slice(0, 20);

      for (const file of files) {
        const filePath = path.join(emailsPath, file);
        const content = fs.readFileSync(filePath, 'utf-8');
        const fileName = file.replace('.md', '');

        const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
        if (frontmatterMatch) {
          const fm = frontmatterMatch[1];
          const fromMatch = fm.match(/from:\s*(.+)/);
          const subjectMatch = fm.match(/subject:\s*(.+)/);
          const receivedMatch = fm.match(/received:\s*(.+)/);
          const priorityMatch = fm.match(/priority:\s*(\w+)/);
          const statusMatch = fm.match(/status:\s*(\w+)/);

          const bodyContent = content.replace(/^---\n[\s\S]*?\n---\n?/, '');
          const snippet = bodyContent.slice(0, 100).replace(/[#*`\n]/g, ' ').trim();

          emails.push({
            id: fileName,
            from: fromMatch ? fromMatch[1].trim() : 'Unknown',
            subject: subjectMatch ? subjectMatch[1].trim() : fileName,
            received: receivedMatch ? receivedMatch[1].trim() : new Date().toISOString(),
            priority: priorityMatch ? priorityMatch[1] : 'normal',
            status: statusMatch ? statusMatch[1] : 'unread',
            snippet: snippet || 'No preview',
          });
        }
      }
    }
  } catch (error) {
    console.error('Error loading emails:', error);
  }

  return emails;
}

function calcInvoiceTotal(invoice: Invoice): number {
  const subtotal = (invoice.line_items || []).reduce(
    (sum, item) => sum + (item.quantity || 0) * (item.unit_price || 0),
    0
  );
  return subtotal - (invoice.discount || 0);
}

function getContactStats(contacts: Contact[]) {
  return {
    total: contacts.length,
    clients: contacts.filter(c => c.type === 'client').length,
    leads: contacts.filter(c => c.type === 'lead').length,
    vips: contacts.filter(c => c.is_vip).length,
  };
}

function getFinancialStats(invoices: Invoice[], expenses: Expense[], contacts: Contact[]) {
  const sentInvoices = invoices.filter(i => i.type === 'sent');
  const receivedInvoices = invoices.filter(i => i.type === 'received');

  const outstandingAR = sentInvoices
    .filter(i => i.status !== 'paid' && i.status !== 'cancelled')
    .reduce((sum, i) => sum + calcInvoiceTotal(i), 0);

  const outstandingAP = receivedInvoices
    .filter(i => i.status !== 'paid' && i.status !== 'cancelled')
    .reduce((sum, i) => sum + calcInvoiceTotal(i), 0);

  const totalExpenses = expenses.reduce((sum, e) => sum + (e.amount || 0), 0);

  const pipelineValue = contacts
    .filter(c => c.lead_stage && c.lead_stage !== 'won' && c.lead_stage !== 'lost')
    .reduce((sum, c) => sum + (c.lead_value || 0), 0);

  return {
    outstandingAR,
    outstandingAP,
    totalExpenses,
    pipelineValue,
  };
}

function getTaskStats(tasks: Task[]) {
  const now = new Date();
  return {
    total: tasks.length,
    todo: tasks.filter(t => t.status === 'todo').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    blocked: tasks.filter(t => t.status === 'blocked').length,
    overdue: tasks.filter(t => {
      if (!t.due_date || t.status === 'completed') return false;
      return new Date(t.due_date) < now;
    }).length,
  };
}

export async function GET() {
  try {
    const approvals = readApprovalsFolder();
    const activities = readActivityLog();
    const health = getSystemHealth();
    const stats = getStats(approvals, activities);

    // Load nerve_center data
    const contacts = getContacts();
    const invoices = getInvoices();
    const expenses = getExpenses();
    const projects = getProjects();
    const tasks = getTasks();
    const emails = getEmails();

    // Calculate stats
    const contactStats = getContactStats(contacts);
    const financialStats = getFinancialStats(invoices, expenses, contacts);
    const taskStats = getTaskStats(tasks);

    return NextResponse.json({
      stats,
      pendingApprovals: approvals,
      activities,
      health,
      // New data
      contacts,
      contactStats,
      invoices,
      expenses,
      financialStats,
      projects,
      tasks,
      taskStats,
      emails,
      lastUpdated: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Dashboard API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
