# Contributing to Cakwe

Thank you for your interest in contributing to Cakwe! Cakwe is an open-source, local-first Career Intelligence and Job Radar application built to help developers find authentic, cross-border remote opportunities and craft targeted resumes.

## Code of Conduct

Please be respectful, collaborative, and constructive when opening issues, submitting pull requests, or participating in discussions.

## How to Contribute

### 1. Reporting Issues
- Check the issue tracker before opening a new issue to avoid duplicates.
- Provide a clear and concise description of the bug or feature request.
- Include logs, system information (OS, Docker version, Python version), and reproduction steps.

### 2. Developing Locally

#### Prerequisites
- Docker & Docker Compose **OR**
- Python 3.11+ / 3.12
- Node.js 20+ & npm

#### Setting Up
1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/cakwe.git
   cd cakwe
   ```
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Run using Docker Compose:
   ```bash
   docker compose up -d --build
   ```
   Or run backend and frontend separately:
   ```bash
   # Backend
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000

   # Frontend (in another terminal)
   cd frontend
   npm install
   npm run dev
   ```

### 3. Code Standards
- **Python**: Follow PEP 8 guidelines. Type hints with Pydantic schemas are strictly enforced.
- **TypeScript / React**: Use functional components, explicit types, and Tailwind CSS.
- Ensure no TypeScript compiler errors before committing:
  ```bash
  cd frontend && npx tsc --noEmit
  ```
- Run tests:
  ```bash
  pytest backend/tests/
  ```

### 4. Submitting Pull Requests
1. Create a feature branch: `git checkout -b feature/your-feature-name`.
2. Commit changes using clear, descriptive messages (Conventional Commits preferred):
   `git commit -m "feat: add support for new ATS provider"`.
3. Push to your fork: `git push origin feature/your-feature-name`.
4. Open a Pull Request against `main`.
