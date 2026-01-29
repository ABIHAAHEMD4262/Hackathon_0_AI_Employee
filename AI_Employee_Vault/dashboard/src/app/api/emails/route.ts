import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..');

interface Email {
  id: string;
  from: string;
  subject: string;
  received: string;
  priority: string;
  status: string;
  snippet: string;
  filePath: string;
}

function parseEmailFile(filePath: string): Email | null {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const fileName = path.basename(filePath, '.md');

    // Parse frontmatter
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) return null;

    const frontmatter = frontmatterMatch[1];

    const fromMatch = frontmatter.match(/from:\s*(.+)/);
    const subjectMatch = frontmatter.match(/subject:\s*(.+)/);
    const receivedMatch = frontmatter.match(/received:\s*(.+)/);
    const priorityMatch = frontmatter.match(/priority:\s*(\w+)/);
    const statusMatch = frontmatter.match(/status:\s*(\w+)/);

    // Get snippet from content
    const bodyContent = content.replace(/^---\n[\s\S]*?\n---\n?/, '');
    const snippetMatch = bodyContent.match(/## Email Content\n\n([\s\S]*?)(?=\n##|$)/);
    const snippet = snippetMatch
      ? snippetMatch[1].slice(0, 150).replace(/\n/g, ' ').trim()
      : bodyContent.slice(0, 150).replace(/[#*`\n]/g, ' ').trim();

    return {
      id: fileName,
      from: fromMatch ? fromMatch[1].trim() : 'Unknown',
      subject: subjectMatch ? subjectMatch[1].trim() : fileName,
      received: receivedMatch ? receivedMatch[1].trim() : new Date().toISOString(),
      priority: priorityMatch ? priorityMatch[1] : 'normal',
      status: statusMatch ? statusMatch[1] : 'unread',
      snippet: snippet || 'No preview available',
      filePath: filePath,
    };
  } catch (error) {
    console.error(`Error parsing ${filePath}:`, error);
    return null;
  }
}

export async function GET() {
  try {
    const emailsPath = path.join(VAULT_PATH, 'Needs_Action', 'Emails');
    const emails: Email[] = [];

    if (fs.existsSync(emailsPath)) {
      const files = fs.readdirSync(emailsPath)
        .filter(f => f.endsWith('.md'))
        .sort((a, b) => {
          // Sort by filename (which contains timestamp) descending
          return b.localeCompare(a);
        })
        .slice(0, 50); // Limit to 50 most recent

      for (const file of files) {
        const filePath = path.join(emailsPath, file);
        const email = parseEmailFile(filePath);
        if (email) {
          emails.push(email);
        }
      }
    }

    return NextResponse.json({
      emails,
      total: emails.length,
      lastChecked: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Emails API error:', error);
    return NextResponse.json({ emails: [], error: 'Failed to fetch emails' });
  }
}

// Mark email as read/processed
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { id, action } = body;

    if (!id) {
      return NextResponse.json({ error: 'Missing email id' }, { status: 400 });
    }

    const emailsPath = path.join(VAULT_PATH, 'Needs_Action', 'Emails');
    const filePath = path.join(emailsPath, `${id}.md`);

    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'Email not found' }, { status: 404 });
    }

    if (action === 'archive') {
      // Move to Done folder
      const donePath = path.join(VAULT_PATH, 'Done', 'Emails');
      if (!fs.existsSync(donePath)) {
        fs.mkdirSync(donePath, { recursive: true });
      }
      fs.renameSync(filePath, path.join(donePath, `${id}.md`));
      return NextResponse.json({ success: true, message: 'Email archived' });
    } else if (action === 'mark_read') {
      // Update status in file
      let content = fs.readFileSync(filePath, 'utf-8');
      content = content.replace(/status:\s*\w+/, 'status: read');
      fs.writeFileSync(filePath, content);
      return NextResponse.json({ success: true, message: 'Email marked as read' });
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    console.error('Email action error:', error);
    return NextResponse.json({ error: 'Failed to process email action' }, { status: 500 });
  }
}
