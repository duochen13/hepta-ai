#!/bin/bash
# Automated Issue Review Hook - Hybrid Approach
#
# Workflow:
# 1. Detect new GitHub issues (created within 60 seconds)
# 2. Run basic Issue Review (quick validation)
# 3. If score >= 7/10, offer to convert to plan and run /plan-eng-review
# 4. Run client code e2e tests if client files changed
#
# This provides both quick scope validation and deep engineering analysis.

# Run client code e2e tests hook
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$SCRIPT_DIR/client-change-hook.sh" ]; then
    "$SCRIPT_DIR/client-change-hook.sh"
fi

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    exit 0  # Silently exit if gh not available
fi

# Try to detect if an issue was just created by checking recent issues
# Get the most recent issue (created within last 60 seconds)
RECENT_ISSUE=$(gh issue list --limit 1 --json number,createdAt --jq '.[] | select((now - (.createdAt | fromdateiso8601)) < 60) | .number' 2>/dev/null)

if [ -n "$RECENT_ISSUE" ]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "🤖 HYBRID ISSUE REVIEW WORKFLOW TRIGGERED"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Issue #$RECENT_ISSUE was just created."
    echo ""
    echo "📋 PHASE 1: Issue Review (Quick Validation)"
    echo "─────────────────────────────────────────────────────────"
    echo "Running basic issue review to validate scope and feasibility..."
    echo ""
    echo "Review issue #$RECENT_ISSUE covering:"
    echo "  1. ✅ Strengths (2-4 points)"
    echo "  2. ⚠️ Concerns & Gaps (3-6 points)"
    echo "  3. 🔍 Technical Feasibility Analysis"
    echo "  4. 📝 Recommendations"
    echo "  5. ✅ Final Verdict (Score/10)"
    echo ""
    echo "📐 PHASE 2: Engineering Review (If Score >= 7/10)"
    echo "─────────────────────────────────────────────────────────"
    echo "If issue passes initial review:"
    echo "  → Convert issue to plan format"
    echo "  → Run /plan-eng-review for deep architecture analysis"
    echo "  → Get implementation recommendations"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "HOOK_ACTION: review-issue-$RECENT_ISSUE"
fi

exit 0
