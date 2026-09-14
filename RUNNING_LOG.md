# Running log

Maintained by the Orchestrator per PLAN.md Section 16. Read this at the start of every
session before doing anything else. Write to it before closing every session, even mid-step.

---

## Session 1 (2026-09-15)

**Steps worked on:** Step 0 (setup), Step 1 (structured sentiment prompt), in progress.

**Open questions asked and how answered:**
- Working directory: confirmed as `C:\Users\felce\OneDrive\MBA\Vibe Coding\Assignment 1`.
- Gift_Cards.jsonl.gz memory vs streaming: confirmed streaming line by line.
- API key environment variable name: confirmed `DOBOLYI_API_KEY`.
- Optional metadata fields beyond rating/title/text: confirmed `verified_purchase`,
  `helpful_vote`, `timestamp`.
- Python not installed on this machine: confirmed installing via winget
  (`Python.Python.3.12`, resolved to 3.12.10).
- Model name at `http://dobolyi.com:9001/v1`: not stated in the assignment PDF or the notes
  file. Resolved by live-probing `GET /v1/models` with the class key, which returned exactly
  one model, confirmed with Felipe: `cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`.
- GitHub CLI (`gh`) not installed: installed via winget (`GitHub.cli`, 2.100.0).
- GitHub authentication: `gh auth login` required interactive browser login, run by Felipe
  in his own terminal (I declined to accept his pasted personal access token directly per
  the credential-handling rule; flagged that the pasted token should be treated as exposed
  and considered for revocation). Authenticated as `felcervino`, scopes `gist, read:org,
  repo, workflow`.
- Session calendar (PLAN.md Section 3): Felipe adjusted it. Fixed calendar dates are not to
  be followed; instead, session boundaries should be paced by actual Claude Pro usage
  (5-hour rolling window / weekly cap), not by a fixed date-per-step schedule. Deadline
  September 24 remains the hard constraint; step grouping per session will flex based on how
  much of the usage window each session's work actually consumes.

**Notable technical finding:** the served model (`cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`) is a
reasoning model that emits hidden "thinking" tokens by default; an initial smoke test with
`max_tokens: 10` returned `content: null` because the token budget was spent entirely on the
hidden reasoning field (`finish_reason: length`). Fixed by passing
`chat_template_kwargs: {"enable_thinking": false}`, which returns a clean, directly-usable
`content` string with zero reasoning tokens spent. This setting will be used for every
classification call in Step 1 onward so responses stay cheap and directly parseable.

**Settings used this session:**
- Smoke test call: `temperature: 0`, `enable_thinking: false`, model
  `cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`.

**Classification-endpoint call count this session:** 2 (both smoke-test calls against
`http://dobolyi.com:9001/v1`, no real review data sent).

**Step 0 self-check (Builder, lean mode, self-verified, not independently verified):**
- Confirmed all five `.claude/agents/*.md` files exist with correct frontmatter (name,
  description, tools, model) matching PLAN.md Section 2.1 exactly, with one deliberate
  deviation: found and fixed 3 em dash characters copied verbatim from PLAN.md's own spec
  text and two headers I authored (`frontend-agent.md` description line, `RUNNING_LOG.md`
  session header, `README.md` title), since Guardrail 7 ("no em dashes anywhere") overrides
  exact-copy fidelity.
- Confirmed `data/Gift_Cards.jsonl.gz` (12,292,543 bytes) downloaded from the McAuley Lab
  host and streams correctly: `src/parse_check.py` read 1000 lines without loading the file
  into memory, first record has all required fields (`rating`, `title`, `text`) and all
  confirmed metadata fields (`verified_purchase`, `helpful_vote`, `timestamp`).
- Confirmed the smoke test (`src/smoke_test.py`) reads `DOBOLYI_API_KEY` only from the
  environment (never hardcoded), calls the confirmed model
  `cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit` at `temperature: 0`, and got a real, non-fabricated
  response (`content: 'OK'`, `finish_reason: 'stop'`).
- Confirmed `.gitignore` excludes `.venv/`, `__pycache__/`, `.env`, and the raw data file
  before any commit was made.
- Confirmed `requirements.txt` has exact pinned versions matching `pip freeze` output.

**QA gates passed:** Step 0 self-check passed (see above), self-verified only, lean mode
per PLAN.md Section 2. Evidence: `src/parse_check.py` output (1000 lines streamed, all
fields present), `src/smoke_test.py` output (`content: 'OK'`), `.claude/agents/*.md` (all
five files), `requirements.txt`, `.gitignore`, skeleton repo at
https://github.com/felcervino/amazon-gift-cards-sentiment. Awaiting Felipe's go-ahead
before committing and pushing the substantive Step 0 files (agent files, scripts,
requirements.txt, this log, and the README em-dash fix).

**What's left for next session / rest of this session:** get go-ahead on the Step 0 QA
gate, commit and push the substantive Step 0 files, then move to Step 1's prompt draft,
edge-case confirmation, parser, unit tests, spot-check, and lean-mode self-check.
