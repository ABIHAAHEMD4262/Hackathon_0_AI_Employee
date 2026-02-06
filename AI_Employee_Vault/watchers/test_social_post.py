"""
Test Social Post Flow - Gold Tier Verification
================================================
Simulates the full cross-platform social posting flow:
  1. Creates draft posts for each platform -> Pending_Approval/
  2. Moves them to Approved/ (simulating human approval)
  3. Runs each poster's process_approved_posts (dry-run)
  4. Verifies summaries appear in Logs/SocialMedia/

Run: python test_social_post.py
"""

import os
import sys
import shutil
import time
from pathlib import Path
from datetime import datetime

# Ensure DRY_RUN is on for safety
os.environ['DRY_RUN'] = 'true'

# Add watchers dir to path
sys.path.insert(0, str(Path(__file__).parent))

VAULT_PATH = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))


def banner(msg: str):
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print('=' * 60)


def test_platform(platform_name: str, poster_module: str, poster_class: str, draft_topic: str):
    """Test a single platform's full flow."""
    print(f"\n--- Testing {platform_name} ---")

    # Import poster
    mod = __import__(poster_module)
    cls = getattr(mod, poster_class)
    poster = cls(VAULT_PATH)

    vault = Path(VAULT_PATH)
    pending = vault / 'Pending_Approval'
    approved = vault / 'Approved'
    done = vault / 'Done'
    social_logs = vault / 'Logs' / 'SocialMedia'

    for d in [pending, approved, done, social_logs]:
        d.mkdir(parents=True, exist_ok=True)

    # Count existing summaries
    summaries_before = len(list(social_logs.glob(f'{platform_name.lower()}_summary_*.md')))

    # Step 1: Create draft
    print(f"  [1/4] Creating draft post...")
    draft_path = poster.create_post_draft(draft_topic)
    assert draft_path.exists(), f"Draft not created: {draft_path}"
    print(f"        -> {draft_path.name}")

    # Step 2: Simulate human approval (move to Approved/)
    print(f"  [2/4] Simulating human approval...")
    approved_path = approved / draft_path.name
    shutil.move(str(draft_path), str(approved_path))
    assert approved_path.exists(), "File not moved to Approved/"
    print(f"        -> Moved to Approved/")

    # Step 3: Run poster
    print(f"  [3/4] Running poster (dry-run)...")
    poster.run_once()

    # Step 4: Verify summary was written
    summaries_after = len(list(social_logs.glob(f'{platform_name.lower()}_summary_*.md')))
    summary_created = summaries_after > summaries_before

    # Check if file was moved to Done/
    done_file = done / draft_path.name
    file_moved = done_file.exists()

    print(f"  [4/4] Verification:")
    print(f"        Summary logged: {'PASS' if summary_created else 'FAIL'}")
    print(f"        File archived:  {'PASS' if file_moved else 'FAIL (may remain in Approved/)'}")

    return summary_created


def test_ceo_briefing():
    """Test CEO briefing generation."""
    print("\n--- Testing CEO Briefing ---")

    from ceo_briefing import CEOBriefingGenerator
    gen = CEOBriefingGenerator(VAULT_PATH)

    print("  [1/2] Generating briefing...")
    briefing_path = gen.generate_weekly_briefing()

    assert briefing_path.exists(), "Briefing not generated"
    content = briefing_path.read_text(encoding='utf-8')

    print("  [2/2] Verification:")
    has_financial = 'Financial Overview' in content
    has_goals = 'Business Goals' in content
    has_recommendations = 'Recommendations' in content or 'suggestions' in content.lower()

    print(f"        Financial section: {'PASS' if has_financial else 'FAIL'}")
    print(f"        Goals section:     {'PASS' if has_goals else 'FAIL'}")
    print(f"        Recommendations:   {'PASS' if has_recommendations else 'FAIL'}")
    print(f"        -> {briefing_path}")

    return has_financial and has_recommendations


def test_approval_executor():
    """Test that approval executor handles social post types."""
    print("\n--- Testing Approval Executor ---")

    from approval_executor import ApprovalExecutor
    executor = ApprovalExecutor(VAULT_PATH)

    print("  [1/1] Checking queue...")
    executor.run_once()
    print("        -> Executor ran without errors: PASS")
    return True


def main():
    banner("AI Employee - Gold Tier Social Post Test")
    print(f"Vault: {VAULT_PATH}")
    print(f"DRY_RUN: {os.getenv('DRY_RUN', 'true')}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Test each social platform
    platforms = [
        ('Facebook', 'facebook_poster', 'FacebookPoster', 'AI automation for small business'),
        ('Instagram', 'instagram_poster', 'InstagramPoster', 'Behind the scenes of our AI project'),
        ('Twitter', 'twitter_x_poster', 'TwitterXPoster', 'Excited about AI automation!'),
    ]

    for name, module, cls, topic in platforms:
        try:
            results[name] = test_platform(name, module, cls, topic)
        except Exception as e:
            print(f"  ERROR: {e}")
            results[name] = False

    # Test CEO Briefing
    try:
        results['CEO Briefing'] = test_ceo_briefing()
    except Exception as e:
        print(f"  ERROR: {e}")
        results['CEO Briefing'] = False

    # Test Approval Executor
    try:
        results['Approval Executor'] = test_approval_executor()
    except Exception as e:
        print(f"  ERROR: {e}")
        results['Approval Executor'] = False

    # Summary
    banner("Test Results")
    passed = 0
    total = len(results)
    for name, ok in results.items():
        status = 'PASS' if ok else 'FAIL'
        icon = '+' if ok else '-'
        print(f"  [{icon}] {name}: {status}")
        if ok:
            passed += 1

    print(f"\n  {passed}/{total} tests passed")
    print(f"\n  Gold Tier Social Integration: {'COMPLETE' if passed == total else 'PARTIAL'}")

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
