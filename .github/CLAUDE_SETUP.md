# Claude Code Provider Setup Guide

This guide explains how to configure the Claude Code GitHub Action to easily switch between Anthropic API and Google Vertex AI.

## Quick Switch Configuration

The workflow uses repository variables to determine which provider to use. You can switch providers without modifying the workflow file.

### Repository Variables (Settings → Secrets and variables → Actions → Variables)

| Variable | Value | Description |
|----------|-------|-------------|
| `CLAUDE_PROVIDER` | `anthropic` or `vertex` | Which provider to use (default: `anthropic`) |
| `VERTEX_REGION` | `us-east5` | GCP region for Vertex AI (optional, defaults to `us-east5`) |

## Provider-Specific Setup

### Option 1: Anthropic API (Default)

**Repository Variables:**
```
CLAUDE_PROVIDER = anthropic  # (or leave empty for default)
```

**Repository Secrets:**
```
ANTHROPIC_API_KEY = your_anthropic_api_key_here
```

**Setup Steps:**
1. Get API key from [console.anthropic.com](https://console.anthropic.com)
2. Add as repository secret: `ANTHROPIC_API_KEY`
3. Set `CLAUDE_PROVIDER` variable to `anthropic` (or leave empty)

### Option 2: Google Vertex AI

**Repository Variables:**
```
CLAUDE_PROVIDER = vertex
VERTEX_REGION = us-east5  # (optional, defaults to us-east5)
```

**Repository Secrets:**
```
GCP_WORKLOAD_IDENTITY_PROVIDER = projects/761793285222/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
GCP_SERVICE_ACCOUNT = claude-github-actions@gcp-samples-ic0.iam.gserviceaccount.com
```

**Prerequisites (✅ Already configured for this repository):**

The following prerequisites are already set up for the `gcp-samples-ic0` project:

1. **✅ APIs enabled:**
   - IAM Credentials API
   - Security Token Service (STS) API  
   - Vertex AI API

2. **✅ Workload Identity Federation configured:**
   - Pool: `github-actions-pool`
   - Provider: `github-provider` 
   - Issuer: `https://token.actions.githubusercontent.com`
   - Repository condition: `kazunori279/adk-streaming-guide`

3. **✅ Service account created:**
   - Name: `claude-github-actions@gcp-samples-ic0.iam.gserviceaccount.com`
   - Role: `roles/aiplatform.user`
   - Workload Identity binding configured

**Setup Steps (for reference only - already completed):**

<details>
<summary>Click to view the commands that were used to set up the prerequisites</summary>

```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable iamcredentials.googleapis.com  
gcloud services enable sts.googleapis.com

# Create workload identity pool (already existed)
gcloud iam workload-identity-pools create github-actions-pool \
    --location="global" \
    --description="GitHub Actions pool"

# Create OIDC provider (already existed)
gcloud iam workload-identity-pools providers create-oidc github-provider \
    --location="global" \
    --workload-identity-pool="github-actions-pool" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"

# Create service account
gcloud iam service-accounts create claude-github-actions \
    --description="Service account for Claude GitHub Actions" \
    --display-name="Claude GitHub Actions"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding gcp-samples-ic0 \
    --member="serviceAccount:claude-github-actions@gcp-samples-ic0.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Configure IAM binding
gcloud iam service-accounts add-iam-policy-binding \
    claude-github-actions@gcp-samples-ic0.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/761793285222/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/kazunori279/adk-streaming-guide"
```

</details>

## Switching Providers

To switch between providers, simply update the repository variable:

1. Go to repository **Settings → Secrets and variables → Actions → Variables**
2. Edit `CLAUDE_PROVIDER`:
   - Set to `anthropic` for Anthropic API
   - Set to `vertex` for Vertex AI
3. The next workflow run will use the selected provider

## Model Configuration

Both providers use the same model configuration in `claude_args`:
```yaml
claude_args: '--model claude-sonnet-4@20250514 --max-turns 10'
```

The model name format is the same for both providers.

## Troubleshooting

### Anthropic API Issues
- Verify `ANTHROPIC_API_KEY` is valid
- Check API usage limits at console.anthropic.com

### Vertex AI Issues
- Ensure all GCP APIs are enabled
- Verify Workload Identity Federation setup
- Check service account permissions
- Confirm repository name matches in attribute condition

### Common Issues
- **Wrong provider**: Check `CLAUDE_PROVIDER` variable value
- **Missing secrets**: Verify required secrets are set for the chosen provider
- **Region issues**: Set `VERTEX_REGION` variable for non-default regions

## Security Notes

- Repository variables are visible to anyone with read access to the repository
- Secrets are encrypted and only accessible during workflow execution
- Vertex AI uses temporary tokens (more secure than static API keys)
- Both providers follow GitHub Actions security best practices