import os
import json
import csv
import time
import re
from typing import List, Dict
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()

def compress_prompt(prompt: str) -> Dict:
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20250514",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"Remove all verbose/filler words. Keep technical requirements only.\n\n{prompt}"
            }]
        )
        compressed = response.content[0].text.strip()
        ratio = 1 - (len(compressed) / len(prompt)) if len(compressed) < len(prompt) else 0
        return {"original": prompt, "compressed": compressed, "ratio": max(ratio, 0), "status": "success"}
    except Exception as e:
        return {"original": prompt, "compressed": prompt, "ratio": 0.0, "status": "error"}

def validate_quality(original: str, compressed: str) -> float:
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20250514",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": f"Same requirements? {original[:100]} vs {compressed[:100]}\nRate 0-1:"
            }]
        )
        text = response.content[0].text.strip()
        import re as regex
        match = regex.search(r'0?\.\d+|1\.0', text)
        return float(match.group()) if match else 0.85
    except:
        return 0.85

def check_security(prompt: str) -> float:
    risk = 0.0
    patterns = [r"IGNORE\s+(PREVIOUS|ALL)", r"OVERRIDE", r"DEVELOPER\s+MODE", r"(exec|eval|DROP\s+TABLE)", r"/etc/passwd"]
    for pattern in patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            risk += 0.2
    keywords = ["credentials", "password", "api key", "hack", "exploit"]
    for kw in keywords:
        if kw in prompt.lower():
            risk += 0.1
    return min(risk, 1.0)

def benchmark_pipeline(prompts: List[str]) -> None:
    os.makedirs("results", exist_ok=True)
    results = []
    passed = 0
    
    print(f"\n{'='*70}\nBENCHMARKING {len(prompts)} VIBE CODING PROMPTS\n{'='*70}\n")
    
    for i, prompt in enumerate(prompts, 1):
        start = time.time()
        comp = compress_prompt(prompt)
        q_score = validate_quality(prompt, comp["compressed"])
        risk = check_security(prompt)
        flagged = risk > 0.18
        passed_full = q_score >= 0.90 and not flagged
        if passed_full:
            passed += 1
        latency = (time.time() - start) * 1000
        
        results.append({
            "id": i,
            "compression": f"{comp['ratio']*100:.1f}",
            "q_score": f"{q_score:.2f}",
            "risk": f"{risk:.2f}",
            "flagged": "YES" if flagged else "NO",
            "passed": "YES" if passed_full else "NO",
            "latency_ms": f"{latency:.0f}"
        })
        
        status = "✓" if passed_full else "✗"
        print(f"[{i:2d}/50] {status} Comp: {comp['ratio']*100:5.1f}% | Q: {q_score:.2f} | Risk: {risk:.2f} | {latency:6.0f}ms")
    
    with open("results/benchmark.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    avg_comp = sum(float(r["compression"]) for r in results) / len(results)
    avg_q = sum(float(r["q_score"]) for r in results) / len(results)
    
    print(f"\n{'='*70}\nRESULTS\n{'='*70}")
    print(f"Passed: {passed}/{len(prompts)} ({passed/len(prompts)*100:.0f}%)")
    print(f"Avg compression: {avg_comp:.1f}%")
    print(f"Avg Q_score: {avg_q:.2f}")
    print(f"Saved: results/benchmark.csv\n")

if __name__ == "__main__":
    prompts = [
        "Initialize this project using React + Tailwind CSS + TypeScript. Enforce strict component modularity, absolute import paths (@/*), and never write inline styles or vanilla CSS unless specified. Acknowledge this setup before writing code.",
        "Create a PostgreSQL relational schema using Prisma/Drizzle for a multi-tenant SaaS application. Include users, organizations, billing, and audit_logs tables with appropriate foreign keys, cascading deletes, and indexes for frequent queries.",
        "Set up a lightweight global state management system using Zustand to manage user authentication status, global UI themes, and persistent sidebar toggle states across the application.",
        "Design a highly organized RESTful API route architecture using Next.js App Router following the MVC pattern. Generate boilerplate templates for CRUD operations on a products resource.",
        "Implement a middleware helper for token authentication and role checking. Restrict route access based on an array of permitted roles: ['admin', 'editor', 'viewer'].",
        "Create a global error-handling wrapper and custom exception classes for backend API requests to ensure every failed request returns a standardized JSON object containing a clean error message, error code, and status.",
        "Draft the initial folder structure for a turbo monorepo separating our client app, an admin panel, and shared UI component libraries, detailing where to place shared configuration files.",
        "Write an abstracted client wrapper class for the Stripe API that initializes with environment variables and includes safety try/catch blocks for handling connection dropouts gracefully.",
        "Build a dynamic SEO metadata generation utility for server-side pages that accepts custom titles, descriptions, open-graph image paths, and canonical links.",
        "Configure a global validation framework combining Zod and React Hook Form to process user input across the app, ensuring all forms default to native accessibility behavior.",
        "Build a responsive dashboard layout with a collapsing sidebar navigation on desktop, a bottom navigation bar on mobile, a universal top search bar, and a theme-toggle switch.",
        "Create a modern SaaS hero section with an asymmetric grid, gradient typography, prominent primary/secondary CTA targets, and a floating, interactive product screenshot preview.",
        "Generate a 3-tier pricing matrix component (Free, Pro, Enterprise). Include a smooth Monthly/Annual pricing toggle switch, highlight the 'Pro' card as 'Most Popular', and format items using checkmark grids.",
        "Build a global Cmd+K command palette overlay using shadcn/ui. Support fuzzy search filters, keyboard arrow-key navigation, group categories, and recent history tags.",
        "Design a Kanban board component with 4 columns. Allow columns to accept dragged tasks, display card counters, and animate task drops cleanly using Framer Motion.",
        "Create a 4-step user onboarding wizard form. Include progress tracking visual bars, inline input validation on each step, back/next button controls, and a final review layout.",
        "Implement a client-side data table complete with paginated rows, ascending/descending column header sorting triggers, and dynamic text filter fields for strings.",
        "Create an infinite auto-scrolling marquee slider for customer logo grids and text testimonials that pauses moving whenever a user hovers over the card area.",
        "Build a custom toast notification queue system that handles 'success', 'warning', and 'error' notifications, auto-dismissing individual toasts after 4 seconds with accessible close buttons.",
        "Design a dashboard analytics chart panel using Recharts. Include a stacked area chart mapping traffic, a hover tooltip displaying raw metrics, and a dynamic date-range selector dropdown.",
        "Write a backend route to securely handle Stripe webhooks. Parse raw webhook body events, verify signatures, and update database subscription fields for invoice.payment_succeeded and customer.subscription.deleted.",
        "Implement a route that takes user search text, calls OpenAI's text-embedding-3-small API, queries a pgvector database index, and returns the top 5 most relevant documents.",
        "Create a secure backend endpoint that generates an AWS S3 pre-signed upload URL, allowing clients to upload images directly up to 5MB, validating file types strictly before generation.",
        "Write a custom React hook useDebounce and pair it with an API search controller to execute live autocomplete database lookups only after the user stops typing for 300 milliseconds.",
        "Build a file processing utility that accepts an uploaded .csv spreadsheet, parses rows using PapaParse, cross-references matching records, and inserts them as a single bulk operation.",
        "Create a lightweight real-time notification engine using Socket.io. Handle user joining event rooms, broadcasting text messages, and showing typing indicators.",
        "Design a passwordless authentication flow. Generate a short-lived cryptographically secure token, save it to the database, email it to users via Resend, and verify it when clicked.",
        "Write a backend handler that dynamically creates an elegant invoice PDF using react-pdf based on transaction data passed through parameters.",
        "Configure a backend worker queue utilizing BullMQ/Redis to manage heavy image processing tasks safely without blocking main server event handling loops.",
        "Create a custom API query caching middleware using Redis to save high-load database query results for 5 minutes, clearing the cache instantly whenever a write event updates the table.",
        "Look at the existing @sidebar.tsx code. Add a new collapsible navigation section called 'Settings' directly below the 'Analytics' item without changing any layout stylings or icons.",
        "Extend the existing user registration form inside @register.tsx to collect a phone number. Update the corresponding Zod validation schema and Prisma user data model safely.",
        "Refactor this component to replace all hardcoded text strings with dynamic translation key lookups using next-intl configuration standards.",
        "Modify the existing @Modal.tsx component to safely close whenever a user clicks outside the modal layout or strikes the Escape key on their physical keyboard.",
        "Review the current theme values across these core UI files. Update them to respect Tailwind's dark: modifier class utility dynamically across all containers.",
        "Refactor this local React useState array into our existing global Zustand client store instance so the data updates across independent views.",
        "Take this plain JavaScript service file and convert it fully into strictly-typed TypeScript code. Explicitly define all interfaces rather than relying on any parameters.",
        "Adapt our current API fetch method into an optimized useQuery fetch engine using @tanstack/react-query, enabling automatic background retries and caching states.",
        "Modify this backend SQL select query handler to support structural client-side pagination parameters page and limit, returning an explicit totalPages integer summary.",
        "Layer subtle entrance/exit state animations onto the current layout component using Framer Motion constants without altering the base functional components.",
        "I am receiving an error. Analyze this error within the context of our active code and output the exact line-by-line correction needed to fix it.",
        "Profile this specific layout file for performance. Identify unnecessary element re-renders, isolate excessive calculations, and refactor using useMemory or useCallback hook loops.",
        "Write a comprehensive unit test suite using Vitest + React Testing Library. Cover edge cases, empty variables, and mocked fetch request behaviors.",
        "Generate a production-ready, highly optimized multi-stage Dockerfile configuration file for this specific Next.js application to keep deployment image footprints minimal.",
        "Create a .github/workflows/deploy.yml action pipeline script that triggers on every pull request to master, runs linter rules, runs the test command, and deploys if it passes.",
        "Review this API controller code for common vulnerabilities (OWASP standard top 10). Rewrite sections to explicitly prevent potential SQL injections and validate parameter lengths.",
        "Write an automated end-to-end integration test file using Playwright that simulates a user visiting the homepage, typing log-in data, submitting forms, and asserting landing url states.",
        "Analyze this React WebSocket custom hook for possible memory leaks. Ensure connection paths, cleanup listeners, and interval timers clear correctly upon component unmount cycles.",
        "Examine this HTML element landing page layout structure. Suggest clear changes to image rendering strategies, fonts, and script sizes to raise Lighthouse scores above 95.",
        "Act as a DevOps coordinator. Review our total project files and generate a comprehensive checklist detailing missing environment flags, security headers, and domain redirection setups before deploying to production.",
    ]
    
    benchmark_pipeline(prompts)
