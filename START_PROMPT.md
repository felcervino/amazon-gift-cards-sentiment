Read PLAN.md in full before doing or saying anything else. It is the authoritative spec
for this project, MBAX 6418 Assignment 1 (sentiment and emotion classification of Amazon
Gift Cards reviews). Follow it exactly, including every guardrail in Section 1, the
full/lean process split in Section 2, and the session calendar in Section 3. Do not
summarize the plan back to me, do not restate it, just confirm you've read it and start
Session 1.

Session 1 scope, today, September 15: Step 0 plus Step 1.

Before writing any code:

1. Build the five subagent files in `.claude/agents/` exactly as specified in Section 2.1
   of PLAN.md (builder-agent, frontend-agent, qa-agent, red-team-agent,
   verification-agent). This comes before everything else in Step 0.
2. Then work through Step 0's checklist (Section 5 of PLAN.md) in order. Where the plan
   says to confirm something with me, stop and ask, don't default silently, this includes
   the working directory, the memory-vs-streaming decision for the gzip file, optional
   metadata fields, the API key's environment variable name, and the model name at
   `http://dobolyi.com:9001/v1`.
3. Once Step 0's QA gate passes and I've given the go-ahead, move to Step 1 (Section 6),
   including its edge-case confirmation and the lean-mode self-check on rating absence and
   prompt injection.
4. Create the running log file per Section 16 as part of Step 0, and write the first entry
   before this session ends, whether or not Step 1 is finished.

Ground rules for this and every session, pulled forward from PLAN.md so they're not easy
to drift from mid-session:

- No em dashes anywhere, in code, commits, or chat.
- Never put the star rating in any payload sent to the classification model.
- Never hardcode the API key, read it from an environment variable only.
- No invented numbers, ever, everything traces to a saved file.
- Stop and ask before assuming anything the plan flags as a confirm-with-me item.
- Commit and push after this session's QA gate passes, not before.
- End this session by writing to the running log, even if Step 1 isn't finished.

Start now: confirm you've read PLAN.md, then begin with the `.claude/agents/` setup.
