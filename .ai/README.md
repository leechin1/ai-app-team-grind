# The `.ai/` council workspace

This directory is the only channel through which council members communicate.
No agent passes its conversation to another agent. Everything goes through files.

## Ownership rules — these are hard rules, not suggestions

Exactly one member may write to each file. Everyone may read everything.

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `context.md` | you (human) | all | repo map, stack, constraints, what must not break |
| `requirements.md` | you (human) | all | the spec. The only source of truth for *what* |
| `architecture-claude.md` | Opus (lead architect) | all | Round 1 independent design |
| `architecture-openrouter.md` | OpenRouter architect | all | Round 1 independent design |
| `review-openrouter.md` | OpenRouter critic | all | Round 1 skeptical review |
| `rebuttal-claude.md` | Opus | all | Round 2 response to the critic |
| `disagreements.md` | Opus | all | the open questions after Round 2 |
| `decisions.md` | synthesizer | all | resolved disagreements, append-only, never edited |
| `plan.md` | synthesizer | all | **authoritative.** Nothing gets built that is not here |
| `todos.md` | synthesizer, then implementer ticks boxes | all | ordered work queue |
| `reviews/task-NN.md` | OpenRouter reviewer | implementer | per-task code review |
| `logs/` | orchestrator script | you | raw transcripts of every phase |

## Rules for every member

1. **Planning phase is read-only on application code.** You may write inside `.ai/`
   and nowhere else until `plan.md` exists and a human has approved it.
2. **`plan.md` is authoritative.** If you want to do something not in `plan.md`,
   stop and append the question to `disagreements.md` instead of improvising.
3. **`decisions.md` is append-only.** A decision is reversed by appending a new
   entry that supersedes the old one, never by editing history.
4. **Every plan item needs an acceptance criterion a test could check.**
   "Improve the pipeline" is not a criterion. "Uploading a 12-page PDF to project
   X produces >=1 row in `embeddings` with `project_id = X` and zero rows with any
   other `project_id`" is.
5. **One writer per source file during implementation.** If two tasks touch the
   same file, they run sequentially, not in parallel.
6. **Cite your sources.** When you critique, name the file and line. Unsourced
   objections get ignored by the synthesizer.
