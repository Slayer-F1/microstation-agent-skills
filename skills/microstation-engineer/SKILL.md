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
| "draw / place / add ..." | `create_elements_body.py` | line, shape, box, arc, circle, ellipse, polyline, bspline (curve through points), chain (road or pipe line with parallel offsets), dimension (linear, radius, diameter, angle), text (styles, centred, rotated), cell, shared_cell, table; any item can have its own `level`, `rgb`, `weight`, line `style` |
| "move / copy / rotate / scale / recolour / delete ..." | `modify_elements_body.py` | list first to get ids; set `expect`; ask before a delete |
| "what is in the drawing?" | `list_elements_body.py`, `list_levels_body.py` | read only |
| "make / remove a level" | `create_level_body.py`, `remove_level_body.py` | `cache.Write()`, then read back |
| "does it follow our standard?" | `microstation-apply-standards` | audit first, fix after approval |
| "give me a PDF" | `plot_pdf_body.py` | set `BOX` (area), `SCALE` (1:N) and `PAPER` ("ISO A3", exact name); measure or open the PDF; warn that printing can be slow |
| "attach / detach a reference" | `references_body.py` | full path of the file |
| anything else | `microstation-scripting` | write a new job body; check names in the stubs |

## From a diagram, sketch or description

The reading of the picture is your own judgement. It is **not verified by any test**, so check it with the engineer.
1. State what you read: the scale, the units and one dimension you can see. Ask the engineer to confirm that one dimension before you place anything.
2. Turn it into a plan in master units. Walls, rooms and outlines become shapes or polylines, circles and arcs stay circles and arcs, labels become text, repeated parts become cells. Give each item its level from the standard.
3. Place in small batches (at most about 50 items per job) on a copy. After each batch read back and compare ranges with the plan.
4. Add dimensions for the key lengths and text for room or part names, then make the PDF and show it.
5. Keep the plan file next to the drawing so the next change can start from it.

Tested once, 2026-10-30: a fresh agent was given only this skill, the template header and a drawn "hand" sketch of a three-room house with a known truth (jittered lines, dimension notes 10.00 m, 7.00 m, 4.00 and 3.50, the note "walls ~ 0.3 m thick", three doors, three windows). It asked the right question (is 10.00 m outside face to outside face?), listed every assumption, and its plan, placed in MicroStation, matched the truth: outline 10.00 x 7.00, the three door gaps and three window gaps at the right places (within 0.1 m), three room labels, four dimensions with the right values and outside the building. The read job after the close found the 34 elements as planned. It also showed a gap, now fixed in the template header: nothing said which side a positive dimension offset falls on. Wall pieces are separate shapes, so seam lines show where they meet. Not tested: a real hand sketch, a photo or a scan, a rotated or skewed page, a sketch without dimension notes. Ask whether a sketch dimension is outside face or wall centre line: it moves everything by half a wall.

## Rules

- Master units only. Work on copies. Real work uses the levels, colours and weights of the approved standard; the test level `ZZ-AGENT-TEST` is for tests only.
- Never delete without showing the matched ids and getting a yes. Never edit an original.
- Never hide a failed item. The create and modify templates keep going after one bad item; report each one.
- If a job leaves a MicroStation window or process behind, stop only the one you started (`microstation-drive`, route 0 limits).
- Say plainly when something was not tested. Not working or not tested yet: printing through a sheet model (made, attached at a scale, but the printed area is ten times too small), named custom line styles, annotation scale, civil or building-specific features beyond plain geometry (no alignments, profiles, parametric doors or windows), rendering, elements inside references, two people editing one file. A file that is not part of a WorkSet stops the launch (see `microstation-drive`, route 0).

## What a good answer looks like

"I placed 14 elements on levels A-WALL and A-TEXT in `plan-v2.dgn` (a copy of `plan.dgn`). I read them back: all 14 ranges match the plan. The PDF is at `...\plot.pdf`; I opened it and the walls and labels show. I did not check text size and the plot scale. The licence adds an 'Academic use only' mark to the PDF."
