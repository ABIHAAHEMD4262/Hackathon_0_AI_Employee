# Setting Up Automatic Scheduling

This guide explains how to make your AI Employee run automatically.

## Option 1: Using Cron (Linux/WSL) - Recommended

### 1. Make the startup script executable
```bash
chmod +x /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/scripts/run_ai_employee.sh
```

### 2. Edit your crontab
```bash
crontab -e
```

### 3. Add these lines to run AI Employee:

```cron
# Start AI Employee on system boot
@reboot /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/scripts/run_ai_employee.sh start

# Check Gmail every 5 minutes (backup if watcher stops)
*/5 * * * * cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/watchers && python3 gmail_watcher.py "$VAULT_PATH" --once

# Run orchestrator check every 10 minutes
*/10 * * * * cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/watchers && python3 orchestrator.py "$VAULT_PATH" --once

# Daily dashboard update at 9 AM
0 9 * * * cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault && python3 -c "from watchers.orchestrator import AIEmployeeOrchestrator; o = AIEmployeeOrchestrator('.'); o.update_dashboard()"
```

### 4. Save and exit (Ctrl+X, then Y, then Enter)

### 5. Verify cron is running
```bash
crontab -l
```

---

## Option 2: Using Windows Task Scheduler (For when PC is always on)

### Step 1: Create a batch file
Create `C:\AI_Employee\start_ai_employee.bat`:

```batch
@echo off
echo Starting AI Employee...
wsl -d Ubuntu -e /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/scripts/run_ai_employee.sh start
echo AI Employee started!
pause
```

### Step 2: Open Task Scheduler
1. Press Win + R
2. Type `taskschd.msc`
3. Press Enter

### Step 3: Create New Task
1. Click "Create Basic Task..."
2. Name: "AI Employee Startup"
3. Trigger: "When the computer starts"
4. Action: "Start a program"
5. Program: `C:\AI_Employee\start_ai_employee.bat`
6. Finish

### Step 4: Set to run with highest privileges
1. Right-click the task → Properties
2. Check "Run with highest privileges"
3. OK

---

## Option 3: Manual Start (Development Mode)

### Start all services:
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/scripts
./run_ai_employee.sh start
```

### Check status:
```bash
./run_ai_employee.sh status
```

### Stop all services:
```bash
./run_ai_employee.sh stop
```

---

## Testing Your Setup

### 1. Test Gmail Watcher
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/watchers
python3 gmail_watcher.py /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault --test
```

### 2. Test Orchestrator
```bash
python3 orchestrator.py /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault --demo
```

### 3. Test Approval Workflow
```bash
python3 approval_workflow.py /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault --demo
```

---

## Troubleshooting

### Services not starting?
1. Check Python is installed: `python3 --version`
2. Check dependencies: `pip list | grep google`
3. Check logs: `cat /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/Logs/System/*.log`

### Cron not running in WSL?
WSL doesn't run cron by default. Start it:
```bash
sudo service cron start
```

To auto-start cron in WSL, add to `~/.bashrc`:
```bash
# Start cron if not running
if ! pgrep -x "cron" > /dev/null; then
    sudo service cron start
fi
```

### Permission denied?
```bash
chmod +x /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/scripts/*.sh
chmod +x /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/watchers/*.py
```

---

## What Gets Scheduled

| Component | Frequency | What It Does |
|-----------|-----------|--------------|
| Gmail Watcher | Every 2 min | Checks for new emails |
| LinkedIn Watcher | Every 5 min | Checks notifications, queued posts |
| Approval Workflow | Every 30 sec | Checks for approved/rejected items |
| Orchestrator | Every 1 min | Processes new tasks, creates plans |
| Dashboard Update | Every 10 min | Updates status metrics |

---

## Security Notes

1. **Never commit credentials** - Keep .env files out of git
2. **Use app passwords** - Don't use your main Gmail password
3. **Review approvals** - Always check Pending_Approval before approving
4. **Monitor logs** - Regularly check Logs folder for issues

---

*Setup guide for AI Employee Silver Tier*
