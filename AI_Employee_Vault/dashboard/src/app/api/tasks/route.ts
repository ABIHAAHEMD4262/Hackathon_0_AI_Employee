import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const NERVE_CENTER = path.join(process.cwd(), '..', '..', 'nerve_center');
const TASKS_FILE = path.join(NERVE_CENTER, 'projects', 'tasks.json');

interface Task {
  id: string;
  title: string;
  project_id: string;
  status: string;
  priority: string;
  due_date?: string;
  created_at: string;
}

function loadTasks(): Task[] {
  try {
    if (fs.existsSync(TASKS_FILE)) {
      const content = fs.readFileSync(TASKS_FILE, 'utf-8');
      return JSON.parse(content);
    }
  } catch (error) {
    console.error('Error loading tasks:', error);
  }
  return [];
}

function saveTasks(tasks: Task[]): boolean {
  try {
    const dir = path.dirname(TASKS_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(TASKS_FILE, JSON.stringify(tasks, null, 2));
    return true;
  } catch (error) {
    console.error('Error saving tasks:', error);
    return false;
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, priority, due_date } = body;

    if (!title) {
      return NextResponse.json(
        { error: 'Title is required' },
        { status: 400 }
      );
    }

    const tasks = loadTasks();
    const newTask: Task = {
      id: `task_${Date.now()}`,
      title,
      project_id: 'default',
      status: 'todo',
      priority: priority || 'medium',
      due_date: due_date || undefined,
      created_at: new Date().toISOString(),
    };

    tasks.push(newTask);

    if (saveTasks(tasks)) {
      return NextResponse.json({
        success: true,
        task: newTask,
        message: 'Task created successfully',
      });
    } else {
      return NextResponse.json(
        { error: 'Failed to save task' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Tasks API error:', error);
    return NextResponse.json(
      { error: 'Failed to create task' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const tasks = loadTasks();
    return NextResponse.json({ tasks });
  } catch (error) {
    console.error('Get tasks error:', error);
    return NextResponse.json({ tasks: [] });
  }
}
