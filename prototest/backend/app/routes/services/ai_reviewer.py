import os

async def review_code(file_path: str, content: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "AI review skipped: GROQ_API_KEY is not set."

    try:
        from groq import Groq
    except ImportError:
        return "AI review skipped: groq package is not installed."

    client = Groq(api_key=api_key)
    prompt = f"""You are a senior software engineer reviewing AI-generated code.
Review this file: {file_path}

Give short, clear feedback (3-5 bullet points max) covering:
- Any bugs or logical errors
- Missing error handling
- Code quality / best practices
- Any security concerns

Be direct and specific. No fluff. If the code looks good, say so briefly.

Code:
{content[:3000]}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{ "role": "user", "content": prompt }],
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()
