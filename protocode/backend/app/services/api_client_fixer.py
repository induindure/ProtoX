"""
Fixes for the generated axios API client:
1. Attach the auth token on every request (avoids 401s from timing bugs).
2. Turn backend validation errors into a readable error.response.data.detail,
   so pages show the real reason ("password: This password is too short...")
   instead of a generic "Registration failed".
"""

import re

from app.services.completeness_checker import _norm

_AXIOS_CREATE = re.compile(
    r"(const\s+(\w+)\s*=\s*axios\.create\([\s\S]*?\}\s*\)\s*;?)"
)

_TOKEN_INTERCEPTOR = """

// Attach the token to every request, read fresh from storage each time.
{name}.interceptors.request.use(config => {{
  const token = localStorage.getItem('token');
  if (token) {{
    config.headers.Authorization = `Bearer ${{token}}`;
  }}
  return config;
}});
"""

_ERROR_MARKER = "Turn backend validation errors into a readable message"

_ERROR_INTERCEPTOR = """

// Turn backend validation errors into a readable message in error.response.data.detail.
{name}.interceptors.response.use(
  response => response,
  error => {{
    const data = error.response?.data;
    if (data && typeof data === 'object') {{
      if (Array.isArray(data.detail)) {{
        // FastAPI validation errors: [{{ loc, msg }}, ...]
        data.detail = data.detail
          .map(d => (d.loc ? `${{d.loc[d.loc.length - 1]}}: ` : '') + (d.msg || JSON.stringify(d)))
          .join(' ');
      }} else if (!data.detail) {{
        // Django REST Framework: {{ field: ["msg", ...] }}; Express: {{ message }} / {{ error }}
        const messages = Object.entries(data).map(([field, value]) => {{
          const text = Array.isArray(value) ? value.join(' ') : String(value);
          return ['non_field_errors', 'message', 'error'].includes(field)
            ? text
            : `${{field.charAt(0).toUpperCase() + field.slice(1)}}: ${{text}}`;
        }});
        if (messages.length) data.detail = messages.join(' ');
      }}
    }}
    return Promise.reject(error);
  }}
);
"""


def fix_api_client_token(files: list[dict]) -> list[dict]:
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("frontend/") or not path.endswith((".js", ".jsx", ".ts", ".tsx")):
            continue
        text = f["content"]
        if "axios.create(" not in text:
            continue

        m = _AXIOS_CREATE.search(text)
        if not m:
            continue
        name = m.group(2)

        additions = ""
        if "interceptors.request" not in text:
            additions += _TOKEN_INTERCEPTOR.format(name=name)
        if _ERROR_MARKER not in text:
            additions += _ERROR_INTERCEPTOR.format(name=name)
        if not additions:
            continue

        f["content"] = text[:m.end()] + additions + text[m.end():]
        print(f"[api-client-fixer] updated interceptors in {path}")

    return files