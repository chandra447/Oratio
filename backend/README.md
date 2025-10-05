# Oratio Backend

FastAPI backend application for Oratio platform.

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Package Manager**: uv
- **Database**: DynamoDB
- **Storage**: S3
- **Authentication**: AWS Cognito
- **AI/ML**: AWS Bedrock

## Getting Started

### Prerequisites

- Python 3.11+
- uv package manager
- AWS credentials configured

### Installation

```bash
# Install dependencies with uv
uv sync

# Install dev dependencies
uv sync --extra dev
```

### Running the Server

```bash
# Development server with hot reload
uv run uvicorn main:app --reload

# Or using the main.py script
uv run python main.py
```

The API will be available at http://localhost:8000

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration settings
├── dependencies.py        # Shared dependencies
├── models/                # Data models
├── routers/               # API endpoints
├── services/              # Business logic
├── aws/                   # AWS client wrappers
└── utils/                 # Helper functions
```

## Development

### Code Quality

```bash
# Run linting
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy .
```

### Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=. --cov-report=term
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

See `.env.example` for required configuration.
