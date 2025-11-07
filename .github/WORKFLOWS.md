# GitHub Actions Workflows

This directory contains automated workflows for maintaining the ADK Streaming Guide documentation.

## Overview

The workflow system consists of two interconnected workflows that automate the process of keeping documentation up-to-date with new ADK releases:

1. **ADK Version Monitor** (`adk-version-monitor.yml`) - Detects new ADK versions and creates tracking issues
2. **Claude Code Reviewer** (`claude-code-reviewer.yml`) - Automatically reviews documentation using Claude Code

## Workflow Architecture

```
┌─────────────────────────────────────┐
│   ADK Version Monitor (Scheduled)   │
│   - Runs every 12 hours             │
│   - Checks PyPI for new versions    │
└─────────────┬───────────────────────┘
              │
              │ New version detected
              ▼
┌─────────────────────────────────────┐
│   Create Parent Issue               │
│   "ADK vX.Y.Z - Compatibility       │
│    Review"                          │
└─────────────┬───────────────────────┘
              │
              │ Creates 5 sub-issues
              ▼
┌─────────────────────────────────────┐
│   Sub-Issues (one per doc part)    │
│   - Part 1: Introduction            │
│   - Part 2: LiveRequestQueue        │
│   - Part 3: run_live()              │
│   - Part 4: RunConfig               │
│   - Part 5: Audio/Video             │
│   Each includes @claude mention     │
└─────────────┬───────────────────────┘
              │
              │ Triggers on issue open
              ▼
┌─────────────────────────────────────┐
│   Claude Code Reviewer              │
│   - Reads issue body                │
│   - Executes adk-reviewer agent     │
│   - Posts findings as comment       │
│   - May create PR with fixes        │
└─────────────────────────────────────┘
```

## Setup Instructions

### 1. Install Claude GitHub App

First, install the Claude GitHub App on your repository:

1. Visit the [Claude GitHub App](https://github.com/apps/claude-code) installation page
2. Click "Install" or "Configure"
3. Select the `adk-streaming-guide` repository
4. Grant the required permissions:
   - Read access to metadata and code
   - Write access to code, issues, and pull requests

### 2. Choose Authentication Method

You have two options for Claude API access:

#### Option A: Use Anthropic API (Simpler)

Add your Anthropic API key to the repository secrets:

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key (starts with `sk-ant-`)
5. Click **Add secret**

Then update the workflow file to use:
```yaml
- name: Execute Claude Code
  uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### Option B: Use Google Cloud Vertex AI (Recommended for this project)

Since you're already using Google Cloud for the ADK demo, this option is recommended:

**Prerequisites:**

1. Enable required APIs in your Google Cloud project:
   - IAM Credentials API
   - Security Token Service (STS) API
   - Vertex AI API

2. Create Workload Identity Federation:
   ```bash
   # Create Workload Identity Pool
   gcloud iam workload-identity-pools create "github-actions" \
     --project="${PROJECT_ID}" \
     --location="global" \
     --display-name="GitHub Actions Pool"

   # Add GitHub OIDC provider
   gcloud iam workload-identity-pools providers create-oidc "github-provider" \
     --project="${PROJECT_ID}" \
     --location="global" \
     --workload-identity-pool="github-actions" \
     --display-name="GitHub provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
     --issuer-uri="https://token.actions.githubusercontent.com"
   ```

3. Create a dedicated Service Account:
   ```bash
   # Create service account
   gcloud iam service-accounts create github-actions-claude \
     --display-name="GitHub Actions - Claude Code"

   # Grant Vertex AI User role
   gcloud projects add-iam-policy-binding ${PROJECT_ID} \
     --member="serviceAccount:github-actions-claude@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   # Allow Workload Identity Pool impersonation
   gcloud iam service-accounts add-iam-policy-binding \
     "github-actions-claude@${PROJECT_ID}.iam.gserviceaccount.com" \
     --project="${PROJECT_ID}" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/attribute.repository/${GITHUB_REPO}"
   ```

4. Get the Workload Identity Provider resource name:
   ```bash
   gcloud iam workload-identity-pools providers describe "github-provider" \
     --project="${PROJECT_ID}" \
     --location="global" \
     --workload-identity-pool="github-actions" \
     --format="value(name)"
   ```

5. Add these secrets to your repository:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`: The full provider resource name from step 4
   - `GCP_SERVICE_ACCOUNT`: Email of the service account (e.g., `github-actions-claude@PROJECT_ID.iam.gserviceaccount.com`)
   - `APP_GITHUB_TOKEN`: GitHub App token for authentication

The workflow is already configured to use Vertex AI (see `.github/workflows/claude-code-reviewer.yml`).

**Security Note**: Never commit API keys or credentials directly to the repository. Always use GitHub Secrets.

### 3. Enable Workflows

The workflows are enabled automatically when you push them to the repository. To verify:

1. Go to the **Actions** tab in your repository
2. You should see:
   - "ADK Version Monitor" workflow
   - "Claude Code Reviewer" workflow
3. Both should show as enabled (green checkmark)

### 4. Initial Version Setup

The `current_adk_version.txt` file tracks the last checked ADK version. It's initialized to `0.0.0`, which means the next scheduled run will detect the current PyPI version as "new" and create issues.

If you want to start from the current version without creating issues:

```bash
# Get current ADK version from PyPI
CURRENT_VERSION=$(curl -s https://pypi.org/pypi/google-adk/json | python3 -c "import sys, json; print(json.load(sys.stdin)['info']['version'])")

# Update the tracking file
echo $CURRENT_VERSION > .github/current_adk_version.txt

# Commit and push
git add .github/current_adk_version.txt
git commit -m "chore: initialize ADK version tracking"
git push
```

## Workflow Details

### ADK Version Monitor

**Trigger Schedule**: Every 12 hours (midnight and noon UTC)

**What it does**:
1. Fetches the latest `google-adk` version from PyPI
2. Compares with the version in `current_adk_version.txt`
3. If a new version is detected:
   - Creates a parent issue titled "ADK vX.Y.Z - Documentation Compatibility Review"
   - Creates 5 sub-issues, one for each documentation part
   - Updates `current_adk_version.txt` with the new version
   - Commits the version file to the repository

**Manual Trigger**:
```bash
# Trigger manually via GitHub CLI
gh workflow run adk-version-monitor.yml

# Force check even if version unchanged
gh workflow run adk-version-monitor.yml -f force_check=true
```

**Outputs**:
- Parent issue with checklist of all documentation parts
- Sub-issues linked to the parent issue
- Commit updating the version tracking file

### Claude Code Reviewer

**Trigger**: When issues are opened or commented on

**What it does**:
1. Checks if the issue has the `adk-version-update` label
2. Checks if `@claude` is mentioned in the issue body or comment
3. If both conditions are met:
   - Checks out the `adk-streaming-guide` repository
   - Clones the `google/adk-python` repository (full clone with git history) as a sibling directory
     - This provides the `google-adk` skill with access to actual ADK source code
     - Enables deep analysis of implementation details, not just documentation
     - Ensures reviews catch subtle API behavior changes
     - Full git history allows checking recent changes and development trends
   - Executes Claude Code with the issue instructions
   - Claude reads the specified documentation file
   - Runs the `adk-reviewer` agent to analyze compatibility
   - The agent uses the `google-adk` skill to access ADK source code from `../adk-python`
   - Posts findings as a comment on the issue
   - May create a pull request with suggested fixes

**Repository Structure in GitHub Actions**:

```
/home/runner/work/adk-streaming-guide/
├── adk-streaming-guide/  (this repository, checked out by actions/checkout)
│   ├── docs/
│   ├── .claude/
│   │   └── skills/
│   │       └── google-adk/   (references ../adk-python)
│   └── ...
└── adk-python/           (cloned via git clone for source code review)
    ├── src/
    └── ...
```

This setup mirrors the local development environment where both repositories are siblings, ensuring the `adk-reviewer` agent can access the actual ADK source code through the `google-adk` skill for accurate compatibility analysis.

**Manual Trigger**:
You can manually trigger reviews by commenting on any issue with the `adk-version-update` label:

```
@claude Please review this documentation part for ADK compatibility
```

## Sub-Issue Structure

Each sub-issue created by the version monitor includes:

**Title**: `ADK vX.Y.Z - Review Part N: [Part Title]`

**Body**: Includes:
- File path to review (e.g., `docs/part1_intro.md`)
- Instructions for Claude to use the `adk-reviewer` agent
- Link to parent issue
- Labels: `adk-version-update`, `documentation`, `automated`, `part-N`

**Example**:
```markdown
## Documentation Review Request

Please review **Part 1: Introduction to ADK Bidi-streaming** for compatibility with ADK v1.5.0.

### File to Review
- `docs/part1_intro.md`

### Review Instructions

@claude Please use the `adk-reviewer` agent to perform a comprehensive review...
```

## Review Process

### Automated Review Steps

1. **Version Detection** (automated, every 12 hours)
   - Monitor workflow detects new ADK version
   - Parent and sub-issues are created

2. **Issue Creation** (automated)
   - One parent issue for overall tracking
   - Five sub-issues for individual parts

3. **Claude Review** (automated, triggered by issue creation)
   - Claude reads the issue body
   - Executes the `adk-reviewer` agent
   - Posts findings as a comment

4. **Manual Review** (manual, by maintainers)
   - Review Claude's findings
   - Make necessary documentation updates
   - Close sub-issues as they're addressed
   - Close parent issue when all parts are reviewed

### Expected Review Outputs

Claude's review comment will include:

- **API Changes**: Any breaking or non-breaking changes affecting the docs
- **Code Examples**: Examples that need updates or corrections
- **New Features**: New ADK features to document
- **Deprecations**: Deprecated functionality to remove or update
- **Terminology**: Changes in concepts or naming
- **Recommendations**: Suggested updates or improvements

### Manual Follow-up

After Claude posts its review:

1. **Assess the findings**: Determine which changes are necessary
2. **Update documentation**: Make required changes to the docs
3. **Test code examples**: Verify all code examples still work
4. **Update cross-references**: Fix any broken internal links
5. **Close sub-issues**: Mark as complete when addressed
6. **Close parent issue**: When all sub-issues are resolved

## Monitoring and Maintenance

### Check Workflow Status

```bash
# List recent workflow runs
gh run list --workflow=adk-version-monitor.yml --limit 5

# View details of the latest run
gh run view

# View logs
gh run view --log
```

### View Created Issues

```bash
# List issues with the adk-version-update label
gh issue list --label adk-version-update

# View a specific issue
gh issue view <issue-number>
```

### Troubleshooting

**Workflow not running**:
- Check that the workflow file is in the `main` branch
- Verify the cron schedule syntax is correct
- Check the Actions tab for any errors

**Claude not responding to issues**:
- Verify the `ANTHROPIC_API_KEY` secret is set correctly
- Check that the issue has the `adk-version-update` label
- Ensure `@claude` is mentioned in the issue body
- Check the Claude Code Reviewer workflow logs

**API rate limits**:
- GitHub Actions: 1,000 API requests per hour per repository
- Anthropic API: Depends on your tier
- PyPI: Generally unlimited for version checks

**False positives**:
If the workflow creates issues for versions you've already reviewed:
- Manually update `current_adk_version.txt` to the latest version
- Commit and push the change

## Cost Considerations

### GitHub Actions

- **Free tier**: 2,000 minutes/month for public repositories, 500 minutes/month for private
- **This workflow**: ~2-5 minutes per run (scheduled twice daily = ~300 minutes/month)
- **Estimate**: Well within free tier limits

### Anthropic API

- **Cost**: Based on token usage (input + output)
- **Per review**: Approximately 10K-50K tokens per documentation part
- **Estimate**: $0.50-$2.00 per ADK version (for all 5 parts)
- **Frequency**: Only runs when new ADK versions are released

## Customization

### Adjust Check Frequency

Edit `adk-version-monitor.yml`:

```yaml
on:
  schedule:
    # Check daily at midnight UTC
    - cron: '0 0 * * *'

    # Check weekly on Mondays
    - cron: '0 0 * * 1'
```

### Add or Remove Documentation Parts

Edit the `matrix.part` section in `adk-version-monitor.yml`:

```yaml
strategy:
  matrix:
    part:
      - { number: 1, title: "Your Title", file: "your_file.md" }
      - { number: 2, title: "Another Title", file: "another_file.md" }
```

### Change Review Instructions

Modify the sub-issue body template in the `create-sub-issues` job to customize what Claude reviews.

## Best Practices

1. **Review promptly**: Address sub-issues within a week of creation to keep docs current
2. **Test thoroughly**: Always test code examples after updates
3. **Keep CLAUDE.md updated**: Ensure Claude has the latest project context
4. **Monitor costs**: Track GitHub Actions minutes and Anthropic API usage
5. **Version tracking**: Keep `current_adk_version.txt` accurate
6. **Label management**: Use labels consistently for filtering and tracking

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Claude Code Documentation](https://code.claude.com/docs)
- [ADK Documentation](https://google.github.io/adk-docs/)
- Repository `CLAUDE.md` - Project instructions for Claude Code
- Repository `STYLES.md` - Documentation style guidelines
