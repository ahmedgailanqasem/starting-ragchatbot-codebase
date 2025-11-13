# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync

   # For development (includes code quality tools)
   uv sync --extra dev
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Development

### Code Quality Tools

This project uses several code quality tools to maintain consistency and catch issues early:

- **Black** - Automatic code formatter
- **isort** - Import statement organizer
- **Flake8** - Linting and style checking
- **mypy** - Static type checking
- **pytest** - Testing framework with coverage

### Development Scripts

Located in the `scripts/` directory:

```bash
# Format code automatically
./scripts/format.sh

# Check code quality (CI/CD friendly)
./scripts/check.sh

# Run linting only
./scripts/lint.sh

# Run tests with coverage
./scripts/test.sh

# Run full quality pipeline
./scripts/quality.sh
```

See `scripts/README.md` for detailed documentation.

### Before Committing

```bash
# Format and check your code
./scripts/format.sh
./scripts/check.sh

# Run tests
./scripts/test.sh
```

