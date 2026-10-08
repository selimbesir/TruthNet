<p align="center">
  <img src="assets/banner.svg" alt="TruthNet — A Journal of Adversarial Fact-Checking" width="100%">
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-2B4C8C?style=flat-square&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/backend-FastAPI-1A5C38?style=flat-square">
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-React-8B1A1A?style=flat-square">
  <img alt="Mock Mode" src="https://img.shields.io/badge/demo-mock%20mode%20available-7A4A00?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-all%20rights%20reserved-3D3D3D?style=flat-square">
</p>

# 🔍 TruthNet

**TruthNet** is a web app for checking suspicious claims, headlines, and social-media posts — not with one model giving an instant opinion, but with an **adversarial multi-agent pipeline** that argues both sides before reaching a verdict.

Instead of asking a single LLM "is this true?", TruthNet splits the job across four specialized agents: one extracts the actual claims, one plays **prosecutor** (hunting for evidence that debunks the claim), one plays **defense** (hunting for the strongest legitimate support), and a final **judge** weighs both cases and delivers a verdict with a confidence score, explanation, missing context, manipulation techniques, and sources.

The site itself is designed like a research journal — paste a claim, watch the pipeline run stage-by-stage in real time, then read the verdict like a dossier.

---

##  What It Does

-  **Parses messy input** into specific, fact-checkable claims
-  **Argues both sides** — a prosecution agent builds the case against the claim, a defense agent builds the strongest honest case for it
-  **Judges the evidence** — a final agent weighs both arguments and renders one verdict, not an average
-  **Streams live progress** to the frontend via Server-Sent Events, so you watch each stage complete instead of staring at a spinner
-  **Ships with a mock pipeline** so the whole flow can be demoed without spending a cent on API calls

##  How It Works

```
          ┌──────────────┐
  Claim ──▶  Agent A      │  extract atomic, checkable claims
          │  "Extract"    │
          └──────┬───────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
 ┌─────────────┐   ┌─────────────┐
 │  Agent B    │   │  Agent C    │   ← run in PARALLEL for speed
 │ Prosecution │   │  Defense    │     and to avoid one-sided bias
 │ argues FALSE│   │ argues TRUE │
 └──────┬──────┘   └──────┬──────┘
        └────────┬────────┘
                  ▼
           ┌─────────────┐
           │  Agent D    │   weighs both arguments,
           │   Judge     │   stamps the final verdict
           └──────┬──────┘
                  ▼
             📋 Verdict
```

Agents **B** and **C** run concurrently — this keeps the pipeline fast and makes the final judgment less one-sided than a single-pass "fact check" prompt.

### 📋 Verdict Taxonomy

| Verdict | Meaning |
|---|---|
|  `TRUE` | The claim checks out against the evidence |
|  `FALSE` | The claim is contradicted by the evidence |
|  `MISLEADING` | Technically defensible but framed to deceive |
|  `PARTIALLY_TRUE` | Some parts hold up, others don't |
|  `UNVERIFIABLE` | Not enough evidence either way |
|  `SATIRE` | Not a genuine factual claim to begin with |

## 🖥️ Website Flow

1. Open the TruthNet website
2. Paste a claim, headline, or post into the input box
3. Submit it for fact-checking
4. Watch the live agent timeline update, stage by stage
5. Read the final verdict, supporting details, missing context, and source list

The frontend lives in [`frontend/TruthNet.html`](frontend/TruthNet.html), with React components in [`frontend/app.jsx`](frontend/app.jsx) and [`frontend/components.jsx`](frontend/components.jsx), styled as an editorial "journal" — serif headlines, letterpress rules, and a verdict that reads like a stamped dossier page.

## 🗂️ Project Structure

```
hackathon-main/
├── backend/
│   ├── main.py             # FastAPI app — serves the API and the frontend
│   ├── pipeline.py         # Coordinates the 4-agent workflow + SSE streaming
│   ├── agents.py           # Live Anthropic / Gemini agent implementations
│   ├── agents_mock.py      # Fake agents for demoing without API calls
│   ├── stripe_config.py    # Tier/pricing scaffolding (standard / pro / max)
│   └── stripe_webhooks.py  # Subscription webhook handling (in progress)
├── frontend/
│   ├── TruthNet.html       # Entry point served at /app
│   ├── app.jsx             # Main React app + pipeline diagram
│   ├── components.jsx      # Verdict cards, chips, shared UI atoms
│   └── history.jsx         # Past fact-check history view
├── scripts/
│   ├── test_pipeline.py    # Pipeline tests (mock mode)
│   ├── test_sse_http.py    # HTTP/SSE smoke test
│   └── test_tiers_api.py   # Billing tier API tests
├── truthnet_terminal.py    # Terminal/CLI demo of the pipeline
└── requirements.txt
```

## ⚙️ Backend

The backend is a **FastAPI** service. The pieces that matter most:

- [`backend/main.py`](backend/main.py) — exposes `/fact-check` and serves the frontend at `/app`
- [`backend/pipeline.py`](backend/pipeline.py) — orchestrates Agents A → B/C → D, with per-agent timeouts
- [`backend/agents.py`](backend/agents.py) — real agent calls against Anthropic and Gemini
- [`backend/agents_mock.py`](backend/agents_mock.py) — deterministic fake agents for mock mode

##  Setup

```bash
cd hackathon-main
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

>  Real API keys belong only in `.env`. Never commit `.env`, screenshots of `.env`, terminal output containing keys, or copied key values.

Use `.env.example` as the template:

```bash
cp .env.example .env
```

Then fill in whichever providers you want to use (Anthropic and/or Gemini).

## ▶️ Run The Website

Start the backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Open:

```
http://127.0.0.1:8000/app
```

Health checks:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

## 🧪 Mock Mode

Mock mode is for demos and tests without spending API credits — the pipeline runs end-to-end with deterministic fake agents.

```bash
TRUTHNET_MOCK=1 uvicorn backend.main:app --reload --port 8000
```

Run the pipeline tests:

```bash
TRUTHNET_MOCK=1 python scripts/test_pipeline.py
TRUTHNET_MOCK=1 python scripts/test_pipeline.py --all-demos
```

Run the HTTP/SSE smoke test after starting the server in mock mode:

```bash
python scripts/test_sse_http.py
```

##  API

**JSON verdict mode:**

```bash
curl -X POST http://127.0.0.1:8000/fact-check \
  -H "Content-Type: application/json" \
  -d '{"claim":"does israel have nukes"}'
```

**Website / SSE mode:**

```bash
curl -N -X POST http://127.0.0.1:8000/fact-check \
  -H "Content-Type: application/json" \
  -d '{"user_input":"does israel have nukes"}'
```

**SSE status order:**

```
agent_a_running → agent_a_done
agents_bc_running → agents_bc_done
agent_d_running → agent_d_done
result
```

**Final SSE message shape:**

```json
{"status":"result","result":{"verdict":"FALSE"}}
```

## 💻 Terminal Demo

```bash
python truthnet_terminal.py
python truthnet_terminal.py "does israel have nukes"
```

## 🔧 Configuration

Useful `.env` flags:

```env
TRUTHNET_MOCK=0
TRUTHNET_TIMEOUT_A=8
TRUTHNET_TIMEOUT_BC=16
TRUTHNET_TIMEOUT_D=30
ANTHROPIC_DISABLE_WEB_SEARCH=false
```

The live model split — which provider and model each of the four agents uses — is configured independently through per-agent flags in `.env` (e.g. `AGENT_A_PROVIDER`, `ANTHROPIC_AGENT_D_MODEL`, `GEMINI_AGENT_B_API_KEY`), so Agent A can run on one provider/model while the Judge runs on another.

## 💳 Tiers & Billing *(in progress)*

Scaffolding exists for `standard` / `pro` / `max` subscription tiers via Stripe ([`backend/stripe_config.py`](backend/stripe_config.py), [`backend/stripe_webhooks.py`](backend/stripe_webhooks.py)) — price-ID mapping and webhook handling are in place, but not yet wired into the main API surface.

## 📄 License

All rights reserved. Provided for evaluation and portfolio review only — see [`LICENSE`](LICENSE).
