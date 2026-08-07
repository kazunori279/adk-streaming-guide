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
│   ├── part1.md            # Introduction to ADK Gemini Live API Toolkit
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

### Deploy the demo application to adk-docs repo

The demo is published to the adjacent adk-docs repo at
`../adk-docs/examples/python/snippets/streaming/bidi-demo/`, alongside the
existing `adk-streaming/` and `adk-streaming-ws/` samples. It used to live in
adk-samples at `python/agents/bidi-demo`, which has since been removed.

Only the **minimum link-preserving set** ships — the files `docs/part1-5.md`
and `../adk-docs/docs/live/*.md` link into, plus what is needed to run:

```text
README.md                              # rewritten for adk-docs; not a copy
pyproject.toml                         # matches the adk-streaming-ws sample
app/.env.example                       # adk-docs .gitignore blocks .env
app/main.py
app/google_search_agent/{__init__,agent}.py
app/static/{index.html, css/style.css, js/*.js}
```

Deliberately **not** shipped (nothing in either repo's `docs/` references them,
and the neighbouring samples stay minimal): `Dockerfile`, `.dockerignore`,
`agent_engine/`, `uv.lock`, `tests/`, `assets/`.

The `app/` nesting level is preserved so every documentation URL is a pure
prefix substitution.

```bash
DEST=../adk-docs/examples/python/snippets/streaming/bidi-demo
mkdir -p "$DEST/app"
cp src/bidi-demo/pyproject.toml "$DEST/"
cp src/bidi-demo/app/main.py "$DEST/app/"
cp -r src/bidi-demo/app/google_search_agent "$DEST/app/"
cp -r src/bidi-demo/app/static "$DEST/app/"
```

**Important**: `src/bidi-demo` is the source of truth and is formatted with
adk-python's toolchain (see "Lint the code"), so the copied files must be
byte-for-byte identical. Verify with `diff -r` after copying.

Because the sample now lives in the same repo as the docs that cite it, the
`docs/live/*.md` source links are `blob/main` URLs with line anchors. **Any
change to `app/main.py`, `app/google_search_agent/agent.py`, or
`app/static/js/*.js` shifts those anchors** — re-check every link listed by:

```bash
grep -rn "snippets/streaming/bidi-demo" ../adk-docs/docs/live/
```

The `.env` file holds real project configuration and must never be copied —
adk-docs' `.gitignore` blocks `.env`, so maintain `app/.env.example` instead.

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
- **`code-lint`** (`.claude/skills/code-lint/SKILL.md`): Python code linter and formatter using black, isort, and flake8
- **`docs-lint`** (`.claude/skills/docs-lint/SKILL.md`): Documentation reviewer that checks links, source code references, and style consistency
- **`mkdocs-lint`** (`.claude/skills/mkdocs-lint/SKILL.md`): MkDocs rendering linter that identifies and fixes critical rendering issues

### Using Skills

To activate a skill, reference it directly:

- **For ADK expertise**: Say "use google-adk skill" or "access the google-adk skill"
- **For bidirectional streaming**: Say "use bidi skill" or "access the bidi skill"
- **For Gemini Live API**: Say "use gemini-live-api skill"
- **For Vertex AI Live API**: Say "use vertexai-live-api skill"
- **For Python code formatting**: Say "use code-lint skill"
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
   # - Validate source code references (if sibling repos available)
   # - Report critical issues and warnings
   # - Fix critical issues only
   ```

2. **Verify all links are valid** by running the link checker directly:

   ```bash
   .claude/skills/docs-lint/check-links.sh docs/part*.md
   ```

3. **Validate source code references** (requires sibling repos):

   ```bash
   python3 .claude/skills/docs-lint/check-source-refs.py \
     --docs docs/ \
     --adk-python-repo ../adk-python \
     --adk-samples-repo ../adk-samples \
     --new-version HEAD
   ```

   This auto-fixes drifted line numbers and reports broken references.

4. **Run mkdocs-lint skill** to verify MkDocs rendering and fix critical issues:

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

**No longer applicable.** The `docs/part*.md` dev guide used to be copied into
`../adk-docs/docs/streaming/dev-guide/`, but that directory has been removed:
the guide was decomposed into the per-topic pages now maintained directly in
`../adk-docs/docs/live/` (index, sessions, events, configuration, voice,
audio-video, tools, workflows, custom-server, models, ...).

Edit those pages in the adk-docs repo. The only thing this repo still ships to
adk-docs is the bidi-demo sample — see "Deploy the demo application" below.

### Adding Documentation Content

1. Read STYLES.md completely to understand all style requirements
2. Identify the correct part file (part1-part5)
3. Follow the section hierarchy and ordering patterns
4. Use consistent terminology (e.g., "Live API" for both platforms, "bidirectional streaming")
5. Add code examples with appropriate commenting level (teaching vs production)
6. Include cross-references to related sections
7. Use the docs-lint skill to review changes

### Lint the code

`src/bidi-demo` is published to adk-python, so it uses **adk-python's**
formatting toolchain rather than black/flake8 — pyink (80 columns, 2-space
indent, majority quotes) plus isort with the `google` profile. Both are pinned
in `src/bidi-demo/pyproject.toml` to the versions in
`../adk-python/.pre-commit-config.yaml`, so the published copy stays
byte-for-byte identical.

```bash
cd src/bidi-demo
uvx isort==8.0.1 app/ tests/
uvx pyink==25.12.0 app/ tests/
uvx ruff@0.15.17 check app/ tests/   # linting only; isort owns import order
```

Two adk-python constraints apply to any Python that ships:

- **Apache 2.0 header** on every `.py` file (`addlicense -c "Google LLC" -l apache`).
- `scripts/compliance_checks.py::check_logger` forbids
  `logging.getLogger(__name__)` repo-wide — use
  `logging.getLogger("google_adk." + __name__)`.

JavaScript, CSS, and HTML are not reformatted by adk-python's hooks, but
`trailing-whitespace` and `end-of-file-fixer` do apply to them, so keep those
files clean.

For other Python under `/src`, the `code-lint` skill (black/isort/flake8) still
applies.

### Modifying Demo Application

1. The demo app follows the 4-phase lifecycle pattern
2. Maintain upstream/downstream task separation
3. Ensure proper error handling in `try/finally` blocks
4. Always close `LiveRequestQueue` in the `finally` block
5. Test with both text and audio modalities
6. Verify WebSocket connection handling
7. Run code-lint skill before committing (see "Lint the code" above)

### Updating Workshop src.tar.gz

When modifying files in `workshops/src/`, always update the `src.tar.gz` archive:

```bash
cd workshops/src && tar -czvf ../src.tar.gz .
```

**IMPORTANT**: Run the command from inside the `src/` directory to avoid including the `src/` prefix in the archive. The archive should extract files directly (e.g., `app/`, `pyproject.toml`) without a parent directory wrapper.

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
# Activate venv (required before any mkdocs command)
source .venv/bin/activate

# After fixing part4.md section
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
rm -rf site/ && mkdocs build && mkdocs serve > /tmp/mkdocs.log 2>&1 &
sleep 2  # Wait for server to start
curl -s "http://127.0.0.1:8000/part4/" | grep -A 20 "section-anchor"

# Leave the server running for:
# - Browsing rendered docs at http://127.0.0.1:8000/
# - Making iterative changes and verifying them
# - Continued development work
# Only kill the server when starting the next clean rebuild cycle
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

**First-time setup** — create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Subsequent sessions** — activate the existing venv before running any `mkdocs` command:

```bash
source .venv/bin/activate
```

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
