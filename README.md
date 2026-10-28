# MicroStation agent skills

Skills that teach AI agents (Claude, Codex, Hermes, ChatGPT-style agents, local models) to work with **MicroStation** the way an organization's CAD standard says, so every engineer on a team gets the same result.

Early version. Built for civil and government work: roads, buildings, utilities, city planning.

## Skills

| Skill | Use |
|---|---|
| [`microstation-standards-setup`](skills/microstation-standards-setup/SKILL.md) | **Start here.** Creates the organization's approved CAD standard in one of three ways: research it online, get a recommended starter, or define it by hand. Includes a validator. |
| [`microstation-scripting`](skills/microstation-scripting/SKILL.md) | How to drive MicroStation's built-in Python safely. |
| [`microstation-drive`](skills/microstation-drive/SKILL.md) | Lets the agent actually run work in MicroStation: wrap code as a job, run it, read the result file back. |
| [`microstation-apply-standards`](skills/microstation-apply-standards/SKILL.md) | Audit and fix drawings against the approved standard, and lock the standard for the whole team. |

## Install

Each skill is a folder with a `SKILL.md`. Copy the folders in `skills/` to where your agent reads skills.

- **Claude Code:** `~/.claude/skills/` (all projects) or `.claude/skills/` (one project).
- **Other agents** (Codex, Hermes, ...): use the agent's skills folder if it supports `SKILL.md`; otherwise paste the skill text as instructions. Check your agent's documentation.

Then tell the agent: *"Set up our MicroStation standard."*

## How the standard works

The standard is one JSON file, `standards/<org>.standards.json`: level names, colors, line styles and weights, text and dimension styles, sheets, units. It is `draft` until a person approves it. Agents refuse to work from a draft. Share the single approved file with the whole team.

Your own `standards/` folder is git-ignored, so an organization's file is not published by accident.

Check a file:

```
python skills/microstation-standards-setup/scripts/validate_standards.py standards/<org>.standards.json
```

## Roadmap

1. These skills (now).
2. A Rust command-line tool, MCP server and API so agents can run MicroStation work directly.
3. A web interface that enforces the organization's standard for every engineer.

## Status and honesty

- The facts in the skills come from public documentation and from observation of a licensed MicroStation 2026 installation (26.00.02.039). Verify on your version.
- Not everything is tested live. Each skill says what was and was not. Work on copies of your drawings.
- Recommended standards are suggestions, not official standards of any organization.

## Legal

Not affiliated with, endorsed by, or sponsored by Bentley Systems. MicroStation is a trademark of Bentley Systems, Incorporated. This repository contains no Bentley software, binaries or code. You need your own MicroStation license. MIT license, see [LICENSE](LICENSE).

## Contributing

Corrections from working engineers are the most valuable thing. Open an issue or pull request. Say which MicroStation version you tested.
