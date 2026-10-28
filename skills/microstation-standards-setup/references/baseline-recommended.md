# Recommended starter standard (Option B)

Data: `templates/baseline-recommended.standards.json`. Copy it, keep only the disciplines the engineer needs, then adjust together.

This is a recommendation. It is not the standard of any organization, authority or software vendor. Say so to the engineer.

## Why it looks this way

| Choice | Reason |
|---|---|
| Level names `DISCIPLINE-ELEMENT[-DETAIL]` | Sort together in the level list; the first part tells who owns the level. |
| Colors with contrast of at least 3:1 on both black and white | Readable on screen (black view) and in review (white view). The validator checks this. |
| Pure white, black and pale yellow/cyan avoided | They vanish on one of the two backgrounds. |
| Line weight carries meaning (0 thin ... 5 heavy) | Drawings stay readable when printed in black and white. |
| No two levels with the same color, style and weight | Reviewers can tell them apart on screen and on paper. |
| `G-CONSTRUCTION` is `plot: false` | Helper geometry never reaches a printed sheet. |

## Things to confirm with the engineer

- Discipline codes (`RD`, `UT`, `BL`, `SV`, `G`) match local habit; change them if the team uses others, and update `level_naming.pattern` to match.
- Units, sheet sizes and scales.
- Built-in line style codes (`0`, `3`, `7`, ...): confirm the names in the engineer's own MicroStation install.
- Text font. `Arial` is a placeholder; Arabic or other scripts may need another font.
- Whether a client or authority requires its own standard. If yes, use Option A or C instead.
