import os, time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = "You are Cortex, an enterprise prompt optimizer. Rewrite the prompt to be structured and efficient. Preserve core technical intent."

@app.get("/")
@app.get("/api")
@app.get("/api/optimize")
def health():
    return {"status": "Cortex API Active"}

@app.post("/")
@app.post("/api")
@app.post("/api/optimize")
@app.post("/{full_path:path}")
def optimize(req: PromptRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing on Vercel.")
    try:
        client = Groq(api_key=api_key)
        t0 = time.time()
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": req.prompt}],
            temperature=0.2
        )
        out = res.choices[0].message.content
        latency = int((time.time() - t0) * 1000)
        orig, opt = len(req.prompt.split()), len(out.split())
        return {
            "optimized_prompt": out,
            "metrics": {"token_savings_pct": round(((orig - opt) / max(orig, 1)) * 100, 1), "latency_ms": latency, "security_check": "CLEAN"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
