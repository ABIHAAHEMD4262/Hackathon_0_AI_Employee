// Shared TypeScript interfaces for the AI Employee Dashboard

export interface Contact {
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

export interface Invoice {
  id: string;
  type: string;
  client_name?: string;
  vendor_name?: string;
  status: string;
  due_date: string;
  line_items: Array<{ quantity: number; unit_price: number; description?: string }>;
  discount?: number;
}

export interface Task {
  id: string;
  title: string;
  project_id: string;
  status: string;
  priority: string;
  due_date?: string;
  assignee?: string;
}

export interface Project {
  id: string;
  name: string;
  client: string;
  status: string;
  budget: number;
  budget_spent: number;
  deadline: string;
}

export interface Email {
  id: string;
  from: string;
  subject: string;
  received: string;
  priority: string;
  status: string;
  snippet: string;
}

export interface ApprovalItem {
  id: string;
  type: string;
  title: string;
  created: string;
  preview: string;
}

export interface CommandHistoryItem {
  id: string;
  command: string;
  response: string;
  timestamp: Date;
  status: 'pending' | 'completed' | 'error';
}

export interface DashboardData {
  stats: {
    needsAction: number;
    inProgress: number;
    pendingApproval: number;
    completedToday: number;
  };
  pendingApprovals: ApprovalItem[];
  activities: Array<{ id: string; action: string; timestamp: string; status: string }>;
  contacts?: Contact[];
  contactStats?: { total: number; clients: number; leads: number; vips: number };
  invoices?: Invoice[];
  expenses?: Array<{ id: string; description: string; amount: number; category: string; date: string }>;
  financialStats?: {
    outstandingAR: number;
    outstandingAP: number;
    totalExpenses: number;
    pipelineValue: number;
  };
  projects?: Project[];
  tasks?: Task[];
  taskStats?: {
    total: number;
    todo: number;
    in_progress: number;
    completed: number;
    blocked: number;
    overdue: number;
  };
  emails?: Email[];
}
