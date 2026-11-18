import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from accessibility_pr_gate.audit import audit_html  # noqa: E402


@contextmanager
def scratch():
    path = ROOT / "tests" / ".work"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class AuditTests(unittest.TestCase):
    def test_detects_missing_names_alt_landmark_and_heading_jump(self):
        findings = audit_html('<img src="x"><input id="email"><h2>Title</h2><h4></h4>')
        rules = {item.rule for item in findings}
        self.assertTrue({"img-alt", "control-name", "main-landmark", "heading-order", "heading-name"} <= rules)

    def test_accepts_label_alt_main_and_named_button(self):
        findings = audit_html('<main><label for="q">Query</label><input id="q">'
                              '<img src="x" alt=""><button>Search</button><h1>Title</h1></main>')
        self.assertEqual([], findings)

    def test_detects_misassociated_label_and_unnamed_repeated_navigation(self):
        findings = audit_html('<label for="missing">Email</label><main><nav></nav><nav></nav></main>')
        rules = {item.rule for item in findings}
        self.assertIn("label-target", rules)
        self.assertEqual(2, sum(item.rule == "landmark-name" for item in findings))

    def test_accepts_implicitly_wrapped_control_label(self):
        self.assertEqual([], audit_html('<main><label>Email<input type="email"></label></main>'))

    def test_detects_unnamed_link_and_accepts_image_link_name(self):
        findings = audit_html('<main><a href="/empty"></a><a href="/image"><img alt="Home"></a></main>')
        self.assertEqual(["link-name"], [item.rule for item in findings])

    def test_boolean_alt_attribute_is_not_a_text_alternative(self):
        findings = audit_html("<main><img alt></main>")
        self.assertIn("img-alt", [item.rule for item in findings])

    def test_cli_json_and_threshold(self):
        with scratch() as directory:
            page = directory / "page.html"
            page.write_text("<img src='x'>", encoding="utf-8")
            run = subprocess.run([sys.executable, "-m", "accessibility_pr_gate.cli", str(page), "--format", "json"],
                                 cwd=ROOT, capture_output=True, text=True,
                                 env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
            self.assertEqual(1, run.returncode)
            self.assertEqual("img-alt", json.loads(run.stdout)["findings"][0]["rule"])


if __name__ == "__main__":
    unittest.main()
