# ProtoX — ProtoIdea

AI-powered application idea generator using **LangChain + Gemini 1.5 Flash + FastAPI + React + TypeScript + Supabase**.

---

## Folder Structure

```
protoidea/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── proto_idea.py       ← LangChain + Gemini agent (core logic)
│   │   ├── db/
│   │   │   └── database.py         ← SQLAlchemy + Supabase connection
│   │   ├── models/
│   │   │   ├── idea_record.py      ← DB table model
│   │   │   └── schemas.py          ← Pydantic request/response schemas
│   │   ├── routes/
│   │   │   └── ideas.py            ← FastAPI endpoints
│   │   ├── config.py               ← Settings from .env
│   │   └── main.py                 ← FastAPI app entry point
│   ├── .env                        ← Your API keys (never commit this)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── ideas.ts            ← Axios API calls
│   │   ├── components/
│   │   │   ├── IdeaForm.tsx        ← Input form
│   │   │   ├── IdeaCard.tsx        ← Idea display card
│   │   │   └── HistoryPanel.tsx    ← Past generations list
│   │   ├── types/
│   │   │   └── index.ts            ← TypeScript types
│   │   ├── App.tsx                 ← Main page
│   │   ├── main.tsx                ← React entry point
│   │   └── index.css               ← Tailwind base styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
└── supabase_migration.sql          ← Run this once in Supabase SQL editor
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) account (free tier is fine)
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free)

---

## Step 1 — Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a new project.
2. In your project, go to **SQL Editor** and run the contents of `supabase_migration.sql`.
3. Go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`
4. Go to **Project Settings → Database → Connection string (URI)** and copy it → `DATABASE_URL`
   - Replace `[YOUR-PASSWORD]` with your DB password.

---

## Step 2 — Backend Setup

```bash
cd protoidea/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Fill in your .env file
# Open .env and replace all placeholder values
```

Your `.env` should look like:
```
GEMINI_API_KEY=AIzaSy...your_key_here
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJh...your_anon_key
DATABASE_URL=postgresql://postgres:yourpassword@db.xxxx.supabase.co:5432/postgres
```

```bash
# Run the backend
uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

---

## Step 3 — Frontend Setup

```bash
cd protoidea/frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## API Endpoints

| Method | Endpoint            | Description                        |
|--------|---------------------|------------------------------------|
| POST   | `/ideas/generate`   | Generate 3–5 ideas using Gemini    |
| GET    | `/ideas/history`    | List all past idea generations     |
| GET    | `/ideas/{id}`       | Get a specific idea record         |
| DELETE | `/ideas/{id}`       | Delete an idea record              |
| GET    | `/health`           | Health check                       |

### Example Request

```bash
curl -X POST http://localhost:8000/ideas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "healthcare",
    "app_type": "Web App",
    "constraints": "must be free, simple UI, for college students"
  }'
```

---

## How the Agent Works

1. User fills in domain, app type, and optional constraints in the form.
2. Frontend sends a POST to `/ideas/generate`.
3. FastAPI receives the request and calls `ProtoIdeaAgent.generate()`.
4. The agent builds a structured prompt and sends it to **Gemini 1.5 Flash** via LangChain.
5. Gemini returns a JSON array of 3–5 idea objects.
6. The agent parses and validates the output into `IdeaModel` Pydantic objects.
7. The result is saved to **Supabase PostgreSQL** and returned to the frontend.
8. The frontend renders each idea as a collapsible card with features and tech hints.
9. The user selects one idea — it will be passed to **ProtoCode** (next agent).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GEMINI_API_KEY invalid` | Get a free key at https://aistudio.google.com/app/apikey |
| `connection refused` on frontend | Make sure backend is running on port 8000 |
| `sqlalchemy.exc.OperationalError` | Check your DATABASE_URL in .env |
| LLM returns invalid JSON | Rare — just retry, Gemini occasionally adds markdown fences |

---

## Built With

- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework
- [LangChain](https://python.langchain.com/) — LLM orchestration
- [Google Gemini 1.5 Flash](https://ai.google.dev/) — AI model
- [Supabase](https://supabase.com/) — PostgreSQL database
- [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/) — Frontend
- [Vite](https://vitejs.dev/) — Frontend build tool
- [Tailwind CSS](https://tailwindcss.com/) — Styling
- [TanStack Query](https://tanstack.com/query) — Server state management
