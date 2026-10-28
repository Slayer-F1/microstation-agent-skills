---
name: microstation-drive
description: Use when the task is to actually DO something in MicroStation (read a drawing, change levels, run a key-in, check a file), not just write a script. Gives the agent a run-and-read-back loop - wrap the code as a job, run it inside MicroStation, read the result file - and says honestly which tool the agent needs to run it by itself.
---

# Drive MicroStation: run a job, read the result

Read `microstation-scripting` first (Python facts, import order, safety). If there is no approved standard and the task depends on one, run `microstation-standards-setup` first.

Status: the pieces below were observed working on MicroStation 2026 (26.00.02.039) in an earlier study (Python Editor plus a loader line, scripts run in-process, key-ins sent from Python). The **whole loop together** is not yet proven end to end. Run the smoke test first, every time.

## The loop

1. **Folders.** `%USERPROFILE%\MicroStation-Agent\jobs` and `...\results`. Create if missing.
2. **Write the body.** Plain Python that uses MicroStation's API (names checked in the stubs). Set `result = ...` to return data. `print()` is captured.
3. **Wrap it.**
   `python scripts/make_job.py body.py jobs/<id>.py results/<id>.json`
   This adds the six imports in the right order, catches errors, and writes the result file even when the body fails. It also stops syntax errors before MicroStation sees them.
4. **Ask the engineer** (once per task): what will change, on which copy of which file. Wait for yes.
5. **Run it inside MicroStation** (see "How to run it" below).
6. **Wait for `results/<id>.json`.** Poll. Allow minutes for long work (a print job took about 4.5 minutes). The file only appears when complete.
7. **Read it.** `ok: false` means read `error`, fix, make a new job. Never repeat a failed job blindly.
8. **Report** in plain words: what you did, what changed, what the result file says.

## First run: smoke test

Wrap `templates/smoke_body.py` and run it. Expected result: `ok: true`, `result: {"sum": 4}`. If this fails, stop and fix the route. Do not try real work.

## How to run it - pick by the tools you have

**A. You can control the Windows desktop** (Claude Code desktop computer-use, UI Automation, or similar):
1. Open MicroStation on a copy of the drawing.
2. *Utilities > Python Editor*. Use *New*; it pre-fills the six imports.
3. Replace the document with one line that runs the job file, then Run:
   `exec(open(r"<full path to jobs/<id>.py>", encoding="utf-8").read())`
   (The earlier study used a one-line loader call. This exact line is a suggestion; the smoke test proves it.)
4. Do not type into the Key-in window with simulated keystrokes. Posted characters did nothing there in earlier tests. Use the Python Editor.
5. Do not touch an engineer's own working session without asking. Prefer a separate MicroStation instance on a copy.

**B. You cannot control the desktop:** give the engineer these steps, in their language, one at a time: open MicroStation, *Utilities > Python Editor*, open `<job path>`, press Run. Then read the result file yourself. The loop is the same; only the click is human.

**C. Same key-ins on many files:** MicroStation's *Batch Process* replays the key-ins of a text command file on each file in a list (text after `#` is a comment), and logs to the file named by `MS_BATCHPROCESS_LOGFILE`. Use it for pure key-in work across many drawings. Test on two copies first.

**D. Fully hands-off (planned):** a Rust command-line tool, MCP server and API in this project's roadmap will run jobs without any clicking. Until it exists, A or B applies.

## Hard rules

- Work on copies. Save under a new name. Keep originals.
- Never retry a failed import in the same MicroStation session. A wrong import order breaks every later import. Ask the engineer to restart MicroStation.
- Do not start pipes, listeners or servers inside MicroStation.
- Do not bypass script signing or security settings.
- A job that prints, plots or renders can block MicroStation for minutes. Warn first.
- If the stubs do not show an API, say it is not available. Do not invent it.
