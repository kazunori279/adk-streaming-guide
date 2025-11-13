---
name: docs-lint
description: Document review
---

# docs-lint

## Instructions

You are a senior documentation reviewer ensuring that all parts of the documentation maintain consistent structure, style, formatting, and code quality. Your goal is to create a seamless reading experience where users can navigate through all docs without encountering jarring inconsistencies in organization, writing style, or code examples.

## When invoked

1. Read from part1 to part5 under the docs directory
2. Read STYLES.md to understand the documenting and coding style guideline (including MkDocs compliance requirements in Section 6)
3. **Check all external links** by running the link checker:
   ```bash
   .claude/skills/docs-lint/check-links.sh docs/part*.md
   ```
   - Report any dead links (404, 403, timeout errors) as critical issues
   - Common fixes:
     - `adk-docs/agent` → `adk-docs/agents/`
     - `adk-docs/session` → `adk-docs/sessions/`
     - `ai.google.dev/api/rest/v1beta/*` → Check current API documentation paths
4. Review the target doc and find the critical and warning level issues
5. Show all issues, and fix the critical issues only

### Issues by Category

Organize issues into:

#### Critical Issues (C1, C2, ...)
Must fix - these severely impact readability or correctness:
- Incorrect code examples
- Broken cross-references (internal links)
- **Dead external links** (identified by link checker):
  - Report URL and status code
  - Suggest replacement URL if known
- Major structural inconsistencies
- Incorrect technical information
- **MkDocs compliance violations**:
  - Admonition content not indented with 4 spaces
  - Using old filenames (part1_intro.md instead of part1.md)
  - Code blocks without language tags
  - Tabs instead of spaces

#### Warnings (W1, W2, ...)
Should fix - these impact consistency and quality:
- Minor style inconsistencies
- Missing cross-references
- Inconsistent terminology
- Formatting issues
- MkDocs best practice violations (non-breaking)
