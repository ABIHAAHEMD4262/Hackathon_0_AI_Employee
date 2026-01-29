# AI Employee Dashboard

A real-time dashboard for monitoring and managing your AI Employee system.

## Features

- **Stats Overview**: See tasks needing action, in progress, pending approval, and completed today
- **Pending Approvals**: Review and approve/reject AI-generated content (emails, social posts)
- **System Health**: Monitor the status of all AI Employee components
- **Weekly Task Chart**: Visualize task completion trends
- **Recent Activity**: View the latest actions and events

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Configuration

Set the `VAULT_PATH` environment variable to point to your AI Employee vault:

```bash
# Windows (PowerShell)
$env:VAULT_PATH="G:\Hackathon_0\AI_Employee\AI_Employee_Vault"

# Linux/Mac
export VAULT_PATH="/path/to/AI_Employee_Vault"
```

If not set, it defaults to the parent directory of the dashboard.

## API Endpoints

### GET /api/dashboard

Returns dashboard data including:
- `stats`: Task counts by status
- `pendingApprovals`: Items awaiting human approval
- `activities`: Recent log entries
- `health`: Component status
- `lastUpdated`: Timestamp

### POST /api/approve

Process an approval decision.

**Body:**
```json
{
  "id": "approval-item-id",
  "action": "approve" | "reject"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Item approved successfully",
  "id": "approval-item-id",
  "newStatus": "approved"
}
```

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS

## Folder Structure

```
dashboard/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dashboard/route.ts  # Dashboard data endpoint
│   │   │   └── approve/route.ts    # Approval action endpoint
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx                # Main dashboard page
│   └── components/
│       ├── PendingApprovals.tsx
│       ├── RecentActivity.tsx
│       ├── StatsCards.tsx
│       ├── SystemHealth.tsx
│       └── TaskChart.tsx
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Integration with AI Employee

The dashboard reads from and writes to the vault structure:

- **Approvals/**: Pending approval items (markdown files)
- **Approved/**: Approved items moved here after approval
- **Rejected/**: Rejected items moved here after rejection
- **Logs/**: Daily log files for activity feed
- **Tasks/**: Task files for stats calculation
- **.status/**: Component health indicators
- **.queue/**: Execution queue for approved items
