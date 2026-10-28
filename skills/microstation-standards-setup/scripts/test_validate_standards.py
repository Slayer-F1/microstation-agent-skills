import copy
import json
import os
import unittest

import validate_standards as v

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "..", "templates", "baseline-recommended.standards.json")


def load():
    with open(BASELINE, encoding="utf-8") as f:
        return json.load(f)


class ValidateStandards(unittest.TestCase):
    def test_baseline_has_no_errors_or_warnings(self):
        self.assertEqual(v.validate(load()), ([], []))

    def test_bad_name_color_weight_are_errors(self):
        d = load()
        d["levels"][0]["name"] = "bad name"
        d["levels"][1]["color"]["rgb"] = "red"
        d["levels"][2]["weight"] = 99
        errors, _ = v.validate(d)
        self.assertEqual(len(errors), 3)

    def test_duplicate_level_is_error(self):
        d = load()
        d["levels"].append(copy.deepcopy(d["levels"][0]))
        self.assertTrue(any("duplicate level" in e for e in v.validate(d)[0]))

    def test_approved_needs_approver_and_researched_needs_references(self):
        d = load()
        d["meta"]["status"] = "approved"
        d["meta"]["source"] = "researched"
        d["meta"]["version"] = ""
        errors, _ = v.validate(d)
        self.assertEqual(len(errors), 4)

    def test_low_contrast_warns_only_on_the_bad_background(self):
        d = load()
        d["levels"][0]["color"]["rgb"] = "#101010"
        errors, warns = v.validate(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("your view background" in w for w in warns))

    def test_dimension_style_needs_existing_text_style(self):
        d = load()
        d["dimension_styles"][0]["text_style"] = "NOPE"
        self.assertEqual(len(v.validate(d)[0]), 1)


if __name__ == "__main__":
    unittest.main()
