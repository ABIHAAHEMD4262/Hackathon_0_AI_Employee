/**
 * Vault Utilities - Server-side helpers for reading/writing vault .md files
 * Used by API routes to interact with the Obsidian vault filesystem
 */

import * as fs from 'fs';
import * as path from 'path';

// Resolve vault path relative to dashboard directory
export const VAULT_PATH = process.env.VAULT_PATH || path.resolve(process.cwd(), '..');
export const NERVE_CENTER = path.resolve(process.cwd(), '..', '..', 'nerve_center');

// ----- Generic Helpers -----

/** Load a JSON file and return parsed array, or empty array on failure */
export function loadJson<T>(filePath: string): T[] {
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

/** Parse YAML-like frontmatter from a markdown string into key-value pairs */
export function parseFrontmatter(content: string): Record<string, string> {
  const meta: Record<string, string> = {};
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (match) {
    for (const line of match[1].split('\n')) {
      const colonIdx = line.indexOf(':');
      if (colonIdx > 0) {
        const key = line.slice(0, colonIdx).trim();
        const value = line.slice(colonIdx + 1).trim();
        meta[key] = value;
      }
    }
  }
  return meta;
}

/** Get the body content after frontmatter */
export function getBodyContent(content: string): string {
  return content.replace(/^---\n[\s\S]*?\n---\n?/, '');
}

/** Ensure a directory exists */
export function ensureDir(dirPath: string): void {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

/** Append a log entry to today's daily log */
export function appendDailyLog(message: string, level: string = 'INFO'): void {
  const logsPath = path.join(VAULT_PATH, 'Logs');
  ensureDir(logsPath);
  const today = new Date().toISOString().split('T')[0];
  const logFile = path.join(logsPath, `daily_${today}.log`);
  const timestamp = new Date().toISOString();
  fs.appendFileSync(logFile, `[${timestamp}] [${level}] ${message}\n`);
}

// ----- Vault Folder Readers -----

/** Read all .md files from a vault folder and return parsed metadata + body */
export function readVaultFolder(folderName: string): Array<{
  filename: string;
  filePath: string;
  meta: Record<string, string>;
  body: string;
  raw: string;
}> {
  const folderPath = path.join(VAULT_PATH, folderName);
  const results: Array<{
    filename: string;
    filePath: string;
    meta: Record<string, string>;
    body: string;
    raw: string;
  }> = [];

  try {
    if (!fs.existsSync(folderPath)) return results;

    const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.md'));
    for (const file of files) {
      const fp = path.join(folderPath, file);
      const raw = fs.readFileSync(fp, 'utf-8');
      results.push({
        filename: file,
        filePath: fp,
        meta: parseFrontmatter(raw),
        body: getBodyContent(raw),
        raw,
      });
    }
  } catch (error) {
    console.error(`Error reading vault folder ${folderName}:`, error);
  }

  return results;
}

/** Move a file from one vault folder to another */
export function moveVaultFile(filename: string, fromFolder: string, toFolder: string): boolean {
  try {
    const src = path.join(VAULT_PATH, fromFolder, filename);
    const destDir = path.join(VAULT_PATH, toFolder);
    ensureDir(destDir);
    const dest = path.join(destDir, filename);

    if (fs.existsSync(src)) {
      fs.renameSync(src, dest);
      return true;
    }
  } catch (error) {
    console.error(`Error moving ${filename} from ${fromFolder} to ${toFolder}:`, error);
  }
  return false;
}

/** Write a markdown file to a vault folder with frontmatter */
export function writeVaultFile(
  folderName: string,
  filename: string,
  meta: Record<string, string>,
  body: string
): string {
  const folderPath = path.join(VAULT_PATH, folderName);
  ensureDir(folderPath);

  const frontmatter = Object.entries(meta)
    .map(([k, v]) => `${k}: ${v}`)
    .join('\n');

  const content = `---\n${frontmatter}\n---\n\n${body}`;
  const filePath = path.join(folderPath, filename);
  fs.writeFileSync(filePath, content, 'utf-8');
  return filePath;
}

/** Update frontmatter field in an existing vault file */
export function updateVaultFileMeta(
  filePath: string,
  updates: Record<string, string>
): boolean {
  try {
    if (!fs.existsSync(filePath)) return false;

    let content = fs.readFileSync(filePath, 'utf-8');
    for (const [key, value] of Object.entries(updates)) {
      const regex = new RegExp(`${key}:\\s*.+`);
      if (regex.test(content)) {
        content = content.replace(regex, `${key}: ${value}`);
      } else {
        // Add field before closing ---
        content = content.replace(/\n---/, `\n${key}: ${value}\n---`);
      }
    }
    fs.writeFileSync(filePath, content, 'utf-8');
    return true;
  } catch (error) {
    console.error(`Error updating ${filePath}:`, error);
    return false;
  }
}

// ----- Emails Reader -----

export interface VaultEmail {
  id: string;
  from: string;
  subject: string;
  received: string;
  priority: string;
  status: string;
  snippet: string;
}

export function getEmails(limit: number = 20): VaultEmail[] {
  const emailsPath = path.join(VAULT_PATH, 'Needs_Action', 'Emails');
  const emails: VaultEmail[] = [];

  try {
    if (!fs.existsSync(emailsPath)) return emails;

    const files = fs.readdirSync(emailsPath)
      .filter(f => f.endsWith('.md'))
      .sort((a, b) => b.localeCompare(a))
      .slice(0, limit);

    for (const file of files) {
      const fp = path.join(emailsPath, file);
      const content = fs.readFileSync(fp, 'utf-8');
      const meta = parseFrontmatter(content);
      const body = getBodyContent(content);
      const snippet = body.slice(0, 100).replace(/[#*`\n]/g, ' ').trim();

      emails.push({
        id: file.replace('.md', ''),
        from: meta.from || 'Unknown',
        subject: meta.subject || file.replace('.md', ''),
        received: meta.received || new Date().toISOString(),
        priority: meta.priority || 'normal',
        status: meta.status || 'unread',
        snippet: snippet || 'No preview',
      });
    }
  } catch (error) {
    console.error('Error loading emails:', error);
  }

  return emails;
}

// ----- Approvals Reader -----

export interface VaultApproval {
  id: string;
  type: string;
  title: string;
  created: string;
  preview: string;
  filePath: string;
}

export function getPendingApprovals(): VaultApproval[] {
  const folders = ['Approvals', 'Pending_Approval'];
  const items: VaultApproval[] = [];

  for (const folder of folders) {
    const approvalsPath = path.join(VAULT_PATH, folder);
    try {
      if (!fs.existsSync(approvalsPath)) continue;

      const files = fs.readdirSync(approvalsPath).filter(f => f.endsWith('.md'));
      for (const file of files) {
        const fp = path.join(approvalsPath, file);
        const content = fs.readFileSync(fp, 'utf-8');
        const meta = parseFrontmatter(content);

        if (meta.status === 'pending' || meta.status === 'pending_approval') {
          const body = getBodyContent(content);
          items.push({
            id: file.replace('.md', ''),
            type: meta.type || 'unknown',
            title: meta.title || meta.subject || file.replace('.md', ''),
            created: meta.created || new Date().toISOString(),
            preview: body.slice(0, 200).replace(/[#*`]/g, '').trim() || 'No preview',
            filePath: fp,
          });
        }
      }
    } catch (error) {
      console.error(`Error reading ${folder}:`, error);
    }
  }

  return items;
}

// ----- CEO Briefing -----

export function getLatestBriefing(): { content: string; date: string } | null {
  const briefingPaths = [
    path.join(VAULT_PATH, 'Business', 'CEO_Briefings'),
    path.join(VAULT_PATH, 'CEO_Briefings'),
  ];

  for (const briefingPath of briefingPaths) {
    try {
      if (!fs.existsSync(briefingPath)) continue;

      const files = fs.readdirSync(briefingPath)
        .filter(f => f.endsWith('.md'))
        .sort((a, b) => b.localeCompare(a));

      if (files.length > 0) {
        const fp = path.join(briefingPath, files[0]);
        const content = fs.readFileSync(fp, 'utf-8');
        const meta = parseFrontmatter(content);
        return {
          content: getBodyContent(content),
          date: meta.date || meta.created || files[0].replace('.md', ''),
        };
      }
    } catch (error) {
      console.error('Error reading briefings:', error);
    }
  }

  return null;
}

// ----- Invoice Helpers -----

export function calcInvoiceTotal(invoice: {
  line_items?: Array<{ quantity: number; unit_price: number }>;
  discount?: number;
}): number {
  const subtotal = (invoice.line_items || []).reduce(
    (sum, item) => sum + (item.quantity || 0) * (item.unit_price || 0),
    0
  );
  return subtotal - (invoice.discount || 0);
}
