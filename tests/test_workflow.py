#!/usr/bin/env python3
"""
AI Employee - End-to-End Workflow Test
======================================
Tests the complete file-based HITL workflow without requiring
external APIs (Gmail, LinkedIn, etc.).

Usage:
    python tests/test_workflow.py
"""

import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PASS = 0
FAIL = 0


def log(status: str, msg: str):
    global PASS, FAIL
    if status == "PASS":
        PASS += 1
        print(f"  [PASS] {msg}")
    else:
        FAIL += 1
        print(f"  [FAIL] {msg}")


def test_folder_structure(vault: Path):
    """Test 1: All required folders exist."""
    print("\n--- Test 1: Folder Structure ---")
    required = [
        "Needs_Action", "Needs_Action/Emails", "Needs_Action/LinkedIn",
        "Needs_Action/WhatsApp", "Needs_Action/Alerts",
        "Plans", "In_Progress", "Pending_Approval", "Approved",
        "Rejected", "Done", "Quarantine", "Logs",
        "Logs/Email", "Logs/Errors", "Logs/RalphWiggum",
        "Business", "Business/CEO_Briefings",
    ]
    for folder in required:
        p = vault / folder
        if p.is_dir():
            log("PASS", f"{folder}/ exists")
        else:
            log("FAIL", f"{folder}/ MISSING")


def test_core_files(vault: Path):
    """Test 2: Core markdown files exist and have content."""
    print("\n--- Test 2: Core Markdown Files ---")
    files = {
        "Dashboard.md": "Dashboard",
        "Company_Handbook.md": "Handbook",
        "Business/Goals.md": "Goals",
    }
    for path, label in files.items():
        fp = vault / path
        if fp.exists() and fp.stat().st_size > 100:
            log("PASS", f"{label} exists ({fp.stat().st_size} bytes)")
        elif fp.exists():
            log("FAIL", f"{label} exists but too small ({fp.stat().st_size} bytes)")
        else:
            log("FAIL", f"{label} MISSING at {path}")


def test_watcher_creates_action_file(vault: Path):
    """Test 3: Simulate a watcher dropping a file into Needs_Action/."""
    print("\n--- Test 3: Watcher -> Needs_Action ---")
    email_dir = vault / "Needs_Action" / "Emails"
    email_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = email_dir / f"EMAIL_{ts}_Test_Client_Inquiry.md"
    content = f"""---
type: email
from: test.client@example.com
subject: Interested in AI Automation
received: {datetime.now().isoformat()}
priority: high
status: pending
gmail_id: test_msg_001
---

# Email from test.client@example.com

**Subject:** Interested in AI Automation

**Priority:** HIGH

---

## Email Content

Hi, I saw your portfolio. Can you build me an AI chatbot?

---

## Suggested Actions

- [ ] Draft response
- [ ] Move to Pending_Approval
"""

    test_file.write_text(content)

    if test_file.exists():
        log("PASS", f"Created test email: {test_file.name}")
    else:
        log("FAIL", "Failed to create test email file")

    return test_file


def test_orchestrator_creates_plan(vault: Path, task_file: Path):
    """Test 4: Orchestrator reads Needs_Action and creates Plan.md."""
    print("\n--- Test 4: Orchestrator -> Plan.md ---")
    # Import the vault-level orchestrator
    sys.path.insert(0, str(vault / "watchers"))

    try:
        from orchestrator import AIEmployeeOrchestrator
        orch = AIEmployeeOrchestrator(str(vault), check_interval=5)
        tasks = orch.scan_needs_action()
        if tasks:
            log("PASS", f"Orchestrator found {len(tasks)} task(s)")
            plan_path = orch.create_plan(tasks[0])
            if plan_path.exists():
                log("PASS", f"Plan created: {plan_path.name}")
            else:
                log("FAIL", "Plan file not created")
        else:
            log("FAIL", "Orchestrator found 0 tasks")
    except ImportError as e:
        log("FAIL", f"Could not import orchestrator: {e}")
    except Exception as e:
        log("FAIL", f"Orchestrator error: {e}")


def test_hitl_approval_flow(vault: Path, task_file: Path):
    """Test 5: File move through Pending_Approval -> Approved -> Done."""
    print("\n--- Test 5: HITL Approval Flow ---")
    pending = vault / "Pending_Approval"
    approved = vault / "Approved"
    done = vault / "Done"

    for d in [pending, approved, done]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Create draft in Pending_Approval
    draft_name = f"EMAIL_DRAFT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    draft_path = pending / draft_name
    draft_path.write_text("""---
type: email_draft
to: test@example.com
subject: Re: AI Chatbot Inquiry
status: pending_approval
---

# Email Draft - Approval Required

Hi, thanks for reaching out! I'd love to help build an AI chatbot for you.

---

## Actions
- [ ] **APPROVE**
- [ ] **REJECT**
""")

    if draft_path.exists():
        log("PASS", f"Draft created in Pending_Approval/")
    else:
        log("FAIL", "Draft not created")
        return

    # Step 2: Simulate human approval (move to Approved/)
    approved_path = approved / draft_name
    shutil.move(str(draft_path), str(approved_path))

    if approved_path.exists() and not draft_path.exists():
        log("PASS", "Human approved: file moved to Approved/")
    else:
        log("FAIL", "Approval move failed")
        return

    # Step 3: Simulate execution complete (move to Done/)
    done_path = done / draft_name
    shutil.move(str(approved_path), str(done_path))

    if done_path.exists():
        log("PASS", "Task completed: file moved to Done/")
    else:
        log("FAIL", "Done move failed")


def test_ralph_wiggum_plan_generation(vault: Path):
    """Test 6: Ralph Wiggum Loop generates correct steps for email tasks."""
    print("\n--- Test 6: Ralph Wiggum Step Generation ---")
    sys.path.insert(0, str(vault / "watchers"))

    try:
        from ralph_wiggum_loop import RalphWiggumLoop
        loop = RalphWiggumLoop(str(vault))
        steps = loop._generate_steps({"type": "email"})
        if len(steps) >= 4:
            log("PASS", f"Email task generates {len(steps)} steps")
        else:
            log("FAIL", f"Only {len(steps)} steps generated, expected >= 4")

        has_approval = any(s.get("needs_approval") for s in steps)
        if has_approval:
            log("PASS", "At least one step requires approval (HITL enforced)")
        else:
            log("FAIL", "No step requires approval -- HITL violation")
    except ImportError as e:
        log("FAIL", f"Could not import RalphWiggumLoop: {e}")
    except Exception as e:
        log("FAIL", f"RalphWiggum error: {e}")


def test_mcp_email_draft(vault: Path):
    """Test 7: MCP Email Server can create drafts."""
    print("\n--- Test 7: MCP Email Server Draft ---")
    sys.path.insert(0, str(vault / "mcp_servers"))

    try:
        from email_server import EmailServer
        server = EmailServer(str(vault))
        result = server.draft_email(
            to="test@example.com",
            subject="Test Draft",
            body="This is a test draft from the MCP server.",
            context="Automated test"
        )
        if result.get("success"):
            log("PASS", f"MCP draft created: {result.get('draft_id')}")
            # Clean up
            draft_file = Path(result.get("draft_file", ""))
            if draft_file.exists():
                draft_file.unlink()
        else:
            log("FAIL", f"MCP draft failed: {result.get('error')}")
    except ImportError as e:
        log("FAIL", f"Could not import EmailServer: {e}")
    except Exception as e:
        log("FAIL", f"MCP error: {e}")


def test_logging(vault: Path):
    """Test 8: Logging works correctly."""
    print("\n--- Test 8: Audit Logging ---")
    log_dir = vault / "Logs" / "Errors"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"test_{datetime.now().strftime('%Y%m%d')}.json"
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "message": "Test log entry from workflow test",
        "component": "test_workflow"
    }
    log_file.write_text(json.dumps(log_data, indent=2))

    if log_file.exists():
        log("PASS", "Log file created successfully")
        log_file.unlink()  # Clean up
    else:
        log("FAIL", "Log file not created")


def main():
    global PASS, FAIL

    print("=" * 60)
    print("AI Employee - Workflow Test Suite")
    print("=" * 60)

    # Determine vault path
    vault = Path(__file__).parent.parent / "AI_Employee_Vault"
    if not vault.exists():
        print(f"ERROR: Vault not found at {vault}")
        sys.exit(1)

    print(f"Vault: {vault}")

    # Run tests
    test_folder_structure(vault)
    test_core_files(vault)
    task_file = test_watcher_creates_action_file(vault)
    test_orchestrator_creates_plan(vault, task_file)
    test_hitl_approval_flow(vault, task_file)
    test_ralph_wiggum_plan_generation(vault)
    test_mcp_email_draft(vault)
    test_logging(vault)

    # Clean up test email
    if task_file and task_file.exists():
        task_file.unlink()

    # Summary
    total = PASS + FAIL
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
