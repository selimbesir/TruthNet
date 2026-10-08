from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Tuple

logger = logging.getLogger("truthnet.pipeline")

AgentA = Callable[[str], Awaitable[Dict[str, Any]]]
AgentB = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
AgentC = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
AgentD = Callable[[str, Dict[str, Any], Dict[str, Any], Dict[str, Any]], Awaitable[Dict[str, Any]]]
Fallback = Callable[[BaseException], Dict[str, Any]]
RunnerBundle = Tuple[AgentA, AgentB, AgentC, AgentD, Fallback, Fallback]

TIMEOUT_A_SECONDS = float(os.getenv("TRUTHNET_TIMEOUT_A", "15"))
TIMEOUT_BC_SECONDS = float(os.getenv("TRUTHNET_TIMEOUT_BC", "30"))
TIMEOUT_D_SECONDS = float(os.getenv("TRUTHNET_TIMEOUT_D", "60"))

DEMO_CLAIMS = [
    "Studies show that 5G towers were proven to spread COVID-19 by activating viral particles in the human bloodstream.",
    "Screen time in children has doubled since 2020 and experts say it is causing an epidemic of ADHD diagnoses worldwide.",
    "Turkey is one of the top 5 countries in the world for social media usage per capita.",
]

EXPECTED_STATUS_SEQUENCE = [
    "agent_a_running",
    "agent_a_done",
    "agents_bc_running",
    "agents_bc_done",
    "agent_d_running",
    "agent_d_done",
    "result",
]


def is_mock_mode() -> bool:
    return os.getenv("TRUTHNET_MOCK", "").strip().lower() in {"1", "true", "yes", "on"}


def using_mock_agents() -> bool:
    return is_mock_mode() or os.getenv("TRUTHNET_USING_MOCK", "").strip() == "1"


def _fallback_agent_b(error: BaseException) -> Dict[str, Any]:
    return {
        "stance": "INCONCLUSIVE",
        "confidence": 0.0,
        "key_evidence": [],
        "identified_manipulations": [],
        "missing_context": ["Agent B failed before completing research."],
        "summary": f"Prosecutor search failed: {type(error).__name__}",
    }


def _fallback_agent_c(error: BaseException) -> Dict[str, Any]:
    return {
        "stance": "INCONCLUSIVE",
        "confidence": 0.0,
        "key_evidence": [],
        "identified_manipulations": [],
        "missing_context": ["Agent C failed before completing research."],
        "summary": f"Defender search failed: {type(error).__name__}",
    }


def _load_agent_runners() -> RunnerBundle:
    if is_mock_mode():
        try:
            from .agents_mock import run_agent_a, run_agent_b, run_agent_c, run_agent_d
        except ImportError:  # Allows direct execution from backend/.
            from agents_mock import run_agent_a, run_agent_b, run_agent_c, run_agent_d  # type: ignore

        os.environ["TRUTHNET_USING_MOCK"] = "1"
        logger.warning("TRUTHNET_MOCK is enabled; using mock agents.")
        return (
            run_agent_a,
            run_agent_b,
            run_agent_c,
            run_agent_d,
            _fallback_agent_b,
            _fallback_agent_c,
        )

    try:
        from .agents import (
            fallback_agent_b,
            fallback_agent_c,
            run_agent_a,
            run_agent_b,
            run_agent_c,
            run_agent_d,
        )
    except ImportError:  # Allows direct execution from backend/.
        from agents import (  # type: ignore
            fallback_agent_b,
            fallback_agent_c,
            run_agent_a,
            run_agent_b,
            run_agent_c,
            run_agent_d,
        )

    os.environ.pop("TRUTHNET_USING_MOCK", None)
    return run_agent_a, run_agent_b, run_agent_c, run_agent_d, fallback_agent_b, fallback_agent_c


async def _run_with_timeout(coro: Awaitable[Dict[str, Any]], seconds: float, stage: str) -> Dict[str, Any]:
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError as exc:
        raise TimeoutError(f"{stage} timed out after {seconds:.0f}s.") from exc


async def _run_research_pair(
    run_agent_b: AgentB,
    run_agent_c: AgentC,
    agent_a: Dict[str, Any],
) -> Tuple[Any, Any]:
    try:
        return await asyncio.wait_for(
            asyncio.gather(run_agent_b(agent_a), run_agent_c(agent_a), return_exceptions=True),
            timeout=TIMEOUT_BC_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise TimeoutError(f"Agents B & C timed out after {TIMEOUT_BC_SECONDS:.0f}s.") from exc


def _sse_data(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def run_pipeline(user_input: str) -> Dict[str, Any]:
    run_agent_a, run_agent_b, run_agent_c, run_agent_d, fallback_agent_b, fallback_agent_c = (
        _load_agent_runners()
    )

    agent_a = await _run_with_timeout(
        run_agent_a(user_input),
        TIMEOUT_A_SECONDS,
        "Agent A",
    )

    agent_b_result, agent_c_result = await _run_research_pair(run_agent_b, run_agent_c, agent_a)

    if isinstance(agent_b_result, BaseException):
        agent_b = fallback_agent_b(agent_b_result)
    else:
        agent_b = agent_b_result

    if isinstance(agent_c_result, BaseException):
        agent_c = fallback_agent_c(agent_c_result)
    else:
        agent_c = agent_c_result

    return await _run_with_timeout(
        run_agent_d(user_input, agent_a, agent_b, agent_c),
        TIMEOUT_D_SECONDS,
        "Agent D",
    )


async def run_pipeline_events(user_input: str) -> AsyncIterator[Dict[str, Any]]:
    run_agent_a, run_agent_b, run_agent_c, run_agent_d, fallback_agent_b, fallback_agent_c = (
        _load_agent_runners()
    )
    pipeline_start = time.perf_counter()

    yield {"event": "agent_a_running", "data": {"status": "running"}}
    agent_a = await _run_with_timeout(
        run_agent_a(user_input),
        TIMEOUT_A_SECONDS,
        "Agent A",
    )
    yield {"event": "agent_a_done", "data": {"status": "done", "agent_a": agent_a}}

    yield {"event": "agents_bc_running", "data": {"status": "running"}}
    agent_b_result, agent_c_result = await _run_research_pair(run_agent_b, run_agent_c, agent_a)

    if isinstance(agent_b_result, BaseException):
        agent_b = fallback_agent_b(agent_b_result)
    else:
        agent_b = agent_b_result

    if isinstance(agent_c_result, BaseException):
        agent_c = fallback_agent_c(agent_c_result)
    else:
        agent_c = agent_c_result

    yield {
        "event": "agents_bc_done",
        "data": {"status": "done", "agent_b": agent_b, "agent_c": agent_c},
    }

    yield {"event": "agent_d_running", "data": {"status": "running"}}
    verdict = await _run_with_timeout(
        run_agent_d(user_input, agent_a, agent_b, agent_c),
        TIMEOUT_D_SECONDS,
        "Agent D",
    )
    yield {"event": "agent_d_done", "data": {"status": "done"}}
    yield {
        "event": "verdict",
        "data": {
            **verdict,
            "pipeline_seconds": round(time.perf_counter() - pipeline_start, 2),
            "mock_mode": using_mock_agents(),
        },
    }


async def stream_pipeline(user_input: str) -> AsyncIterator[str]:
    """POST-friendly SSE stream used by the React backend contract."""
    try:
        async for item in run_pipeline_events(user_input):
            event = item["event"]
            data = item["data"]

            if event == "verdict":
                yield _sse_data({"status": "result", "result": data})
            elif event == "agent_a_done":
                agent_a = data.get("agent_a", {})
                yield _sse_data(
                    {
                        "status": event,
                        "data": {
                            "domain": agent_a.get("domain"),
                            "core_claims": agent_a.get("core_claims", []),
                            "original_tone": agent_a.get("original_tone"),
                        },
                    }
                )
            elif event == "agents_bc_done":
                yield _sse_data({"status": event, "data": data})
            else:
                yield _sse_data({"status": event})
    except Exception as exc:
        logger.exception("Pipeline stream failed.")
        yield _sse_data({"status": "error", "message": str(exc)})
