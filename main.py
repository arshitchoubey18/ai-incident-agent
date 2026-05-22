import os, json, re
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import httpx

load_dotenv()
from langchain_groq import ChatGroq

app = FastAPI()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_tokens=300
)

def extract_json(text: str) -> dict:
    # find first {...} block, even if LLM adds explanation
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"raw": text[:200]}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {"raw": text[:200]}

@app.post("/alert")
async def handle_alert(request: Request):
    data = await request.json()
    results = []

    for alert in data.get("alerts", []):
        name = alert.get("labels", {}).get("alertname", "TestAlert")

        prompt = f"""You are an SRE. For alert '{name}', output ONLY a JSON object with keys: summary, cause, steps (array of 3 strings). No other text."""

        resp = llm.invoke(prompt)
        print(f"\n[DEBUG] Raw LLM output: {resp.content[:200]}")

        rca = extract_json(resp.content)

        # ensure keys exist
        rca.setdefault("summary", name)
        rca.setdefault("cause", "unknown")
        rca.setdefault("steps", ["investigate", "mitigate", "verify"])

        results.append(rca)

    return {"status": "ok", "rca": results}

@app.get("/")
def health():
    return {"ok": True}
