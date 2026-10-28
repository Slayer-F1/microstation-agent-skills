import json
import os
import sys
import tempfile
import types
import unittest

import make_job


def run(body):
    """Execute a generated job with fake MicroStation modules; return the result file content."""
    saved = {m: sys.modules.get(m) for m in make_job.IMPORT_ORDER}
    for m in make_job.IMPORT_ORDER:
        sys.modules[m] = types.ModuleType(m)
    try:
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.json")
            exec(compile(make_job.make_job(body, path), "job", "exec"), {})
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    finally:
        for m, old in saved.items():
            if old is None:
                sys.modules.pop(m, None)
            else:
                sys.modules[m] = old


class MakeJob(unittest.TestCase):
    def test_success_returns_result_and_stdout(self):
        r = run("print('hi')\nresult = {'n': 2 + 2}")
        self.assertEqual((r["ok"], r["result"], r["stdout"].strip(), r["error"]),
                         (True, {"n": 4}, "hi", None))

    def test_failure_still_writes_result_with_traceback(self):
        r = run("raise ValueError('boom')")
        self.assertFalse(r["ok"])
        self.assertIn("boom", r["error"])

    def test_multiline_body_with_blocks(self):
        r = run("total = 0\nfor i in range(3):\n    total += i\nresult = total")
        self.assertEqual(r["result"], 3)

    def test_imports_are_in_the_required_order(self):
        job = make_job.make_job("pass", "r.json")
        pos = [job.index(f"from {m} import") for m in make_job.IMPORT_ORDER]
        self.assertEqual(pos, sorted(pos))

    def test_bad_body_syntax_is_caught_before_microstation(self):
        with self.assertRaises(SyntaxError):
            compile(make_job.make_job("def (", "r.json"), "job", "exec")


if __name__ == "__main__":
    unittest.main()
