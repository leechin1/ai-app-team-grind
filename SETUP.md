# Notiq council — setup and run guide

Four members, one repo, shared files, no chat-between-agents.

| Member | Runs as | Role |
|---|---|---|
| Lead architect | Claude Code main session, Opus | designs, runs the debate, owns disagreements |
| Implementation engineer | `implementer` subagent, Sonnet | writes code, one task at a time |
| Skeptical reviewer | DeepSeek via `scripts/orx.py`, reached through the `or-liaison` subagent | attacks everything |
| Decision maker | final synthesis pass (Fable if you have it, else Opus) | resolves and decides |

The design principle from your orchestration notes, made concrete: **no agent ever
receives another agent's conversation.** They read and write files in `.ai/`. The
only thing that crosses a boundary is a markdown artifact.

---

## Step 1 — Drop the scaffold in and branch

From your Notiq repo root:

```bash
git switch -c council/setup
cp -r /path/to/council/. .
cat .gitignore.append >> .gitignore && rm .gitignore.append
cp .env.example .env         # then edit .env, put your real OpenRouter key in
chmod +x scripts/*.py scripts/*.sh .claude/hooks/*.py
```

Verify `.env` is ignored before you commit anything: `git check-ignore -v .env`.
If that prints nothing, stop and fix the gitignore.

## Step 2 — Prove the OpenRouter bridge works

This is the piece most likely to fail silently at 3am, so test it while awake.

```bash
./scripts/orx.py ask "reply with exactly: ok"
```

Expect `ok` plus a token/cost line on stderr. If it fails, the error is real —
usually a bad key or a stale model slug. Confirm the current slug on
<https://openrouter.ai/deepseek>; model names move faster than any doc.

Then try the actual reviewer role against a real file, with `--dry-run` first so
you can see what gets sent before you pay for it:

```bash
./scripts/orx.py run --role critic --context .ai/requirements.md \
  --task "Which of these requirements is underspecified?" --dry-run

./scripts/orx.py run --role critic --context .ai/requirements.md \
  --task "Which of these requirements is underspecified?"
```

Read that output carefully. It is your first real signal about whether DeepSeek is
a useful council member for this codebase or just noise. If it is noise, switch
`ORX_MODEL` to `deepseek/deepseek-v4-pro` and compare — the Pro model reasons
noticeably harder, and at roughly $0.44/$0.87 per million tokens it is still
almost free next to Opus.

**Your OpenRouter interface, in order of effort:**
- terminal one-shot: `./scripts/orx.py ask "..."` — already works
- terminal chat with file injection: `./scripts/orx.py chat --role critic`, then
  `@src/rag.ts what's wrong with this retrieval query?` — already works
- anything fancier: skip it. The council members don't need a UI, and neither do
  you if the reports land in `.ai/` where you read them anyway.

## Step 3 — Edit the requirements, then leave them alone

`.ai/requirements.md` is your Portuguese change list turned into testable
requirements. Read it now and fix anything I got wrong about Notiq — especially:

- the real list of upload formats
- whether the `projects` table is actually called that
- whether "project" and "note" are the same concept in your schema

Two things I deliberately changed from your original list, and you should decide
whether you agree:

1. **R5 (Spark / Beam / LangChain) is a preference, not a mandate**, and the critic
   is explicitly instructed to challenge any distributed data-processing choice
   against your real document volume. If Notiq ingests tens of documents a day,
   Beam is a liability, not an achievement — a second runtime to deploy, monitor,
   and debug for work a background job does in twenty lines. FastAPI and LangChain
   are far easier to justify. I would rather the council tell you that out loud
   than quietly adopt Beam because the requirements implied it.
2. **R2 has a leakage test as a hard acceptance criterion.** Project-scoped RAG
   where the scoping is a `WHERE` clause someone might forget is one refactor away
   from serving another user's study notes. The `pre_write_guard.py` hook now
   blocks any file that queries `embeddings` without mentioning `project_id`.

After this step, treat the file as frozen. The hook enforces that agents can't
edit it; the discipline of not editing it yourself mid-run is on you.

## Step 4 — Restart Claude Code, confirm it loaded everything

Subagents in `.claude/agents/` are read **at startup only**, so a running session
won't see them.

```bash
claude
```

Then inside the session:

```
/agents          # expect: implementer, or-liaison, plan-auditor
/hooks           # expect: PreToolUse, PostToolUse, Stop
/permissions     # confirm the deny rules on .env are live
```

If a hook doesn't appear, the usual causes are: not executable, wrong settings
file, or a matcher typo (matchers are case-sensitive — `Write`, not `write`).

Sanity-test the guard before trusting it overnight. Ask Claude to write a throwaway
file containing `select * from embeddings`. It should be blocked and told why.
A guard you haven't seen fire is a guard you don't have.

## Step 5 — Enable auto mode (this is your "no permissions every 5 seconds")

`auto` is the mode you want, not `--dangerously-skip-permissions`. It runs every
tool call past a separate classifier that blocks destructive and exfiltrating
actions, and it nudges Claude to keep working rather than stopping to ask
questions. As of today it's generally available and, on Pro/Max/Team, becoming the
default for new sessions.

Set it in your **user** settings — `~/.claude/settings.json`, not the project file.
Claude Code deliberately ignores `defaultMode: "auto"` from a repo's
`.claude/settings.json` so that a checked-in repo can't grant itself autonomy:

```json
{ "permissions": { "defaultMode": "auto" } }
```

Two things worth knowing before you leave it running:

- In a non-interactive `-p` run there is no prompt to fall back to, so when the
  classifier blocks something repeatedly the action just doesn't happen and Claude
  keeps going. Good for not hanging; means you must read the logs in the morning.
- Boundaries you state in conversation are enforced. Saying "don't push to remote"
  makes the classifier block pushes even where its defaults would allow them.

Use `bypassPermissions` only inside a container or VM. On your own machine with
Supabase credentials in reach, it's the wrong trade.

## Step 6 — Run the planning phase

Interactive first, so you can watch the debate happen:

```
/council-plan
```

This runs Round 0 (verify the repo against the requirements), Round 1 (your Opus
design and DeepSeek's independent design, in parallel, plus DeepSeek's critique of
yours), Round 2 (your rebuttal, then DeepSeek's rebuttal of your rebuttal), and
Round 3 (synthesis into `decisions.md`, `plan.md`, `todos.md`).

Headless equivalent, if you'd rather it ran while you cook dinner:

```bash
./scripts/run_overnight.sh plan
```

**Optional: use a real agent team for Round 1.** Agent teams are enabled in the
project settings (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) and give you teammates
that can message each other directly, rather than subagents that only report back
to the lead. For Round 1 that's a genuine upgrade, because the debate is the point:

```
Spawn two teammates using the agent team feature. One using the implementer agent
type to design the ingestion pipeline, one to design the retrieval and RAG layer.
Have them challenge each other's assumptions directly before either writes to .ai/.
Use Sonnet for both. Require plan approval before either makes any changes.
```

Be aware it costs 3–7x the tokens of a single session, teammates can't be resumed,
and it's still experimental. For Round 1 planning it's worth it. For the overnight
build loop it usually isn't — sequential tasks with file dependencies are exactly
the case the docs say to use a single session for.

## Step 7 — Read the plan yourself. This is the gate.

Do not skip this and do not do it at 1am. Specifically check:

- Does `decisions.md` resolve every numbered disagreement, or does it hedge?
  Hedging here means the plan has holes the implementer will improvise into.
- Does every phase item have an acceptance criterion a test could check?
- Did the council actually decide on Spark/Beam, with a reason, or did it adopt it
  because R5 mentioned it?
- Are the two agentic features real agents (multi-step, tool-using) or single
  Gemini prompts with ambition?
- Are migrations reversible?

Then read the last thing `/council-plan` prints: the part the lead is least
confident about. That is usually where you should spend your attention.

## Step 8 — Let it build overnight

```bash
git switch -c council/build-$(date +%m%d)
./scripts/run_overnight.sh build
```

The script preflights before it commits you to anything: it refuses to run on
`main`, refuses a dirty tree, and pings OpenRouter once so a dead key fails at
23:00 rather than silently voiding every review until 07:00.

Then per task: implementer writes it → DeepSeek reviews the diff against the plan →
lead triages the findings → implementer fixes → tests → commit. Every third task,
`plan-auditor` independently checks that ticked boxes are actually done.

The `Stop` hook is what keeps it going instead of idling: if todos remain and no
`BLOCKED.md` exists, it pushes Claude back to work. Capped at 40 nudges per
session, respects `stop_hook_active`, disabled with `COUNCIL_NUDGE=0`, and never
fires when the run has stopped on purpose. A clean stop with a clear question is a
success; that's why `BLOCKED.md` silences the nudge instead of triggering it.

In the morning, read in this order:

```
.ai/logs/*-MORNING.md     # generated summary: commits, files touched, diff stat
.ai/BLOCKED.md            # if it exists, this is the only thing that matters
.ai/audit.md              # the auditor's verdict, which is often "not really done"
git log --oneline
git diff main...HEAD
```

---

## What this costs, roughly

- DeepSeek's share is rounding error: ~$0.08–0.25 per million tokens.
- The Opus lead is most of the bill. Keeping it in a coordination role and pushing
  implementation to Sonnet is the main lever.
- Auto mode's classifier adds a Sonnet-class round trip before shell and network
  calls; reads and in-directory edits skip it.
- Agent teams multiply everything by the number of teammates. Use them for Round 1,
  not for the build loop.
- Set a hard spending cap on the OpenRouter key before the first overnight run.

## Things that will actually go wrong

| Symptom | Cause | Fix |
|---|---|---|
| Subagents missing from `/agents` | added while session was running | restart `claude` |
| Hook never fires | not executable, or matcher case wrong | `chmod +x`, check `/hooks` |
| Every DeepSeek review is empty | stale model slug or dead key | `./scripts/orx.py ask ok` |
| Reviews are vague and useless | you didn't pass enough context files | it can't see the repo, only `--context` |
| Overnight run did nothing | preflight refused (dirty tree / on main) | read the preflight output |
| Implementer keeps expanding scope | `plan.md` is vague | tighten acceptance criteria, rerun planning |
| Two agents clobber one file | parallel tasks touching the same file | serialize them in `todos.md` |
| Ticked todos that aren't done | model optimism | that's what `plan-auditor` is for; trust it over the commit message |

## The one habit that makes this work

Run the loop on a small requirement first — R1 alone, maybe R2 — before you point
it at all seven overnight. You are not testing whether the models are smart. You
are testing whether your `.ai/` contract holds, whether the hooks fire, and whether
the reviews are worth reading. Those either work or they don't, and you find out in
forty minutes instead of losing a night.
