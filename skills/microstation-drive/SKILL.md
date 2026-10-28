---
name: microstation-drive
description: Use when the task is to actually DO something in MicroStation (read a drawing, change levels, run a key-in, check a file), not just write a script. Gives the agent a run-and-read-back loop - wrap the code as a job, run it inside MicroStation, read the result file - and says honestly which tool the agent needs to run it by itself.
---

# Drive MicroStation: run a job, read the result

Read `microstation-scripting` first (Python facts, import order, safety). If there is no approved standard and the task depends on one, run `microstation-standards-setup` first.

Status: the smoke test below was run end to end on MicroStation 2026 (26.00.02.039) on 2026-10-28: job file opened in the Python Editor, run, result file read back with `ok: true` and `sum: 4`. Reading levels through the loop was also checked against Level Manager (see below). Creating and removing a level was tested too (below). Other changes (elements, styles, key-ins) are **not yet proven**. Run the smoke test first, every time.

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

## Example: read the levels (read-only, tested)

Wrap `templates/list_levels_body.py`. It lists every level in the active file: id, code, name, description, color index, weight, line style code, display, frozen, plot.

Tested on 2026-10-28 on a test copy: result `count: 2`, `count_with_libraries: 7`. Level Manager showed the same 7. **`count` is the levels stored in the file; the rest come from attached level libraries (DGNLIB).** Report both numbers, do not call 2 "all levels".

Raw values not decoded yet: `color_index` is a color-table index (one level returned 19232, which is not a plain 0-255 index) and `style` -1 is unexplained. Do not turn them into RGB or names without checking.

## Example: create and remove a level (changes the file, tested)

Templates: `templates/create_level_body.py` (creates `ZZ-AGENT-TEST`, weight 3, color 3, then `cache.Write()` and reads it back) and `templates/remove_level_body.py` (removes it; refuses a level that has elements).

Tested on 2026-10-28 on a throwaway copy, one MicroStation session:
1. create: `created: true`, count 2 to 3, `write_status: eNone`.
2. fresh read job: the level is listed (weight 3, color index 3).
3. file closed and reopened from disk, read job again: **the level is still there**. `cache.Write()` is what makes it permanent.
4. remove: `removed: true`, count back to 2.

Rules this showed:
- **Always `cache.Write()` after a level change, then read back with a separate read job.** Do not trust the change job's own readback alone.
- **Closing a DGN rewrites it, even if you only read it.** The original test file changed size and time when MicroStation closed it. Work on a copy and treat the original as touched the moment you open it. Copy first (`Copy-Item`), open the copy by File > Open, and check the window title before running a change job.
- Only weight and color index were set and checked. RGB colors, line styles and descriptions are untested. `CreateLevel` returns an invalid handle for a duplicate or invalid name.

## How to run it - pick by the tools you have

**A. You can control the Windows desktop** (Claude Code desktop computer-use, UI Automation, or similar):
1. Open MicroStation on a copy of the drawing. Do not use a launcher tool to "bring MicroStation forward": each call starts a new empty MicroStation instance, and clicks and typing land in it. Check `Get-Process microstation` first and drive the instance whose window title shows the drawing. If another app (a game, a launcher) steals the foreground, the tool will refuse to type; bring MicroStation back with `(New-Object -ComObject WScript.Shell).AppActivate(<its PID>)`, not by launching it again.
2. *Utilities > Python Editor* (Utilities ribbon tab, Python Editor button).
3. Click the *Open* folder icon (tooltip "Open a Python project from disk"), type the full path of `jobs/<id>.py` in the File name box, press Enter. Then click *Run Python File* (the Python icon right of the save icons). The status bar says "The Python script runs to completion". Do not use *New*: it asks for a save path first. The job already contains the six imports.
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
