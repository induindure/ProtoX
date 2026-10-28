PAGES_WORKFLOW = """name: Deploy frontend to GitHub Pages
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install
        run: npm install
        working-directory: frontend
      - name: Build
        run: npm run build -- --base=/__REPO__/
        working-directory: frontend
        env:
          VITE_API_URL: __API_URL__
      - name: SPA fallback
        run: cp frontend/dist/index.html frontend/dist/404.html
      - uses: actions/upload-pages-artifact@v3
        with:
          path: frontend/dist
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
"""

GITIGNORE = """node_modules/
dist/
.env
.venv/
venv/
__pycache__/
*.pyc
db.sqlite3
staticfiles/
.DS_Store
"""

def render_yaml(stack: dict, api_name: str, owner: str) -> str:
    cors = f"https://{owner}.github.io"
    if stack["backend"] == "fastapi":
        build = "pip install -r requirements.txt"
        start = f"uvicorn {stack['entry']} --host 0.0.0.0 --port $PORT"
        extra = ""
    else:
        build = ("pip install -r requirements.txt && "
                 "python manage.py collectstatic --noinput && "
                 "python manage.py migrate")
        start = f"gunicorn {stack['django_project']}.wsgi:application"
        extra = """      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: .onrender.com
"""
    return f"""services:
  - type: web
    name: {api_name}
    runtime: python
    rootDir: backend
    plan: free
    buildCommand: {build}
    startCommand: {start}
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: CORS_ORIGINS
        value: {cors}
{extra}"""