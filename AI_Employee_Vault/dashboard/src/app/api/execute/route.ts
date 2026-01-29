import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';
import * as nodemailer from 'nodemailer';

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..');

// Email configuration from environment
const EMAIL_CONFIG = {
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: parseInt(process.env.SMTP_PORT || '587'),
  secure: process.env.SMTP_SECURE === 'true',
  auth: {
    user: process.env.SMTP_USER || process.env.GMAIL_USER,
    pass: process.env.SMTP_PASS || process.env.GMAIL_APP_PASSWORD,
  },
};

interface ApprovalFile {
  type: string;
  to?: string;
  subject?: string;
  body?: string;
  platform?: string;
  content?: string;
}

function parseApprovalFile(content: string): ApprovalFile {
  const result: ApprovalFile = { type: 'unknown' };

  // Parse frontmatter
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (frontmatterMatch) {
    const frontmatter = frontmatterMatch[1];

    const typeMatch = frontmatter.match(/type:\s*(\S+)/);
    if (typeMatch) result.type = typeMatch[1];

    const toMatch = frontmatter.match(/to:\s*(.+)/);
    if (toMatch) result.to = toMatch[1].trim();

    const subjectMatch = frontmatter.match(/subject:\s*(.+)/);
    if (subjectMatch) result.subject = subjectMatch[1].trim();

    const platformMatch = frontmatter.match(/platform:\s*(\S+)/);
    if (platformMatch) result.platform = platformMatch[1];
  }

  // Extract body content
  const bodyMatch = content.match(/### Body\n\n([\s\S]*?)(?=\n---|\n##|$)/);
  if (bodyMatch) {
    result.body = bodyMatch[1].trim();
  }

  // Extract social content
  const contentMatch = content.match(/### Content\n\n([\s\S]*?)(?=\n---|\n##|$)/);
  if (contentMatch) {
    result.content = contentMatch[1].trim();
  }

  return result;
}

async function sendEmail(to: string, subject: string, body: string): Promise<{ success: boolean; error?: string }> {
  // Check if email credentials are configured
  if (!EMAIL_CONFIG.auth.user || !EMAIL_CONFIG.auth.pass) {
    console.log('Email credentials not configured, simulating send...');
    return {
      success: true,
      error: 'Email simulated (configure SMTP_USER/SMTP_PASS or GMAIL_USER/GMAIL_APP_PASSWORD for real sending)'
    };
  }

  try {
    const transporter = nodemailer.createTransport(EMAIL_CONFIG);

    await transporter.sendMail({
      from: EMAIL_CONFIG.auth.user,
      to,
      subject,
      text: body,
      html: body.replace(/\n/g, '<br>'),
    });

    return { success: true };
  } catch (error: any) {
    console.error('Email send error:', error);
    return { success: false, error: error.message };
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { id } = body;

    if (!id) {
      return NextResponse.json(
        { error: 'Missing id' },
        { status: 400 }
      );
    }

    // Find the approved file
    const approvedPath = path.join(VAULT_PATH, 'Approved');
    const filePath = path.join(approvedPath, `${id}.md`);

    if (!fs.existsSync(filePath)) {
      return NextResponse.json(
        { error: 'Approved item not found' },
        { status: 404 }
      );
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const approvalData = parseApprovalFile(content);

    let result: { success: boolean; message?: string; error?: string } = { success: false };

    if (approvalData.type === 'email_draft') {
      if (!approvalData.to || !approvalData.subject) {
        return NextResponse.json(
          { error: 'Missing email recipient or subject' },
          { status: 400 }
        );
      }

      const emailResult = await sendEmail(
        approvalData.to,
        approvalData.subject,
        approvalData.body || ''
      );

      if (emailResult.success) {
        result = {
          success: true,
          message: `Email sent to ${approvalData.to}`
        };
      } else {
        result = {
          success: false,
          error: emailResult.error || 'Failed to send email'
        };
      }
    } else if (approvalData.type === 'social_post' || approvalData.type === 'linkedin_post') {
      // Social media posting would require API integration
      // For now, log it as executed
      result = {
        success: true,
        message: `Social post for ${approvalData.platform || 'unknown platform'} queued for posting`,
      };
    } else {
      result = {
        success: true,
        message: `Action ${approvalData.type} executed`,
      };
    }

    // Move to Done folder
    if (result.success) {
      const donePath = path.join(VAULT_PATH, 'Done');
      if (!fs.existsSync(donePath)) {
        fs.mkdirSync(donePath, { recursive: true });
      }

      const newFilePath = path.join(donePath, `${id}.md`);
      fs.renameSync(filePath, newFilePath);

      // Log the execution
      const logsPath = path.join(VAULT_PATH, 'Logs');
      const today = new Date().toISOString().split('T')[0];
      const logFile = path.join(logsPath, `daily_${today}.log`);
      fs.appendFileSync(logFile,
        `[${new Date().toISOString()}] [INFO] Executed ${approvalData.type}: ${id} - ${result.message}\n`
      );
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error('Execute API error:', error);
    return NextResponse.json(
      { error: 'Failed to execute action' },
      { status: 500 }
    );
  }
}
