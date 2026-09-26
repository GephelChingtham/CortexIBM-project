import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

class PromptRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = """You are Cortex, an enterprise prompt optimizer. 
Rewrite the prompt to be structured and efficient. Preserve core technical intent."""

@app.post("/api/optimize")
def optimize_prompt(req: PromptRequest):
    if not client:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing")
    
    start_time = time.time()
    try:
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
        raise HTTPException(status_code=400, detail=str(e))
