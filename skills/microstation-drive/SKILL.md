---
name: microstation-drive
description: Use when the task is to actually DO something in MicroStation (read a drawing, change levels, run a key-in, check a file), not just write a script. Gives the agent a run-and-read-back loop - wrap the code as a job, run it inside MicroStation, read the result file - and says honestly which tool the agent needs to run it by itself.
---

# Drive MicroStation: run a job, read the result

Read `microstation-scripting` first (Python facts, import order, safety). If there is no approved standard and the task depends on one, run `microstation-standards-setup` first.

Status: the smoke test below was run end to end on MicroStation 2026 (26.00.02.039) on 2026-10-28: job file opened in the Python Editor, run, result file read back with `ok: true` and `sum: 4`. Reading levels through the loop was also checked against Level Manager (see below). Creating and removing a level was tested too (below). Running a job with **no clicks at all** (launch, run, result file, exit) was tested on 2026-10-29 (route 0 below). Placing a line, a shape, a box, an arc, text, a cell, a circle, an ellipse, a polyline and a dimension from a spec, with colour and weight, was tested on 2026-10-29. So were editing what is already there (move, copy, rotate, scale, restyle, delete), printing to PDF, and attaching and detaching reference files (all below). On 2026-10-30 these were tested too (section "styles, curves, tables, dimensions, a house and a road"): line style codes 0 to 7, RGB colours, text styles, text justification and rotation, shared cells, B-splines, line-and-arc chains with offsets, text tables, linear, radius, diameter and angle dimensions, a house and a road read back and printed, and printing at an exact scale on a chosen paper size. A sheet model can be made and a reference attached at a scale, but **printing through a sheet does not work yet** (see the print section). Key-ins and other element types are **not yet proven**. Run the smoke test first, every time.

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

Templates: `templates/create_elements_body.py` (edit `SPEC`, a list of `line`, `shape`, `box`, `arc`, `circle`, `ellipse`, `polyline`, `bspline`, `chain`, `text`, `cell`, `shared_cell`, `table` and `dimension` items in **master units**; the comment at the top of the file lists every field with an example. Any item can carry `level` (made if the file has none; default `ZZ-AGENT-TEST`), `color` index, `rgb`, `weight` and `style` (line code 0 to 7)) and `templates/list_elements_body.py` (read-only: counts by level and element type, plus id, type, range, colour and weight of each element on one level, the string of text elements, and the name, header level and child lines of cells).

Tested on 2026-10-29 on a throwaway copy, three separate no-click launches:
1. before: 100 elements, none on the test level.
2. place: line, shape and box all `ok`.
3. fresh read after MicroStation had closed: 103 elements. The three are on the test level as type 3 (line), 6 (shape) and 19 (solid). Their ranges match the spec exactly: line 0 to 10 along x, shape 0 to 10 by 5 to 15, box 0 to 10 by 22 to 28 by 0 to 3.

Second test, same day, on a fresh throwaway copy, three no-click launches (100 elements, place, then 106). The spec had all six types:
- **Arc** (type 16): range 1 to 9 by 33 to 37 as specified, colour 3, weight 4.
- **Text** (type 17): the string `AGENT TEST` read back, colour 5. Its range is 8.7 wide and 2.0 tall for a requested character height of 1, and the origin is inside it. The range is more than the letters, so do not use it to check text size or position yet.
- **Cell** (type 2): name `AGENT-CELL`, range 0 to 8 by 45 to 49 as specified, two child lines on the test level with weight 2. **The cell header itself stays on level 0**, although the template asked for the test level. Level, colour and weight stick on the child lines. Six ways to move the header were tried on a fresh copy (the level setter before and after `AddChildComplete`; after `AddToModel` with `ReplaceInModel`; with `SetChangeEntireElement`; writing `GetElement().ehdr.level` before and after adding). The header read level 0 every time, checked three ways (element ref, property getter, raw header). So treat the header level as not settable here and put the standard's level on the child lines. Whether level display and level locks go by the children was not tested.
- Line, shape and box with no colour or weight given read back colour 0, weight 0. Treat that as "not set".

Rules this showed:
- The spec is in master units. The template converts to UORs (10000 per master unit in the test file). Never pass raw UORs.
- No explicit save call was needed. The test used MicroStation's default *Auto-save Design Changes* preference (on). Check it before trusting this on another machine.
- Always read back with a separate read job and compare the ranges to the spec, not just the count.
- Tested: line, shape, box, arc, text, a cell made of lines, colour index and weight. Third test, same day: **circle and ellipse** (type 15, ranges exact, colour and weight read back), **polyline** (type 4, range exact, colour read back), **linear dimension** (type 33, `points` = two points, `offset` in master units; a positive offset puts the dimension line to the left of the direction first point to second point; the range 0 to 10 by -5 to -3 matched, colour read back). The range of a dimension does not include its text. Bentley's sample `C:\ProgramData\Bentley\PowerPlatformPython\Examples\Microstation\DgnElements\CreateElements.py` shows 36 element types; shared cells, B-splines, text tables and angular and radial dimensions, and line style, RGB colour and text style, were tested on 2026-10-30 (see the section below); other solids and the rest are untested here. Text uses the default TrueType font unless `text_style` is given.
- To change or delete what is already in the file, use the modify template (next section). Remove-level still refuses a level that has elements.

## Example: styles, curves, tables, dimensions, a house and a road (tested 2026-10-30)

Template: the same `templates/create_elements_body.py`. Tested on throwaway copies of a metric 3D drawing. Each test was: place (no-click launch), read back in a separate launch after MicroStation had closed, print to PDF, then measure the PDF with a PDF library (page size, stroke dash patterns, colours, text, rectangle sizes).

- **Line style codes 0 to 7** (`style`): each reads back as asked. PDF dash patterns in points: 0 solid, 1 dotted `[.96 3]`, 2 medium dash `[4.92 3]`, 3 long dash `[11.88 3.96]`, 4 dash-dot `[7.92 3 2.04 3]`, 5 short dash `[3.96 3.96]`, 6 dash-dot-dot, 7 long dash short dash. Named custom line styles were not tested: the test file has none.
- **RGB colour** (`rgb`: [r, g, b]): `DgnColorMap.CreateElementColor(IntColorDef(r, g, b), None, None, dgn)` returns an element colour id (19459, 19713, 20098 and 20230 for the four test colours). It reads back unchanged, `ExtractElementColorInfo` returns the exact RGB with `isTrueColor` true, and the PDF strokes had exactly those colours. A `color_index` such as 19232 in the level list is the same kind of id (a true colour, not a table index); decode it with `ExtractElementColorInfo` (not tried on that level yet).
- **Text styles** (`text_style`, `bold`, `italic`): a named `DgnTextStyle` is made in the file once. Read back: font size 1 and 3, bold and italic flags as asked. The text range box is **two text heights tall**. Default justification is left-top (box from 1.5 h below to 0.5 h above the origin). `just` is two letters, l c r plus t m b: `cm` puts the box exactly on the origin (used for room labels), `lb` puts the baseline on the origin (box from 0.5 h below to 1.5 h above). `rot_deg` 90 turns the text counter-clockwise (range checked). `\n` in `text` starts a new line (tested, centred).
- **Shared cells**: a definition from `lines` and instances at the `at` points with `scale` and `deg`. In one job: 1 definition (type 34) and 4 instances (type 35); the scale-2 instance has exactly twice the range, the 45-degree instance the exact rotated range, all survived the close. A definition made by an **earlier job** works too (leave out `lines`): two instances with scale 1.5 and 30 degrees had exactly the predicted range. Not tested: shared cell libraries, editing a definition.
- **B-spline** (`bspline`, passes through the points): the distance from the curve to every input point is 0.0000 m. Element type 27. `CalcElementRange` gives the range of the control polygon, which is larger than the curve, so do not check a spline by its range.
- **Chain** (`chain`): lines and arcs joined as one complex string (type 12). Test: line 40, arc of radius 30 over 60 degrees, line 40: length read back 111.416 (expected 111.416). With `offsets`, **a positive offset is on the right of the direction of travel**, a negative one on the left; the two offset lengths read back 115.081 and 107.751 (expected the same). `base: false` places only the offsets.
- **Text table** (`table`): a real MicroStation table (type 106). `origin` is the top-left corner. Rows, columns and every cell string read back exactly. For a text height of 1 the default row height is 1.99 and the column width 10.8. `col_width` is exact (2 columns of 4 gave a table 8.0 wide). `row_height` is only a minimum: a row never gets smaller than the text needs (1 asked, 1.99 got). A named text style keeps the height it was first made with; asking for another `height` with the same name changes nothing, so use a new style name for a new size.
- **Dimensions** (`dimension` with `kind`): a dimension needs a real dimension style, otherwise it prints lines with no text and no arrowheads (an empty default style did exactly that). The template makes the style `AGENT-DIM` in the file the first time (text size from `text_height`, arrowheads). Points per kind: `linear` [a, b] with `offset` (positive is to the left of a to b); `radius` [centre, point on the circle, where the text goes] (two points gave an empty dimension); `diameter` [centre, point on the circle] (**the first point is the centre, not one side**); `angle` [vertex, point on the first leg, point on the second leg]. Printed texts: "R 5", "∅ 20" (point 10 m from the centre), "90°", "60°", "15.00". Two style switches matter. An angle shows the **arc length** instead of degrees unless `AngleMeasure` is true (the template sets it). The length `accuracy` code: 130 gives two decimals (default; 5.678 prints 5.68), 129 one decimal, 132 four, 0 whole numbers, and 1 to 8 give fractions ("5 1/2"). Trailing zeros are shown ("12.00").
- **A house and a road.** 30 items: 9 wall shapes, 2 door swings and 2 leaves, 6 window lines, 2 centred room labels and 3 dimensions on `A-WALL`, `A-DOOR`, `A-GLAZ`, `A-ANNO-TEXT`, `A-ANNO-DIMS`; a road as a centre line, 2 edges and 2 lane lines (chains), 2 station texts and 1 width dimension on `C-ROAD-*` levels. The read job after the close found 32 elements, the planned count on every level and type, and all 9 wall ranges exactly as specified. Printed at 1:50 on A3, the 9.1 m wall is 182.0 x 6.0 mm and the 7.4 m wall 6.0 x 148.0 mm in the PDF, and the dimension texts read "12.00", "8.00" and "5.60". The road printed with a dash-dot centre line, dashed lane lines and solid edges through a line, arc, line path. The level names are examples; use the names of the approved standard.
- Text placed 0.5 m from a line collides with it: give labels a clear offset from the geometry. The agent places, it does not judge layout.

## Example: change what is already there (changes the file, tested)

Template: `templates/modify_elements_body.py`. Edit `OPS`: each op has a `select` and one action. Pick elements with `select` = `ids` (from a list job), `level` (name), or `cell` (a cell name), and narrow with `types` (type codes: 2 cell, 3 line, 4 polyline, 6 shape, 15 ellipse or circle, 16 arc, 17 text, 19 solid, 33 dimension). Actions, distances in master units: `move` (`by`), `copy` (`by`; the copy gets a new id, returned as `new_id`), `rotate` (`about` point, `deg` counter-clockwise), `scale` (`about` point, `factor`), `props` (`level`, `color`, `weight`), `delete`.

**Safety.** `expect` is the number of elements you think match. If the count differs, the op does nothing and reports `expected N, found M`. A `delete` without `expect` is refused. Ask the engineer before a delete and show them the matched ids first (run a list job).

Tested on 2026-10-29 on a fresh throwaway copy, three no-click launches (create 6 elements, modify, read; 100 to 106 elements, as expected). The read job ran after MicroStation had closed, so the changes were saved:
- **move** a line by 2: range 0 to 10 became 2 to 12. **copy** a shape by 20: the copy 20 to 30, original untouched. **rotate** an arc 90 degrees about its centre: 1 to 9 by 33 to 37 became 3 to 7 by 31 to 39. **scale** a box by 2 about a point: 0 to 10 by 22 to 28 by 0 to 3 became -5 to 15 by 19 to 31 by 0 to 6. All exact.
- **delete** a cell by name: gone. A level-based delete of the same cell matched 0 elements, because **a cell header sits on level 0**: select cells with `cell`.
- **props**: colour and weight changed on line, polyline, ellipse, solid and shape. **Text takes the colour but ignores the weight** (it reads back 0). The first version failed on text with status 32768; the fix is to keep `old = eeh.GetElementRef()` before the change and call `ReplaceInModel(old)`. Do not use `SetChangeEntireElement` for this (did nothing on text).
- Guards: wrong count refused, delete without `expect` refused, an op that fails does not stop the next one.
- Not tested: edits to elements inside a cell, shared cells, elements in references, mirror, offset, arrays, undo (there is none: work on a copy).

## Example: print to PDF (tested)

Template: `templates/plot_pdf_body.py` (read-only for the drawing; writes `results\plot.pdf`). It uses MicroStation's own PDF driver (`pdf.pltcfg`, shipped with the product) through `PrintDescriptionRef`, as in Bentley's `Plot\Pdf\PdfPlot.py`. Settings at the top: `BOX` (x0, y0, x1, y1 in master units, the area to print; `None` prints what view 1 shows), `SCALE` (200 means 1:200; `None` fits the area to the paper; needs `BOX`) and `PAPER` (a form name exactly as in the plot config, such as `"ISO A3"`; `None` is the driver default, Letter). It returns the paper and plot size in mm, `fits`, and whether the view was put back.

Tested 2026-10-30 on a metric 3D drawing, then measured in the PDF (page size, rectangle sizes, strokes). Earlier, on 2026-10-29, the plain version printed view 1 (`print_status: 0`, about 24 seconds).
- **Paper and scale are exact.** `BOX` around a 30 x 20 m rectangle, `SCALE` 200, `PAPER` "ISO A3": the page is 420.0 x 297.0 mm and the rectangle 150.0 x 100.0 mm. Fit on "ISO A4": page 297.0 x 210.0 mm. A house at 1:50: the 9.1 m wall is 182.0 mm and the 7.4 m wall 148.0 mm.
- **Why `BOX` exists.** View 1 of the test drawing is a rotated 3D view with a camera and shaded rendering, looking at the far corner of the model. Printing "what view 1 shows" gave only the frame and the licence mark, and a shaded view prints as a raster. `BOX` sets a plan view of the box (identity rotation, wireframe, camera off) through `ViewGeomInfo` and `SynchWithViewInfo`, then puts the view back after the print. `Viewport.Zoom` did not re-centre where asked, so the template does not use it. `SetViewIndependentFence` returned an error, `SetFenceFromFitRange(True)` gave a blank page.
- Output is vector: lines, arcs, dash patterns, true colours and weights come through, and text is real text.
- **Print units are inches here** (Letter 11 x 8.5 in). The template reads the print units and the master unit (m, mm, cm, ft, in), and takes the units from the view's root model, not from the active model.
- **Do not guess form names.** `SetFormName` with a name that is not in the config (we tried "A3") and `desc.GetPlotter()` each ended MicroStation without a result file. The valid names are in the `<Forms>` list of `...\MicroStation\Default\Pltcfg\pdf.pltcfg`: "ISO A0" to "ISO A4", "Arch E1", "Arch E", "Arch D" and more.
- The licence on this machine is an academic one: every page carries "[Academic use only]". Tell the engineer; it is not a bug.
- Open or measure the PDF before you say it worked. A blank page is a valid PDF.
- **Sheet models: made and attached, but printing through a sheet does not work yet.** A sheet made with `dgn.CreateNewModel(error, name, DgnModelType.eSheet, False)` took its size (`SheetDef.SetSize(420, 297)` with `SetUnits` millimetres) and an attachment of the design model with `SetStoredScale(0.005)` for 1:200 (the attached rectangle landed 25 mm in for 5 m, correct). `ModelRef.ActivateAndDisplay(sheet)` worked. But printing the sheet (`PlotAreaMode.eSheet`) used a 42 x 29.7 mm area instead of 420 x 297 mm, ten times too small, although the units of the sheet model and the design model read identical. With the sheet size given in metres instead (`SetUnits` metres, `SetSize(0.42, 0.297)`) the print units become metres, the sheet area prints at the right 420 x 297 mm, but the attached design is missing from the print (frame only), although the attachment maps design (5, 5) m to sheet (25, 25) mm and (35, 25) m to (175, 125) mm correctly. So sheet size and content each print right in one setting and wrong in the other. Not solved. Print the design model with `BOX`, `SCALE` and `PAPER` instead. A sheet whose attachment was made in one session was not found again when the file was reloaded and its attachments listed (not investigated).
- Not tested: plot styles (pen tables), a driver other than PDF, printing several views.

## Example: reference files (tested)

Template: `templates/references_body.py`. Set `ACTION` to `list`, `attach` or `detach`, and `FILE` to the full path. Tested 2026-10-29 on a throwaway copy: attach returned `status: 0` and the list showed the file (model "3D Metric Design", displayed); after MicroStation closed and a new launch, the list still showed it; detach returned `status: 0` and the list was empty. Not tested: nested references, a model other than the default, clipping, scale or rotation of the attachment (the sample shows `SetRotMatrix`), live references that the engineer has open.

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
- **Limits:** each launch is a new MicroStation, so do not aim it at a file already open in the engineer's session (not tested, expect a file lock). A job takes 18 to 35 seconds start to finish in the tests. **Two launches at the same time, on two different copies, both worked** (read-levels job, 26 seconds in total, same result as a single run, 2026-10-29). More than two, and how many licence seats an instance uses, were not checked.
- **Licence:** use route 0 on the engineer's own machine, under their own licence, while they are signed in. Bentley's EULA (version 2023-10-16) bars use "in an automated, unattended, non-interactive server application" (section 21), commercial hosting (section 5) and licence pooling (section 6). Do not run it as a server or for other people. Have the terms checked by a lawyer, or ask Bentley, before anyone sells a service built on it. One launch per job. `exit` rewrites the DGN like any close. After every job check `Get-Process microstation`: one job that wrote `GetElement().ehdr.level` and then called `ReplaceInModel` finished and wrote its result, but left a windowless MicroStation running after `exit`. Stop only instances you started. Not tested: sites that need a workspace or project on the command line (`-wu -ws -wp`), very large files, what `exit` does after a failed job or with unsaved changes, licence or start-up dialogs.
- **A file that is not part of a WorkSet stops the launch.** MicroStation shows a "No WorkSet Alert" ("This file is not part of a WorkSet. What do you want to do?") and waits for a click, so the job never runs and the launch hangs until you stop it. It happened with a raw copy of `...\MicroStation\Default\Seed\seed2d.dgn`. Copies of a drawing that MicroStation had already saved inside the active WorkSet opened without it. Start a new drawing from a copy of one the engineer already uses, or open the new file once by hand and choose. The preference or switch that would turn the alert off was not looked for.
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
