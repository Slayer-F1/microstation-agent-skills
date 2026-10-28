#!/usr/bin/env python3
"""Validate an organization CAD standards file. Standard library only.

Usage: python validate_standards.py <file.standards.json>
Exit code 1 if any ERROR. Keys starting with "_" are comments and ignored.
"""
import json
import re
import sys

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
MIN_CONTRAST = 3.0  # WCAG minimum for graphical objects


def luminance(hexcolor):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(hexcolor, background):
    a, b = luminance(hexcolor), (0.0 if background == "black" else 1.0)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def validate(doc):
    errors, warns = [], []
    err, warn = errors.append, warns.append

    org = doc.get("organization") or {}
    meta = doc.get("meta") or {}
    if not org.get("name"):
        err("organization.name is missing")
    if meta.get("status") not in ("draft", "approved"):
        err("meta.status must be 'draft' or 'approved'")
    if meta.get("source") not in ("researched", "recommended", "manual"):
        err("meta.source must be 'researched', 'recommended' or 'manual'")
    if meta.get("status") == "approved":
        for k in ("version", "approved_by", "approved_on"):
            if not meta.get(k):
                err(f"approved standard needs meta.{k}")
    if meta.get("source") == "researched" and not meta.get("references"):
        err("source 'researched' needs meta.references (url, title, accessed)")
    background = doc.get("view_background")
    if background not in ("black", "white"):
        err("view_background must be 'black' or 'white'")
    if not (doc.get("units") or {}).get("master"):
        err("units.master is missing")

    pattern = None
    pattern_text = (doc.get("level_naming") or {}).get("pattern")
    if not pattern_text:
        err("level_naming.pattern is missing")
    else:
        try:
            pattern = re.compile(pattern_text)
        except re.error as e:
            err(f"level_naming.pattern is not a valid regex: {e}")

    levels = doc.get("levels") or []
    if not levels:
        err("levels is empty")
    seen, looks = set(), {}
    for lv in levels:
        name = lv.get("name", "")
        if not name:
            err("a level has no name")
            continue
        if name in seen:
            err(f"duplicate level name {name}")
        seen.add(name)
        if pattern is not None and not pattern.match(name):
            err(f"level {name} does not match level_naming.pattern")
        w = lv.get("weight")
        if not isinstance(w, int) or isinstance(w, bool) or not 0 <= w <= 31:
            err(f"level {name}: weight must be an integer 0-31")
        rgb = (lv.get("color") or {}).get("rgb", "")
        if not HEX.match(rgb):
            err(f"level {name}: color.rgb must look like #RRGGBB")
            continue
        looks.setdefault((rgb.upper(), str(lv.get("style")), w), []).append(name)
        for bg in ("black", "white"):
            if contrast(rgb, bg) < MIN_CONTRAST:
                where = "your view background" if bg == background else "a " + bg + " background"
                warn(f"level {name}: {rgb} is hard to see on {where} (contrast {contrast(rgb, bg):.1f}:1)")
    for names in looks.values():
        if len(names) > 1:
            warn("levels look identical (same color, style, weight): " + ", ".join(names))

    texts = doc.get("text_styles") or []
    tnames = [t.get("name") for t in texts]
    if len(set(tnames)) != len(tnames):
        err("duplicate text style name")
    for t in texts:
        if not isinstance(t.get("height_mm"), (int, float)) or t["height_mm"] <= 0:
            err(f"text style {t.get('name')}: height_mm must be > 0")
    for d in doc.get("dimension_styles") or []:
        if d.get("text_style") not in tnames:
            err(f"dimension style {d.get('name')}: text_style {d.get('text_style')} does not exist")
    return errors, warns


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR cannot read {argv[1]}: {e}")
        return 1
    errors, warns = validate(doc)
    for m in errors:
        print("ERROR", m)
    for m in warns:
        print("WARN ", m)
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
