#!/usr/bin/env python3
"""
AI Employee - Comprehensive Feature Test Suite
==============================================
Tests all features across Bronze, Silver, and Gold tiers.

Usage: python test_all_features.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_success(text):
    print(f"  {Colors.GREEN}✓{Colors.END} {text}")

def print_fail(text):
    print(f"  {Colors.RED}✗{Colors.END} {text}")

def print_warn(text):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {text}")

def print_section(text):
    print(f"\n{Colors.BOLD}{text}{Colors.END}")

# Paths
PROJECT_ROOT = Path(__file__).parent
VAULT_PATH = PROJECT_ROOT / 'AI_Employee_Vault'

results = {
    'bronze': {'passed': 0, 'failed': 0, 'tests': []},
    'silver': {'passed': 0, 'failed': 0, 'tests': []},
    'gold': {'passed': 0, 'failed': 0, 'tests': []}
}

def test(tier, name, condition, details=""):
    """Run a test and record results."""
    if condition:
        print_success(f"{name}")
        results[tier]['passed'] += 1
        results[tier]['tests'].append({'name': name, 'status': 'passed', 'details': details})
    else:
        print_fail(f"{name}")
        results[tier]['failed'] += 1
        results[tier]['tests'].append({'name': name, 'status': 'failed', 'details': details})

# ==================== BRONZE TIER TESTS ====================

def test_bronze_tier():
    print_header("BRONZE TIER TESTS")

    # Test 1: Vault exists
    print_section("1. Obsidian Vault Structure")
    test('bronze', "Vault directory exists", VAULT_PATH.exists())
    test('bronze', ".obsidian folder exists", (VAULT_PATH / '.obsidian').exists())
    test('bronze', "Dashboard.md exists", (VAULT_PATH / 'Dashboard.md').exists())
    test('bronze', "Company_Handbook.md exists", (VAULT_PATH / 'Company_Handbook.md').exists())

    # Test 2: Folder structure
    print_section("2. Folder Structure")
    folders = ['Needs_Action', 'In_Progress', 'Pending_Approval', 'Approved', 'Rejected', 'Done', 'Plans', 'Logs']
    for folder in folders:
        test('bronze', f"Folder /{folder} exists", (VAULT_PATH / folder).exists())

    # Test 3: Subfolders
    print_section("3. Subfolders")
    subfolders = [
        'Needs_Action/Emails',
        'Needs_Action/LinkedIn',
        'Needs_Action/WhatsApp',
        'Logs/Email',
        'Logs/Errors'
    ]
    for subfolder in subfolders:
        test('bronze', f"Subfolder /{subfolder} exists", (VAULT_PATH / subfolder).exists())

    # Test 4: Agent Skills
    print_section("4. Agent Skills")
    skills_path = VAULT_PATH / '.claude' / 'skills'
    test('bronze', "Skills directory exists", skills_path.exists())

    expected_skills = ['email-manager.md', 'social-media-manager.md', 'ceo-briefing.md', 'task-orchestrator.md']
    for skill in expected_skills:
        test('bronze', f"Skill {skill} exists", (skills_path / skill).exists())

    # Test 5: Watcher scripts exist
    print_section("5. Watcher Scripts")
    watchers_path = VAULT_PATH / 'watchers'
    test('bronze', "Watchers directory exists", watchers_path.exists())

    watcher_files = ['gmail_watcher.py', 'base_watcher.py']
    for watcher in watcher_files:
        test('bronze', f"Watcher {watcher} exists", (watchers_path / watcher).exists())

# ==================== SILVER TIER TESTS ====================

def test_silver_tier():
    print_header("SILVER TIER TESTS")

    # Test 1: Multiple watchers
    print_section("1. Multiple Watcher Scripts")
    watchers_path = VAULT_PATH / 'watchers'
    watchers = ['gmail_watcher.py', 'linkedin_watcher.py', 'whatsapp_watcher.py']
    for watcher in watchers:
        test('silver', f"Watcher {watcher} exists", (watchers_path / watcher).exists())

    # Additional watchers in src
    src_watchers = PROJECT_ROOT / 'src' / 'watchers'
    if src_watchers.exists():
        for watcher in ['calendar_watcher.py', 'slack_watcher.py', 'twitter_watcher.py']:
            test('silver', f"Extended watcher {watcher} exists", (src_watchers / watcher).exists())

    # Test 2: MCP Servers
    print_section("2. MCP Servers")
    mcp_path = VAULT_PATH / 'mcp_servers'
    test('silver', "MCP servers directory exists", mcp_path.exists())
    test('silver', "Email server exists", (mcp_path / 'email_server.py').exists())

    # Verify email server has required functions
    if (mcp_path / 'email_server.py').exists():
        content = (mcp_path / 'email_server.py').read_text()
        test('silver', "Email server has send_email", "def send_email" in content)
        test('silver', "Email server has draft_email", "def draft_email" in content)
        test('silver', "Email server has get_tool_definitions", "def get_tool_definitions" in content)

    # Test 3: Orchestrator
    print_section("3. Orchestrator & Plan.md")
    test('silver', "Orchestrator exists", (watchers_path / 'orchestrator.py').exists())

    if (watchers_path / 'orchestrator.py').exists():
        content = (watchers_path / 'orchestrator.py').read_text()
        test('silver', "Orchestrator has create_plan", "def create_plan" in content)
        test('silver', "Orchestrator has scan_needs_action", "def scan_needs_action" in content)
        test('silver', "Orchestrator has run_cycle", "def run_cycle" in content)

    test('silver', "Plans folder exists", (VAULT_PATH / 'Plans').exists())

    # Test 4: HITL Approval workflow
    print_section("4. Human-in-the-Loop Approval")
    approval_folders = ['Pending_Approval', 'Approvals', 'Approved', 'Rejected']
    for folder in approval_folders:
        test('silver', f"HITL folder /{folder} exists", (VAULT_PATH / folder).exists())

    # Test approval API
    api_path = VAULT_PATH / 'dashboard' / 'src' / 'app' / 'api'
    test('silver', "API directory exists", api_path.exists())
    test('silver', "Approve API exists", (api_path / 'approve' / 'route.ts').exists())
    test('silver', "Drafts API exists", (api_path / 'drafts' / 'route.ts').exists())

    # Test 5: Scheduled Tasks
    print_section("5. Scheduled Tasks")
    test('silver', "Scheduled tasks script exists", (watchers_path / 'scheduled_tasks.py').exists())

    if (watchers_path / 'scheduled_tasks.py').exists():
        content = (watchers_path / 'scheduled_tasks.py').read_text()
        test('silver', "Has ceo_briefing task", "ceo_briefing" in content)
        test('silver', "Has email_check task", "email_check" in content)
        test('silver', "Has health_check task", "health_check" in content)
        test('silver', "Supports cron scheduling", "cron" in content.lower())

# ==================== GOLD TIER TESTS ====================

def test_gold_tier():
    print_header("GOLD TIER TESTS")

    # Test 1: Social Media MCP Server
    print_section("1. Social Media MCP Server")
    mcp_path = VAULT_PATH / 'mcp_servers'
    test('gold', "Social media server exists", (mcp_path / 'social_media_server.py').exists())

    if (mcp_path / 'social_media_server.py').exists():
        content = (mcp_path / 'social_media_server.py').read_text()
        test('gold', "Supports Facebook", "FacebookAPI" in content)
        test('gold', "Supports Instagram", "InstagramAPI" in content)
        test('gold', "Supports Twitter", "TwitterAPI" in content)
        test('gold', "Has post_to_social", "def post_to_social" in content)
        test('gold', "Has draft_social_post", "def draft_social_post" in content)
        test('gold', "Has get_social_analytics", "def get_social_analytics" in content)

    # Test 2: CEO Briefing Generator
    print_section("2. CEO Briefing Generator")
    watchers_path = VAULT_PATH / 'watchers'
    test('gold', "CEO briefing script exists", (watchers_path / 'ceo_briefing.py').exists())
    test('gold', "CEO Briefings folder exists", (VAULT_PATH / 'Business' / 'CEO_Briefings').exists())

    if (watchers_path / 'ceo_briefing.py').exists():
        content = (watchers_path / 'ceo_briefing.py').read_text()
        test('gold', "Has generate_weekly_briefing", "def generate_weekly_briefing" in content)
        test('gold', "Has _analyze_tasks", "def _analyze_tasks" in content)
        test('gold', "Has _generate_recommendations", "def _generate_recommendations" in content)

    # Test 3: Ralph Wiggum Loop
    print_section("3. Ralph Wiggum Loop (Persistence)")
    test('gold', "Ralph Wiggum script exists", (watchers_path / 'ralph_wiggum_loop.py').exists())

    if (watchers_path / 'ralph_wiggum_loop.py').exists():
        content = (watchers_path / 'ralph_wiggum_loop.py').read_text()
        test('gold', "Has execute_task", "def execute_task" in content)
        test('gold', "Has _execute_step_with_retry", "def _execute_step_with_retry" in content)
        test('gold', "Has _wait_for_approval", "def _wait_for_approval" in content)
        test('gold', "Has run_loop", "def run_loop" in content)
        test('gold', "Implements StepStatus enum", "class StepStatus" in content)

    # Test 4: Error Recovery
    print_section("4. Error Recovery & Graceful Degradation")
    test('gold', "Error recovery script exists", (watchers_path / 'error_recovery.py').exists())
    test('gold', "Quarantine folder exists", (VAULT_PATH / 'Quarantine').exists())

    if (watchers_path / 'error_recovery.py').exists():
        content = (watchers_path / 'error_recovery.py').read_text()
        test('gold', "Has RETRY strategy", "RETRY" in content)
        test('gold', "Has FALLBACK strategy", "FALLBACK" in content)
        test('gold', "Has QUARANTINE strategy", "QUARANTINE" in content)
        test('gold', "Has circuit breaker", "circuit_breaker" in content)
        test('gold', "Has handle_error", "def handle_error" in content)

    # Test 5: Comprehensive Audit Logging
    print_section("5. Audit Logging")
    log_folders = ['Logs/Email', 'Logs/SocialMedia', 'Logs/Errors', 'Logs/Scheduled', 'Logs/RalphWiggum']
    for folder in log_folders:
        test('gold', f"Log folder /{folder} exists", (VAULT_PATH / folder).exists())

    # Test 6: MCP Configuration
    print_section("6. MCP Configuration")
    config_path = PROJECT_ROOT / 'config'
    test('gold', "Config directory exists", config_path.exists())
    test('gold', "MCP config exists", (config_path / 'mcp_config.json').exists())

    if (config_path / 'mcp_config.json').exists():
        try:
            content = json.loads((config_path / 'mcp_config.json').read_text())
            test('gold', "MCP config is valid JSON", True)
            test('gold', "MCP config has servers", "servers" in content)
            test('gold', "MCP config has security", "security" in content)
        except:
            test('gold', "MCP config is valid JSON", False)

    # Test 7: Documentation
    print_section("7. Documentation")
    test('gold', "README.md exists", (PROJECT_ROOT / 'README.md').exists())
    test('gold', "DOCUMENTATION.md exists", (VAULT_PATH / 'DOCUMENTATION.md').exists())
    test('gold', "CLAUDE.md exists", (PROJECT_ROOT / 'CLAUDE.md').exists())

    if (PROJECT_ROOT / 'README.md').exists():
        content = (PROJECT_ROOT / 'README.md').read_text()
        test('gold', "README has architecture diagram", "```" in content and "PERCEPTION" in content.upper())
        test('gold', "README has installation guide", "Installation" in content)
        test('gold', "README has feature list", "Bronze" in content and "Silver" in content and "Gold" in content)

# ==================== DASHBOARD TESTS ====================

def test_dashboard():
    print_header("DASHBOARD TESTS")

    dashboard_path = VAULT_PATH / 'dashboard'

    print_section("1. Dashboard Structure")
    test('bronze', "Dashboard directory exists", dashboard_path.exists())
    test('bronze', "package.json exists", (dashboard_path / 'package.json').exists())
    test('bronze', "Main page exists", (dashboard_path / 'src' / 'app' / 'page.tsx').exists())

    print_section("2. API Routes")
    api_path = dashboard_path / 'src' / 'app' / 'api'
    api_routes = ['dashboard', 'drafts', 'approve']
    for route in api_routes:
        test('silver', f"API route /{route} exists", (api_path / route / 'route.ts').exists())

    print_section("3. Dashboard Features")
    if (dashboard_path / 'src' / 'app' / 'page.tsx').exists():
        content = (dashboard_path / 'src' / 'app' / 'page.tsx').read_text()

        # Check for tab implementations
        tabs = ['command', 'email', 'social', 'crm', 'financial', 'tasks', 'approvals', 'settings']
        for tab in tabs:
            test('silver', f"Tab '{tab}' implemented", f"'{tab}'" in content or f'"{tab}"' in content)

        # Check for key functions
        test('silver', "Email composer implemented", "emailTo" in content and "emailBody" in content)
        test('silver', "Social media composer implemented", "socialPlatform" in content)
        test('silver', "Approval workflow implemented", "handleApproval" in content)
        test('silver', "Command processing implemented", "processCommand" in content)

# ==================== RUN ALL TESTS ====================

def print_summary():
    print_header("TEST SUMMARY")

    total_passed = 0
    total_failed = 0

    for tier, data in results.items():
        passed = data['passed']
        failed = data['failed']
        total = passed + failed
        total_passed += passed
        total_failed += failed

        status = Colors.GREEN + "PASS" + Colors.END if failed == 0 else Colors.RED + "FAIL" + Colors.END
        print(f"  {tier.upper()} TIER: {passed}/{total} tests passed [{status}]")

    print(f"\n{Colors.BOLD}TOTAL: {total_passed}/{total_passed + total_failed} tests passed{Colors.END}")

    if total_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed! Your AI Employee is ready for submission.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}{total_failed} tests failed. Review the output above.{Colors.END}")

    # Write results to file
    results_file = PROJECT_ROOT / 'test_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_passed': total_passed,
                'total_failed': total_failed
            }
        }, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      🧪 AI EMPLOYEE - COMPREHENSIVE FEATURE TEST 🧪          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Run all tests
    test_bronze_tier()
    test_silver_tier()
    test_gold_tier()
    test_dashboard()

    # Print summary
    print_summary()

if __name__ == '__main__':
    main()
