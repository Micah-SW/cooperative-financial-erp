# Cooperative Financial Management ERP — Setup Guide
#
# TODO (Gemini): Write comprehensive setup documentation covering:
#
# 1. Prerequisites
#    - Python 3.11+
#    - Node.js 20+
#    - Docker & Docker Compose
#    - PostgreSQL 16+ (or use Docker)
#
# 2. Quick Start
#    docker-compose up -d
#    cd backend && pip install -e ".[dev]"
#    alembic upgrade head
#    cd frontend && npm install && npm run dev
#
# 3. Environment Configuration
#    - Copy .env.example to .env
#    - Configure DATABASE_URL, SECRET_KEY
#
# 4. Database Setup
#    - Create 'coop' schema
#    - Run migrations
#    - Seed initial data (funds, admin user, config)
#
# 5. Running Tests
#    cd backend && pytest
#    cd frontend && npm test
#
# 6. Development Workflow
#    - Backend: uvicorn with --reload
#    - Frontend: vite dev server
#    - Migrations: alembic revision --autogenerate
