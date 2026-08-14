#!/usr/bin/env python3
"""
orx - OpenRouter eXchange.

A dependency-free bridge that turns an OpenRouter model into a council member
that reads and writes the same .ai/ files as Claude Code.

Usage
-----
  # one-shot question, printed to stdout
  ./scripts/orx.py ask "Is Apache Beam justified for a note-taking app?"

  # role-based analysis over repo files, written to an .ai/ artifact
  ./scripts/orx.py run --role critic \
      --context .ai/requirements.md .ai/architecture-claude.md \
      --out .ai/review-openrouter.md

  # interactive terminal chat, @path injects a file
  ./scripts/orx.py chat

  # see exactly what would be sent, spend nothing
  ./scripts/orx.py run --role critic --context .ai/*.md --dry-run

Env
---
  OPENROUTER_API_KEY   required
  ORX_MODEL            default model slug (default: deepseek/deepseek-v4-flash-0731)
  ORX_EFFORT           reasoning effort: low|medium|high|xhigh (default: high)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("ORX_MODEL", "deepseek/deepseek-v4-flash-0731")
DEFAULT_EFFORT = os.environ.get("ORX_EFFORT", "high")
MAX_CONTEXT_CHARS = 400_000  # ~100k tokens; V4 Flash holds 1M but keep runs cheap

# --------------------------------------------------------------------------
# Roles. Each role is a system prompt. Add your own freely.
# --------------------------------------------------------------------------
ROLES: dict[str, str] = {
    "critic": """You are the SKEPTICAL REVIEWER on a four-member engineering council.
The other members are strong models that tend to agree with each other. Your job is
to be the one who does not.

Assume every proposal you are shown is wrong in at least two important ways. Hunt for:
  - security holes, especially data leaking across tenant/project boundaries
  - requirements that were silently dropped or reinterpreted
  - accidental complexity: tools chosen for resume value rather than need
  - scalability and cost claims asserted without numbers
  - failure modes nobody handled (partial writes, retries, poison messages, cold starts)

Rules:
  - Be specific. Cite file paths, function names, table names, line numbers.
  - Rank findings: BLOCKER / MAJOR / MINOR. A BLOCKER means "do not merge".
  - For each finding give the cheapest fix, not the most elegant one.
  - If a proposal is genuinely sound, say so plainly in one line and move on.
    Do not manufacture objections to look useful.
  - No praise, no preamble, no summary of what you were asked. Findings only.

Output format:
## Verdict
<one line: SHIP / SHIP WITH FIXES / DO NOT SHIP>

## Findings
### [BLOCKER|MAJOR|MINOR] <short title>
**Where:** <file/table/function>
**Problem:** <2-3 sentences>
**Cheapest fix:** <1-2 sentences>

## Requirements possibly dropped
- <bullet, or "none found">

## Questions the council must answer before implementing
- <bullet>""",
    "architect": """You are a SENIOR ARCHITECT working independently. You have been given
requirements and (possibly) another engineer's proposal.

Do not defer to the other proposal. Solve the problem yourself first, then compare.
Optimize for: fewest moving parts, boring proven technology, ease of debugging at 3am.

Output format:
## My design
<prose + ASCII diagram if useful>
## Data model changes
## Failure modes and how this design handles them
## Where I disagree with the other proposal
- **Their choice:** ... **My objection:** ... **My alternative:** ...
## What I would cut from the scope entirely""",
    "reviewer": """You are a CODE REVIEWER. You are shown a diff or a set of files plus the
plan they were supposed to implement.

Your only question: does this code do what the plan says, correctly and safely?

Check in this order:
  1. Does it implement the plan's acceptance criteria? Name any criterion not met.
  2. Correctness bugs: off-by-one, unhandled None/null, wrong await, swallowed errors.
  3. Data isolation: can data from project A ever reach a query scoped to project B?
  4. Missing tests for the paths you just flagged.
  5. Style, last and briefly.

Output format:
## Plan compliance
- [x] criterion met
- [ ] criterion NOT met - <why>
## Bugs
### [BLOCKER|MAJOR|MINOR] <title> - <file:line>
<problem> -> <fix>
## Missing tests
## Verdict
APPROVE / REQUEST CHANGES""",
    "synthesizer": """You are the TECHNICAL LEAD and final decision maker. You are shown
competing proposals, critiques, and disagreements.

Your job is to DECIDE, not to summarize. For every disagreement, pick a side and state
why in one sentence. Prefer the simpler option unless there is a concrete, named reason
not to. Ties go to whatever is easier to delete later.

Output format:
## Decisions
| # | Question | Decision | Why | Rejected alternative |
## Authoritative plan
<numbered phases, each with acceptance criteria that a test could check>
## Explicitly out of scope
## Open risks accepted
""",
    "raw": "",
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def load_dotenv() -> None:
    """Load .env from cwd or repo root, without overwriting real env vars."""
    for candidate in (Path(".env"), Path(__file__).resolve().parent.parent / ".env"):
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        return


def die(message: str, code: int = 1) -> None:
    print(f"orx: {message}", file=sys.stderr)
    sys.exit(code)


def read_context(paths: list[str]) -> str:
    """Concatenate files with clear delimiters so the model can cite them."""
    chunks: list[str] = []
    total = 0
    for raw in paths:
        p = Path(raw)
        if not p.is_file():
            print(f"orx: skipping missing file {p}", file=sys.stderr)
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"orx: cannot read {p}: {exc}", file=sys.stderr)
            continue
        total += len(body)
        if total > MAX_CONTEXT_CHARS:
            print(
                f"orx: context budget hit at {p}; truncating. "
                f"Pass fewer files or raise MAX_CONTEXT_CHARS.",
                file=sys.stderr,
            )
            body = body[: max(0, MAX_CONTEXT_CHARS - (total - len(body)))]
            chunks.append(f"===== FILE: {p} (TRUNCATED) =====\n{body}")
            break
        chunks.append(f"===== FILE: {p} =====\n{body}")
    return "\n\n".join(chunks)


def call_openrouter(
    messages: list[dict],
    model: str,
    effort: str,
    stream: bool = False,
    timeout: int = 900,
    retries: int = 4,
):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        die("OPENROUTER_API_KEY is not set. Put it in .env or export it.")

    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "usage": {"include": True},
    }
    if effort and effort != "off":
        # V4-family models accept reasoning effort up to xhigh.
        payload["reasoning"] = {"enabled": True, "effort": effort}

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-Title": "orx-council",
    }

    last_error: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:600]
            # 429 and 5xx are worth retrying; 4xx otherwise is our fault.
            if exc.code in (408, 429, 500, 502, 503, 504) and attempt < retries - 1:
                wait = 2 ** attempt * 3
                print(
                    f"orx: HTTP {exc.code}, retry {attempt + 1}/{retries - 1} in {wait}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
                last_error = exc
                continue
            die(f"HTTP {exc.code} from OpenRouter: {detail}")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries - 1:
                wait = 2 ** attempt * 3
                print(f"orx: {exc}; retry in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
    die(f"all retries failed: {last_error}")


def complete(messages: list[dict], model: str, effort: str) -> tuple[str, dict]:
    """Non-streaming completion. Returns (text, usage)."""
    resp = call_openrouter(messages, model, effort, stream=False)
    data = json.loads(resp.read().decode("utf-8"))
    if "error" in data and data["error"]:
        die(f"OpenRouter error: {data['error']}")
    try:
        text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        die(f"unexpected response shape: {json.dumps(data)[:600]}")
    return text, data.get("usage", {}) or {}


def stream_print(messages: list[dict], model: str, effort: str) -> tuple[str, dict]:
    """Streaming completion, printed as it arrives. Returns (text, usage)."""
    resp = call_openrouter(messages, model, effort, stream=True)
    collected: list[str] = []
    usage: dict = {}
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if chunk in ("", "[DONE]"):
            continue
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if obj.get("usage"):
            usage = obj["usage"]
        for choice in obj.get("choices") or []:
            piece = (choice.get("delta") or {}).get("content")
            if piece:
                collected.append(piece)
                sys.stdout.write(piece)
                sys.stdout.flush()
    sys.stdout.write("\n")
    return "".join(collected), usage


def report_usage(usage: dict, model: str) -> None:
    if not usage:
        return
    cost = usage.get("cost")
    cost_str = f" | cost ${cost:.4f}" if isinstance(cost, (int, float)) else ""
    print(
        f"orx: {model} | in {usage.get('prompt_tokens', '?')} tok "
        f"| out {usage.get('completion_tokens', '?')} tok{cost_str}",
        file=sys.stderr,
    )


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_run(args: argparse.Namespace) -> None:
    if args.role not in ROLES:
        die(f"unknown role '{args.role}'. Available: {', '.join(ROLES)}")
    system = ROLES[args.role]
    if args.system_file:
        system = Path(args.system_file).read_text(encoding="utf-8")

    context = read_context(args.context or [])
    task = args.task or "Perform your role on the material below."
    user = task if not context else f"{task}\n\n--- MATERIAL ---\n\n{context}"

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})

    if args.dry_run:
        print(f"--- model: {args.model} | effort: {args.effort} ---")
        for m in messages:
            print(f"\n[{m['role']}] ({len(m['content'])} chars)\n{m['content'][:2000]}")
        print(f"\n--- total {sum(len(m['content']) for m in messages)} chars ---")
        return

    if args.out:
        text, usage = complete(messages, args.model, args.effort)
    else:
        text, usage = stream_print(messages, args.model, args.effort)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        header = (
            f"<!-- generated by orx.py | role={args.role} | model={args.model} "
            f"| {stamp} -->\n"
            f"# OpenRouter {args.role} report\n\n"
            f"*Model: `{args.model}` | Effort: {args.effort} | {stamp}*\n\n"
            f"**Inputs reviewed:** {', '.join(args.context or ['(none)'])}\n\n---\n\n"
        )
        out.write_text(header + text.strip() + "\n", encoding="utf-8")
        print(f"orx: wrote {out} ({len(text)} chars)", file=sys.stderr)

    report_usage(usage, args.model)


def cmd_ask(args: argparse.Namespace) -> None:
    messages = [{"role": "user", "content": " ".join(args.words)}]
    _, usage = stream_print(messages, args.model, args.effort)
    report_usage(usage, args.model)


def cmd_chat(args: argparse.Namespace) -> None:
    system = ROLES.get(args.role, "")
    history: list[dict] = [{"role": "system", "content": system}] if system else []
    print(f"orx chat | model={args.model} | role={args.role or 'raw'}")
    print("  @path/to/file  inject a file      /reset  clear history")
    print("  /role <name>   switch role        /quit   exit\n")
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line in ("/quit", "/exit"):
            return
        if line == "/reset":
            history = [{"role": "system", "content": system}] if system else []
            print("orx: history cleared")
            continue
        if line.startswith("/role "):
            name = line.split(maxsplit=1)[1].strip()
            if name not in ROLES:
                print(f"orx: unknown role. Available: {', '.join(ROLES)}")
                continue
            system = ROLES[name]
            history = [{"role": "system", "content": system}] if system else []
            print(f"orx: role -> {name} (history cleared)")
            continue

        # @file injection, anywhere in the line
        words, files = [], []
        for word in line.split():
            if word.startswith("@") and len(word) > 1:
                files.append(word[1:])
            else:
                words.append(word)
        content = " ".join(words) or "Review the attached material."
        if files:
            content += "\n\n" + read_context(files)

        history.append({"role": "user", "content": content})
        print("\nor> ", end="")
        text, usage = stream_print(history, args.model, args.effort)
        history.append({"role": "assistant", "content": text})
        report_usage(usage, args.model)
        print()


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="orx", description="OpenRouter council member bridge"
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"default {DEFAULT_MODEL}")
    parser.add_argument(
        "--effort",
        default=DEFAULT_EFFORT,
        choices=["off", "low", "medium", "high", "xhigh"],
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="role-based analysis over files")
    p_run.add_argument("--role", default="critic", help=f"one of: {', '.join(ROLES)}")
    p_run.add_argument("--system-file", help="override the role prompt with a file")
    p_run.add_argument("--task", help="the specific instruction for this run")
    p_run.add_argument("--context", nargs="*", help="files to include")
    p_run.add_argument("--out", help="write markdown here instead of stdout")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_ask = sub.add_parser("ask", help="one-shot question")
    p_ask.add_argument("words", nargs="+")
    p_ask.set_defaults(func=cmd_ask)

    p_chat = sub.add_parser("chat", help="interactive terminal chat")
    p_chat.add_argument("--role", default="", help=f"one of: {', '.join(ROLES)}")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
