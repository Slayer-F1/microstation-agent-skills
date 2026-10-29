---
name: microstation-drive
description: Use when the task is to actually DO something in MicroStation (read a drawing, change levels, run a key-in, check a file), not just write a script. Gives the agent a run-and-read-back loop - wrap the code as a job, run it inside MicroStation, read the result file - and says honestly which tool the agent needs to run it by itself.
---

# Drive MicroStation: run a job, read the result

Read `microstation-scripting` first (Python facts, import order, safety). If there is no approved standard and the task depends on one, run `microstation-standards-setup` first.

Status: the smoke test below was run end to end on MicroStation 2026 (26.00.02.039) on 2026-10-28: job file opened in the Python Editor, run, result file read back with `ok: true` and `sum: 4`. Reading levels through the loop was also checked against Level Manager (see below). Creating and removing a level was tested too (below). Running a job with **no clicks at all** (launch, run, result file, exit) was tested on 2026-10-29 (route 0 below). Placing a line, a shape, a box, an arc, text and a cell from a spec, with colour and weight, was tested on 2026-10-29 (below). Other changes (dimensions, styles, references, key-ins) are **not yet proven**. Run the smoke test first, every time.

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

## Example: place elements from a spec (changes the file, tested)

Templates: `templates/create_elements_body.py` (edit `SPEC`, a list of `line`, `shape`, `box`, `arc`, `text` and `cell` items in **master units**, each with an optional `color` index and `weight`; places them on level `ZZ-AGENT-TEST`, creating the level if missing) and `templates/list_elements_body.py` (read-only: counts by level and element type, plus id, type, range, colour and weight of each element on one level, the string of text elements, and the name, header level and child lines of cells).

Tested on 2026-10-29 on a throwaway copy, three separate no-click launches:
1. before: 100 elements, none on the test level.
2. place: line, shape and box all `ok`.
3. fresh read after MicroStation had closed: 103 elements. The three are on the test level as type 3 (line), 6 (shape) and 19 (solid). Their ranges match the spec exactly: line 0 to 10 along x, shape 0 to 10 by 5 to 15, box 0 to 10 by 22 to 28 by 0 to 3.

Second test, same day, on a fresh throwaway copy, three no-click launches (100 elements, place, then 106). The spec had all six types:
- **Arc** (type 16): range 1 to 9 by 33 to 37 as specified, colour 3, weight 4.
- **Text** (type 17): the string `AGENT TEST` read back, colour 5. Its range is 8.7 wide and 2.0 tall for a requested character height of 1, and the origin is inside it. The range is more than the letters, so do not use it to check text size or position yet.
- **Cell** (type 2): name `AGENT-CELL`, range 0 to 8 by 45 to 49 as specified, two child lines on the test level with weight 2. **The cell header itself is on level 0, not on the test level**, although the template asked for the test level. Level, colour and weight stick on the child lines. If the standard needs the header on a level, that is untested.
- Line, shape and box with no colour or weight given read back colour 0, weight 0. Treat that as "not set".

Rules this showed:
- The spec is in master units. The template converts to UORs (10000 per master unit in the test file). Never pass raw UORs.
- No explicit save call was needed. The test used MicroStation's default *Auto-save Design Changes* preference (on). Check it before trusting this on another machine.
- Always read back with a separate read job and compare the ranges to the spec, not just the count.
- Tested: line, shape, box, arc, text, a cell made of lines, colour index and weight. Bentley's sample `C:\ProgramData\Bentley\PowerPlatformPython\Examples\Microstation\DgnElements\CreateElements.py` shows 36 element types; the rest (ellipses, dimensions, shared cells, B-splines, text tables, other solids) are untested here. Line style, RGB colour and text style were not set or checked. Text uses the default TrueType font.
- There is no template to delete elements. Leave test elements on the copy and discard the copy. The remove-level template refuses a level that still has elements.

## How to run it - pick by the tools you have

**0. No-click launch (tested 2026-10-29, use this first).** Needs only a shell. MicroStation can replay a text file of key-ins at start-up, and the key-in `Python Load` runs a Python file.
- **One-time setup per user:** *File > Settings > User > Preferences > Operation > Command Line > Execute Startup Script*: tick it, press OK. It is off by default, and while it is off the `-s` file is ignored. This changes the engineer's preference, so tell them.
- **Per job:**
  1. Write `jobs/<id>.cmd.txt` as plain ASCII, no BOM, two lines. The quotes matter when the path has spaces. Leave out `exit` only if you want MicroStation to stay open.
     ```
     python load "C:\full\path\jobs\<id>.py"
     exit
     ```
  2. Launch (PowerShell), on a copy of the drawing:
     ```
     Start-Process 'C:\Program Files\Bentley\MicroStation 2026\MicroStation\microstation.exe' -ArgumentList ('-s"{0}" "{1}"' -f $cmdFile, $dgnCopy)
     ```
  3. Wait for `results/<id>.json` (16 to 20 seconds in the tests). MicroStation then closes itself.
- **Tested on a throwaway copy:** smoke job (`sum: 4`); read levels (2 in file, 7 with libraries, same as the Python Editor route); create a level, `exit`, then a fresh launch whose remove job found the level (so the change survived the close) and removed it.
- **Limits:** each launch is a new MicroStation, so do not aim it at a file already open in the engineer's session (not tested, expect a file lock). One launch per job. `exit` rewrites the DGN like any close. Not tested: sites that need a workspace or project on the command line (`-wu -ws -wp`), very large files, what `exit` does after a failed job or with unsaved changes, licence or start-up dialogs.
- Bentley's own help documents the start-up script setting (Preferences, Operation category) and the `Python Load` key-in (Python config variables topic).

**A. You can control the Windows desktop** (Claude Code desktop computer-use, UI Automation, or similar):
1. Open MicroStation on a copy of the drawing. Do not use a launcher tool to "bring MicroStation forward": each call starts a new empty MicroStation instance, and clicks and typing land in it. Check `Get-Process microstation` first and drive the instance whose window title shows the drawing. If another app (a game, a launcher) steals the foreground, the tool will refuse to type; bring MicroStation back with `(New-Object -ComObject WScript.Shell).AppActivate(<its PID>)`, not by launching it again.
2. *Utilities > Python Editor* (Utilities ribbon tab, Python Editor button).
3. Click the *Open* folder icon (tooltip "Open a Python project from disk"), type the full path of `jobs/<id>.py` in the File name box, press Enter. Then click *Run Python File* (the Python icon right of the save icons). The status bar says "The Python script runs to completion". Do not use *New*: it asks for a save path first. The job already contains the six imports.
4. Do not type into the Key-in window with simulated keystrokes. Posted characters did nothing there in earlier tests. Use the Python Editor.
5. Do not touch an engineer's own working session without asking. Prefer a separate MicroStation instance on a copy.

**B. You cannot control the desktop:** give the engineer these steps, in their language, one at a time: open MicroStation, *Utilities > Python Editor*, open `<job path>`, press Run. Then read the result file yourself. The loop is the same; only the click is human.

**C. Same key-ins on many files:** MicroStation's *Batch Process* replays the key-ins of a text command file on each file in a list (text after `#` is a comment), and logs to the file named by `MS_BATCHPROCESS_LOGFILE`. Use it for pure key-in work across many drawings. Test on two copies first.

**D. One-command wrapper (planned):** a command-line tool, MCP server and API in this project's roadmap will wrap route 0 (write files, launch, wait, read) into a single call. Until it exists, use 0, then A or B.

## Hard rules

- Work on copies. Save under a new name. Keep originals.
- Never retry a failed import in the same MicroStation session. A wrong import order breaks every later import. Ask the engineer to restart MicroStation.
- Do not start pipes, listeners or servers inside MicroStation.
- Do not bypass script signing or security settings.
- A job that prints, plots or renders can block MicroStation for minutes. Warn first.
- If the stubs do not show an API, say it is not available. Do not invent it.
