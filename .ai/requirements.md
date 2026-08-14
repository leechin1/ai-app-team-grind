# Notiq — requirements for this council run

Source: `Notiq_mudancas.txt`. Translated and turned into testable requirements.
**You (human) own this file.** Agents may not edit it. If an agent thinks a
requirement is wrong, it writes the objection to `disagreements.md`.

Product context: Notiq is an AI note-taker and study copilot. Supabase backend
with a working `embeddings` table and pgvector already in place. Gemini is the
LLM already in use for agentic features.

---

## R1 — Every uploaded document lands in embeddings

Modify the ingestion pipeline so that **all** uploaded documents reach the
embeddings table, not just some formats.

- In scope: PDF, plain text, markdown, docx. Confirm the real list against the
  existing upload code before assuming.
- Chunking strategy, chunk size and overlap must be chosen explicitly and
  written down in `decisions.md` with a reason.
- Ingestion must be idempotent: re-uploading the same file must not create
  duplicate embedding rows.

**Acceptance criteria**
- [ ] Uploading a multi-page PDF produces N > 0 rows in `embeddings`.
- [ ] Uploading a `.txt` produces N > 0 rows in `embeddings`.
- [ ] Re-uploading the identical file produces no new rows (or replaces cleanly).
- [ ] A file that fails to parse produces a visible error state, not a silent
      success with zero embeddings.

## R2 — `project_id` is mandatory and never crosses projects

The `embeddings` table has a required `project_id` column, populated
automatically with the FK of the project the document was created in.

**Acceptance criteria**
- [ ] `project_id` is `NOT NULL` with a FK constraint to the projects table.
- [ ] The ingestion path derives `project_id` from the document's project. It is
      never accepted from client input.
- [ ] Row Level Security (or equivalent) prevents a user from reading embeddings
      belonging to a project they do not own.
- [ ] A test proves that a retrieval query issued in project A returns **zero**
      chunks from project B, even when the text is a near-exact match.

> This is the single highest-risk requirement in this run. Cross-project leakage
> is a data breach, not a bug. The critic must attack this specifically.

## R3 — Working chatbot with RAG, scoped per project

Make the chatbot functional and add retrieval-augmented generation. The chatbot
is **project-exclusive**: it retrieves context only from its own project.

**Acceptance criteria**
- [ ] Asking a question whose answer exists only in an uploaded document produces
      an answer grounded in that document, with a citation back to the chunk.
- [ ] Asking a question whose answer exists only in *another* project's document
      produces "I don't know", not the answer.
- [ ] Retrieval parameters (top-k, similarity threshold) are configurable and
      their chosen defaults are recorded in `decisions.md`.
- [ ] Streaming responses work end to end, and a failed retrieval degrades to a
      plain answer with a warning rather than a 500.

## R4 — Two new agentic AI features

Read the whole project and its stack, then propose exactly **two** new features
that are genuinely agentic (multi-step, tool-using, Gemini-based, consistent with
the existing Gemini usage) and that make sense for an AI note-taker and study
copilot.

**Acceptance criteria**
- [ ] Each proposed feature has: user problem, why an agent is needed rather than
      a single prompt, tools it calls, failure modes, and a rough cost per run.
- [ ] Each is decomposed into a phased roadmap in `plan.md`.
- [ ] Rejected candidate features are listed with one line on why they lost.
      At least four candidates must be considered.
- [ ] No feature is proposed that duplicates something the app already does.

## R5 — Tooling preferences, subject to justification

Prefer, **where the scope genuinely calls for it**: FastAPI, Spark or Apache
Beam, LangChain, and other common AIOps tooling.

**This is a preference, not a mandate.** Each of these must earn its place.

**Acceptance criteria**
- [ ] For each tool adopted, `decisions.md` records the concrete reason and the
      simpler alternative that was rejected.
- [ ] For each tool declined, `decisions.md` records one line on why.
- [ ] The critic must specifically challenge any distributed data-processing
      choice against the actual expected document volume. If the app processes
      tens of documents per day, a batch framework is accidental complexity and
      the council must say so out loud rather than adopting it to look serious.

## R6 — Create skills and hooks along the way

As the work reveals repeatable procedures, capture them.

**Acceptance criteria**
- [ ] At least one hook enforces R2 mechanically (e.g. blocking a migration or
      insert that omits `project_id`).
- [ ] Any procedure repeated three or more times becomes a skill or a script.
- [ ] Each new skill/hook is listed in `decisions.md` with its trigger.

## R7 — Create subagents along the way

**Acceptance criteria**
- [ ] Every subagent added has a single clear job and a restricted tool list.
- [ ] No subagent is created that duplicates an existing one.

---

## Hard constraints for every member

- Do not break existing working functionality. The embeddings table already
  works; migrations must be additive and reversible.
- Do not commit secrets. Supabase service-role keys never enter source or logs.
- Every schema change ships with an up migration and a down migration.
- No new dependency without a line in `decisions.md`.
