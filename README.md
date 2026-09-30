# 🚗 Smart Car Service & Maintenance System

A full-stack Django + PostgreSQL platform for managing vehicles, maintenance
history, and service appointments — featuring a **context-aware AI chatbot**
and an **Agentic AI tool-calling layer** that can check overdue services,
find open slots, and book/cancel appointments on the user's behalf.

Built for the Summer Training Full-Stack Python Program 2026 graduation project.

## Tech Stack
- **Backend:** Python 3.12, Django 5 (MVT)
- **Database:** PostgreSQL
- **Frontend:** HTML5, CSS3, vanilla ES6+ (async fetch)
- **AI:** Google Gemini Claude — system prompts + LLM tool calling (no RAG/vector DB)

## Project Structure
```
config/            # settings, root urls
apps/
  authentication/  # CustomUser (RBAC roles), auth views, permission decorators
  core/             # landing page, role-aware dashboard
  vehicles/         # Vehicle, ServiceType, Appointment, SparePart, MaintenanceRecord
  ai_agent/         # services.py (agent loop), tools.py (tool registry), prompts.py
templates/          # Django templates per app
static/             # css/js, including agent_chat.js
docs/               # SRS.docx
```

## User Roles (RBAC)
| Role | Capabilities |
|---|---|
| ADMIN | Full access, manages technicians & service catalog |
| MANAGER | Confirms appointments, manages inventory |
| TECHNICIAN | Views/updates assigned jobs |
| CUSTOMER | Owns vehicles, books appointments, uses AI agent |

## Local Setup

1. **Clone & enter the project**
   ```bash
   git clone <your-repo-url>
   cd smart-car-maintenance-system
   ```

2. **Create a virtual environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL**
   ```sql
   CREATE DATABASE smart_car_db;
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # then edit .env: DB credentials + GEMINI_API_KEY
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Seed realistic demo data**
   ```bash
   python manage.py seed_data
   ```

8. **Run the server**
   ```bash
   python manage.py runserver
   ```

9. Visit `http://127.0.0.1:8000` and log in with:
   - `admin` / `admin12345`
   - `manager1` / `manager12345`
   - `tech1` / `tech12345`
   - `customer1` / `customer12345`

## Trying the AI Agent
Log in as `customer1` and open **AI Assistant** from the nav bar. Try:
- "What services are overdue on my car?"
- "Find me an available slot for an oil change."
- "Book my Corolla in for tire rotation next week."
- "Cancel my upcoming appointment." (agent will ask you to confirm first)

## Git Workflow
This repo follows Conventional Commits (`feat:`, `fix:`, `docs:`, ...) and was
initialized on Day 1 of development — see commit history for the continuous
build-up of the project (no bulk-upload).

## Documentation
Full Software Requirements Specification: [`docs/SRS.docx`](docs/SRS.docx)
