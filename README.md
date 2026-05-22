# How I Built an AI SRE That Runs on a ₹25,000 Laptop

> **TL;DR:** I reduced incident response time from ~25 minutes to ~90 seconds using a free LLM (Groq), running on a low-end laptop (Intel Celeron N4020, 8GB RAM). Total cost: $0/month.

![Python](https://img.shields.io/badge/Built_with-Python_3.12-blue)
![Cost](https://img.shields.io/badge/Monthly_Cost-%240-success)
![RAM](https://img.shields.io/badge/Runs_on-8GB_RAM-orange)

---

## The Problem

Every SRE team I observed had the same bottleneck:

An alert fires at 2am → engineers open dashboards → grep logs → read runbooks → manually guess root cause.

Enterprise AIOps tools solve this — but they require expensive infra, GPUs, or paid APIs.

I wanted a **zero-cost version** that still works.

---

## The Constraint

I forced myself into real-world constraints:

- No paid APIs  
- No Docker/Kubernetes  
- Must run on low-end hardware  
- Prefer free-tier LLM inference  

My system: ASUS VivoBook X515MA (Intel Celeron N4020, 8GB RAM, Ubuntu 24.04)

---

## The Architecture

Alertmanager only needs a webhook — that became my entry point.

**Flow:**

Alertmanager → FastAPI → Groq LLM → JSON RCA

---

## The Build

Core idea: keep backend lightweight, push intelligence to LLM, and strictly control output format.

### Key challenge: messy LLM output

LLMs often return:

Here is the analysis:
{
  ...
}

So instead of fighting it, I extracted JSON safely:

```python
def extract_json(text: str) -> dict:
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return {"raw": text[:200]}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {"raw": text[:200]}
```

---

## The Breakthrough

I used **Groq’s free inference API** with:

- `llama-3.1-8b-instant`
- Fast response (~1–2s)
- Zero cost

Example output:

```json
{
  "summary": "Disk full alert",
  "cause": "Disk usage exceeded threshold",
  "steps": [
    "Check disk usage",
    "Delete logs or temp files",
    "Restart affected service"
  ]
}
```

---

## Real Test

```bash
curl -X POST localhost:8000/alert \
-H "Content-Type: application/json" \
-d '{
  "alerts": [
    {"labels": {"alertname": "DiskFull"}},
    {"labels": {"alertname": "PodCrashLoop"}}
  ]
}'
```

---

## Architecture Diagram

```
┌──────────────┐
│ Alertmanager │
└──────┬───────┘
       │ webhook
       ▼
┌──────────────┐
│  FastAPI     │  (~80MB RAM)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Groq LLM     │
│ llama-3.1-8b │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ JSON RCA     │
└──────────────┘
```

---

## Try It Yourself

```bash
git clone https://github.com/arshitchoubey18/ai-incident-agent
cd ai-incident-agent

python3 -m venv venv
source venv/bin/activate

pip install fastapi uvicorn langchain-groq python-dotenv

cp .env.example .env  # add GROQ_API_KEY

uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## What I Learned

- Production engineering is **80% parsing + reliability**, not prompting  
- Free-tier tools are enough if architecture is lean  
- Constraints force better design than unlimited resources  
- LLMs are unreliable → structure matters more than intelligence  

---

## What's Next

- Runbook-based RAG (real incident fixes)
- Slack/Telegram alert integration
- Failure pattern detection

---

## Closing

Built by Arshit Choubey

SRE aspirant building production systems on low-cost hardware — proving that good engineering is constraint-driven, not resource-driven.

If you're hiring for SRE / Platform Engineering roles, let's connect.
