"""
Maps a ProtoCode tech_stack string to the right test runner (pytest or jest)
and tells us which language the generated test file should be written in.
"""

# Backend half of tech_stack determines the runner — frontend half (React/Vue/Next.js) doesn't matter for testing
PYTHON_BACKENDS = ["FastAPI", "Django"]
JS_BACKENDS = ["Node/Express"]

def get_runner(tech_stack: str) -> str:
    """
    Returns "pytest", "jest", or "unsupported"
    tech_stack examples: "React + FastAPI", "Vue + Node/Express", "Next.js + Node/Express"
    """
    if any(backend in tech_stack for backend in PYTHON_BACKENDS):
        return "pytest"
    if any(backend in tech_stack for backend in JS_BACKENDS):
        return "jest"
    if "Next.js" in tech_stack:
        # Next.js API routes are still JS — use jest
        return "jest"
    return "unsupported"