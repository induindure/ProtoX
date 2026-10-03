import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.file_builder import build_file_tree
from app.services.dependency_scanner import build_requirements_txt
from app.services.typing_fixer import fix_missing_typing_imports
from app.services.pydantic_fixer import fix_pydantic_v2_settings_import
from app.services.env_builder import apply_database_url
from app.services.import_fixer import fix_relative_imports
from app.services.completeness_checker import fill_missing_files
from app.services.frontend_checker import fill_missing_frontend_exports
from app.services.package_json_fixer import fix_package_json_dependencies
from app.services.provider_fixer import fix_missing_providers
from app.services.django_auth_fixer import fix_django_auth_views
from app.services.migration_fixer import drop_generated_migrations

load_dotenv()


SYSTEM_PROMPT = """
You are a senior software engineer. Given an app idea and a tech stack, generate a complete, realistic, polished project.

Return ONLY a valid JSON object with this exact structure, no extra text, no markdown:
{
  "project_name": "snake_case_name",
  "description": "one line description",
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "content": "full file content as a string"
    }
  ]
}

General requirements:
- Generate as many files as the app needs (typically 25-40). Completeness matters more than brevity.
- Put frontend code under frontend/ and backend code under backend/.
- Include: README.md, proper config files, .env.example, folder structure matching the tech stack.
- Write real, working code with actual logic, not placeholder comments.
- Tailor everything to the described app. Do not generate generic boilerplate.
- Every name imported from a project file must be defined and exported by that file.
  Before finishing, check every import in every frontend and backend file.

Configuration and secrets:
- Never hardcode secrets or connection strings in code. Read them from environment variables.
- Read the database connection string from DATABASE_URL and the server port from PORT.
- If a Database URL is given in the user message, put it ONLY in a backend/.env file
  (DATABASE_URL=...). .env.example must contain placeholder values only.
- Every setting must have a safe default so the app starts without a .env file
  (e.g. SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me") in Django,
  a default value on the Settings field in FastAPI, process.env.X || "default" in Express).

Backend requirements:
- Main entry point, routes for every feature (at least 3), at least 2 data models,
  database config, and requirements.txt or package.json listing every
  third-party package imported anywhere.
- Authentication: register, login and protected routes.

Backend structure rules (FastAPI):
- All backend code lives in backend/app/. Use only `from . import x` or
  `from .x import y` for imports between these files. Never use `from ..`.
- database.py defines the engine, SessionLocal, Base, and get_db. Nothing else defines these.
- dependencies.py only re-exports and builds on these: it must start with
  `from .database import get_db`.
- models.py: SQLAlchemy models only. schemas.py: Pydantic models only.
  crud.py: database functions only.
- Use Pydantic v2 syntax. Import BaseSettings from "pydantic_settings"
  (`from pydantic_settings import BaseSettings`), never from "pydantic".

Backend rules (Django):
- settings.py is a plain Django settings module: UPPERCASE variables at module level
  (INSTALLED_APPS, DATABASES, SIMPLE_JWT, ...). Never define a Settings class and
  never import pydantic or pydantic_settings anywhere in a Django project.
- If you define a custom User model, set AUTH_USER_MODEL = "<app>.User" in settings.py.
- Read DATABASES from DATABASE_URL using dj-database-url, falling back to SQLite.
- Every app with models has an empty migrations/__init__.py. Never write migration
  files yourself; they are generated from the models.
- Use django-cors-headers so the frontend can call the API.
- With Django REST Framework, register, login and token views must set
  permission_classes = [AllowAny] and authentication_classes = [].
- Use Django REST Framework serializers (serializers.Serializer / ModelSerializer)
  for all request validation. Never use Pydantic in a Django project.
- Settings come from django.conf.settings; never use pydantic_settings in Django.
- In development, allow all CORS origins (Django: CORS_ALLOW_ALL_ORIGINS = True with
  django-cors-headers; FastAPI: CORSMiddleware with allow_origin_regex=".*";
  Express: app.use(cors())).

Backend rules (Node/Express):
- For password hashing always use "bcryptjs", never "bcrypt" (bcrypt needs native compilation).

Database rules (all backends):
- The database is PostgreSQL in production. Never use MongoDB or Mongoose.
- If DATABASE_URL is not set, fall back to a local SQLite database.
- The app must create its own tables on startup:
  - FastAPI: call Base.metadata.create_all(bind=engine) in main.py.
  - Django: migrations as above.
  - Node/Express: use Prisma with provider "postgresql" (schema in prisma/schema.prisma),
    OR Sequelize with sequelize.sync() called before app.listen().
  - Use only portable column types (Integer, String, Text, Boolean, DateTime, Float, ForeignKey). No Postgres-only types like ARRAY or JSONB.

Frontend rules:
- Build a complete, polished UI, not a skeleton. Every backend endpoint must be
  reachable from the UI.
- React: use Vite (never Create React App), react-router-dom for routing,
  one API service file that reads the backend URL from import.meta.env.VITE_API_URL.
- Include all auth screens the backend supports: login, register (with a link
  between them), and logout.
- After login, show a main dashboard with navigation (navbar or sidebar) to every
  feature page. Each feature has pages to list, create, edit and delete its items.
- Styling: add Tailwind via <script src="https://cdn.tailwindcss.com"></script>
  in index.html and style every component with Tailwind classes. Use a consistent
  color scheme, cards, spacing, hover states, and a responsive layout.
- Show loading states, error messages and empty states (e.g. "No notes yet").
- If you create a React context provider (AuthProvider, ThemeProvider, ...), wrap <App /> with it in main.jsx.
- Use current library APIs: @tanstack/react-query v5 object syntax
  (useQuery({ queryKey, queryFn })), react-router-dom v6,
  jwt-decode v4 (import { jwtDecode } from "jwt-decode").

User flow (every app):
- "/" is a landing page: app name, a one-line pitch, 3 feature highlights, and
  two buttons: "Get started" (goes to /register) and "Log in" (goes to /login).
- /register and /login are centered cards on a colored gradient background,
  each linking to the other. After registering, log the user in automatically
  and go straight to the dashboard.
- /dashboard shows a welcome message, summary stat cards (counts, recent activity)
  and quick actions. Protected pages redirect to /login when not logged in.
- On first run, the backend seeds 3-5 realistic sample items so the dashboard
  never looks empty.

Visual design (every app):
- Pick a primary color that fits the app (e.g. indigo for productivity, emerald for
  health, rose for social) and use it consistently for buttons, links and accents.
- Layout after login: a sidebar or top navbar with the app name, icons, and links
  to every feature, plus a logout button.
- Use cards with rounded-xl corners, soft shadows and generous padding.
  Use a light gray page background (bg-slate-50), never plain white everywhere.
- Buttons: solid primary color, rounded-lg, hover and disabled states.
  Inputs: full width, rounded-lg, visible border, focus ring in the primary color.
- Use icons from lucide-react (React) or lucide-vue-next (Vue) for navigation
  and actions, and add them to package.json.
- The app must look like a modern, finished SaaS product, not a tutorial.

Authentication contract (every stack, exactly this):
- POST {API}/auth/register/ with {"username", "email", "password"}
  -> 201 {"access": "<jwt>", "user": {"id", "username", "email"}}
  Registering also logs the user in.
- POST {API}/auth/login/ with {"username", "password"}
  -> 200 {"access": "<jwt>", "user": {"id", "username", "email"}}
- GET {API}/auth/me/ with header "Authorization: Bearer <access>"
  -> 200 {"id", "username", "email"}
- The frontend stores the "access" value in localStorage under the key "token",
  and its API client adds "Authorization: Bearer <token>" to every request.
- The backend accepts exactly that header format on every protected route
  (Django: rest_framework_simplejwt JWTAuthentication; FastAPI: OAuth2 bearer;
  Express: a middleware reading the Bearer token).
- When any request returns 401, the frontend clears the token and redirects to /login.

Frontend robustness:
- Every page that loads data handles loading, error and empty states.
  Treat a missing list as [] (e.g. (data ?? []).length), never assume data exists.
"""

def fix_react_package_json(files: list[dict]) -> list[dict]:
    """
    Deterministically fixes React package.json files.

    The LLM sometimes generates:
        "start": "react-scripts start"

    without adding react-scripts to dependencies.

    This function ensures CRA projects always have the dependency they need.
    """

    for file in files:
        path = file.get("path", "")

        if not path.endswith("package.json"):
            continue

        try:
            package_data = json.loads(file.get("content", "{}"))
        except (json.JSONDecodeError, TypeError):
            continue

        dependencies = package_data.setdefault("dependencies", {})
        scripts = package_data.get("scripts", {})

        # If the generated project uses react-scripts,
        # make sure react-scripts is actually installed.
        uses_react_scripts = any(
            "react-scripts" in str(command)
            for command in scripts.values()
        )

        if uses_react_scripts:
            dependencies["react-scripts"] = "5.0.1"

        # Write the corrected package.json back.
        file["content"] = json.dumps(
            package_data,
            indent=2
        )

    return files


async def generate_code(
    idea: str,
    tech_stack: str,
    database_url: str | None = None
):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-120b",
        temperature=0.5,
        max_tokens=32000,
        reasoning_effort="low",
    )

    user_content = f"App idea:\n{idea}\n\nTech stack: {tech_stack}"

    if database_url:
        user_content += (
            f"\n\nDatabase URL to use exactly as given "
            f"(do not invent a different one): {database_url}"
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    response = await llm.ainvoke(messages)

    print(
        "RAW RESPONSE CONTENT:",
        repr(response.content)
    )

    print(
        "RESPONSE METADATA:",
        response.response_metadata
    )

    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]

        if raw.startswith("json"):
            raw = raw[4:]

    raw = raw.strip()

    print("RAW LENGTH:", len(raw))
    print("RAW PREVIEW:", raw[:300])

    try:
        parsed = json.loads(raw)

    except json.JSONDecodeError:

        repair_messages = [
            SystemMessage(
                content=(
                    "You output broken JSON. "
                    "Return ONLY the corrected, valid JSON — "
                    "no markdown, no explanation."
                )
            ),
            HumanMessage(content=raw),
        ]

        repair_response = await llm.ainvoke(
            repair_messages
        )

        repaired = repair_response.content.strip()

        if repaired.startswith("```"):
            repaired = repaired.split("```")[1]

            if repaired.startswith("json"):
                repaired = repaired[4:]

        parsed = json.loads(
            repaired.strip()
        )

    print(
        "PARSED KEYS:",
        list(parsed.keys())
    )

    # ---------------------------------------------------------
    # Deterministic Python fixes
    # ---------------------------------------------------------

    parsed["files"] = drop_generated_migrations(
        parsed["files"]
    )

    parsed["files"] = fix_missing_typing_imports(
        parsed["files"]
    )

    parsed["files"] = fix_pydantic_v2_settings_import(
        parsed["files"]
    )

    parsed["files"] = fix_relative_imports(
        parsed["files"]
    )

    parsed["files"] = fill_missing_files(
        parsed["files"],
        llm,
    )

    parsed["files"] = fill_missing_frontend_exports(
        parsed["files"],
        llm,
    )

    parsed["files"] = fix_missing_providers(
        parsed["files"]
    )

    parsed["files"] = fix_django_auth_views(
        parsed["files"]
    )

    parsed["files"] = fix_package_json_dependencies(
        parsed["files"]
    )

    # Fix React package.json dependencies.
    #
    # This catches the exact problem we just encountered:
    # "react-scripts" being used in scripts but missing
    # from dependencies.
    if "React" in tech_stack:
        parsed["files"] = fix_react_package_json(
            parsed["files"]
        )

    # ---------------------------------------------------------
    # Backend requirements
    # ---------------------------------------------------------

    if "FastAPI" in tech_stack or "Django" in tech_stack:

        backend_framework = (
            "FastAPI"
            if "FastAPI" in tech_stack
            else "Django"
        )

        req_content = build_requirements_txt(
            parsed["files"],
            backend_framework
        )

        existing_req = next(
            (
                f
                for f in parsed["files"]
                if f["path"].endswith(
                    "requirements.txt"
                )
            ),
            None
        )

        if existing_req:
            existing_req["content"] = req_content

        else:
            # Find the backend folder prefix from
            # an existing backend file.
            backend_file = next(
                (
                    f
                    for f in parsed["files"]
                    if f["path"].startswith(
                        "backend/"
                    )
                ),
                None
            )

            req_path = (
                "backend/requirements.txt"
                if backend_file
                else "requirements.txt"
            )

            parsed["files"].append(
                {
                    "path": req_path,
                    "content": req_content
                }
            )

    # ---------------------------------------------------------
    # Database URL
    # ---------------------------------------------------------

    parsed["files"] = apply_database_url(
        parsed["files"],
        database_url
    )

    # ---------------------------------------------------------
    # File tree
    # ---------------------------------------------------------

    parsed["file_tree"] = build_file_tree(
        parsed["files"]
    )

    return parsed