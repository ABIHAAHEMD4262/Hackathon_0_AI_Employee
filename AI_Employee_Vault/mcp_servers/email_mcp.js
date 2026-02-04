#!/usr/bin/env node
/**
 * MCP Email Server (Node.js) - Gold Tier Component
 * ==================================================
 * A Model Context Protocol server that lets Claude send emails.
 *
 * Protocol: JSON-RPC 2.0 over stdin/stdout (MCP standard)
 *
 * Tools provided:
 *   - send_email      Send an approved email via SMTP
 *   - draft_email     Create a draft in Pending_Approval/ for HITL review
 *   - list_drafts     List all pending email drafts
 *
 * Environment variables (required):
 *   EMAIL_USER        Gmail address
 *   EMAIL_PASS        Gmail App Password (16 chars, no spaces)
 *   VAULT_PATH        Path to the Obsidian vault root
 *
 * Usage:
 *   EMAIL_USER=you@gmail.com EMAIL_PASS=xxxx VAULT_PATH=../  node email_mcp.js
 */

"use strict";

const nodemailer = require("nodemailer");
const fs = require("fs");
const path = require("path");
const readline = require("readline");

// ---------------------------------------------------------------------------
// Configuration from environment
// ---------------------------------------------------------------------------
const EMAIL_USER = process.env.EMAIL_USER || "";
const EMAIL_PASS = (process.env.EMAIL_PASS || "").replace(/\s/g, "");
const VAULT_PATH = process.env.VAULT_PATH || path.resolve(__dirname, "..");

const PENDING_APPROVAL = path.join(VAULT_PATH, "Pending_Approval");
const APPROVED = path.join(VAULT_PATH, "Approved");
const LOGS = path.join(VAULT_PATH, "Logs", "Email");

// Ensure directories exist
for (const dir of [PENDING_APPROVAL, APPROVED, LOGS]) {
  fs.mkdirSync(dir, { recursive: true });
}

// ---------------------------------------------------------------------------
// SMTP transporter (lazy init)
// ---------------------------------------------------------------------------
let _transporter = null;

function getTransporter() {
  if (_transporter) return _transporter;
  if (!EMAIL_USER || !EMAIL_PASS) {
    throw new Error(
      "EMAIL_USER and EMAIL_PASS environment variables must be set. " +
      "Use a Gmail App Password (not your regular password)."
    );
  }
  _transporter = nodemailer.createTransport({
    service: "gmail",
    auth: { user: EMAIL_USER, pass: EMAIL_PASS },
  });
  return _transporter;
}

// ---------------------------------------------------------------------------
// Tool definitions (MCP schema)
// ---------------------------------------------------------------------------
const TOOL_DEFINITIONS = [
  {
    name: "send_email",
    description:
      "Send an email that has been approved by the human. ONLY call this after approval.",
    inputSchema: {
      type: "object",
      properties: {
        to: { type: "string", description: "Recipient email address" },
        subject: { type: "string", description: "Email subject line" },
        body: { type: "string", description: "Email body (plain text or HTML)" },
        reply_to: { type: "string", description: "Optional reply-to address" },
      },
      required: ["to", "subject", "body"],
    },
  },
  {
    name: "draft_email",
    description:
      "Create an email draft for human approval. Does NOT send the email.",
    inputSchema: {
      type: "object",
      properties: {
        to: { type: "string", description: "Recipient email address" },
        subject: { type: "string", description: "Email subject line" },
        body: { type: "string", description: "Email body" },
        context: {
          type: "string",
          description: "Why this email is being sent (for the human reviewer)",
        },
      },
      required: ["to", "subject", "body"],
    },
  },
  {
    name: "list_drafts",
    description: "List all email drafts pending human approval.",
    inputSchema: { type: "object", properties: {} },
  },
];

// ---------------------------------------------------------------------------
// Tool implementations
// ---------------------------------------------------------------------------

async function sendEmail({ to, subject, body, reply_to }) {
  const emailId = new Date()
    .toISOString()
    .replace(/[-:T]/g, "")
    .slice(0, 15);

  try {
    const transporter = getTransporter();
    const info = await transporter.sendMail({
      from: EMAIL_USER,
      to,
      subject,
      text: body,
      html: body,
      ...(reply_to ? { replyTo: reply_to } : {}),
    });

    logEmail(emailId, to, subject, "sent");

    return {
      success: true,
      message: `Email sent to ${to}`,
      email_id: emailId,
      messageId: info.messageId,
    };
  } catch (err) {
    logEmail(emailId, to, subject, "failed", err.message);
    return { success: false, error: err.message, email_id: emailId };
  }
}

function draftEmail({ to, subject, body, context }) {
  const ts = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 15);
  const draftId = `EMAIL_DRAFT_${ts}`;
  const filePath = path.join(PENDING_APPROVAL, `${draftId}.md`);

  const content = `---
type: email_draft
draft_id: ${draftId}
to: ${to}
subject: ${subject}
created: ${new Date().toISOString()}
status: pending_approval
---

# Email Draft - Approval Required

## Recipient
**To:** ${to}

## Subject
${subject}

## Email Body

${body}

---

## Context
${context || "No context provided"}

---

## Actions

- [ ] **APPROVE** - Move this file to /Approved to send
- [ ] **REJECT** - Delete this file or move to /Rejected

---

*Draft created by AI Employee MCP Server (Node.js)*
`;

  fs.writeFileSync(filePath, content, "utf-8");

  return {
    success: true,
    message: "Draft created, awaiting human approval",
    draft_id: draftId,
    draft_file: filePath,
  };
}

function listDrafts() {
  const files = fs
    .readdirSync(PENDING_APPROVAL)
    .filter((f) => f.startsWith("EMAIL_DRAFT_") && f.endsWith(".md"));

  const drafts = files.map((f) => {
    const content = fs.readFileSync(path.join(PENDING_APPROVAL, f), "utf-8");
    const meta = {};
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (fmMatch) {
      for (const line of fmMatch[1].split("\n")) {
        const idx = line.indexOf(":");
        if (idx > 0) {
          meta[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
        }
      }
    }
    return { file: f, to: meta.to || "", subject: meta.subject || "" };
  });

  return { success: true, count: drafts.length, drafts };
}

// ---------------------------------------------------------------------------
// Logging helper
// ---------------------------------------------------------------------------
function logEmail(emailId, to, subject, status, error) {
  const logFile = path.join(LOGS, `${emailId}.json`);
  const data = {
    email_id: emailId,
    to,
    subject,
    status,
    timestamp: new Date().toISOString(),
    ...(error ? { error } : {}),
  };
  fs.writeFileSync(logFile, JSON.stringify(data, null, 2));
}

// ---------------------------------------------------------------------------
// MCP JSON-RPC 2.0 handler over stdin/stdout
// ---------------------------------------------------------------------------

const HANDLERS = {
  initialize: () => ({
    protocolVersion: "2024-11-05",
    capabilities: { tools: {} },
    serverInfo: { name: "ai-employee-email-mcp", version: "1.0.0" },
  }),

  "notifications/initialized": () => null,

  "tools/list": () => ({ tools: TOOL_DEFINITIONS }),

  "tools/call": async ({ name, arguments: args }) => {
    switch (name) {
      case "send_email":
        return { content: [{ type: "text", text: JSON.stringify(await sendEmail(args)) }] };
      case "draft_email":
        return { content: [{ type: "text", text: JSON.stringify(draftEmail(args)) }] };
      case "list_drafts":
        return { content: [{ type: "text", text: JSON.stringify(listDrafts()) }] };
      default:
        throw { code: -32601, message: `Unknown tool: ${name}` };
    }
  },
};

async function handleMessage(line) {
  let req;
  try {
    req = JSON.parse(line);
  } catch {
    return;
  }

  const handler = HANDLERS[req.method];
  if (!handler) {
    // Unknown method -- ignore notifications, error on requests
    if (req.id !== undefined) {
      send({ jsonrpc: "2.0", id: req.id, error: { code: -32601, message: "Method not found" } });
    }
    return;
  }

  try {
    const result = await handler(req.params || {});
    if (req.id !== undefined && result !== null) {
      send({ jsonrpc: "2.0", id: req.id, result });
    }
  } catch (err) {
    if (req.id !== undefined) {
      send({
        jsonrpc: "2.0",
        id: req.id,
        error: { code: err.code || -32000, message: err.message || String(err) },
      });
    }
  }
}

function send(obj) {
  const json = JSON.stringify(obj);
  process.stdout.write(json + "\n");
}

// ---------------------------------------------------------------------------
// Main - start reading from stdin
// ---------------------------------------------------------------------------

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on("line", (line) => handleMessage(line.trim()));

process.stderr.write(
  `[ai-employee-email-mcp] Server started. VAULT=${VAULT_PATH} USER=${EMAIL_USER || "(not set)"}\n`
);
