import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..');

export async function POST(request: Request) {
  try {
    const body = await request.json();
    console.log('Approve API received:', body);
    console.log('VAULT_PATH:', VAULT_PATH);

    const { id, action } = body;

    if (!id || !action) {
      console.log('Missing id or action. id:', id, 'action:', action);
      return NextResponse.json(
        { error: `Missing id or action. Received: ${JSON.stringify(body)}` },
        { status: 400 }
      );
    }

    if (!['approve', 'reject'].includes(action)) {
      return NextResponse.json(
        { error: 'Invalid action. Must be "approve" or "reject"' },
        { status: 400 }
      );
    }

    const approvalsPath = path.join(VAULT_PATH, 'Approvals');
    const filePath = path.join(approvalsPath, `${id}.md`);

    if (!fs.existsSync(filePath)) {
      return NextResponse.json(
        { error: 'Approval item not found' },
        { status: 404 }
      );
    }

    // Read the file
    let content = fs.readFileSync(filePath, 'utf-8');

    // Update the status in frontmatter
    const newStatus = action === 'approve' ? 'approved' : 'rejected';
    content = content.replace(
      /status:\s*pending/,
      `status: ${newStatus}`
    );

    // Add decision timestamp
    const timestamp = new Date().toISOString();
    content = content.replace(
      /---\n/,
      `---\ndecision_time: ${timestamp}\ndecision: ${action}\n`
    );

    // Write updated content
    fs.writeFileSync(filePath, content);

    // Move to appropriate folder
    const targetFolder = action === 'approve' ? 'Approved' : 'Rejected';
    const targetPath = path.join(VAULT_PATH, targetFolder);

    // Create target folder if it doesn't exist
    if (!fs.existsSync(targetPath)) {
      fs.mkdirSync(targetPath, { recursive: true });
    }

    // Move the file
    const newFilePath = path.join(targetPath, `${id}.md`);
    fs.renameSync(filePath, newFilePath);

    // Log the action
    const logsPath = path.join(VAULT_PATH, 'Logs');
    if (!fs.existsSync(logsPath)) {
      fs.mkdirSync(logsPath, { recursive: true });
    }

    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(logsPath, `daily_${today}.log`);
    const logEntry = `[${timestamp}] [INFO] Item ${id} was ${newStatus} via dashboard\n`;
    fs.appendFileSync(logFile, logEntry);

    // If approved, trigger execution
    let executionResult = null;
    if (action === 'approve') {
      // Parse the file to determine action type
      const typeMatch = content.match(/type:\s*(\S+)/);
      const itemType = typeMatch ? typeMatch[1] : 'unknown';

      if (itemType === 'email_draft') {
        // Extract email details
        const toMatch = content.match(/to:\s*(.+)/);
        const subjectMatch = content.match(/subject:\s*(.+)/);
        const bodyMatch = content.match(/### Body\n\n([\s\S]*?)(?=\n---|\n##|$)/);

        const to = toMatch ? toMatch[1].trim() : '';
        const subject = subjectMatch ? subjectMatch[1].trim() : '';
        const emailBody = bodyMatch ? bodyMatch[1].trim() : '';

        if (to && subject) {
          // Try to send email using nodemailer (if configured)
          try {
            const nodemailer = require('nodemailer');
            const smtpUser = process.env.SMTP_USER || process.env.GMAIL_USER;
            const smtpPass = process.env.SMTP_PASS || process.env.GMAIL_APP_PASSWORD;

            if (smtpUser && smtpPass) {
              const transporter = nodemailer.createTransport({
                host: process.env.SMTP_HOST || 'smtp.gmail.com',
                port: parseInt(process.env.SMTP_PORT || '587'),
                secure: process.env.SMTP_SECURE === 'true',
                auth: { user: smtpUser, pass: smtpPass },
              });

              await transporter.sendMail({
                from: smtpUser,
                to,
                subject,
                text: emailBody,
                html: emailBody.replace(/\n/g, '<br>'),
              });

              executionResult = { sent: true, to, subject };
              fs.appendFileSync(logFile, `[${timestamp}] [INFO] Email sent to ${to}: ${subject}\n`);
            } else {
              executionResult = { sent: false, reason: 'SMTP not configured', to, subject };
              fs.appendFileSync(logFile, `[${timestamp}] [WARNING] Email not sent (SMTP not configured): ${to}\n`);
            }
          } catch (emailError: any) {
            executionResult = { sent: false, error: emailError.message };
            fs.appendFileSync(logFile, `[${timestamp}] [ERROR] Email failed: ${emailError.message}\n`);
          }
        }
      } else if (itemType === 'social_post' || itemType === 'linkedin_post') {
        // Log social post for manual execution or API integration
        executionResult = { queued: true, type: itemType };
        fs.appendFileSync(logFile, `[${timestamp}] [INFO] Social post queued for ${itemType}\n`);
      }

      // Also write to queue for background processing
      const queuePath = path.join(VAULT_PATH, '.queue');
      if (!fs.existsSync(queuePath)) {
        fs.mkdirSync(queuePath, { recursive: true });
      }

      const queueFile = path.join(queuePath, `execute_${id}.json`);
      fs.writeFileSync(queueFile, JSON.stringify({
        id,
        approvedAt: timestamp,
        sourcePath: newFilePath,
        executionResult,
      }));
    }

    return NextResponse.json({
      success: true,
      message: executionResult?.sent
        ? `Item approved and email sent to ${executionResult.to}`
        : `Item ${newStatus} successfully`,
      id,
      newStatus,
      executionResult,
    });
  } catch (error) {
    console.error('Approve API error:', error);
    return NextResponse.json(
      { error: 'Failed to process approval' },
      { status: 500 }
    );
  }
}
