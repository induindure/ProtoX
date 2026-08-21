import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.file_builder import build_file_tree

load_dotenv()

SYSTEM_PROMPT = """
You are a senior software engineer. Given an app idea and a tech stack, generate a complete, realistic starter project.

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

Requirements:
- Generate between 12 and 18 files
- Include: README.md, proper config files, folder structure matching the tech stack
- For React frontend: include App.jsx, at least 4 components, routing with react-router-dom, one API service file, basic CSS
- For backend: include main entry point, at least 3 routes, 2 data models, database config, requirements.txt or package.json
- Write real, working code with actual logic — not placeholder comments
- Include at least one authentication-related file (login route or auth middleware)
- Include a .env.example file
- All file content must have newlines escaped as \\n
- Do not generate the same boilerplate for every project — tailor code specifically to the described app
"""

async def generate_code(idea: str, tech_stack: str):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-120b",
        temperature=0.5,
        max_tokens=8000,
        reasoning_effort="low",
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"App idea:\n{idea}\n\nTech stack: {tech_stack}")
    ]

    response = await llm.ainvoke(messages)
    print("RAW RESPONSE CONTENT:", repr(response.content))
    print("RESPONSE METADATA:", response.response_metadata)

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
            SystemMessage(content="You output broken JSON. Return ONLY the corrected, valid JSON — no markdown, no explanation."),
            HumanMessage(content=raw),
        ]
        repair_response = await llm.ainvoke(repair_messages)
        repaired = repair_response.content.strip()
        if repaired.startswith("```"):
            repaired = repaired.split("```")[1]
            if repaired.startswith("json"):
                repaired = repaired[4:]
        parsed = json.loads(repaired.strip())

    print("PARSED KEYS:", list(parsed.keys()))
    parsed["file_tree"] = build_file_tree(parsed["files"])
    return parsed