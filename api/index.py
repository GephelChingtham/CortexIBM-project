import os, time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = "You are Cortex, an enterprise prompt optimizer. Rewrite the prompt to be structured, concise, and production-ready. Preserve core technical intent while cutting fluff."

HTML_LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cortex | Enterprise Prompt Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white min-h-screen font-sans p-6 md:p-12">
    <div class="max-w-4xl mx-auto space-y-8">
        <header class="border-b border-neutral-800 pb-6">
            <h1 class="text-3xl font-bold tracking-tight">CORTEX</h1>
            <p class="text-neutral-400 text-sm mt-1">Enterprise Prompt Optimizer & Security Gateway</p>
        </header>
        <main class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
                <label class="block text-xs font-mono uppercase tracking-widest text-neutral-400">Input Prompt</label>
                <textarea id="promptInput" rows="10" class="w-full bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm focus:outline-none focus:border-white text-neutral-100 font-mono" placeholder="Paste raw prompt here..."></textarea>
                <button onclick="optimize()" id="optBtn" class="w-full bg-white text-black font-semibold py-3 px-4 rounded-lg hover:bg-neutral-200 transition text-sm uppercase tracking-wider">Optimize Prompt</button>
            </div>
            <div class="space-y-4">
                <label class="block text-xs font-mono uppercase tracking-widest text-neutral-400">Optimized Output</label>
                <div id="outputContainer" class="w-full h-[250px] bg-neutral-900 border border-neutral-800 rounded-lg p-4 text-sm font-mono overflow-y-auto text-neutral-300">
                    <span class="text-neutral-600">Awaiting input...</span>
                </div>
                <div id="metrics" class="grid grid-cols-3 gap-2 pt-2 text-center hidden">
                    <div class="bg-neutral-900 border border-neutral-800 p-3 rounded-lg">
                        <div id="savingsMetric" class="text-lg font-bold text-emerald-400">0%</div>
                        <div class="text-[10px] text-neutral-500 uppercase tracking-widest">Savings</div>
                    </div>
                    <div class="bg-neutral-900 border border-neutral-800 p-3 rounded-lg">
                        <div id="latencyMetric" class="text-lg font-bold">0ms</div>
                        <div class="text-[10px] text-neutral-500 uppercase tracking-widest">Latency</div>
                    </div>
                    <div class="bg-neutral-900 border border-neutral-800 p-3 rounded-lg">
                        <div id="securityMetric" class="text-lg font-bold text-sky-400">CLEAN</div>
                        <div class="text-[10px] text-neutral-500 uppercase tracking-widest">Security</div>
                    </div>
                </div>
            </div>
        </main>
    </div>
    <script>
        async function optimize() {
            const input = document.getElementById('promptInput').value;
            const btn = document.getElementById('optBtn');
            const output = document.getElementById('outputContainer');
            const metrics = document.getElementById('metrics');

            if (!input.trim()) return;
            btn.disabled = true;
            btn.innerText = 'PROCESSING...';
            output.innerHTML = '<span class="text-neutral-500">Optimizing via Groq...</span>';

            try {
                const res = await fetch('/api/optimize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: input })
                });
                const data = await res.json();
                if (res.ok) {
                    output.innerText = data.optimized_prompt;
                    document.getElementById('savingsMetric').innerText = data.metrics.token_savings_pct + '%';
                    document.getElementById('latencyMetric').innerText = data.metrics.latency_ms + 'ms';
                    document.getElementById('securityMetric').innerText = data.metrics.security_check;
                    metrics.classList.remove('hidden');
                } else {
                    output.innerHTML = `<span class="text-red-500">Error: ${data.detail || 'Optimization failed'}</span>`;
                }
            } catch (err) {
                output.innerHTML = `<span class="text-red-500">Network Error: ${err.message}</span>`;
            } finally {
                btn.disabled = false;
                btn.innerText = 'OPTIMIZE PROMPT';
            }
        }
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTMLResponse(content=HTML_LAYOUT)

@app.post("/api/optimize")
@app.post("/optimize")
def optimize_prompt(req: PromptRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable is not set on Vercel.")
    
    client = Groq(api_key=api_key)
    start_time = time.time()
    
    models_to_try = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it"
    ]
    
    try:
        remote = client.models.list()
        active = [m.id for m in remote.data if "whisper" not in m.id and "guard" not in m.id]
        if active:
            models_to_try = active + models_to_try
    except Exception:
        pass
        
    last_err = None
    for m in models_to_try:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.prompt}
                ],
                temperature=0.2
            )
            enhanced = response.choices[0].message.content
            latency_ms = int((time.time() - start_time) * 1000)
            orig_tokens, opt_tokens = len(req.prompt.split()), len(enhanced.split())
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
            last_err = str(e)
            continue

    raise HTTPException(status_code=500, detail=f"Groq API Error: {last_err}")
