import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

export async function GET() {
  const cwd = process.cwd();
  const vaultPath = process.env.VAULT_PATH || path.resolve(cwd, '..');
  const approvalsPath = path.join(vaultPath, 'Approvals');
  const emailsPath = path.join(vaultPath, 'Needs_Action', 'Emails');

  const debug: any = {
    cwd,
    vaultPath,
    approvalsPath,
    emailsPath,
    env: {
      VAULT_PATH: process.env.VAULT_PATH || 'not set',
      NODE_ENV: process.env.NODE_ENV,
    },
    checks: {
      vaultExists: fs.existsSync(vaultPath),
      approvalsExists: fs.existsSync(approvalsPath),
      emailsExists: fs.existsSync(emailsPath),
    },
    files: {
      approvals: [],
      emails: [],
    },
  };

  // List approval files
  if (debug.checks.approvalsExists) {
    try {
      const files = fs.readdirSync(approvalsPath).filter(f => f.endsWith('.md'));
      debug.files.approvals = files.map(f => {
        const content = fs.readFileSync(path.join(approvalsPath, f), 'utf-8');
        const statusMatch = content.match(/status:\s*(\w+)/);
        return {
          name: f,
          status: statusMatch ? statusMatch[1] : 'unknown',
        };
      });
    } catch (e: any) {
      debug.files.approvalsError = e.message;
    }
  }

  // List email files (just count)
  if (debug.checks.emailsExists) {
    try {
      const files = fs.readdirSync(emailsPath).filter(f => f.endsWith('.md'));
      debug.files.emailsCount = files.length;
      debug.files.emails = files.slice(0, 5); // Just first 5
    } catch (e: any) {
      debug.files.emailsError = e.message;
    }
  }

  return NextResponse.json(debug);
}
