# mkdocs-lint - MkDocs Rendering Linter and Fixer

## Description

Quick MkDocs rendering verification and automatic issue fixing. This skill identifies and fixes critical rendering issues in MkDocs HTML output without generating comprehensive reports. Use this as part of the pre-commit linting workflow.

## When to Use

Use this skill when:
- Making documentation changes that need verification before commit
- Running the "Lint the docs" workflow (see CLAUDE.md)
- Quick check for critical MkDocs rendering issues
- Want automatic fixes for common problems

**Do NOT use when:**
- You need a comprehensive verification report (use `mkdocs-reviewer` agent instead)
- You need detailed analysis for deployment readiness
- You're doing final pre-deployment verification

## What This Skill Does

1. **Clean rebuild** the MkDocs site
2. **Identify critical issues**:
   - Broken code fences (code blocks rendering as paragraphs)
   - Unclosed admonitions
   - Missing code block language tags
   - Table rendering failures
3. **Automatically fix** issues where possible:
   - Fix admonition indentation
   - Add missing blank lines around code blocks
   - Correct code block syntax
4. **Report unfixable issues** that require manual intervention

## Instructions

When this skill is invoked:

### Step 1: Clean Rebuild (Required)

Follow the critical workflow from CLAUDE.md:

```bash
# Kill any existing server
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Clean rebuild
rm -rf site/
mkdocs build

# Start fresh server in background
mkdocs serve > /tmp/mkdocs.log 2>&1 &

# Wait for server to start
sleep 2
```

**CRITICAL**: Never skip the clean rebuild. MkDocs auto-reload can serve stale cached content.

### Step 2: Quick Verification

Fetch HTML and check for critical issues:

```bash
# Fetch all parts
for i in 1 2 3 4 5; do
  curl -s "http://127.0.0.1:8000/part${i}/" > /tmp/part${i}.html
done

# Check for broken code fences (most common issue)
grep -n '<p>```' /tmp/part*.html

# Check for unclosed admonitions
for i in 1 2 3 4 5; do
  open=$(grep -c '<div class="admonition' /tmp/part${i}.html)
  close=$(grep -c '</div>' /tmp/part${i}.html | grep -A1 'admonition')
  if [ "$open" != "$close" ]; then
    echo "⚠️ part${i}.html: Potential unclosed admonition (open: $open)"
  fi
done

# Check for missing language tags in code blocks
grep -n '<pre><code>' /tmp/part*.html | grep -v 'class="language-'
```

### Step 3: Fix Issues Automatically

For each critical issue found:

#### Fix Broken Code Fences

If you find `<p>```python` in HTML:

1. Read the markdown file at the line number reported
2. Check for common causes:
   - Missing blank line before code fence
   - Incorrect indentation in admonition
   - Mixed tabs/spaces
3. Fix by:
   - Adding blank lines
   - Ensuring 4-space indentation in admonitions
   - Converting tabs to spaces

#### Fix Unclosed Admonitions

If admonitions don't close properly:

1. Find the admonition in markdown
2. Verify all content is indented with exactly 4 spaces
3. Ensure there's a blank line after the admonition
4. Fix indentation issues

#### Fix Missing Language Tags

If code blocks lack language identifiers:

1. Identify the code block in markdown
2. Add appropriate language tag (python, bash, json, etc.)

### Step 4: Verify Fixes

After making fixes:

```bash
# Rebuild and verify
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
rm -rf site/ && mkdocs build && mkdocs serve > /tmp/mkdocs.log 2>&1 &
sleep 2

# Re-check for broken fences
grep -n '<p>```' /tmp/part*.html
```

### Step 5: Report Results

Output a concise summary:

```markdown
## MkDocs Lint Results

**Status**: ✅ PASS / ❌ FAIL

### Issues Fixed
- ✅ Fixed N broken code fences in partX.md
- ✅ Fixed M admonition indentation issues in partY.md

### Issues Requiring Manual Fix
- ❌ Unclosed admonition at docs/partZ.md:123
- ❌ Complex table structure issue at docs/partW.md:456

### Verification
- All parts rendering correctly: ✅/❌
- No broken code fences: ✅/❌
- All admonitions closed: ✅/❌
```

## Critical Checks (Priority Order)

Run these checks in order and fix immediately:

1. **Broken code fences** - Most common and breaks documentation
   ```bash
   grep '<p>```' /tmp/part*.html
   ```

2. **Unclosed admonitions** - Causes content bleeding
   ```bash
   # Count admonition divs
   grep -c 'class="admonition' /tmp/part*.html
   ```

3. **Missing blank lines** - Causes fence failures
   - Check for code fences immediately after text
   - Ensure blank lines before/after admonitions

4. **Indentation in admonitions** - Must be exactly 4 spaces
   - Read admonition content
   - Verify all lines indented with 4 spaces
   - No tabs allowed

## Common Fixes

### Broken Code Fence in Admonition

**Before:**
```markdown
!!! note "Title"
    This is some text
    ```python
    code here
    ```
```

**After:**
```markdown
!!! note "Title"

    This is some text

    ```python
    code here
    ```
```

### Missing Language Tag

**Before:**
```markdown
\`\`\`
code here
\`\`\`
```

**After:**
```markdown
\`\`\`python
code here
\`\`\`
```

## Important Notes

- **Speed over completeness**: Fix critical issues quickly, don't generate reports
- **Auto-fix safe issues**: Only fix formatting/syntax issues, never content
- **Report complex issues**: If unsure, report for manual review
- **Always verify**: Rebuild after fixes to confirm they worked
- **Use Edit tool**: Make precise fixes using the Edit tool, not sed/awk

## Reference

- **STYLES.md Section 2.5**: Admonitions and Callouts (indentation rules)
- **STYLES.md Section 6.3**: MkDocs Admonition Requirements
- **CLAUDE.md**: MkDocs Debugging and Best Practices section
- **mkdocs-reviewer agent**: For comprehensive verification before deployment
