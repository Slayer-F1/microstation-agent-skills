---
name: microstation-apply-standards
description: Use after microstation-standards-setup has produced an approved standards file, when a MicroStation drawing must be checked or brought into line with the organization's standard (levels, colors, line styles, weights), or when the standard must be made the same for every engineer in the team. Audits first, changes only with permission, and explains how to lock the standard organization-wide.
---

# Apply the organization's standard in MicroStation

Needs: an approved `standards/<org>.standards.json` (`meta.status = "approved"`). If it is `draft` or missing, stop and use `microstation-standards-setup`. For running scripts, follow `microstation-scripting`.

Status of the facts: observed on MicroStation 2026 (26.00.02.039). Level creation through the Python API was **not exercised live** by the authors of this skill. Always test on a copy and read the result back.

## Three jobs, in this order

### 1. Audit (read only)

Compare the drawing with the standard and report, without changing anything:

- Levels in the drawing that are not in the standard.
- Standard levels missing from the drawing.
- Levels whose color, style or weight differ from the standard.
- Elements whose own color/style/weight override the level (by-level vs. fixed).
- Text and dimension styles that are not in the standard.

Output a table with counts first, then details. Ask which findings to fix.

### 2. Fix (only what the engineer approved)

On a copy: create missing levels, set the standard symbology, move or recolor as approved. For each step find the real call in the Python stubs (search for `Level`, `LevelCache`, symbology classes). The Level Manager key-ins (`LEVELMANAGER ...`, `LEVEL SET ...` families) exist too; check the exact text in the engineer's Key-in window before using them. Report what changed and what did not.

Do not delete levels that contain elements. Propose a move or a review instead.

### 3. Make it the same for everyone

An audit fixes one drawing. To stop colleagues drifting apart, the standard must live where MicroStation loads it for everyone:

- MicroStation reads configuration in levels, lowest to highest priority: System, Application, **Organization**, WorkSpace, WorkSet, Role, User. A higher level can override a lower one.
- A variable set at Organization level can be frozen with the `%lock` directive, so WorkSpace, WorkSet and User files cannot change it.
- Level libraries and seed files are found through configuration variables (the `MS_DGNLIBLIST` family and the level-library folder variable; confirm names in *Manage Configurations* or the variables dialog on the engineer's install).
- So the shape is: one shared folder owned by the standard's owner, containing the DGNLIB (levels, styles, cells) and seed; Organization-level `.cfg` that points to it and locks it; every engineer opens work through the organization's WorkSpace and WorkSet.

Explain this plan to the engineer and to whoever administers MicroStation. Do not edit organization configuration yourself unless the administrator asks you to, and keep a backup of any file you change.

## Report format

```
Standard: <org> v<version> (approved <date>)
Drawing: <file> (copy)
Found: N differences   Fixed: N   Left for review: N
<table of changes>
```

## Rules

- Never apply a draft standard.
- The standard wins over the agent's taste and over a single engineer's preference. If someone wants an exception, send it to the standard's owner as a change request.
- Audits are free; changes need a yes.
