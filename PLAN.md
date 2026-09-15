# MBAX 6418 — Assignment 1 Execution Plan (Multi-Agent, Claude Code, Claude Pro)

## 0. Brutal audit log

**Round 1** (against the assignment PDF): fixed the "hunch to test, not a finding to
confirm" instruction, the "use your judgment about metadata" call-out, the "coherent theme
the host can recolor" requirement, the Step 3 mistake-clustering wording, the "not an
optional pass" enforcement on the report, and added XSS/prompt-injection guardrails the
assignment doesn't mention but the situation requires.

**Round 2** (engineering-rigor gaps, now fixed below): no usage/cost ceiling, no
determinism control on the model's own output, no unit tests on the logic itself, no
incremental commits, no defined failure path when a QA or Red Team check fails, no
multi-session continuity plan, no explicit streaming/memory decision for the gzip file.

**Round 3** (this revision): Haiku removed entirely from the routing plan per instruction,
every role now runs on Sonnet 5 by default with Opus 5 reserved for exactly two moments.
Token/usage planning reframed around a **Claude Pro subscription** (5-hour rolling window
plus a weekly cap, shared across Claude Code, chat, and Cowork, not per-token billing) and
explicit session boundaries added since this will run across multiple sessions, not one
sitting.

**Round 4** (red team pass against the assignment text, this revision): fixed five concrete
gaps — no QA check for the assignment's named "library-shuffle look" failure mode, no QA
check for non-technical-reader comprehensibility, an unresolved ambiguity in Step 5's scope
(does extending the prompt re-spend Step 2's API calls or reuse them), no dependency
pinning to back up the seed-based reproducibility claim, and a Step 9 verification that
could pass on residual local auth instead of a genuinely clean check. Four further findings
are **not** fixable by editing this document and are recorded as named, accepted risks
instead of false claims of resolution: see Section 15.

**Round 5** (self-audit of the document's own internal consistency, this revision): fixed a
broken section-numbering sequence (headers had jumped 14 to 16 with no 15, now unbroken 0
through 16), a role-scope mismatch where Step 3 assigned QA Agent a visual/comprehension
judgment its Section 2 definition never covered, a missing model tag on Step 3's Red Team
pass (Steps 1 and 6 both name their model, Step 3 didn't), and a missing Section 4
call-count reminder on Step 5 despite it being the step most likely to spend new calls
against the shared endpoint.

**Round 6** (full re-audit against the assignment text, this revision, the most consequential
finding to date): Step 2's own unit-test specification had the binary answer-key rule
**wrong**. The assignment states the rule explicitly: "≥4 positive, else negative." That
means a 3-star review is NEGATIVE at the Step 2 stage, not excluded, not neutral, not
dropped. The plan's unit test had said 3.0 should be "excluded from this binary split,"
which directly contradicts the assignment and could have led to Builder silently filtering
out 3-star reviews from a batch that's supposed to include them. This was a real logic
error sitting inside the plan's own correctness-testing scaffolding, not a documentation
gap. Fixed. See Section 17 for the full pass this was caught in.

**Round 7** (all three contention points resolved, this revision): concrete `.claude/agents`
subagent setup added in Section 2.1, with read-only tool access on QA/Red Team/Verification
as a real enforcement mechanism, not just an instruction. Process weight split into full
mode (Steps 2, 3, 6, 8, 9) and lean self-checked mode (Steps 0, 1, 4, 5, 7), catching and
correcting a gap in my own earlier four-step proposal, which had dropped Step 7 entirely
and under-weighted Step 9's cheap-but-high-consequence checks. Session calendar backed
against the real September 24 deadline with a buffer day built in. See Section 18 for the
full record of how each was resolved. One process bug caught and fixed mid-edit this round:
an early replace accidentally dropped a checklist line from Step 2, restored immediately
when verified against the file.

---

## 1. Non-negotiable guardrails (apply at every step, enforced by every agent)

1. **Never let the classification model see the star rating.**
2. **No invented numbers.** Nothing stated unless just computed from a saved output file.
3. **Fixed seeds, fixed settings, and pinned dependencies** for every sampling step. A seed
   alone doesn't guarantee reproducibility if the library versions producing the random
   sequence differ later. Save a `requirements.txt` (or equivalent) with exact versions
   alongside the seed, see Step 0.
4. **Fixed temperature on the classification model itself.** A seed only fixes *which rows*
   get sampled, not what the model returns for them. Set temperature to 0 (or the lowest the
   endpoint allows) and record it. Accept that some residual non-determinism may still exist
   between runs against a live third-party endpoint, that's expected model variance, not a
   bug to chase, and is *not* something QA should treat as a failed check on its own.
5. **Stop and ask before assuming.** Paths, field naming, edge cases, framework choices,
   "enough detail" judgment calls, all confirmed with me.
6. **QA gate before the next step**, evidence shown, my explicit go-ahead required.
7. **No em dashes anywhere.**
8. **Show your work.** Point to the exact file/line backing any claim.
9. **Fixed choice, not negotiable: classification/scoring code (prompt-calling, scoring/
   comparison, NRC word-list) must be Python.** Only the dashboard layer is free to be HTML
   or another framework, confirmed at Step 3.
10. **Untrusted content discipline.** Review `title`/`text` are user-generated and
    untrusted: HTML-escaped before rendering (stored-XSS risk), and passed to the model as
    clearly delimited data, never concatenated into the instruction portion of a prompt
    (prompt-injection risk).
11. **No anchoring on hinted "known findings."** Where the assignment or a prior step hints
    at what a later step "should" show (the Step 6 hint about 3-star reviews above all),
    treat it strictly as a hypothesis. Report what the data shows even if it disagrees.
12. **Unit tests on logic, not just output numbers.** Every piece of parsing/scoring/mapping
    logic gets hand-written test cases *before* it's trusted with real data, see per-step
    detail below. A QA gate that only checks output numbers can't catch a bug that happens
    to cancel itself out across 100 rows.
13. **Commit after every QA gate, not just at the end.** Local commits happen the moment a
    step's gate passes. The public GitHub repo is created in Step 0 (empty/skeleton) so
    pushes can happen incrementally, giving a real commit history instead of one giant
    commit at submission time.
14. **Defined failure path.** If a QA or Red Team check fails: the Orchestrator logs the
    finding in the running log, routes it back to the specific agent that owns the affected
    artifact, that agent fixes it, and QA/Red Team re-checks *only the fixed item* before
    the gate reopens. No step is marked complete while any finding is unresolved.
15. **Multi-session continuity.** This project runs across more than one Claude Code
    session. Every session starts by reading the running log (Section 16) to know exactly
    where the last session left off, and ends by writing to it before the session closes,
    even mid-step. Never assume a fresh session remembers unstated context.
16. **Usage discipline for two separate budgets, don't conflate them:**
    - **Claude Pro's own usage window** (5-hour rolling window plus a weekly cap, shared
      across Claude Code, Claude.ai chat, and Cowork, billed as a flat subscription, not
      per token). Opus 5 consumes this budget noticeably faster than Sonnet 5. See Section 3.
    - **The class's shared classification endpoint** (`http://dobolyi.com:9001/v1`, key
      `6418`), a separate resource used by the whole class, with its own call-count
      discipline, see Section 4. A runaway loop here isn't a Claude Pro billing problem,
      it's you hammering a shared class resource.
17. **Confirmed context for this run:**
    - GitHub repo will be **public**.
    - OpenAI-compatible endpoint: `http://dobolyi.com:9001/v1`, API key `6418`. Environment
      variable, never hardcoded, never committed.
    - I am working **solo**, executing across **multiple Claude Code sessions**, on a
      **Claude Pro** subscription.

---

## 2. Agent roster, model assignment, and process mode (Sonnet 5 only, Haiku removed)

**Two process modes, assigned per step by risk, not applied uniformly.** Running the full
Builder/QA/Red-Team/Verification separation on every single step was the biggest drag on
the proportionality score across five audit rounds, since the assignment itself says each
step is "a goal to reach, not a checklist." Resolved by splitting steps into two modes:

- **Full mode, Steps 2, 3, 6, 8, and 9**: these are where a wrong number, a broken security
  check, or a bent narrative actually costs points, either because they carry the graded
  numbers (2, 6), they're the named "product, not demo" deliverable (3), they're the report
  itself (8), or the consequence of a miss is high even though the work is simple, a leaked
  secret or a broken public-visibility check at submission time (9). Builder/Frontend
  implements, a genuinely separate subagent (QA, Red Team, or Verification as applicable)
  independently checks, exactly as designed in prior rounds.
- **Lean mode, Steps 0, 1, 4, 5, and 7**: setup, prompt design, filtering, emotion
  detection, and descriptive visualization. Lower complexity and lower blast radius if
  something slips. Builder or Frontend performs its own self-check against the same
  checklist items instead of a separate subagent being invoked, and **says so explicitly in
  the running log** ("self-verified, not independently verified"), so this trade-off is
  visible, never silently assumed to be as independent as full mode. The checklist content
  itself does not shrink, Step 1's rating-leakage and prompt-injection checks still happen,
  just as Builder's own self-check rather than a separate Red Team invocation.

| Agent | Owns | Model | Tool access | Why |
|---|---|---|---|---|
| **Orchestrator** | Sequencing, asking me questions, gating, maintaining the running log, deciding full vs lean per the table above | **Sonnet 5** | Full (this is the main Claude Code session, not a subagent) | Runs constantly across the whole project; this is where model choice most affects total Pro-plan usage. |
| **Builder Agent** | Step 1 prompt, Step 2/6 scoring & sampling scripts, Step 5 NRC script, Step 8 README draft, self-checks on all lean steps | **Sonnet 5** | Read, Write, Edit, Bash, Grep, Glob | All of this is well within Sonnet's coding and judgment range; nothing here needs Opus-level reasoning. |
| **Frontend/Design Agent** | Steps 3, 4, 7 dashboard build and interactivity | **Sonnet 5**, escalate to **Opus 5** for the Step 3/7 final polish pass only | Read, Write, Edit, Bash, Grep, Glob | Sonnet builds it; the assignment's "product, not demo" design bar is the one place extra aesthetic judgment earns its cost, and only for the final pass, not every iteration. |
| **QA Agent** | Full-mode independent number recomputation, used at Steps 2, 3, 6, 8. At Step 3 specifically, also gives an independent read on the "library-shuffle" and non-technical-reader checks | **Sonnet 5** | **Read, Bash, Grep, Glob only, no Write/Edit** | Read-only access is a real, enforceable independence mechanism, not just an instruction: this agent physically cannot "fix" a discrepancy it finds, only report it. |
| **Red Team Agent** | Adversarial checks at Steps 1 (full-mode content, run as Builder self-check per the lean-mode note above), 3, and 6 | **Sonnet 5** for Step 3; **Opus 5** for the Step 6 anchoring check specifically | Read, Bash, Grep, Glob | Catching whether a report quietly bent its numbers to match the assignment's own hint is the single most nuanced judgment call in this whole project, worth the one-time extra cost. |
| **Verification Agent** | Step 8/9 final cross-check of README numbers, citations, file inventory, repo hygiene | **Sonnet 5** | **Read, Bash, Grep, Glob only, no Write/Edit** | Same read-only reasoning as QA Agent. |

**Isolation is only real if it's configured, not role-played.** The subsection below sets up
QA, Red Team, and Verification as actual separate Claude Code subagents with their own
context and, for QA and Verification, tooling that makes independence a technical fact
rather than a promise. This closes the residual risk named in prior rounds; the only
genuinely unclosable risk left is the shared external endpoint, see Section 15.

### 2.1 Concrete subagent setup (build these files in Session 1, before Step 0's other work)

Create a `.claude/agents/` directory in the project root and add one file per subagent
below. Claude Code will treat each as an invocable, separately-contexted subagent once these
exist. Do this first, so every subsequent step actually has real agents to delegate to
rather than one continuous conversation switching hats.

**`.claude/agents/builder-agent.md`**
```
---
name: builder-agent
description: Implements the Python classification/scoring/sampling code, the NRC word-list
  logic, and the Step 8 README draft for the MBAX 6418 assignment. Also performs self-checks
  on lean-mode steps (0, 1, 4, 5, 9).
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are the Builder Agent for this project. Implement the code PLAN.md calls for: the
sentiment prompt (Step 1), the scoring/answer-key logic (Step 2), the NRC emotion word-list
logic (Step 5), the three-class balanced sampler and scorer (Step 6), and the first
README.md draft (Step 8).

Non-negotiable rules, sourced from PLAN.md:
- Never include the `rating` field in any payload sent to the classification model.
- Read the API key only from its environment variable, never hardcode or print it.
- Set temperature to 0 (or the lowest available) on every classification call, record the
  exact setting used.
- Write unit tests for any parsing or boundary-mapping logic before running it on real data.
  Binary answer key (Step 2): rating >= 4 is POSITIVE, everything else, including 3, is
  NEGATIVE. Three-class answer key (Step 6): 4 to 5 POSITIVE, 3 NEUTRAL, 1 to 2 NEGATIVE. Do
  not confuse these two rules, they are genuinely different for 3-star reviews.
- Pin exact library versions to requirements.txt alongside every fixed random seed.
- Cache classification results by review id; never re-call the endpoint for a row already
  classified.
- Save everything you produce to a file. Never report a number that isn't backed by a file
  on disk.
- On lean-mode steps (0, 1, 4, 5, 9), perform your own self-check against that step's
  checklist before reporting done, and log it explicitly as "self-verified, not
  independently verified." On Step 1 specifically, this self-check must include confirming
  the rating field is absent from the actual outgoing request body, and testing one
  adversarial review string with an embedded instruction to confirm it doesn't change
  classifier behavior.
- Stop and ask the Orchestrator whenever PLAN.md says to confirm something with Felipe,
  never default silently.
```

**`.claude/agents/frontend-agent.md`**
```
---
name: frontend-agent
description: Builds and refines the HTML dashboard (Steps 3, 4, 7) — structure,
  interactivity, and visual design.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are the Frontend/Design Agent, owning Step 3 (dashboard v1), Step 4 (filtering), and
Step 7 (descriptive/prediction visualizations).

Rules from PLAN.md:
- HTML-escape every piece of user-generated review text before inserting it into the DOM.
  Test with an adversarial string containing `<script>` and raw quote/angle-bracket
  characters before considering any dashboard step done.
- Build the palette and typography on theme tokens/CSS variables so the whole dashboard can
  be recolored without touching layout code, an explicit assignment requirement.
- Actively avoid a "library-shuffle" look, the assignment's own named anti-pattern: no
  default, unstyled component-library output.
- Show a class-by-class mistake breakdown (how errors cluster), not just a right/wrong
  total.
- Cross-check every number you render against the specific saved output file it comes from,
  in the browser, not from memory of what Builder told you.
- Test for layout bugs at multiple viewport sizes, specifically zero-width bars from
  label/positioning interactions.
- Use the Opus 5 configuration only for the final visual-polish pass after QA has signed off
  on functionality, never for new functionality.
```

**`.claude/agents/qa-agent.md`**
```
---
name: qa-agent
description: Independently re-derives every claimed number from saved output files, full
  mode only (Steps 2, 3, 6, 8). Read-only by design, cannot edit project files.
tools: Read, Bash, Grep, Glob
model: sonnet
---

You are the QA Agent. You do not write or edit project code, your tools are read-only by
design: your value is that you cannot "fix" a discrepancy, only report it.

Given a claim and a path to the file it should come from, open that file yourself and
recompute or directly verify the claim. Report match or mismatch plainly. On mismatch,
describe exactly what you found instead, and stop, do not attempt to correct the source.

At Step 3, additionally give an independent read on two things, distinct from Frontend
Agent's own design judgment: (1) whether the dashboard reads as default, unstyled
component-library output (the "library-shuffle" check), and (2) what a reader with no ML
background would conclude about model quality from the page alone, no surrounding
explanation. Report these as your own independent read, not a rubber stamp of Frontend
Agent's opinion of its own work.

Never accept a claim because Builder or Frontend said so. Recompute from the file every
time.
```

**`.claude/agents/red-team-agent.md`**
```
---
name: red-team-agent
description: Adversarial correctness and security testing, full mode at Steps 3 and 6.
  Sonnet 5 except Step 6, which uses Opus 5.
tools: Read, Bash, Grep, Glob
model: sonnet
---

You are the Red Team Agent. Actively try to break the assumptions the other agents rely on,
don't confirm them.

At Step 3: construct one adversarial review-like string containing `<script>` tags and raw
quote/angle-bracket characters, run it through the actual rendering pipeline, confirm it
displays as inert text in the rendered page.

At Step 6 (the Opus 5 configuration, the single most important check in this project): read
the actual saved confusion matrix file directly. Independently determine which direction the
confusion runs (3-star called NEGATIVE, NEGATIVE called NEUTRAL, or something else). Compare
that independently-derived answer to whatever the draft report claims. If they don't match,
or the draft's wording looks like it was shaped to match the assignment's own hint about
3-star reviews rather than the actual matrix, flag it explicitly as a finding.

You report findings, you do not fix them. Findings go back to the Orchestrator, which routes
them to the agent that owns the affected artifact.
```

**`.claude/agents/verification-agent.md`**
```
---
name: verification-agent
description: Final cross-check of README numbers, citations, and repo file inventory
  against saved output and the live repo. Used at Step 8 and Step 9. Read-only by design.
tools: Read, Bash, Grep, Glob
model: sonnet
---

You are the Verification Agent, the last independent check before submission. Read-only by
design, same reasoning as QA Agent: you report, you don't fix.

At Step 8: read the final README.md. For every number it states, trace it back to the
specific saved output file it should come from, confirm an exact match. Confirm the Amazon
Reviews '23 dataset citation is present. Confirm the file inventory the README implies
(prompt, scoring script, NRC script, dashboard generator, balanced run's raw output, final
dashboard, unit test files) actually exists in the project directory.

At Step 9: confirm the live GitHub repository contains exactly that file inventory, no more
(no stray secrets, no large data file), no less. Confirm the commit history shows real
incremental progress across sessions, not one dump at the end.

You do not judge whether the narrative is well-written or the conclusions are insightful,
that is explicitly reserved for Felipe's own personal review, not any agent's job.
```

---

## 3. Claude Code usage plan (Pro license, multi-session)

Pro is a flat subscription with a 5-hour rolling window and a separate weekly cap, shared
across Claude Code, Claude.ai chat, and Cowork, not a per-token bill. The practical
consequences for this plan:

- [ ] **Default every agent to Sonnet 5.** Confirmed above; this is the single biggest lever
      on how much of the weekly window this project consumes.
- [ ] **Use Opus 5 only at the two flagged moments** (Step 3/7 final polish, Step 6
      anchoring check), and treat each as a deliberate, single, bounded use, not an ongoing
      mode.
- [ ] **Scope each session by how heavy the step actually is, not by a fixed count of
      steps, backed against the actual due date of September 24.** Today is September 14,
      giving 10 days. Light steps (mostly code, little back-and-forth, no screenshots) pair
      well; heavy steps (iterative, screenshot-driven, or touching many files at once) get
      their own session. Concrete calendar, not just a content grouping:
      - Session 1, **Sep 15**: Step 0 (including the `.claude/agents` setup in 2.1), Step 1.
      - Session 2, **Sep 16**: Step 2, first real data run against the shared endpoint,
        isolated so QA's recomputation happens in a clean context.
      - Session 3, **Sep 17**: Step 3, dashboard v1 build, the first screenshot-heavy step.
      - Session 4, **Sep 18**: Step 4, Step 5.
      - Session 5, **Sep 19 to 20**: Step 6, the heaviest single step, given two days of
        margin. **This is the one step allowed a mid-step break**: stop after the
        backend/confusion-matrix half is saved and QA'd, resume the dashboard carry-through
        half the next day, using that saved matrix file as the resumable checkpoint. Every
        other step still follows the "never break mid-step" rule.
      - Session 6, **Sep 21**: Step 7, more chart/screenshot iteration.
      - Session 7, **Sep 22**: Step 8, Step 9.
      - **Sep 23**: buffer day. Felipe's personal README review and rewrite (Step 8's
        non-delegable gate), the incognito-window visibility check (Step 9), and the Canvas
        submission itself all happen here, not on the deadline day.
      - **Sep 24**: deadline. Nothing new is scheduled here on purpose, this day only exists
        as slack if Sep 23 runs over.
      This calendar assumes steady daily progress; if a session slips, absorb it into the
      Sep 23 buffer first before compressing any of Steps 2, 3, 6, or 8, those are the four
      full-mode steps and are the wrong place to rush. Confirm or adjust with me at the
      start of Session 1.
- [ ] **Write summaries to files, not raw data into chat.** Builder and Frontend agents save
      batch review text, full API responses, and large intermediate data to files and refer
      to them by path plus a short summary, rather than printing full batches into the
      conversation. This cuts token usage independently of how sessions are split, and keeps
      context room for the actual reasoning work in heavy steps.
- [ ] **Start every session by reading the running log** (Section 16) to resume state
      exactly, and **end every session by writing to it**, even if a step isn't finished,
      so no session change ever relies on unstated memory.
- [ ] **Check Settings > Usage in Claude Code periodically**, especially before starting an
      Opus 5 pass, since Anthropic doesn't publish a fixed number of Sonnet/Opus hours per
      plan tier, actual headroom is visible only there.

---

## 4. Security and shared-resource guardrails

- [ ] API key read only from an environment variable, never logged, never committed.
- [ ] All user-generated review text HTML-escaped before insertion into the dashboard DOM,
      verified with an adversarial test string (`<script>`, raw `"`/`<`/`>`).
- [ ] Review text passed to the classification model as clearly delimited data, tested with
      one adversarial review containing an embedded instruction.
- [ ] **Call-count ceiling against the shared class endpoint.** Confirm a per-step ceiling
      with me before running Step 2 or Step 6 at scale (e.g. "I'll stop and check in if this
      step needs more than N calls"), since `dobolyi.com:9001` with key `6418` is shared
      across the whole class, not a personal budget.
- [ ] Results cached per review id so a re-run never needlessly re-calls the endpoint for
      rows already classified; confirm the cache key/format with me before building it.
- [ ] Basic retry/backoff on transient endpoint failures, bounded (no infinite retry loops).
- [ ] Track and show total call count per run so usage stays visible, not assumed.

---

## 5. Step 0 — Setup, repo skeleton, and access checks
**Owner: Orchestrator + Builder. Lean mode: Builder self-checks against this step's
checklist and logs it as "self-verified," no separate subagent invocation.**

- [ ] **Build the five subagent files in `.claude/agents/` per Section 2.1**, before
      anything else this step. This is what makes every later full-mode step's
      independence real rather than aspirational.
- [ ] Confirm the working directory / project folder path with me.
- [ ] Confirm Python version and virtual environment setup, and save a `requirements.txt`
      (or equivalent) with exact pinned versions of every library used for sampling or
      scoring, committed alongside the code, so a re-run with the same seed can actually
      reproduce the same result.
- [ ] Download/locate `Gift_Cards.jsonl.gz`. **Confirm with me whether to load it fully
      into memory or stream it line by line** given its size, don't default silently either
      way, and confirm one line parses with all required fields.
- [ ] Propose which optional metadata fields (beyond rating/title/text) are worth keeping,
      and why, get my confirmation before locking the schema.
- [ ] Set the API key as an environment variable (confirm variable name with me), confirm
      the model name to call at `http://dobolyi.com:9001/v1`, and confirm temperature (0 by
      default per Guardrail 4, unless the endpoint requires otherwise).
- [ ] Run a live smoke-test call reading the key from the environment, confirm a response.
- [ ] Create/check `.gitignore` (env files, data file) before any commit.
- [ ] **Initialize git and create the public GitHub repo now**, with a skeleton README, so
      every later step's QA gate can be followed by an incremental push, not one big commit
      at the end.
- [ ] Confirm the session calendar in Section 3, or adjust it with me.
- [ ] Create the running log file (Section 16) and write the first entry.

**QA gate:** Builder self-check confirms the parsed sample and the smoke-test output are
both real, the five agent files exist and are correctly formed, and logs this as
self-verified. Show me all of it, plus the repo skeleton URL. Wait for go-ahead, then commit
and push.

---

## 6. Step 1 — Structured sentiment prompt (POSITIVE / NEGATIVE)
**Owner: Builder Agent. Lean mode: Builder self-checks, including the rating-absence and
prompt-injection content that would otherwise be a separate Red Team pass, logged
explicitly as "self-verified, not independently verified."**

- [ ] Draft one reusable prompt template, `title` + `text` only, strict machine-parseable
      output, no rating in the payload.
- [ ] Propose edge-case handling (conflicting title/text, terse/angry short reviews) to me
      for confirmation before locking it in.
- [ ] Parser rejects/flags anything that doesn't match the expected format.
- [ ] **Write unit tests for the parser first**: hand-craft a handful of expected-good
      responses, expected-malformed responses (truncated, extra text, wrong casing), and
      confirm the parser handles each exactly as intended, before pointing it at real data.
- [ ] Spot-check on a small, manually chosen set of obvious positive/negative reviews.

**Self-check (Builder, lean mode):** confirm the rating field is genuinely absent from the
actual API request body, and run one adversarial review string containing an embedded
instruction to confirm it doesn't hijack the output. Log this explicitly as self-verified.

**QA gate:** Show me the prompt template, parser, unit test results, spot-check results, and
the self-check results. Wait for go-ahead, then commit and push.

---

## 7. Step 2 — Score against the rating (100-row batch)
**Owner: Builder Agent. Full mode: QA Agent (genuinely separate subagent, read-only)
independently checks.**

- [ ] Confirm with me: literally the first 100 rows, or a seeded random 100.
- [ ] **Write unit tests for the rating-to-class boundary logic** (confirm rating 4.0 and
      5.0 map to POSITIVE, and confirm rating 3.0 maps to NEGATIVE, not excluded or dropped,
      since the assignment's binary rule is "≥4 positive, else negative," meaning every
      rating below 4, including 3-star reviews, is NEGATIVE at this stage; a true NEUTRAL
      class only exists starting at Step 6. Also confirm any unexpected value is flagged,
      not silently coerced) before running it over real data.
- [ ] Derive the answer key from rating only, model never sees it.
- [ ] Save raw per-review results to a file (id, label, derived key, match/mismatch).
- [ ] Compute and save: overall agreement rate, per-class accuracy, actual class balance,
      skew toward high ratings stated plainly, not buried.
- [ ] List mismatched reviews.
- [ ] Respect the Section 4 call-count ceiling, confirm before running at full scale.

**QA gate:** QA Agent independently recomputes the agreement rate and per-class accuracy
from the saved file. Show me both numbers side by side, plus the unit test results. Wait
for go-ahead, then commit and push.

---

## 8. Step 3 — Results dashboard v1
**Owner: Frontend/Design Agent (Sonnet 5, Opus 5 for final polish). Full mode: QA Agent +
Red Team Agent (genuinely separate subagents, XSS check).**

- [ ] Confirm dashboard framework choice with me (single self-contained HTML file is the
      assignment's suggested default).
- [ ] Headline agreement numbers, a class-by-class mistake breakdown (how mistakes cluster,
      not just totals), enough per-review detail to back the claims, confirmed with me.
- [ ] Deliberate palette and typography built on theme tokens/CSS variables so the whole
      dashboard can be recolored without touching layout code, this is an explicit
      assignment requirement, not optional polish.
- [ ] Every number on the page cross-checked against the Step 2 saved file, in the browser.
- [ ] **Opus 5 final polish pass**, once the functional version is signed off by QA, for
      visual refinement only, not new functionality.
- [ ] **Explicit "library-shuffle" check**: QA Agent confirms the dashboard does not read as
      default, unstyled component library output (stock Bootstrap/Tailwind look). This is
      the assignment's own named failure mode, not generic polish, and gets its own
      pass/fail rather than being folded into "deliberate palette."
- [ ] **Explicit non-technical-reader check**: QA Agent states, in one or two sentences,
      what a reader with no ML background would conclude about model quality from the page
      alone, without reading any surrounding text. If that isn't obvious from the page, the
      step isn't done.

**Red Team pass (Sonnet 5):** inject an adversarial review-like string (`<script>`, raw
`"`/`<`/`>`) into the rendered table, confirm it displays as inert text, not executable
markup or broken layout.

**QA gate:** Screenshot, numbers walked through against source file, XSS test result shown.
Wait for go-ahead, then commit and push.

---

## 9. Step 4 — Interactive review filtering
**Owner: Frontend/Design Agent. Lean mode: self-check, logged as "self-verified."**

- [ ] Live filter (at minimum correct vs mismatched) with a live, correct count.
- [ ] Test at least two filter states against a manual count from the Step 2 saved data.

**QA gate:** Self-check shows the filter working and the manual-count cross-check. Wait for
go-ahead, then commit and push.

---

## 10. Step 5 — Primary-emotion detection (two independent methods)
**Owner: Builder Agent. Lean mode: self-check, logged as "self-verified."**

- [ ] **Confirm scope with me before making any calls**: does extending the Step 1 prompt
      mean re-running the model on the same reviews already classified in Step 2 (new calls
      against the shared endpoint, replacing those cached results), or classifying a fresh
      batch, or adding a second, separate emotion-only call per already-classified review.
      This determines how many additional calls this step spends against the shared class
      endpoint (Section 4), don't default to any of these silently.
- [ ] Extend the Step 1 prompt to also return a primary emotion. Confirm with me whether the
      LLM's label set is constrained to the same 8 NRC labels or left free-text and
      reconciled after.
- [ ] Implement the NRC word-list method separately (no model calls, runs over existing
      text). Confirm the exact lexicon source/license with me before pulling it in.
- [ ] **Write unit tests for the NRC lookup logic** (a hand-picked word known to map to a
      specific emotion, a word with no entry, a tie between two emotions, confirm the
      tie-break rule) before running it over real data.
- [ ] Save both label sets per review plus an agreement/disagreement flag.
- [ ] Compute agreement rate and pull concrete disagreement examples.
- [ ] Respect the Section 4 call-count ceiling for whatever scope was confirmed above.

**QA gate:** Builder self-check recomputes the agreement rate from the saved file, logged as
self-verified. Show
me the rate, unit test results, and 3 to 5 disagreement examples. Wait for go-ahead, then
commit and push.

---

## 11. Step 6 — Three-class scoring with balanced sampling
**Owner: Builder Agent. Full mode: QA Agent + Red Team Agent (Opus 5, anchoring check),
genuinely separate subagents.**

- [ ] Redefine the answer key: 4 to 5 = POSITIVE, 3 = NEUTRAL, 1 to 2 = NEGATIVE, carried
      through the prompt, scoring, and dashboard everywhere.
- [ ] **Extend the unit tests from Step 2** to cover the new three-way boundary explicitly
      (rating exactly 3.0 must land in NEUTRAL, not silently fall through to NEGATIVE or
      POSITIVE) before running over real data.
- [ ] Draw a balanced sample (~50 per class) with a fixed, recorded random seed. **Write a
      test confirming the sampler actually returns ~50 per class**, not an assumed-correct
      count.
- [ ] Confirm with me whether this run fully replaces Steps 1 to 5 outputs or is kept as a
      separate labeled run.
- [ ] Compute and save the full 3-class confusion matrix and per-class accuracy.
- [ ] Compare imbalanced (Step 2) vs balanced numbers explicitly.
- [ ] Report, with the actual matrix numbers, where 3-star/NEUTRAL reviews land and in
      which direction.
- [ ] Respect the Section 4 call-count ceiling for this larger batch.

**Red Team pass (Opus 5, anchoring check):** confirm the reported direction of confusion was
read off the actual matrix, not written to match the assignment's own hint about 3-star
reviews. If the matrix disagrees with the hint, that disagreement is reported as-is, and
flagged as a positive finding, not smoothed over.

**QA gate:** Show me the confusion matrix, seed, unit test results, balanced-vs-imbalanced
comparison, and the anchoring check. Wait for go-ahead, then commit and push.

---

## 12. Step 7 — Descriptive and prediction visualizations
**Owner: Frontend/Design Agent (Sonnet 5, Opus 5 for final polish). Lean mode: self-check,
logged as "self-verified."**

- [ ] Star-rating distribution chart.
- [ ] Correct-answer vs predicted comparison per class.
- [ ] Per-class "answered right" rate, visible at a glance without drilling in, this is the
      explicit point of the step.
- [ ] Test for layout bugs collapsing small chart elements at multiple viewport sizes.
- [ ] Every rendered chart value cross-checked against the Step 6 saved file, in the browser.
- [ ] Opus 5 final polish pass once functionally signed off.

**QA gate:** Self-check screenshot, chart-vs-file confirmation, confirm no collapsed
elements at any tested size. Wait for go-ahead, then commit and push.

---

## 13. Step 8 — Report (README.md) and final deliverables
**Owner: Builder Agent drafts (Sonnet 5). Full mode: Verification Agent (genuinely separate
subagent, read-only) checks. I personally review and rewrite the narrative, this step
cannot be signed off by any agent.**

- [ ] Draft `README.md`, numbers pulled from saved files, every number's source file
      flagged inline for my review.
- [ ] Cite the Amazon Reviews '23 dataset and its page
      (`https://amazon-reviews-2023.github.io`).
- [ ] Include at least one dashboard screenshot.
- [ ] Answer, with evidence pointing to saved files, all four required questions (imbalance,
      confusion clustering, LLM-vs-NRC emotion divergence, bugs/issues hit).
- [ ] Confirm final file set: prompt(s), scoring script, word-list emotion script, dashboard
      generator, balanced run's raw output, final dashboard, plus the unit test files.
      Confirm with me anything unsure (large data file excluded, credentials never
      included).
- [ ] I personally reread the full draft, confirm the framing and conclusions are in my own
      words, before this step is marked done.

**Verification Agent pass:** independently checks every number in the final README against
the saved output files, checks the citation, checks the file inventory against the actual
repo directory listing.

**QA gate:** Walk through the README section by section against source files, confirm I
have personally rewritten the narrative. Wait for go-ahead, then commit and push.

---

## 14. Step 9 — Final GitHub verification and handoff
**Owner: Orchestrator + Builder. Full mode: Verification Agent (genuinely separate
subagent, read-only), despite low complexity, because the consequence of a miss (leaked
secret, broken public visibility) is high and the check itself is cheap.**

Since the repo was created in Step 0 and pushed incrementally, this step is a final check,
not a first push.

- [ ] Confirm `.gitignore` has held throughout, no secrets or the data file ever landed in
      the history.
- [ ] Final commit and push of the README and any last dashboard changes.
- [ ] Fetch the live repo URL and confirm the README renders correctly with screenshots
      visible.
- [ ] **Genuinely clean visibility check, not just a local fetch.** A fetch from this same
      Claude Code session could succeed on residual local auth even if something about
      public visibility is actually broken. Ask me to open the link myself in an incognito
      window (or a device where I'm not logged into GitHub) and confirm it renders, before
      this step is marked done.
- [ ] Give me the final shareable link. I submit it to Canvas manually.

**Verification Agent pass:** confirms the live repo contains exactly the files listed in
Step 8's inventory, no more, no less, and that the commit history shows real incremental
progress rather than one dump at the end.

**QA gate:** Confirm the live URL renders correctly and the file-inventory check passes.
Wait for my final go-ahead.

---

## 15. Named risks this plan does not fully solve

Down to one from four, tracked honestly rather than declared solved by fiat.

**Resolved this round:**
- Agent isolation (previously item 1): closed by Section 2.1's concrete `.claude/agents`
  setup, plus read-only tool access on QA, Red Team, and Verification, a technical
  enforcement, not just an instruction.
- Process overhead versus the assignment's "goal, not checklist" framing (previously item
  3): closed by the full/lean mode split in Section 2, full rigor on the five steps that
  carry real risk (2, 3, 6, 8, 9), self-checked lean mode on the five that don't (0, 1, 4,
  5, 7).
- No calendar back-plan (previously item 4): closed by Section 3's concrete session-to-date
  calendar against the September 24 deadline, with a buffer day built in.

**Still open, genuinely unclosable by editing this document:**

1. **Single point of failure on the shared class endpoint.** Everything downstream of Step 1
   depends on `dobolyi.com:9001` staying available and responsive, a resource shared with
   the entire class, not something this project controls. There is no substitute path, since
   the endpoint is a fixed assignment requirement. Mitigation is the calendar itself, heavy
   steps (2, 6) are scheduled with margin, not on the last day before the deadline, but that
   reduces exposure, it doesn't eliminate the risk.

---

## 16. Running log (Orchestrator maintains this section, every session)

Each session, before doing anything else, read this section to resume exactly where the
last session left off. Before closing a session, write to it, even mid-step.

Log format per entry:
- Session number, date, steps worked on.
- Every QA gate passed, with a one-line pointer to the evidence file.
- Every open question asked and how I answered it.
- Every Red Team finding and how it was resolved.
- The seed, temperature, and settings used for every sampling/model run this session.
- Total classification-endpoint call count this session (Section 4 discipline).
- What's left to do next session.

---

## 17. Round 6 full re-audit against the assignment text

Every clause of the assignment PDF checked again, line by line, against the current
document. Presenting the complete result, not just the misses, so nothing is hidden.

| Assignment requirement | Status | Note |
|---|---|---|
| Goal statement (classify, detect emotion, check against rating, dashboard) | Covered | Spans Steps 1 to 7 collectively. |
| "Each step is a goal, not a checklist" | Resolved via the full/lean process split | Section 2's full mode (Steps 2, 3, 6, 8, 9) versus lean self-checked mode (Steps 0, 1, 4, 5, 7) directly answers this: full rigor only where a miss costs points, lightweight self-checks elsewhere. The document itself stays checklist-formatted for QA-gate tracking, that's a documentation format choice, not process weight on every step. |
| Fixed choices: Python for classification/scoring, OpenAI-compatible endpoint | Covered | Guardrail 9, Guardrail 17. |
| Dashboard can be HTML or anything else | Covered | Step 3, framework confirmed with me, not assumed. |
| "Work in order, each step leaves you with something working" | Covered | Enforced structurally by the QA-gate-before-next-step rule. |
| Classmates fair game, but own write-up, own repo | Covered | Guardrail 17 (solo), Step 8 (personal rewrite non-delegable). |
| Treat hinted "known findings" as a hunch, not a target | Covered | Guardrail 11, Step 6 anchoring Red Team pass. |
| Dataset fields and source, judgment on optional metadata | Covered | Step 0. Minor: Step 0 doesn't spell out the exact field name list from the assignment inline, it's implicit via delegation to the assignment text itself. Low-priority, noted, not fixed, see below. |
| Step 1: prompt design, edge cases, no rating exposure, programmatic parsing | Covered | Step 1, plus Red Team check that rating is genuinely absent from the request body. |
| Step 2: 100-row batch, answer key ≥4 positive else negative, model blind to rating, report agreement/per-class/mismatches, call out skew | Covered, one bug found and fixed | The unit test spec had the ≥4/else-negative rule backwards for the 3-star case. Fixed this round, see Round 6 in Section 0. |
| Step 3: dashboard content minimums, "product not demo" design bar, "library-shuffle" anti-pattern, non-technical-reader clarity | Covered | Fixed in Round 4, model-tagged and role-scoped correctly in Round 5. |
| Step 4: live filtering with correct count | Covered | Step 4. |
| Step 5: two independent emotion methods, LLM and NRC, kept separate and compared | Covered | Step 5, scope ambiguity resolved in Round 4, call-count reminder added in Round 5. |
| Step 6: three-class redefinition, carried through everywhere, balanced ~50/class with fixed seed, 3-star placement question | Covered | Step 6, unit tests correctly distinguish this step's true NEUTRAL class from Step 2's binary NEGATIVE treatment of 3-star reviews. |
| Step 7: descriptive visuals, in-browser number check, layout-bug watch | Covered | Step 7. |
| Final deliverables: report content, file list, citation, screenshot, four required questions | Covered | Step 8. |
| Author/review split, "not an optional pass" | Covered | Step 8, only step no agent can sign off. |
| Submission mechanics: public repo, link in Canvas, verify it works | Covered | Step 9, including the Round 4 fix for a genuinely clean visibility check. |
| Standing considerations (rating is answer key, repeatability, show your work, honesty about imbalance, product bar) | Covered | Distributed across Guardrails 1 to 17. |

**Result of this pass:** one real logic bug found and fixed (the Step 2 answer-key unit
test), one minor documentation completeness note found and left open by choice (see below),
nothing else new. Four rounds of prior audits had already closed the rest.

**Minor, low-priority, intentionally not auto-fixed:** Step 0 doesn't inline the assignment's
exact list of expected field names (rating, title, text, verified_purchase, helpful_vote,
timestamp, images, asin, parent_asin, user_id). This isn't a gap in what gets checked, the
agent reading the original assignment document will see them directly, but a document meant
to be fully self-contained arguably should list them. Left out deliberately rather than
padding the document with a restatement of text the agent already has direct access to;
noted here so it isn't silently dropped from the record.

---

## 18. Points of contention resolved this round

The three questions previously open here are now answered, converted into the plan itself
rather than left as loose decisions. Kept as a record, not deleted, since the reasoning
behind each choice matters as much as the choice.

1. **Agent isolation: build it for real.** Resolved by Section 2.1's five concrete
   `.claude/agents` file specs, with read-only tool access on QA, Red Team, and Verification
   as a technical enforcement of independence, not just an instruction to behave
   independently.
2. **Process weight: full mode where it earns its cost, lean where it doesn't.** Resolved
   as full mode on Steps 2, 3, 6, 8, and 9 (the five where a miss actually costs points, or
   costs little to check even at low risk), lean self-checked mode on Steps 0, 1, 4, 5, and
   7. This differs slightly from the original four-step proposal, Step 7 was missing from
   that proposal entirely (a gap in my own earlier framing, caught while implementing this
   round) and Step 9 moved from the lean list to the full list, since its checks are cheap
   but the consequence of missing one, a leaked secret or a broken public repo, is high
   enough that the independence is worth keeping even on a low-complexity step.
3. **Deadline: September 24.** Resolved with a concrete session-to-date calendar in Section
   3, Sessions 1 through 7 running September 15 through 22, a buffer day on the 23rd for the
   non-delegable personal review and the incognito visibility check, and the 24th held open
   as pure slack, not scheduled work.
