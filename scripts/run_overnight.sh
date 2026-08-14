#!/usr/bin/env bash
# Overnight council orchestrator.
#
# Sequences: plan -> [optional human gate] -> build loop -> audit.
# Each phase is a fresh headless Claude Code session. Continuity comes from the
# .ai/ files, not from session state — that is the whole point of the architecture.
#
#   ./scripts/run_overnight.sh plan          # planning only, then stop
#   ./scripts/run_overnight.sh build         # build loop only (plan must exist)
#   ./scripts/run_overnight.sh all           # plan then build, no human gate (bold)
#
# Deliberately NOT using `set -e`: one failed phase should not kill the night.
set -uo pipefail

MODE="${1:-plan}"
LEAD_MODEL="${LEAD_MODEL:-opus}"
IMPL_MODEL="${IMPL_MODEL:-sonnet}"
# Set FINAL_MODEL to the Fable alias shown by /model in your Claude Code if you
# want Fable 5 as the decision maker. Verify the alias first: `claude --model ?`
FINAL_MODEL="${FINAL_MODEL:-$LEAD_MODEL}"
PERM_MODE="${PERM_MODE:-auto}"
MAX_BUILD_PASSES="${MAX_BUILD_PASSES:-12}"

LOG_DIR=".ai/logs"
mkdir -p "$LOG_DIR" ".ai/reviews"
RUN_ID="$(date +%Y%m%d-%H%M%S)"

say() { printf '\n\033[1m[council %s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }

# ---------------------------------------------------------------- preflight
preflight() {
  local fail=0

  command -v claude >/dev/null 2>&1 || { echo "MISSING: claude CLI"; fail=1; }
  command -v python3 >/dev/null 2>&1 || { echo "MISSING: python3"; fail=1; }
  [[ -n "${OPENROUTER_API_KEY:-}" ]] || [[ -f .env ]] || {
    echo "MISSING: OPENROUTER_API_KEY (env or .env)"; fail=1; }
  [[ -f .ai/requirements.md ]] || { echo "MISSING: .ai/requirements.md"; fail=1; }
  [[ -x scripts/orx.py ]] || { echo "MISSING: scripts/orx.py not executable"; fail=1; }

  git rev-parse --git-dir >/dev/null 2>&1 || { echo "MISSING: not a git repo"; fail=1; }

  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  if [[ "$branch" == "main" || "$branch" == "master" ]]; then
    echo "REFUSING: you are on '$branch'. Run: git switch -c council/$RUN_ID"
    fail=1
  fi

  if [[ -n "$(git status --porcelain | grep -v '^?? \.ai/' || true)" ]]; then
    echo "REFUSING: working tree is dirty. Commit or stash first, so that"
    echo "          'what changed overnight' is answerable by git diff."
    fail=1
  fi

  # Cheapest possible check that the OpenRouter key actually works, before
  # you find out at 3am that every review silently failed.
  if ! ./scripts/orx.py ask "reply with exactly: ok" >/dev/null 2>"$LOG_DIR/orx-preflight.err"; then
    echo "FAILED: orx.py could not reach OpenRouter. See $LOG_DIR/orx-preflight.err"
    fail=1
  fi

  [[ $fail -eq 0 ]] || { echo; echo "Preflight failed. Nothing has run."; exit 1; }
  say "preflight OK | branch=$branch | lead=$LEAD_MODEL impl=$IMPL_MODEL perm=$PERM_MODE"
}

# Run one headless phase. Args: <name> <model> <prompt>
phase() {
  local name="$1" model="$2" prompt="$3"
  local log="$LOG_DIR/${RUN_ID}-${name}.log"
  say "phase '$name' on $model -> $log"
  claude -p "$prompt" \
    --model "$model" \
    --permission-mode "$PERM_MODE" \
    >"$log" 2>&1
  local rc=$?
  tail -n 25 "$log"
  say "phase '$name' exited $rc"
  return $rc
}

remaining_todos() {
  [[ -f .ai/todos.md ]] || { echo 0; return; }
  grep -c -- '- \[ \]' .ai/todos.md 2>/dev/null || echo 0
}

# ---------------------------------------------------------------- phases
do_plan() {
  phase plan "$LEAD_MODEL" "/council-plan"

  if [[ "$FINAL_MODEL" != "$LEAD_MODEL" ]]; then
    phase synthesis "$FINAL_MODEL" \
      "You are the final decision maker. Read every file in .ai/. Independently \
re-resolve .ai/disagreements.md, then rewrite .ai/decisions.md, .ai/plan.md and \
.ai/todos.md as the authoritative versions. Where you disagree with the lead \
architect's resolution, say so explicitly in decisions.md. Do not touch \
application code."
  fi

  if [[ ! -f .ai/plan.md ]]; then
    say "NO PLAN PRODUCED. Read $LOG_DIR/${RUN_ID}-plan.log. Stopping."
    return 1
  fi
  say "plan ready: $(remaining_todos) tasks queued"
}

do_build() {
  if [[ ! -f .ai/plan.md ]]; then
    say "no .ai/plan.md — run '$0 plan' first and approve it."
    return 1
  fi
  rm -f .ai/BLOCKED.md

  local pass=1
  while [[ $pass -le $MAX_BUILD_PASSES ]]; do
    local left
    left="$(remaining_todos)"
    if [[ "$left" -eq 0 ]]; then
      say "todos empty after $((pass - 1)) passes"
      break
    fi
    say "build pass $pass/$MAX_BUILD_PASSES | $left task(s) left"

    phase "build-$pass" "$LEAD_MODEL" "/council-build"

    if [[ -f .ai/BLOCKED.md ]]; then
      say "BLOCKED. Stopping cleanly."
      cat .ai/BLOCKED.md
      break
    fi
    pass=$((pass + 1))
  done

  phase audit "$IMPL_MODEL" \
    "Use the plan-auditor subagent to audit every completed task in .ai/todos.md \
against the acceptance criteria in .ai/plan.md. Write .ai/audit.md. Be harsh: a \
ticked box with no test is NOT MET."
}

# ---------------------------------------------------------------- morning report
report() {
  local out=".ai/logs/${RUN_ID}-MORNING.md"
  {
    echo "# Council run $RUN_ID"
    echo
    echo "## Where it got to"
    echo "- tasks remaining: $(remaining_todos)"
    echo "- blocked: $([[ -f .ai/BLOCKED.md ]] && echo YES || echo no)"
    echo
    echo "## Commits made overnight"
    git log --oneline "@{u}..HEAD" 2>/dev/null || git log --oneline -20
    echo
    echo "## Files touched (in order)"
    tail -n 200 "$LOG_DIR/writes.log" 2>/dev/null || echo "(no write log)"
    echo
    echo "## Read these first"
    for f in .ai/BLOCKED.md .ai/audit.md .ai/plan.md .ai/decisions.md .ai/progress.md; do
      [[ -f "$f" ]] && echo "- $f"
    done
    echo
    echo "## Diff stat"
    git diff --stat "@{u}..HEAD" 2>/dev/null || git diff --stat HEAD~10..HEAD 2>/dev/null
  } > "$out"
  say "morning report -> $out"
  cat "$out"
}

# ---------------------------------------------------------------- main
preflight
case "$MODE" in
  plan)  do_plan ;;
  build) do_build ;;
  all)
    say "WARNING: 'all' skips the human plan-approval gate."
    do_plan && do_build
    ;;
  *) echo "usage: $0 {plan|build|all}"; exit 2 ;;
esac
report
