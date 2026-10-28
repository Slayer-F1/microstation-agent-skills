---
name: microstation-scripting
description: Use when an AI agent must read, create or change MicroStation design files (DGN) by script, run key-ins, or automate work in MicroStation 2026 (CONNECT Edition lineage). Covers where MicroStation's Python lives, the import order that must not be broken, how to find the real API, how to run key-ins from Python, and the safe way to work on a drawing. Load microstation-standards-setup first if the organization has no approved standard.
---

# MicroStation scripting with Python

Status of the facts below: observed on MicroStation 2026 (26.00.02.039). Other versions may differ. Check on the engineer's machine before relying on any path or name.

## Before you touch a drawing

1. Is there an **approved** `standards/*.standards.json`? If not, run `microstation-standards-setup` first.
2. Work on a **copy** of the DGN. Never the original, never a drawing someone has open.
3. Say what the script will change before it runs. Get a yes.

## How MicroStation runs Python

- Python runs **inside the MicroStation process** (a Bentley build of CPython 3.12). It is not a normal external Python.
- The engineer can open it with *Utilities > Python Editor* (run scripts there), or run a saved file with the key-in:
  `PYTHON LOAD "C:\path\to\script.py"`
- `print()` goes to MicroStation's Python console.
- An agent outside MicroStation cannot call the API directly. The agent writes the script; the engineer runs it in MicroStation and pastes the console output back. (A command-line bridge is on this repository's roadmap.)

## Where things are

| What | Usual location |
|---|---|
| Python runtime | `C:\ProgramData\Bentley\PowerPlatformPython` |
| About 190 sample scripts | `C:\ProgramData\Bentley\PowerPlatformPython\Examples\Microstation` |
| API stub files (`.pyi`, six of them) | in the same Examples folder |

The stubs are the API reference. **Search them before using any class or method.** Do not guess names. If a name is not in the stubs, it does not exist for this version.

## The six modules and the import order

| Module | Holds |
|---|---|
| `MSPyBentley` | base utilities |
| `MSPyBentleyGeom` | geometry (points, curves, surfaces, transforms) |
| `MSPyECObjects` | EC data and schemas |
| `MSPyDgnPlatform` | files, models, elements, levels, symbology |
| `MSPyDgnView` | views and tools |
| `MSPyMstnPlatform` | the application: key-ins, printing, MicroStation-level services |

**Import them in exactly this order**, as the editor's *New* script template does:
`MSPyBentley`, `MSPyBentleyGeom`, `MSPyECObjects`, `MSPyDgnPlatform`, `MSPyDgnView`, `MSPyMstnPlatform`.

A wrong order raises an `ImportError` and then **every later import fails** ("type ... is already registered") until MicroStation is restarted. Never retry a failed import in the same session; tell the engineer to restart MicroStation.

## Key-ins from Python

`PyCadInputQueue.SendKeyin(...)` (in `MSPyMstnPlatform`; confirm the exact signature in the stubs) does what the Key-in window does. It **returns only when the key-in has finished**, so a long job (printing, for example) blocks the script and MicroStation until done. Warn the engineer before long jobs.

## Workflow for any change

1. Read first: print what exists (levels, elements, model names). Show it.
2. Plan the change in plain words and in numbers ("rename 12 levels, recolor 5").
3. Change a copy in small steps.
4. Read back and compare with the plan. Report the difference, even if it is zero.
5. Save under a new name. Keep the original.

## Rules

- Do not bypass script signing or security settings. If the organization uses signed scripts, ask IT to sign yours.
- Do not start background network listeners or pipes in MicroStation unless the engineer explicitly asks.
- Never delete user data to make a script work.
- If the API does not support something, say so. Do not fake it with undocumented tricks.
- Sample scripts in the Examples folder are the best recipes. Copy their pattern.
