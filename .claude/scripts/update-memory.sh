#!/bin/bash
# Update Memory Helper Script
#
# Makes it easy to add dated entries to memory files.
# Usage:
#   ./update-memory.sh patterns "New pattern description"
#   ./update-memory.sh decisions "Why we chose approach X"
#   ./update-memory.sh gotchas "Watch out for Y"
#   ./update-memory.sh tips "Useful command: ..."

set -e

MEMORY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/memory"
DATE=$(date +%Y-%m-%d)

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: $0 <file> <entry>"
    echo ""
    echo "Files:"
    echo "  patterns   - Coding patterns and architectural decisions"
    echo "  decisions  - Key decisions and their rationale"
    echo "  gotchas    - Common pitfalls and gotchas"
    echo "  tips       - Useful commands and tips"
    echo ""
    echo "Examples:"
    echo "  $0 patterns 'E2E testing hook pattern for frontend changes'"
    echo "  $0 decisions 'Chose lowest NE = best for recommendation systems'"
    echo "  $0 gotchas 'Router base path must match Vite base configuration'"
    echo "  $0 tips 'Run e2e tests: python3 tests/e2e/test_playground_page.py'"
    exit 1
}

# Check arguments
if [ $# -lt 2 ]; then
    show_usage
fi

FILE_NAME="$1"
ENTRY="$2"

# Validate file name
case "$FILE_NAME" in
    patterns|decisions|gotchas|tips)
        FILE_PATH="$MEMORY_DIR/${FILE_NAME}.md"
        ;;
    *)
        echo -e "${YELLOW}Error: Invalid file name. Must be one of: patterns, decisions, gotchas, tips${NC}"
        show_usage
        ;;
esac

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${YELLOW}Warning: $FILE_PATH does not exist. Creating it...${NC}"
    mkdir -p "$MEMORY_DIR"
    echo "# $(echo ${FILE_NAME^})" > "$FILE_PATH"
    echo "" >> "$FILE_PATH"
fi

# Format the entry with date
FORMATTED_ENTRY="## [$DATE] $ENTRY"

# Add entry to the top of the file (after the title)
{
    head -n 2 "$FILE_PATH"
    echo ""
    echo "$FORMATTED_ENTRY"
    echo ""
    tail -n +3 "$FILE_PATH"
} > "${FILE_PATH}.tmp"

mv "${FILE_PATH}.tmp" "$FILE_PATH"

echo -e "${GREEN}✓${NC} Added to ${BLUE}${FILE_NAME}.md${NC}:"
echo -e "${GREEN}  $FORMATTED_ENTRY${NC}"
echo ""
echo -e "File: ${BLUE}$FILE_PATH${NC}"

# Offer to open in editor
read -p "Open file in editor? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ${EDITOR:-vim} "$FILE_PATH"
fi
