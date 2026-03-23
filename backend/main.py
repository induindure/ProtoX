from fastapi import FastAPI
from models import IdeaRequest, IdeaResponse, IdeaModel
from groq_service import generate_ideas

app = FastAPI()

@app.get("/")
def home():
    return {"message": "ProtoX API running"}

@app.post("/generate-idea")
def generate_idea(request: IdeaRequest):
    raw_output = generate_ideas(request.domain, request.app_type)

    # VERY SIMPLE PARSING (keep it basic)
    ideas = []

    blocks = raw_output.split("Title:")

    for block in blocks[1:]:
        try:
            lines = block.strip().split("\n")
            title = lines[0].strip()
            description = lines[1].replace("Description:", "").strip()
            features = [f.strip().lstrip("- ") for f in lines if f.strip().startswith("-")]
            ideas.append(IdeaModel(
                title=title,
                description=description,
                features=features
            ))
        except:
            continue

    return IdeaResponse(ideas=ideas)