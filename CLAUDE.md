# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive technical guide for building real-time, bidirectional streaming AI applications using Google's Agent Development Kit (ADK). The repository contains detailed documentation covering ADK's streaming architecture and a working demo application showcasing bidirectional communication with Gemini models.

## Project Structure

```text
adk-streaming-guide/
├── .github/                       # GitHub configuration
│   ├── workflows/                # Automated workflows
│   │   ├── adk-version-monitor.yml    # Monitor ADK releases
│   │   └── claude-code-reviewer.yml   # Automated doc reviews
│   ├── current_adk_version.txt   # Tracked ADK version
│   └── WORKFLOWS.md              # Workflow documentation
├── docs/                          # Multi-part documentation guide
│   ├── part1.md            # Introduction to ADK Bidi-streaming
│   ├── part2.md  # Unified message processing
│   ├── part3.md         # Event handling with run_live()
│   ├── part4.md       # RunConfig configuration
│   └── part5.md  # Multimodal features
├── reviews/                       # Documentation review reports
├── src/bidi-demo/                # Working demo application
│   ├── app/
│   │   ├── main.py              # FastAPI WebSocket server
│   │   ├── static/              # Frontend HTML/JS/CSS
│   │   └── .env                 # Environment configuration
│   └── pyproject.toml           # Python dependencies
├── tests/e2e/                    # End-to-end tests with Chrome DevTools
├── STYLES.md                     # Documentation and code style guide
└── AGENTS.md                     # Claude Code agent configuration
```

## Key Architecture Concepts

This guide covers ADK's bidirectional streaming architecture, which consists of four key phases:

1. **Application Initialization** (once at startup): Create `Agent`, `SessionService`, and `Runner`
2. **Session Initialization** (per user connection): Get/create `Session`, create `RunConfig` and `LiveRequestQueue`, start `run_live()` event loop
3. **Bidi-streaming** (active communication): Concurrent upstream (client → queue) and downstream (events → client) tasks
4. **Termination**: Close `LiveRequestQueue`, disconnect from Live API session

The upstream/downstream concurrent task pattern is fundamental to all streaming applications in this codebase.

## Documentation Standards

**CRITICAL**: All documentation must follow the comprehensive style guidelines in `STYLES.md`.

## Demo Application

The `src/bidi-demo/` directory contains a working FastAPI application demonstrating ADK bidirectional streaming.

For setup instructions, running the server, and feature details, see [`src/bidi-demo/README.md`](src/bidi-demo/README.md).

### Deploy the demo application to adk-samples repo

To deploy the demo application to the adjacent adk-samples repo, copy all files of `src/bidi-demo` to `../adk-samples/python/agents/bidi-demo` except for the files included in `.gitignore`.

## GitHub Actions Workflows

This repository includes automated workflows for maintaining documentation compatibility with ADK updates:

### ADK Version Monitor

- **Schedule**: Runs every 12 hours to check for new ADK releases on PyPI
- **What it does**: When a new version is detected, creates a parent issue and 5 sub-issues (one per documentation part)
- **Location**: `.github/workflows/adk-version-monitor.yml`

### Claude Code Reviewer

- **Trigger**: Automatically responds to issues with the `adk-version-update` label that mention `@claude`
- **What it does**: Uses the `adk-reviewer` agent to analyze documentation for compatibility issues and posts findings
- **Location**: `.github/workflows/claude-code-reviewer.yml`

### Setup Required

To enable these workflows:

1. Install the [Claude GitHub App](https://github.com/apps/claude-code) on this repository
2. Add `ANTHROPIC_API_KEY` to repository secrets (Settings → Secrets and variables → Actions)
3. The workflows will automatically run on schedule and when triggered by issue creation

See `.github/WORKFLOWS.md` for complete setup instructions and workflow details.

## Claude Code Skills

This repository provides specialized knowledge through skill configuration files in `.claude/skills/`:

- **`bidi`** (`.claude/skills/bidi/SKILL.md`): Expert in ADK bidirectional streaming documentation and implementation
- **`google-adk`** (`.claude/skills/google-adk/SKILL.md`): Agent Development Kit (ADK) expertise for Python SDK and API reference
- **`gemini-live-api`** (`.claude/skills/gemini-live-api/SKILL.md`): Google Gemini Live API documentation and guides
- **`vertexai-live-api`** (`.claude/skills/vertexai-live-api/SKILL.md`): Google Cloud Vertex AI Live API documentation
- **`docs-lint`** (`.claude/skills/docs-lint/SKILL.md`): Documentation consistency and style reviewer
- **`mkdocs-lint`** (`.claude/skills/mkdocs-lint/SKILL.md`): MkDocs rendering linter that identifies and fixes critical rendering issues

### Using Skills

To activate a skill, reference it directly:

- **For ADK expertise**: Say "use google-adk skill" or "access the google-adk skill"
- **For bidirectional streaming**: Say "use bidi skill" or "access the bidi skill"
- **For Gemini Live API**: Say "use gemini-live-api skill"
- **For Vertex AI Live API**: Say "use vertexai-live-api skill"
- **For documentation review**: Say "use docs-lint skill"
- **For MkDocs rendering check**: Say "use mkdocs-lint skill"

The skills are implemented through repository documentation and configuration files that Claude reads directly.

## Claude Code Agents

This repository provides specialized agent configurations in `.claude/agents/` for automated reviews and analysis:

- **`adk-reviewer`** (`.claude/agents/adk-reviewer.md`): Code and document reviewer with ADK source code expertise
- **`change-reviewer`** (`.claude/agents/change-reviewer.md`): Analyzes changes between ADK releases and identifies impacts on documentation and demo code
- **`docs-reviewer`** (`.claude/agents/docs-reviewer.md`): Documentation consistency and style reviewer across all parts
- **`gemini-scanner`** (`.claude/agents/gemini-scanner.md`): Research agent for Gemini Live API and Vertex AI Live API model information
- **`mkdocs-reviewer`** (`.claude/agents/mkdocs-reviewer.md`): MkDocs rendering verification agent that validates HTML output matches markdown expectations

### Agent Usage

Agents are primarily used in GitHub Actions workflows but can also be invoked manually:

- **For ADK compatibility review**: The `adk-reviewer` agent analyzes code/docs against latest ADK source
- **For release change analysis**: The `change-reviewer` agent analyzes changes between ADK releases and their impact
- **For documentation style review**: The `docs-reviewer` agent ensures consistent structure and formatting
- **For model research**: The `gemini-scanner` agent gathers latest model capabilities and availability
- **For MkDocs rendering verification**: The `mkdocs-reviewer` agent validates HTML output matches markdown expectations before deployment

All agents generate timestamped reports in the `reviews/` directory with structured findings categorized as Critical, Warnings, and Suggestions.

## Common Tasks

### Lint the docs

Before deploying or committing documentation changes, verify documentation quality:

1. **Run docs-lint skill** to verify documentation quality and check for dead links:

   ```bash
   # Use the docs-lint skill to review all parts
   # The skill will:
   # - Check STYLES.md compliance
   # - Run link checker (.claude/skills/docs-lint/check-links.sh)
   # - Report critical issues and warnings
   # - Fix critical issues only
   ```

2. **Verify all links are valid** by running the link checker directly:

   ```bash
   .claude/skills/docs-lint/check-links.sh docs/part*.md
   ```

3. **Run mkdocs-lint skill** to verify MkDocs rendering and fix critical issues:

   ```bash
   # Use the mkdocs-lint skill to:
   # - Clean site directory and rebuild: rm -rf site/ && mkdocs build
   # - Restart server: mkdocs serve
   # - Check for broken code fences, unclosed admonitions, etc.
   # - Automatically fix critical rendering issues
   # - Report unfixable issues requiring manual intervention
   ```

**Important**: Always run these verification steps before committing changes. Dead links and rendering issues will cause problems in production.

### Deploy the docs files

After linting the docs successfully, deploy to the adjacent adk-docs repo:

```bash
# Copy all documentation files
cp docs/part*.md ../adk-docs/docs/streaming/dev-guide/

# Copy assets (excluding agent-development-kit.png and hidden files)
find docs/assets/ -type f ! -name "agent-development-kit.png" ! -name ".*" -exec cp {} ../adk-docs/docs/streaming/dev-guide/assets/ \;
```

**Important**: Never deploy without linting first (see "Lint the docs" section above). Dead links and rendering issues will cause CI/CD failures in the adk-docs repository.

### Adding Documentation Content

1. Read STYLES.md completely to understand all style requirements
2. Identify the correct part file (part1-part5)
3. Follow the section hierarchy and ordering patterns
4. Use consistent terminology (e.g., "Live API" for both platforms, "bidirectional streaming")
5. Add code examples with appropriate commenting level (teaching vs production)
6. Include cross-references to related sections
7. Use the docs-lint skill to review changes

### Modifying Demo Application

1. The demo app follows the 4-phase lifecycle pattern
2. Maintain upstream/downstream task separation
3. Ensure proper error handling in `try/finally` blocks
4. Always close `LiveRequestQueue` in the `finally` block
5. Test with both text and audio modalities
6. Verify WebSocket connection handling

### Running Documentation Reviews

Use the `docs-lint` skill to perform comprehensive documentation reviews:

```python
# The skill will analyze structure, style, cross-references, code examples, and more
# Review reports are saved in reviews/
```

### MkDocs Debugging and Best Practices

When working with MkDocs rendering issues, follow these critical practices:

> **Important**: See STYLES.md section 2.5 "Admonitions and Callouts" for detailed rules on admonition formatting, including common issues with code blocks in admonitions.

#### Required Workflow After Fixes

**CRITICAL**: After every fix to markdown files, you MUST:

1. **Kill any process using port 8000**: `lsof -ti:8000 | xargs kill -9` (or `pkill -f "mkdocs serve"`)
2. **Clean the site directory**: `rm -rf site/`
3. **Rebuild**: `mkdocs build`
4. **Restart server**: `mkdocs serve` (run in background with `&` if needed)
5. **Verify the fix**: Fetch the page with `curl` and check the HTML output

Do NOT rely on MkDocs auto-reload - it may serve stale/cached content.

**Verification command template:**
```bash
# After fixing part4.md section
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
rm -rf site/ && mkdocs build && mkdocs serve > /tmp/mkdocs.log 2>&1 &
sleep 2  # Wait for server to start
curl -s "http://127.0.0.1:8000/part4/" | grep -A 20 "section-anchor"
```

#### Debugging Indentation Issues

When code blocks appear broken in rendered output:

1. **Check the HTML output** - Look for `<p>```python` which indicates the fence isn't recognized
2. **Find the admonition** - Look for `<div class="admonition">` to see where it opens/closes
3. **Inspect blank lines** - Use Python to check exact whitespace:
   ```bash
   python3 -c "with open('docs/partX.md') as f: lines = f.readlines(); print(repr(lines[N]))"
   ```
4. **Check for trailing spaces** - These can break admonitions unexpectedly

#### MkDocs Environment Setup

The repository includes MkDocs configuration files:

- `mkdocs.yml` - Site configuration
- `requirements.txt` - Python dependencies (mkdocs-material, mkdocs-redirects, mkdocs-linkcheck)
- `docs/stylesheets/` - Custom CSS
- `docs/assets/` - Images and logos
- `overrides/` - Theme customizations

## Reference Documentation

- **ADK Documentation**: <https://google.github.io/adk-docs/>
- **Gemini Live API**: <https://ai.google.dev/gemini-api/docs/live>
- **Vertex AI Live API**: <https://cloud.google.com/vertex-ai/generative-ai/docs/live-api>
- **ADK Python Repository**: <https://github.com/google/adk-python>

## Git Workflow

This repository follows **[Conventional Commits](https://www.conventionalcommits.org/)**, a standardized format for commit messages.

### Commit Message Format

```
<type>: <short description>

<optional body>

<optional footer>
```

### Commit Types

| Type | When to Use | Examples |
|------|-------------|----------|
| **`feat:`** | New features or capabilities | `feat: add mkdocs-lint skill for quick rendering fixes` |
| **`fix:`** | Bug fixes in code or broken functionality | `fix: correct broken API endpoint` |
| **`docs:`** | Documentation-only changes | `docs: update STYLES.md to mandate prefixes`<br>`docs: align part3.md with STYLES.md rules` |
| **`refactor:`** | Code restructuring without changing behavior | `refactor: simplify upstream task logic` |
| **`chore:`** | Maintenance tasks, tooling, config updates | `chore: update skill activation instructions` |
| **`style:`** | Code formatting, whitespace (not CSS styling) | `style: format Python code with black` |
| **`test:`** | Adding or updating tests | `test: add e2e tests for WebSocket handling` |
| **`perf:`** | Performance improvements | `perf: optimize event processing loop` |
| **`ci:`** | CI/CD pipeline changes | `ci: update GitHub Actions workflow` |

### Guidelines for This Repository

1. **Use `docs:` for all documentation changes** - Fixing markdown, updating guides, correcting links, STYLES.md compliance fixes

2. **Use `feat:` for new features** - Adding new skills, agents, or capabilities

3. **Use `fix:` for corrections** - Bug fixes in code or critical functionality errors

4. **Use `chore:` for maintenance** - Updating instructions, configs, or tooling

### When to Use `fix:` vs `docs:`

- **`fix:`** - Code bug, broken feature, app crashes, API errors
- **`docs:`** - Improving docs, fixing typos, updating guides, compliance issues, rendering fixes

Most commits in this repository use `docs:` because it's primarily documentation-focused.
