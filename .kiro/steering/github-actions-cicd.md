# GitHub Actions CI/CD Pipeline

## Overview

We use GitHub Actions for continuous integration and deployment. The pipeline includes linting, testing, validation, and automated deployment for both application code and infrastructure.

## Workflow Structure

```
.github/
└── workflows/
    ├── backend-lint.yml          # Python backend linting with Ruff
    ├── frontend-lint.yml         # TypeScript/Next.js linting
    ├── cdk-validate.yml          # CDK infrastructure validation
    ├── cdk-deploy-staging.yml    # Automated staging deployment
    ├── cdk-deploy-prod.yml       # Production deployment with approval
    └── test.yml                  # Automated testing
```

## Backend Linting Workflow (Ruff)

**`.github/workflows/backend-lint.yml`**:
```yaml
name: Backend Linting

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - 'lambdas/**'
      - 'voice_service/**'
      - 'text_service/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - 'lambdas/**'
      - 'voice_service/**'
      - 'text_service/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff mypy
          pip install -r backend/requirements.txt
      
      - name: Run Ruff linting
        run: |
          # Check for linting errors
          ruff check backend/ lambdas/ voice_service/ text_service/
      
      - name: Run Ruff formatting check
        run: |
          # Check if code is formatted correctly
          ruff format --check backend/ lambdas/ voice_service/ text_service/
      
      - name: Run type checking with mypy
        run: |
          mypy backend/ --ignore-missing-imports
        continue-on-error: true  # Don't fail on type errors initially

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Backend linting passed!'
            })
```

**Ruff Configuration** (`backend/pyproject.toml`):
```toml
[tool.ruff]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "DTZ", "T10", "DJ", "EM", "ISC", "ICN", "G", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["E501"]  # Line too long

# Allow autofix for all enabled rules (when `--fix`) is provided.
fixable = ["ALL"]
unfixable = []

# Exclude a variety of commonly ignored directories.
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]

line-length = 120
target-version = "py311"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports in __init__.py
```

## Frontend Linting Workflow

**`.github/workflows/frontend-lint.yml`**:
```yaml
name: Frontend Linting

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'frontend/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Run ESLint
        working-directory: frontend
        run: npm run lint
      
      - name: Run TypeScript type checking
        working-directory: frontend
        run: npm run type-check
      
      - name: Check formatting with Prettier
        working-directory: frontend
        run: npm run format:check
      
      - name: Build check
        working-directory: frontend
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Frontend linting and build passed!'
            })
```

**Frontend Package.json Scripts**:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,css,md}\"",
    "format:check": "prettier --check \"**/*.{ts,tsx,js,jsx,json,css,md}\""
  }
}
```

## CDK Validation Workflow

**`.github/workflows/cdk-validate.yml`**:
```yaml
name: CDK Validation

on:
  push:
    branches: [main, develop]
    paths:
      - 'infrastructure/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'infrastructure/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Set up Node.js (for CDK CLI)
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install CDK CLI
        run: npm install -g aws-cdk
      
      - name: Install Python dependencies
        working-directory: infrastructure
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff mypy
      
      - name: Run Ruff linting on CDK code
        working-directory: infrastructure
        run: |
          ruff check .
          ruff format --check .
      
      - name: Run type checking
        working-directory: infrastructure
        run: |
          mypy . --ignore-missing-imports
        continue-on-error: true
      
      - name: CDK Synth
        working-directory: infrastructure
        run: cdk synth
        env:
          CDK_DEFAULT_ACCOUNT: ${{ secrets.AWS_ACCOUNT_ID }}
          CDK_DEFAULT_REGION: us-east-1
      
      - name: CDK Diff (if PR)
        if: github.event_name == 'pull_request'
        working-directory: infrastructure
        run: |
          cdk diff || true
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          CDK_DEFAULT_ACCOUNT: ${{ secrets.AWS_ACCOUNT_ID }}
          CDK_DEFAULT_REGION: us-east-1
      
      - name: Comment PR with CDK diff
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ CDK validation passed! Check the workflow logs for infrastructure changes.'
            })
```

## CDK Deployment Workflow (Staging)

**`.github/workflows/cdk-deploy-staging.yml`**:
```yaml
name: Deploy to Staging

on:
  push:
    branches: [develop]
    paths:
      - 'infrastructure/**'
  workflow_dispatch:  # Allow manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install CDK CLI
        run: npm install -g aws-cdk
      
      - name: Install dependencies
        working-directory: infrastructure
        run: pip install -r requirements.txt
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: CDK Bootstrap (if needed)
        working-directory: infrastructure
        run: cdk bootstrap
        continue-on-error: true
      
      - name: CDK Deploy
        working-directory: infrastructure
        run: cdk deploy --all --require-approval never
        env:
          CDK_DEFAULT_ACCOUNT: ${{ secrets.AWS_ACCOUNT_ID }}
          CDK_DEFAULT_REGION: us-east-1
          ENVIRONMENT: staging
      
      - name: Notify deployment success
        if: success()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.repos.createCommitStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: context.sha,
              state: 'success',
              description: 'Staging deployment successful',
              context: 'CDK Deploy Staging'
            })
      
      - name: Notify deployment failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.repos.createCommitStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: context.sha,
              state: 'failure',
              description: 'Staging deployment failed',
              context: 'CDK Deploy Staging'
            })
```

## CDK Deployment Workflow (Production)

**`.github/workflows/cdk-deploy-prod.yml`**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/**'
  workflow_dispatch:  # Allow manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: 
      name: production
      url: https://oratio.io
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install CDK CLI
        run: npm install -g aws-cdk
      
      - name: Install dependencies
        working-directory: infrastructure
        run: pip install -r requirements.txt
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
          aws-region: us-east-1
      
      - name: CDK Diff
        working-directory: infrastructure
        run: cdk diff
        env:
          CDK_DEFAULT_ACCOUNT: ${{ secrets.AWS_ACCOUNT_ID_PROD }}
          CDK_DEFAULT_REGION: us-east-1
          ENVIRONMENT: production
      
      - name: CDK Deploy
        working-directory: infrastructure
        run: cdk deploy --all --require-approval never
        env:
          CDK_DEFAULT_ACCOUNT: ${{ secrets.AWS_ACCOUNT_ID_PROD }}
          CDK_DEFAULT_REGION: us-east-1
          ENVIRONMENT: production
      
      - name: Create deployment tag
        if: success()
        run: |
          git tag -a "deploy-prod-$(date +%Y%m%d-%H%M%S)" -m "Production deployment"
          git push origin --tags
      
      - name: Notify deployment success
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Production deployment successful!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Deployment Successful* :rocket:\n\nCommit: ${{ github.sha }}\nAuthor: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Testing Workflow

**`.github/workflows/test.yml`**:
```yaml
name: Run Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run backend tests
        working-directory: backend
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml
          flags: backend
          name: backend-coverage
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Run frontend tests
        working-directory: frontend
        run: npm run test:ci
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./frontend/coverage/coverage-final.json
          flags: frontend
          name: frontend-coverage
```

## GitHub Secrets Configuration

Required secrets in GitHub repository settings:

### Staging Environment
- `AWS_ACCESS_KEY_ID` - AWS access key for staging
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for staging
- `AWS_ACCOUNT_ID` - AWS account ID for staging

### Production Environment
- `AWS_ACCESS_KEY_ID_PROD` - AWS access key for production
- `AWS_SECRET_ACCESS_KEY_PROD` - AWS secret key for production
- `AWS_ACCOUNT_ID_PROD` - AWS account ID for production

### Optional
- `SLACK_WEBHOOK_URL` - Slack webhook for deployment notifications
- `CODECOV_TOKEN` - Codecov token for coverage reporting

## Best Practices

1. **Branch Protection**: Require status checks to pass before merging
2. **Environment Protection**: Use GitHub environments with approval gates for production
3. **Secrets Management**: Use GitHub secrets for sensitive data, never commit credentials
4. **Caching**: Use action caching for dependencies to speed up workflows
5. **Fail Fast**: Configure workflows to fail fast on critical errors
6. **Notifications**: Set up Slack/email notifications for deployment status
7. **Rollback Strategy**: Tag successful deployments for easy rollback
8. **Monitoring**: Monitor workflow execution times and optimize as needed

## Workflow Triggers

- **Push to main**: Triggers production deployment (with approval)
- **Push to develop**: Triggers staging deployment
- **Pull Request**: Triggers linting, validation, and tests
- **Manual Trigger**: Use `workflow_dispatch` for manual deployments

## Status Badges

Add to README.md:
```markdown
![Backend Linting](https://github.com/org/oratio/workflows/Backend%20Linting/badge.svg)
![Frontend Linting](https://github.com/org/oratio/workflows/Frontend%20Linting/badge.svg)
![CDK Validation](https://github.com/org/oratio/workflows/CDK%20Validation/badge.svg)
![Tests](https://github.com/org/oratio/workflows/Run%20Tests/badge.svg)
```
