"""Run the eval suite against the real model and the local DB.

Usage: uv run python -m evals.run [--runs 3] [--category X] [--concurrency 4] [--label before]
"""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from app.agent.openai_client import openai_client_from_settings
from app.config import get_settings
from app.db.engine import get_engine
from evals.case_model import Case, load_cases
from evals.grade import grade
from evals.graders.judge import Judge
from evals.harness import run_case
from evals.report import summarize, table
from evals.transcript import CaseRun
from scripts.seed_menu import load_menu

RESULTS_DIR = Path(__file__).resolve().parent / "results"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "db"}


async def main(args: argparse.Namespace) -> None:
    settings = get_settings()
    host = urlsplit(settings.database_url).hostname
    if host not in LOCAL_HOSTS:
        raise SystemExit(f"Refusing to run evals against a non-local database ({host}).")
    cases = [c for c in load_cases() if args.category in (None, c.category)]
    llm = openai_client_from_settings(settings)
    judge = Judge(llm)
    prices = [item.price_sar for item in load_menu()]
    limit = asyncio.Semaphore(args.concurrency)

    async def one(slot: int, case: Case, run: int) -> CaseRun:
        async with limit:
            result = await run_case(case, slot, run, llm, settings.turn_deadline_seconds)
            result.checks = await grade(case, result, prices, judge)
        print(f"{'pass' if result.passed else 'FAIL'}  {case.id} run {run}", flush=True)
        return result

    jobs = [one(slot, c, run) for slot, c in enumerate(cases) for run in range(1, args.runs + 1)]
    results = await asyncio.gather(*jobs)
    await get_engine().dispose()
    rows = summarize(results)
    started = datetime.now(UTC)
    name = f"{started:%Y-%m-%d}-{settings.openai_model}" + (f"-{args.label}" if args.label else "")
    out = RESULTS_DIR / f"{name}.json"
    out.write_text(
        json.dumps(
            {
                "model": settings.openai_model,
                "date": started.isoformat(timespec="seconds"),
                "label": args.label,
                "runs_per_case": args.runs,
                "case_count": len(cases),
                "summary": [row.model_dump() for row in rows],
                "results": [r.model_dump(mode="json") for r in results],
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"\n{table(rows)}\n\nmodel {settings.openai_model}, {args.runs} runs, wrote {out.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--category")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--label")
    asyncio.run(main(parser.parse_args()))
