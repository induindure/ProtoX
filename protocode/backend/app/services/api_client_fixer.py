"""
Makes the generated axios API client attach the auth token on every request.
Generated code often sets the header in a React useEffect, which runs AFTER
the first page's requests, so they go out without a token and get 401.
"""

import re

from app.services.completeness_checker import _norm

_AXIOS_CREATE = re.compile(
    r"(const\s+(\w+)\s*=\s*axios\.create\([\s\S]*?\}\s*\)\s*;?)"
)

_INTERCEPTOR = """

// Attach the token to every request, read fresh from storage each time.
{name}.interceptors.request.use(config => {{
  const token = localStorage.getItem('token');
  if (token) {{
    config.headers.Authorization = `Bearer ${{token}}`;
  }}
  return config;
}});
"""


def fix_api_client_token(files: list[dict]) -> list[dict]:
    for f in files:
        path = _norm(f["path"])
        if not path.startswith("frontend/") or not path.endswith((".js", ".jsx", ".ts", ".tsx")):
            continue
        text = f["content"]
        if "axios.create(" not in text or "interceptors.request" in text:
            continue

        m = _AXIOS_CREATE.search(text)
        if not m:
            continue

        insert = _INTERCEPTOR.format(name=m.group(2))
        f["content"] = text[:m.end()] + insert + text[m.end():]
        print(f"[api-client-fixer] added token interceptor to {path}")

    return files