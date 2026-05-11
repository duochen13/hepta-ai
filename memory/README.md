# Memory System

The memory system maintains context across sessions by documenting learnings, decisions, patterns, and gotchas.

## Files

- **patterns.md** - Coding patterns and architectural decisions
- **decisions.md** - Key decisions and their rationale
- **gotchas.md** - Common pitfalls and things to watch out for
- **tips.md** - Useful commands, shortcuts, and tips

## Quick Update (Recommended)

Use the helper script to add dated entries:

```bash
# Add a new pattern
./.claude/scripts/update-memory.sh patterns "E2E testing hook pattern"

# Add a decision
./.claude/scripts/update-memory.sh decisions "Chose lowest NE = best for rec systems"

# Add a gotcha
./.claude/scripts/update-memory.sh gotchas "Router base path must match Vite config"

# Add a tip
./.claude/scripts/update-memory.sh tips "Run e2e tests with: python3 tests/e2e/test_playground_page.py"
```

The script automatically adds dates and offers to open the file for editing.

## Manual Update

Edit files directly and add dated entries:

```markdown
## [2026-05-11] Your Entry Title

Description of the pattern, decision, gotcha, or tip.

**Key Points:**
- Bullet point 1
- Bullet point 2

**Files:**
- `path/to/file.py`
```

## Pre-Push Hook

**Automatic enforcement:** Before pushing to main, the pre-push hook checks if memory files were updated.

**Options if not updated:**
- [a] Abort push - update memory files first (recommended)
- [c] Continue anyway - skip memory update
- [e] Edit memory file now and commit it

**Why this matters:**
- ✓ Maintains context across sessions
- ✓ Documents learnings and decisions
- ✓ Prevents repeating mistakes
- ✓ Helps future sessions start with full context

## Date Format

Always use `[YYYY-MM-DD]` format in section headers:

```markdown
## [2026-05-11] New Pattern Name
```

**Why dates matter:**
- Plans change over time
- Prevents conflicts with old context
- Shows evolution of decisions
- Helps identify outdated patterns

## Loading Memory

Memory files are automatically loaded at session start via `.claude/load-memory.sh`.

To manually load:

```bash
./.claude/load-memory.sh
```

## Best Practices

1. **Update before pushing to main** - The hook will remind you
2. **Use dated entries** - Prevents confusion with old context
3. **Be specific** - Include file paths, code snippets, rationale
4. **Keep it actionable** - Future sessions should be able to use this immediately
5. **Update regularly** - Don't wait until the end of a session
