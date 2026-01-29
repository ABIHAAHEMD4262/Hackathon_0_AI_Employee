import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..');

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { type, data } = body;

    console.log('=== DRAFTS API ===');
    console.log('VAULT_PATH:', VAULT_PATH);
    console.log('Type:', type);
    console.log('Data:', JSON.stringify(data, null, 2));

    if (!type || !data) {
      return NextResponse.json(
        { error: 'Missing type or data' },
        { status: 400 }
      );
    }

    // Ensure Approvals folder exists
    const approvalsPath = path.join(VAULT_PATH, 'Approvals');
    console.log('Approvals path:', approvalsPath);
    if (!fs.existsSync(approvalsPath)) {
      fs.mkdirSync(approvalsPath, { recursive: true });
    }

    const timestamp = new Date().toISOString();
    const id = `${type}_${Date.now()}`;

    let content = '';
    let title = '';
    let preview = '';

    if (type === 'email_draft') {
      title = `Email to ${data.to}: ${data.subject}`;
      preview = data.body?.substring(0, 200) || '';
      content = `---
type: email_draft
status: pending
created: ${timestamp}
title: ${title}
to: ${data.to}
subject: ${data.subject}
tone: ${data.tone || 'professional'}
---

## Email Draft

**To:** ${data.to}
**Subject:** ${data.subject}
**Tone:** ${data.tone || 'professional'}

### Body

${data.body}

---
*Created by AI Employee Dashboard*
`;
    } else if (type === 'linkedin_post' || type === 'social_post') {
      title = `${data.platform || 'Social'} Post: ${data.topic || 'Update'}`;
      preview = data.content?.substring(0, 200) || '';
      content = `---
type: ${type}
status: pending
created: ${timestamp}
title: ${title}
platform: ${data.platform || 'linkedin'}
topic: ${data.topic || ''}
---

## Social Media Post

**Platform:** ${data.platform || 'LinkedIn'}
**Topic:** ${data.topic || 'General Update'}

### Content

${data.content}

---
*Created by AI Employee Dashboard*
`;
    } else {
      title = `Draft: ${type}`;
      preview = JSON.stringify(data).substring(0, 200);
      content = `---
type: ${type}
status: pending
created: ${timestamp}
title: ${title}
---

## Draft Content

${JSON.stringify(data, null, 2)}

---
*Created by AI Employee Dashboard*
`;
    }

    // Save to Approvals folder
    const filePath = path.join(approvalsPath, `${id}.md`);
    console.log('Saving to:', filePath);
    fs.writeFileSync(filePath, content);
    console.log('File saved successfully!');

    // Log the action
    const logsPath = path.join(VAULT_PATH, 'Logs');
    if (!fs.existsSync(logsPath)) {
      fs.mkdirSync(logsPath, { recursive: true });
    }
    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(logsPath, `daily_${today}.log`);
    fs.appendFileSync(logFile, `[${timestamp}] [INFO] Draft created: ${id} - ${title}\n`);

    return NextResponse.json({
      success: true,
      id,
      title,
      preview,
      message: 'Draft saved for approval',
    });
  } catch (error) {
    console.error('Drafts API error:', error);
    return NextResponse.json(
      { error: 'Failed to save draft' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const approvalsPath = path.join(VAULT_PATH, 'Approvals');
    const drafts: any[] = [];

    if (fs.existsSync(approvalsPath)) {
      const files = fs.readdirSync(approvalsPath);

      for (const file of files) {
        if (file.endsWith('.md')) {
          const filePath = path.join(approvalsPath, file);
          const content = fs.readFileSync(filePath, 'utf-8');

          // Parse frontmatter
          const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
          if (frontmatterMatch) {
            const frontmatter = frontmatterMatch[1];
            const statusMatch = frontmatter.match(/status:\s*(\w+)/);

            if (statusMatch && statusMatch[1] === 'pending') {
              const typeMatch = frontmatter.match(/type:\s*(\w+)/);
              const titleMatch = frontmatter.match(/title:\s*(.+)/);
              const createdMatch = frontmatter.match(/created:\s*(.+)/);

              const bodyContent = content.replace(/^---\n[\s\S]*?\n---\n?/, '');
              const preview = bodyContent.slice(0, 200).replace(/[#*`]/g, '').trim();

              drafts.push({
                id: file.replace('.md', ''),
                type: typeMatch ? typeMatch[1] : 'unknown',
                title: titleMatch ? titleMatch[1] : file.replace('.md', ''),
                created: createdMatch ? createdMatch[1] : new Date().toISOString(),
                preview: preview || 'No preview available',
              });
            }
          }
        }
      }
    }

    return NextResponse.json({ drafts });
  } catch (error) {
    console.error('Get drafts error:', error);
    return NextResponse.json({ drafts: [] });
  }
}
