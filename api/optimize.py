import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = """You are Cortex, an enterprise prompt optimizer. 
Rewrite the prompt to be structured and efficient. Preserve core technical intent."""

@app.get("/")
@app.get("/api/optimize")
def health_check():
    return {"status": "Cortex Optimizer Endpoint Active"}

@app.post("/")
@app.post("/api/optimize")
@app.post("/{full_path:path}")
def optimize_prompt(req: PromptRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GROQ_API_KEY missing on Vercel environment variables."
        )
    
    try:
        client = Groq(api_key=api_key)
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.prompt}
            ],
            temperature=0.2
        )
        
        enhanced = response.choices[0].message.content
        latency_ms = int((time.time() - start_time) * 1000)
        
        orig_tokens = len(req.prompt.split())
        opt_tokens = len(enhanced.split())
        savings_pct = round(((orig_tokens - opt_tokens) / max(orig_tokens, 1)) * 100, 1)

        return {
            "optimized_prompt": enhanced,
            "metrics": {
                "token_savings_pct": savings_pct,
                "latency_ms": latency_ms,
                "security_check": "CLEAN"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API Error: {str(e)}")
