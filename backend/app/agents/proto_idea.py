import json
import re
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.models.schemas import IdeaModel


SYSTEM_PROMPT = """You are ProtoIdea, an expert software architect and product strategist.
Your job is to generate creative but practical application ideas based on the user's inputs.

For each idea you MUST return a valid JSON array. Do not include any text outside the JSON.
Each element in the array must have exactly these keys:
  - title        : short catchy name (string)
  - description  : 2-3 sentence overview of what the app does (string)
  - features     : list of 4-6 core features (array of strings)
  - tech_hints   : recommended technologies (array of strings, e.g. ["React", "FastAPI", "PostgreSQL"])
  - target_users : who will use this app (string)

Return between 3 and 5 ideas. Be specific and practical — each idea must be buildable
by a small team or a solo developer within a few months.
"""

USER_PROMPT_TEMPLATE = """Generate application ideas for the following:

Domain       : {domain}
App Type     : {app_type}
Constraints  : {constraints}

Return ONLY a valid JSON array of idea objects. No markdown, no explanation, just the JSON array.
"""


class ProtoIdeaAgent:
    def _get_llm(self):
        # ✅ Create fresh each call — avoids event loop issues
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=settings.gemini_api_key,
            temperature=0.8,
            max_output_tokens=4096,
        )

    def _build_messages(self, domain: str, app_type: str, constraints: str):
        user_content = USER_PROMPT_TEMPLATE.format(
            domain=domain,
            app_type=app_type,
            constraints=constraints or "None specified",
        )
        return [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

    def _parse_ideas(self, raw: str) -> List[IdeaModel]:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\nRaw output:\n{raw}")

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array but got: {type(data)}")

        ideas = []
        for item in data:
            try:
                ideas.append(IdeaModel(**item))
            except Exception as e:
                raise ValueError(f"Invalid idea object: {e}\nItem: {item}")
        return ideas

    async def generate(self, domain: str, app_type: str, constraints: str = "") -> List[IdeaModel]:
        llm = self._get_llm()   # ✅ created here, inside the running event loop
        parser = StrOutputParser()
        messages = self._build_messages(domain, app_type, constraints)
        response = await llm.ainvoke(messages)
        raw_output = parser.invoke(response)
        return self._parse_ideas(raw_output)


proto_idea_agent = ProtoIdeaAgent()