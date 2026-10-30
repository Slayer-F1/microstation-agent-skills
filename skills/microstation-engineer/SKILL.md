---
name: microstation-engineer
description: Use first when an engineer asks, in plain words, to design, draw, edit, check or deliver something in MicroStation (a plan, a layout, a sheet, a PDF, a fix to a drawing). Gives the working order - understand, get the standard, plan, confirm, run, verify, report - and sends each request to the right skill and template.
---

# Work like a MicroStation engineer

This is the front door. Read it first, then use the skill it points to. It adds no new API; every action below was run on MicroStation 2026 and is recorded in `microstation-drive`.

## The order of work (always)

1. **Understand.** Find out the file, the units, the scale, the standard and the output. Ask one question at a time, only for what you cannot decide. Never guess a file path. If the engineer gave a picture or a sketch, see "From a diagram" below.
2. **Standard.** No approved standard yet and the task depends on one: run `microstation-standards-setup` first. Otherwise load the approved one (levels, colours, weights, text sizes) and use only its names.
3. **Plan.** Write the plan as a list of items in master units (the `SPEC` format of `microstation-drive`). Show the engineer a short summary: how many elements by type and level, and the overall size. List every assumption you made (scale, origin, units).
4. **Confirm.** Say which copy of which file will change. Wait for a clear yes. Work on a copy, never the original.
5. **Run.** Use `microstation-drive`: wrap the template as a job, run it, read the result file.
6. **Verify.** Read back with a separate job and compare ranges and counts with the plan. For a drawing someone will print, make the PDF and look at it.
7. **Report** in plain words: what changed, where the copy is, what you checked, what you did not check.

## Which template for which request

| The engineer says | Use | Notes |
|---|---|---|
| "draw / place / add ..." | `create_elements_body.py` | line, shape, box, arc, circle, ellipse, polyline, dimension, text, cell |
| "move / copy / rotate / scale / recolour / delete ..." | `modify_elements_body.py` | list first to get ids; set `expect`; ask before a delete |
| "what is in the drawing?" | `list_elements_body.py`, `list_levels_body.py` | read only |
| "make / remove a level" | `create_level_body.py`, `remove_level_body.py` | `cache.Write()`, then read back |
| "does it follow our standard?" | `microstation-apply-standards` | audit first, fix after approval |
| "give me a PDF" | `plot_pdf_body.py` | open the PDF and look; warn that printing can be slow |
| "attach / detach a reference" | `references_body.py` | full path of the file |
| anything else | `microstation-scripting` | write a new job body; check names in the stubs |

## From a diagram, sketch or description

The reading of the picture is your own judgement. It is **not verified by any test**, so check it with the engineer.
1. State what you read: the scale, the units and one dimension you can see. Ask the engineer to confirm that one dimension before you place anything.
2. Turn it into a plan in master units. Walls, rooms and outlines become shapes or polylines, circles and arcs stay circles and arcs, labels become text, repeated parts become cells. Give each item its level from the standard.
3. Place in small batches (at most about 50 items per job) on a copy. After each batch read back and compare ranges with the plan.
4. Add dimensions for the key lengths and text for room or part names, then make the PDF and show it.
5. Keep the plan file next to the drawing so the next change can start from it.

## Rules

- Master units only. Work on copies. Real work uses the levels, colours and weights of the approved standard; the test level `ZZ-AGENT-TEST` is for tests only.
- Never delete without showing the matched ids and getting a yes. Never edit an original.
- Never hide a failed item. The create and modify templates keep going after one bad item; report each one.
- If a job leaves a MicroStation window or process behind, stop only the one you started (`microstation-drive`, route 0 limits).
- Say plainly when something was not tested. Not tested yet: shared cells, B-splines, text tables, line styles, RGB colours, text styles, annotation scale, sheet models and plot scale, angular and radial dimensions, civil or building-specific features, rendering, elements inside references, two people editing one file.

## What a good answer looks like

"I placed 14 elements on levels A-WALL and A-TEXT in `plan-v2.dgn` (a copy of `plan.dgn`). I read them back: all 14 ranges match the plan. The PDF is at `...\plot.pdf`; I opened it and the walls and labels show. I did not check text size and the plot scale. The licence adds an 'Academic use only' mark to the PDF."
