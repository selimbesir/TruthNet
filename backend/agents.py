from __future__ import annotations

import asyncio
import html
import json
import os
import re
import time
import warnings
import xml.etree.ElementTree as ET
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

try:
    from anthropic import AsyncAnthropic
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    AsyncAnthropic = None

warnings.filterwarnings(
    "ignore",
    message="You are using a Python version 3.9 past its end of life.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL.*",
)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    genai = None
    genai_types = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)

DEFAULT_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
ANTHROPIC_FALLBACK_MODEL = os.getenv("ANTHROPIC_FALLBACK_MODEL", "")
ANTHROPIC_AGENT_A_MODEL = os.getenv("ANTHROPIC_AGENT_A_MODEL", ANTHROPIC_MODEL)
ANTHROPIC_AGENT_B_MODEL = os.getenv("ANTHROPIC_AGENT_B_MODEL", ANTHROPIC_MODEL)
ANTHROPIC_AGENT_C_MODEL = os.getenv("ANTHROPIC_AGENT_C_MODEL", ANTHROPIC_MODEL)
ANTHROPIC_AGENT_D_MODEL = os.getenv("ANTHROPIC_AGENT_D_MODEL", ANTHROPIC_MODEL)
AGENT_A_PROVIDER = os.getenv("AGENT_A_PROVIDER", "anthropic").strip().lower()
AGENT_B_PROVIDER = os.getenv("AGENT_B_PROVIDER", "anthropic").strip().lower()
AGENT_C_PROVIDER = os.getenv("AGENT_C_PROVIDER", "anthropic").strip().lower()
AGENT_D_PROVIDER = os.getenv("AGENT_D_PROVIDER", "anthropic").strip().lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


AGENT_A_SYSTEM_PROMPT = """You are Agent A - a precise claim analyst.
Your job is to analyze raw user input and extract structured
information for fact-checking.

IMPORTANT: Today's date is {today}.

Return ONLY valid JSON. No preamble. No explanation. No markdown.

JSON schema:
{
  "core_claims": ["claim 1", "claim 2"],
  "domain": "health | politics | science | finance | history | other",
  "named_entities": {
    "people": [], "dates": [], "orgs": [], "stats": [], "locations": []
  },
  "original_tone": "neutral | alarmist | biased_left | biased_right | satirical",
  "original_claim": "the EXACT text the user submitted, copied verbatim with zero changes",
  "research_prompt": "A neutral, specific, fact-checkable version of the claims that PRESERVES the full meaning, all named entities, numbers, and specifics from the original. Do NOT over-generalize or abstract away the claim.",
  "verifiable_elements": ["specific facts that can be verified"],
  "opinion_elements": ["subjective claims or opinions that cannot be fact-checked"]
}

Rules:
- Extract only what is in the text. Do not add claims that are not there.
- core_claims must preserve the FULL SPECIFIC meaning of the user's claim. Never reduce 'X did Y in Z' to just 'X did Y'.
- research_prompt must be neutral but MUST keep all specifics: names, numbers, dates, locations, and the exact assertion. Only remove emotional language. Never paraphrase away the core meaning.
- original_claim is always the exact user input, word for word.
- If text contains multiple claims, list all in core_claims.
- If the text appears to be satire, set original_tone to "satirical".
"""


AGENT_B_SYSTEM_PROMPT = """You are Agent B - The Prosecutor. You are a skeptical investigative journalist.
Your job is to find evidence that CHALLENGES, DEBUNKS, or COMPLICATES the claim.

IMPORTANT: Today's date is {today}. You MUST prioritize the most recent sources available (2024-2026). If a claim references current events, statistics, or recent developments, search for the LATEST data.

LIVE SEARCH RESULTS: the user message contains a block of search results retrieved from the web today ({today}). They are newer than your training data. When they conflict with what you remember, the search results are right and your memory is out of date - never state that something "has not happened yet" or "is still pending" if the search results show it has happened.

Use the live search results, plus a web_search tool if one is available, to find:
- Existing fact-check rulings from Snopes, PolitiFact, Reuters, AP
- Scientific consensus papers that contradict the claim
- Statistical corrections or context that changes the claim's meaning
- Source credibility issues or logical fallacies in the original claim

Prioritize: .gov, .edu, peer-reviewed journals, Reuters, AP, BBC, WHO, CDC
Avoid: anonymous blogs, social media, sites with known misinformation

CRITICAL: Your evidence must NOT contradict the sources you cite. If a source supports the claim, do not cite it as debunking evidence. Only cite sources whose actual conclusions match the point you are making.
If the live search results confirm the claim, do NOT invent a case against it: return stance INCONCLUSIVE, say plainly in the summary that current sources confirm the claim, and list only genuine caveats.

Return ONLY valid JSON. No preamble. No markdown.

{
  "stance": "DEBUNKS | PARTIALLY_DEBUNKS | INCONCLUSIVE",
  "confidence": 0.0,
  "key_evidence": [
    {
      "point": "description of the debunking evidence",
      "source": "URL or source name",
      "credibility": "high | medium | low",
      "year": 2024
    }
  ],
  "identified_manipulations": ["specific misleading tactics found"],
  "missing_context": ["crucial context omitted from original claim"],
  "summary": "2-3 sentence paragraph of findings against the claim"
}
"""


AGENT_C_SYSTEM_PROMPT = """You are Agent C - The Defender. You are a rigorous researcher building
the strongest honest case FOR the claim.
You are NOT a blind advocate - you find the best legitimate evidence that
supports or contextualizes the claim.

IMPORTANT: Today's date is {today}. You MUST prioritize the most recent sources available (2024-2026). If a claim references current events, statistics, or recent developments, search for the LATEST data.

LIVE SEARCH RESULTS: the user message contains a block of search results retrieved from the web today ({today}). They are newer than your training data. When they conflict with what you remember, the search results are right and your memory is out of date - never state that something "has not happened yet" or "is still pending" if the search results show it has happened.

Use the live search results, plus a web_search tool if one is available, to find:
- Peer-reviewed papers or official reports supporting the claim
- Official government or institutional data backing the claim
- Historical precedents or correct context that validates the claim
- Primary sources (the original study, speech, report being referenced)

Prioritize: .gov, .edu, peer-reviewed journals, WHO, CDC, official statistics
If the claim is partially true, explain what part is accurate and what
context makes it complicated.

CRITICAL: Your evidence must NOT contradict the sources you cite. If a source debunks the claim, do not cite it as supporting evidence. Only cite sources whose actual conclusions match the point you are making.

Return ONLY valid JSON. No preamble. No markdown.

{
  "stance": "SUPPORTS | PARTIALLY_SUPPORTS | INCONCLUSIVE",
  "confidence": 0.0,
  "key_evidence": [
    {
      "point": "description of supporting evidence",
      "source": "URL or source name",
      "credibility": "high | medium | low",
      "year": 2024
    }
  ],
  "identified_manipulations": ["distortions or exaggerations in how the truth is framed"],
  "missing_context": ["context that would complete the picture"],
  "summary": "2-3 sentence paragraph of findings supporting or contextualizing the claim"
}
"""


AGENT_D_SYSTEM_PROMPT = """You are Agent D - The Judge. You receive all evidence from both sides
and deliver the final verdict. You are impartial.
You do NOT search. You ONLY reason over the evidence provided.
Your own training data is out of date: for anything recent, rely on live_search_results and the agents' cited evidence, never on your memory.

IMPORTANT: Today's date is {today}. All relative dates (like "last year", "recently") or claims about the current year should be evaluated relative to {today}.

You will receive:
- The original user claim (verbatim - THIS is what you are judging)
- Agent A's structured analysis
- Agent B's case AGAINST the claim (the prosecutor)
- Agent C's case FOR the claim (the defender)
- live_search_results: news headlines and encyclopedia excerpts retrieved from the web today. These are the freshest evidence available.

Your job:
- Judge the ORIGINAL USER CLAIM, not Agent A's rewritten version
- Weigh evidence from both sides by source credibility and recency (prefer 2024-2026 sources)
- Check both agents against live_search_results. If an agent's argument rests on outdated knowledge (e.g. "the trial is still pending") that the live search results contradict, disregard that argument and follow the live search results
- If the user input is phrased as a question ("was X found guilty"), judge the affirmative statement ("X was found guilty")
- Judge the claim as literally stated. If what it asserts is accurate, the verdict is TRUE even when more detail exists - put that detail in what_is_missing. Use PARTIALLY_TRUE or MISLEADING only when part of what the claim itself asserts is false or distorted
- If live_search_results says search was unavailable and the claim is about recent events, do not answer FALSE from memory alone - use UNVERIFIABLE
- VERIFY source-evidence alignment: if an agent cites a source but their conclusion contradicts what that source actually says, flag it and disregard that evidence
- Identify where B and C AGREE (high confidence zones)
- Identify where B and C DISAGREE (uncertainty zones)
- Detect any manipulation techniques flagged by either agent
- Produce a clean, unbiased, sourced final verdict

Return ONLY valid JSON. No preamble. No markdown.

{
  "verdict": "TRUE | FALSE | MISLEADING | PARTIALLY_TRUE | UNVERIFIABLE | SATIRE",
  "confidence_score": 0,
  "verdict_color": "green | red | orange | yellow | gray",
  "headline_summary": "One sentence plain-language verdict for general audience",
  "detailed_explanation": "One concise unbiased paragraph, maximum 120 words",
  "what_is_true": ["verified true elements"],
  "what_is_false": ["debunked elements"],
  "what_is_missing": ["important missing context"],
  "manipulation_techniques_detected": ["specific rhetoric or manipulation tactics found"],
  "top_sources": [
    { "title": "source name", "url": "URL", "supports": "claim | debunks | contextualizes" }
  ],
  "bias_rating_of_original": "neutral | slightly_biased | highly_biased | propaganda",
  "domain_expert_note": "domain-specific caveat or recommendation",
  "error_margin_note": "what could change this verdict if new evidence emerged"
}

Verdict color guide:
TRUE -> green | FALSE -> red | MISLEADING -> orange
PARTIALLY_TRUE -> yellow | UNVERIFIABLE -> gray | SATIRE -> gray

Rules:
- Keep the entire JSON response under 450 words.
- confidence_score must be an integer from 0 to 100, not a decimal.
- Use at most 3 items in each list.
- Use at most 3 top_sources.
- If agents cite sources that contradict their own conclusions, lower your confidence in their arguments.
"""


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _anthropic_client(*env_names: str) -> Any:
    if AsyncAnthropic is None:
        raise RuntimeError("Missing dependency: run `python3 -m pip install -r requirements.txt`.")

    for env_name in env_names:
        api_key = os.getenv(env_name)
        if api_key:
            return AsyncAnthropic(api_key=api_key)

    raise RuntimeError(
        "No Anthropic API key found. Set one of: " + ", ".join(env_names)
    )


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _gemini_client(*env_names: str) -> Any:
    if genai is None or genai_types is None:
        raise RuntimeError("Missing dependency: run `.venv/bin/python -m pip install google-genai`.")

    candidate_names = env_names or (
        "GEMINI_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
    )
    api_key = next((os.getenv(name) for name in candidate_names if os.getenv(name)), None)
    if not api_key:
        raise RuntimeError("No Gemini API key found. Set one of: " + ", ".join(candidate_names))

    # google-genai gives GOOGLE_API_KEY precedence over GEMINI_API_KEY, and a
    # shell can keep stale exports after .env changes. This project uses
    # GOOGLE_FACT_CHECK_API_KEY for Fact Check Tools, so shield Gemini from
    # GOOGLE_API_KEY entirely.
    os.environ.pop("GOOGLE_API_KEY", None)
    return genai.Client(api_key=api_key)


_GEMINI_SEARCH_RETRY_SECONDS = 3600
_GEMINI_MAX_BACKOFF_SECONDS = 45.0
_GEMINI_BACKOFF_RETRIES = 3
_gemini_search_disabled_until = 0.0


def _gemini_search_available() -> bool:
    return _env_bool("GEMINI_USE_GOOGLE_SEARCH", True) and time.time() >= _gemini_search_disabled_until


def _disable_gemini_search(exc: BaseException) -> None:
    # Search grounding has its own quota; free-tier keys reject it with 429
    # while plain generation still works. Stop retrying it for a while.
    global _gemini_search_disabled_until
    _gemini_search_disabled_until = time.time() + _GEMINI_SEARCH_RETRY_SECONDS
    print(
        "[TruthNet] WARNING: Gemini Google Search grounding is unavailable "
        f"({type(exc).__name__}: {str(exc)[:120]}). Agents will rely on the keyless "
        f"live search results instead. Retrying grounding in {_GEMINI_SEARCH_RETRY_SECONDS}s."
    )


def _is_gemini_overload_error(exc: BaseException) -> bool:
    exc_str = str(exc)
    return any(marker in exc_str for marker in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"))


def _gemini_retry_delay(exc: BaseException) -> float:
    """Seconds the API asked us to wait ("Please retry in 1m2.5s"), or a default."""
    match = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", str(exc))
    if not match or not any(match.groups()):
        return 7.0
    hours, minutes, seconds = (float(part) if part else 0.0 for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _gemini_api_key_names(env_names: Optional[List[str]]) -> List[str]:
    names = list(env_names or [])
    for fallback_name in ("GEMINI_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"):
        if fallback_name not in names:
            names.append(fallback_name)
    return names


def _extract_text_blocks(response: Any) -> str:
    return " ".join(
        block.text
        for block in getattr(response, "content", [])
        if hasattr(block, "text") and block.text
    ).strip()


def safe_parse_json(text: str) -> Dict[str, Any]:
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        match = re.search(r"\{[\s\S]*?\}", text)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from agent response: {text[:200]}")


async def _call_gemini_json(
    *,
    system_prompt: str,
    user_message: str,
    max_tokens: Optional[int] = None,
    api_key_env_names: Optional[List[str]] = None,
    use_google_search: bool = False,
    retries: int = 2,
) -> Dict[str, Any]:
    last_text = ""
    current_user_message = user_message
    key_names = _gemini_api_key_names(api_key_env_names)

    for key_index, key_name in enumerate(key_names):
        if not os.getenv(key_name):
            continue
        client = _gemini_client(key_name)

        try:
            return await _call_gemini_json_with_client(
                client=client,
                system_prompt=system_prompt,
                user_message=current_user_message,
                max_tokens=max_tokens,
                use_google_search=use_google_search,
                retries=retries,
            )
        except Exception as exc:
            if not any(os.getenv(name) for name in key_names[key_index + 1 :]):
                raise
            print(f"[TruthNet] Gemini key {key_name} failed ({type(exc).__name__}). Trying fallback key.")

    raise RuntimeError("No configured Gemini API key worked.")


async def _call_gemini_json_with_client(
    *,
    client: Any,
    system_prompt: str,
    user_message: str,
    max_tokens: Optional[int],
    use_google_search: bool,
    retries: int,
) -> Dict[str, Any]:
    last_text = ""
    current_user_message = user_message

    for attempt in range(retries + 1):
        search_enabled = use_google_search and _gemini_search_available()

        def generate(with_search: bool) -> Any:
            tools = (
                [genai_types.Tool(google_search=genai_types.GoogleSearch())]
                if with_search
                else None
            )
            config = genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0,
                max_output_tokens=max_tokens or _env_int("GEMINI_MAX_TOKENS", 800),
                response_mime_type="application/json",
                tools=tools,
            )
            return client.models.generate_content(
                model=GEMINI_MODEL,
                contents=current_user_message,
                config=config,
            )

        async def generate_with_backoff() -> Any:
            for backoff_attempt in range(_GEMINI_BACKOFF_RETRIES + 1):
                try:
                    return await asyncio.to_thread(generate, False)
                except Exception as exc:
                    if not _is_gemini_overload_error(exc) or backoff_attempt >= _GEMINI_BACKOFF_RETRIES:
                        raise
                    delay = _gemini_retry_delay(exc)
                    if delay > _GEMINI_MAX_BACKOFF_SECONDS:
                        # A long wait means the daily quota is gone; retrying cannot help.
                        raise RuntimeError(
                            f"Gemini quota for {GEMINI_MODEL} is exhausted; the API asks to retry in "
                            f"{delay / 60:.0f} minutes. Use another key or model, or wait for the quota to reset."
                        ) from exc
                    print(f"[TruthNet] Gemini rate limit/server load. Waiting {delay:.0f}s before retry...")
                    await asyncio.sleep(delay + 1.0)

        if search_enabled:
            try:
                response = await asyncio.to_thread(generate, True)
            except Exception as exc:
                _disable_gemini_search(exc)
                response = await generate_with_backoff()
        else:
            response = await generate_with_backoff()

        last_text = ""
        if hasattr(response, "candidates") and response.candidates:
            parts = getattr(response.candidates[0].content, "parts", []) or []
            for part in parts:
                p_text = getattr(part, "text", "") or ""
                if "{" in p_text and "}" in p_text:
                    last_text = p_text.strip()
                    break

        if not last_text:
            last_text = str(getattr(response, "text", "") or "").strip()
        if not last_text:
            raise ValueError("Gemini returned an empty response.")

        try:
            return safe_parse_json(last_text)
        except (json.JSONDecodeError, ValueError):
            if attempt >= retries:
                raise
            current_user_message = (
                f"{user_message}\n\n"
                "Your previous response was not valid JSON. Return only one complete "
                "valid JSON object matching the required schema. No markdown. No preamble."
            )

    raise ValueError(f"Could not parse JSON from Gemini response: {last_text[:200]}")


async def _call_agent_json(
    *,
    client: Any,
    system_prompt: str,
    user_message: str,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
    retries: int = 1,
) -> Dict[str, Any]:
    messages = [{"role": "user", "content": user_message}]
    last_text = ""
    primary_model = model or ANTHROPIC_MODEL
    models = [primary_model]
    if ANTHROPIC_FALLBACK_MODEL and ANTHROPIC_FALLBACK_MODEL not in models:
        models.append(ANTHROPIC_FALLBACK_MODEL)

    rate_limit_wait_seconds = _env_int("ANTHROPIC_RATE_LIMIT_WAIT_SECONDS", 20)
    rate_limit_retries = _env_int("ANTHROPIC_RATE_LIMIT_RETRIES", 1)

    for model in models:
        model_not_found = False
        for attempt in range(retries + 1):
            kwargs: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens or _env_int("ANTHROPIC_MAX_TOKENS", 1000),
                "temperature": 0,
                "system": system_prompt,
                "messages": messages,
            }
            if tools and "haiku" not in model.lower():
                kwargs["tools"] = tools

            response = None
            for rate_attempt in range(rate_limit_retries + 1):
                try:
                    response = await client.messages.create(**kwargs)
                    break
                except Exception as exc:
                    if _is_model_not_found_error(exc) and model != models[-1]:
                        print(f"[TruthNet] Model '{model}' is unavailable. Falling back to '{models[-1]}'.")
                        model_not_found = True
                        break
                    if _is_rate_limit_error(exc) and rate_attempt < rate_limit_retries:
                        print(
                            "[TruthNet] Anthropic rate limit hit. "
                            f"Waiting {rate_limit_wait_seconds}s before retry..."
                        )
                        await asyncio.sleep(rate_limit_wait_seconds)
                        continue
                    raise

            if model_not_found:
                break
            if response is None:
                continue

            last_text = _extract_text_blocks(response)
            if not last_text:
                raise ValueError(
                    f"Agent returned empty response. stop_reason={getattr(response, 'stop_reason', 'unknown')}"
                )

            try:
                return safe_parse_json(last_text)
            except (json.JSONDecodeError, ValueError):
                if attempt >= retries:
                    raise
                messages = [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": last_text[:4000]},
                    {
                        "role": "user",
                        "content": (
                            "The previous response was not valid JSON. Return only one valid "
                            "JSON object matching the required schema. No markdown. No preamble."
                        ),
                    },
                ]

    raise ValueError(f"Could not parse JSON from agent response: {last_text[:200]}")


def _is_model_not_found_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 404:
        return True
    return "not_found_error" in str(exc) and "model" in str(exc)


def _is_rate_limit_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True
    return "rate_limit_error" in str(exc) or "RateLimitError" in type(exc).__name__


def _core_claim(agent_a_output: Dict[str, Any]) -> str:
    claims = agent_a_output.get("core_claims", [])
    if isinstance(claims, str):
        claim_text = claims
    else:
        claim_text = " ".join(str(claim) for claim in claims if claim)
    return claim_text.strip() or str(agent_a_output.get("research_prompt", "")).strip()


def _truncate(value: Any, max_chars: int = 500) -> Any:
    if isinstance(value, str):
        return value if len(value) <= max_chars else value[: max_chars - 3].rstrip() + "..."
    if isinstance(value, list):
        return [_truncate(item, max_chars) for item in value[:3]]
    if isinstance(value, dict):
        return {key: _truncate(item, max_chars) for key, item in value.items()}
    return value


def _compact_agent_for_judge(agent_output: Dict[str, Any]) -> Dict[str, Any]:
    compact: Dict[str, Any] = {}
    for key in (
        "stance",
        "confidence",
        "summary",
        "key_evidence",
        "identified_manipulations",
        "missing_context",
    ):
        if key in agent_output:
            compact[key] = _truncate(agent_output[key], 500)
    return compact


def _normalize_verdict(result: Dict[str, Any]) -> Dict[str, Any]:
    score = result.get("confidence_score")
    if isinstance(score, float) and 0 <= score <= 1:
        result["confidence_score"] = round(score * 100)
    elif isinstance(score, (int, float)):
        result["confidence_score"] = max(0, min(100, round(score)))
    return result


async def _get_fact_checks(claim: str, *api_key_env_names: str) -> str:
    api_key = next((os.getenv(name) for name in api_key_env_names if os.getenv(name)), None)
    if not api_key:
        return "No Google Fact Check API key configured."

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": claim, "key": api_key}

    try:
        async with httpx.AsyncClient(timeout=4.0) as httpx_client:
            response = await httpx_client.get(url, params=params)
        if response.status_code != 200:
            return f"Google Fact Check API returned status {response.status_code}."

        data = response.json()
        claims = data.get("claims") or []
        if not claims:
            return "No existing fact-check articles found in Google database."

        results = []
        for item in claims[:3]:
            for review in item.get("claimReview", []):
                publisher = review.get("publisher", {}).get("name", "Unknown")
                rating = review.get("textualRating", "Unknown")
                source_url = review.get("url", "")
                results.append(
                    f"Publisher: {publisher} | Rating: {rating} | URL: {source_url}"
                )
        return "\n".join(results) if results else "No existing fact-check articles found in Google database."
    except httpx.TimeoutException:
        return "Google Fact Check API timed out."
    except Exception:
        return "Google Fact Check API error."


_LIVE_SEARCH_HEADERS = {"User-Agent": "TruthNet/2.0 (fact-checking research tool)"}
_LIVE_SEARCH_UNAVAILABLE = "Live search was unavailable; no current web results could be retrieved."
_LIVE_SEARCH_CACHE_SECONDS = 600
_live_search_cache: Dict[str, Any] = {}


async def _search_news(httpx_client: Any, query: str, limit: int = 6) -> List[str]:
    response = await httpx_client.get(
        "https://news.google.com/rss/search",
        params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
    )
    response.raise_for_status()
    results = []
    for item in ET.fromstring(response.text).iter("item"):
        title = html.unescape(item.findtext("title") or "").strip()
        if not title:
            continue
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "").date().isoformat()
        except (TypeError, ValueError):
            published = "unknown date"
        results.append(f"[{published}] {title} | {item.findtext('link') or ''}")
        if len(results) >= limit:
            break
    return results


async def _search_wikipedia(httpx_client: Any, query: str, limit: int = 2) -> List[str]:
    response = await httpx_client.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": limit,
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "exlimit": limit,
        },
    )
    response.raise_for_status()
    pages = (response.json().get("query") or {}).get("pages") or {}
    results = []
    for page in sorted(pages.values(), key=lambda page: page.get("index", 0)):
        extract = " ".join(str(page.get("extract") or "").split())
        if not extract:
            continue
        title = str(page.get("title", ""))
        url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
        results.append(f"Wikipedia - {title} | {url}\n{_truncate(extract, 1200)}")
    return results


async def _get_live_evidence(agent_a_output: Dict[str, Any]) -> str:
    """Keyless web retrieval so agents see current facts even without model-side search."""
    queries = []
    for value in (agent_a_output.get("original_claim"), agent_a_output.get("research_prompt"), _core_claim(agent_a_output)):
        query = " ".join(str(value or "").split())[:200]
        if query and query not in queries:
            queries.append(query)
    queries = queries[:2]
    if not queries:
        return _LIVE_SEARCH_UNAVAILABLE

    cache_key = "\n".join(queries)
    cached = _live_search_cache.get(cache_key)
    if cached and time.time() - cached[0] < _LIVE_SEARCH_CACHE_SECONDS:
        return cached[1]

    async with httpx.AsyncClient(
        timeout=6.0, headers=_LIVE_SEARCH_HEADERS, follow_redirects=True
    ) as httpx_client:
        searches = [_search_news(httpx_client, query) for query in queries]
        searches += [_search_wikipedia(httpx_client, query) for query in queries]
        batches = await asyncio.gather(*searches, return_exceptions=True)

    news: List[str] = []
    wiki: List[str] = []
    for index, batch in enumerate(batches):
        if isinstance(batch, BaseException):
            print(f"[TruthNet] Live search request failed ({type(batch).__name__}: {str(batch)[:120]}).")
            continue
        target = news if index < len(queries) else wiki
        target.extend(line for line in batch if line not in target)

    if not news and not wiki:
        return _LIVE_SEARCH_UNAVAILABLE

    sections = [f"Retrieved {date.today().isoformat()}."]
    if news:
        sections.append("Recent news headlines ([published date] headline - outlet | link):\n" + "\n".join(news[:10]))
    if wiki:
        sections.append("Encyclopedia excerpts:\n" + "\n\n".join(wiki[:3]))
    text = "\n\n".join(sections)
    _live_search_cache[cache_key] = (time.time(), text)
    return text


def _fact_check_evidence(fact_checks: str) -> List[Dict[str, Any]]:
    if not fact_checks or "No existing fact-check" in fact_checks:
        return []
    if "API key" in fact_checks or "timed out" in fact_checks or "error" in fact_checks:
        return []

    evidence = []
    for line in fact_checks.splitlines():
        if not line.strip():
            continue
        publisher = "Google Fact Check Tools"
        rating = "Unknown"
        source_url = ""
        for part in line.split("|"):
            label, _, value = part.strip().partition(":")
            if label == "Publisher":
                publisher = value.strip() or publisher
            elif label == "Rating":
                rating = value.strip() or rating
            elif label == "URL":
                source_url = value.strip()
        evidence.append(
            {
                "point": f"Existing fact-check result from {publisher}: {rating}",
                "source": source_url or publisher,
                "credibility": "high",
                "year": 2026,
            }
        )
    return evidence[:3]


def _normalize_research_agent_output(
    result: Dict[str, Any],
    *,
    fact_checks: str,
    agent: str,
) -> Dict[str, Any]:
    evidence = result.get("key_evidence")
    if not isinstance(evidence, list):
        evidence = []

    if not evidence:
        evidence = _fact_check_evidence(fact_checks)

    if not evidence:
        evidence = [
            {
                "point": "No direct pre-existing fact-check result was found; judgment should rely on the other agent and final synthesis.",
                "source": "Google Fact Check Tools",
                "credibility": "medium",
                "year": 2026,
            }
        ]

    result["key_evidence"] = evidence

    confidence = result.get("confidence", 0)
    if isinstance(confidence, (int, float)):
        if confidence > 1:
            confidence = confidence / 100
        if confidence <= 0 and evidence:
            confidence = 0.35
        result["confidence"] = round(max(0.0, min(1.0, float(confidence))), 2)
    else:
        result["confidence"] = 0.35

    if not result.get("summary"):
        role = "challenging" if agent == "b" else "supporting/contextualizing"
        result["summary"] = f"No decisive {role} result was found, but available source context was passed to the Judge."

    if agent == "b" and result.get("stance") not in {"DEBUNKS", "PARTIALLY_DEBUNKS", "INCONCLUSIVE"}:
        result["stance"] = "INCONCLUSIVE"
    if agent == "c" and result.get("stance") not in {"SUPPORTS", "PARTIALLY_SUPPORTS", "INCONCLUSIVE"}:
        result["stance"] = "INCONCLUSIVE"

    result.setdefault("identified_manipulations", [])
    result.setdefault("missing_context", [])
    return result


def _web_search_tools(model: Optional[str] = None) -> List[Dict[str, str]]:
    if os.getenv("ANTHROPIC_DISABLE_WEB_SEARCH", "").lower() in {"1", "true", "yes"}:
        return []
    active_model = model or ANTHROPIC_MODEL
    if "haiku" in active_model.lower():
        return []
    return [{"type": "web_search_20250305", "name": "web_search"}]


async def run_agent_a(user_input: str) -> Dict[str, Any]:
    if not user_input.strip():
        raise ValueError("user_input cannot be empty.")

    if AGENT_A_PROVIDER == "gemini":
        return await _call_gemini_json(
            system_prompt=AGENT_A_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
            user_message=user_input,
            max_tokens=_env_int("GEMINI_MAX_TOKENS", 800),
            api_key_env_names=["GEMINI_AGENT_A_API_KEY", "GEMINI_API_KEY"],
            retries=1,
        )

    client = _anthropic_client("ANTHROPIC_AGENT_A_API_KEY", "ANTHROPIC_API_KEY")
    return await _call_agent_json(
        client=client,
        system_prompt=AGENT_A_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
        user_message=user_input,
        model=ANTHROPIC_AGENT_A_MODEL,
        retries=1,
    )


async def get_fact_checks_prosecutor(claim: str) -> str:
    return await _get_fact_checks(claim, "GOOGLE_FACT_CHECK_API_KEY", "GOOGLE_API_KEY")


async def get_fact_checks_defender(claim: str) -> str:
    return await _get_fact_checks(claim, "GOOGLE_FACT_CHECK_API_KEY", "GOOGLE_API_KEY")


async def run_agent_b(agent_a_output: Dict[str, Any]) -> Dict[str, Any]:
    core_claim = _core_claim(agent_a_output)
    original_claim = str(agent_a_output.get("original_claim") or core_claim)
    research_prompt = str(agent_a_output.get("research_prompt") or core_claim)
    fact_checks, live_evidence = await asyncio.gather(
        get_fact_checks_prosecutor(core_claim),
        _get_live_evidence(agent_a_output),
    )

    user_message = (
        "Existing fact-check results from Google Fact Check Tools:\n"
        f"{fact_checks}\n\n"
        "LIVE SEARCH RESULTS (retrieved from the web today; newer than your training data):\n"
        f"{live_evidence}\n\n"
        f"ORIGINAL USER CLAIM (verbatim): {original_claim}\n\n"
        "Research and identify credible evidence that challenges this claim:\n"
        f"{research_prompt}\n\n"
        f"Core claims identified: {json.dumps(agent_a_output.get('core_claims', []))}\n"
        f"Named entities to focus on: {json.dumps(agent_a_output.get('named_entities', {}))}\n"
        f"Domain: {agent_a_output.get('domain', 'other')}\n\n"
        "Return ONLY valid JSON using the required schema."
    )

    if AGENT_B_PROVIDER == "gemini":
        result = await _call_gemini_json(
            system_prompt=AGENT_B_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
            user_message=user_message,
            max_tokens=_env_int("GEMINI_MAX_TOKENS", 800),
            api_key_env_names=["GEMINI_AGENT_B_API_KEY", "GEMINI_API_KEY"],
            use_google_search=True,
            retries=1,
        )
        return _normalize_research_agent_output(result, fact_checks=fact_checks, agent="b")

    client = _anthropic_client(
        "ANTHROPIC_AGENT_B_API_KEY",
        "ANTHROPIC_AGENT_BC_API_KEY",
        "ANTHROPIC_API_KEY",
    )
    result = await _call_agent_json(
        client=client,
        system_prompt=AGENT_B_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
        user_message=user_message,
        tools=_web_search_tools(ANTHROPIC_AGENT_B_MODEL),
        model=ANTHROPIC_AGENT_B_MODEL,
        retries=1,
    )
    return _normalize_research_agent_output(result, fact_checks=fact_checks, agent="b")


async def run_agent_c(agent_a_output: Dict[str, Any]) -> Dict[str, Any]:
    core_claim = _core_claim(agent_a_output)
    original_claim = str(agent_a_output.get("original_claim") or core_claim)
    research_prompt = str(agent_a_output.get("research_prompt") or core_claim)
    fact_checks, live_evidence = await asyncio.gather(
        get_fact_checks_defender(core_claim),
        _get_live_evidence(agent_a_output),
    )

    user_message = (
        "Existing fact-check results from Google Fact Check Tools:\n"
        f"{fact_checks}\n\n"
        "LIVE SEARCH RESULTS (retrieved from the web today; newer than your training data):\n"
        f"{live_evidence}\n\n"
        f"ORIGINAL USER CLAIM (verbatim): {original_claim}\n\n"
        "Research and identify credible evidence that supports or contextualizes this claim:\n"
        f"{research_prompt}\n\n"
        f"Core claims identified: {json.dumps(agent_a_output.get('core_claims', []))}\n"
        f"Named entities to focus on: {json.dumps(agent_a_output.get('named_entities', {}))}\n"
        f"Domain: {agent_a_output.get('domain', 'other')}\n\n"
        "Return ONLY valid JSON using the required schema."
    )

    if AGENT_C_PROVIDER == "gemini":
        result = await _call_gemini_json(
            system_prompt=AGENT_C_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
            user_message=user_message,
            max_tokens=_env_int("GEMINI_MAX_TOKENS", 800),
            api_key_env_names=["GEMINI_AGENT_C_API_KEY", "GEMINI_API_KEY"],
            use_google_search=True,
            retries=1,
        )
        return _normalize_research_agent_output(result, fact_checks=fact_checks, agent="c")

    client = _anthropic_client(
        "ANTHROPIC_AGENT_C_API_KEY",
        "ANTHROPIC_AGENT_BC_API_KEY",
        "ANTHROPIC_API_KEY",
    )
    result = await _call_agent_json(
        client=client,
        system_prompt=AGENT_C_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
        user_message=user_message,
        tools=_web_search_tools(ANTHROPIC_AGENT_C_MODEL),
        model=ANTHROPIC_AGENT_C_MODEL,
        retries=1,
    )
    return _normalize_research_agent_output(result, fact_checks=fact_checks, agent="c")


async def run_agent_d(
    user_input: str,
    agent_a: Dict[str, Any],
    agent_b: Dict[str, Any],
    agent_c: Dict[str, Any],
) -> Dict[str, Any]:
    payload = {
        "original_user_claim": user_input,
        "agent_a": _truncate(agent_a, 600),
        "agent_b": _compact_agent_for_judge(agent_b),
        "agent_c": _compact_agent_for_judge(agent_c),
        "live_search_results": await _get_live_evidence({**agent_a, "original_claim": agent_a.get("original_claim") or user_input}),
    }

    user_message = json.dumps(payload, ensure_ascii=False, indent=2)
    if AGENT_D_PROVIDER == "gemini":
        result = await _call_gemini_json(
            system_prompt=AGENT_D_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
            user_message=user_message,
            max_tokens=_env_int("GEMINI_AGENT_D_MAX_TOKENS", 1400),
            api_key_env_names=["GEMINI_AGENT_D_API_KEY", "GEMINI_API_KEY"],
            retries=1,
        )
    else:
        client = _anthropic_client("ANTHROPIC_AGENT_D_API_KEY", "ANTHROPIC_API_KEY")
        result = await _call_agent_json(
            client=client,
            system_prompt=AGENT_D_SYSTEM_PROMPT.replace("{today}", date.today().isoformat()),
            user_message=user_message,
            max_tokens=_env_int("ANTHROPIC_AGENT_D_MAX_TOKENS", 1200),
            model=ANTHROPIC_AGENT_D_MODEL,
            retries=1,
        )
    return _normalize_verdict(result)


def fallback_agent_b(error: BaseException) -> Dict[str, Any]:
    return {
        "stance": "INCONCLUSIVE",
        "confidence": 0.0,
        "key_evidence": [],
        "identified_manipulations": [],
        "missing_context": ["Agent B failed before completing research."],
        "summary": f"Prosecutor search failed: {type(error).__name__}",
    }


def fallback_agent_c(error: BaseException) -> Dict[str, Any]:
    return {
        "stance": "INCONCLUSIVE",
        "confidence": 0.0,
        "key_evidence": [],
        "identified_manipulations": [],
        "missing_context": ["Agent C failed before completing research."],
        "summary": f"Defender search failed: {type(error).__name__}",
    }
