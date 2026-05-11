#!/bin/bash
# Client Code E2E Testing Hook
#
# Runs e2e tests whenever client directory files are modified
# to ensure /playground page functionality is not broken.

# Check if there are uncommitted changes in client/ directory
CLIENT_CHANGES=$(git diff --name-only client/ 2>/dev/null)
CLIENT_STAGED=$(git diff --cached --name-only client/ 2>/dev/null)

if [ -n "$CLIENT_CHANGES" ] || [ -n "$CLIENT_STAGED" ]; then
    echo "═══════════════════════════════════════════════════════════"
    echo "🧪 CLIENT CODE CHANGES DETECTED - RUNNING E2E TESTS"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Modified files in client/:"
    if [ -n "$CLIENT_CHANGES" ]; then
        echo "$CLIENT_CHANGES" | sed 's/^/  - /'
    fi
    if [ -n "$CLIENT_STAGED" ]; then
        echo "$CLIENT_STAGED" | sed 's/^/  - (staged) /'
    fi
    echo ""
    echo "Running e2e tests for /playground page..."
    echo "─────────────────────────────────────────────────────────"
    echo ""

    # Run the e2e test
    if python3 tests/e2e/test_playground_page.py; then
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "✅ E2E TESTS PASSED - /playground page working correctly"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
    else
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "❌ E2E TESTS FAILED - /playground page has issues"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "⚠️  Please fix the issues before committing."
        echo ""
        # Don't block the commit, just warn
    fi
else
    # No client changes, exit silently
    exit 0
fi

exit 0
