import re
import unittest

from tests.helpers import ROOT


class StyleRules(unittest.TestCase):
    def setUp(self):
        self.css = (ROOT / "style.css").read_text(encoding="utf-8")
        self.js = (ROOT / "script.js").read_text(encoding="utf-8")

    def test_no_gradients_glass_or_gradient_text(self):
        for bad in ("linear-gradient", "radial-gradient", "conic-gradient", "background-clip: text", "backdrop-filter"):
            self.assertNotIn(bad, self.css)

    def test_no_infinite_animation(self):
        self.assertNotIn("infinite", self.css)

    def test_reduced_motion(self):
        self.assertIn("prefers-reduced-motion: reduce", self.css)

    def test_dark_mode(self):
        self.assertIn("prefers-color-scheme: dark", self.css)

    def test_fade_hidden_only_with_js(self):
        for m in re.finditer(r"([^{}]*\.fade[^{}]*)\{([^}]*)\}", self.css):
            body = m.group(2).replace(" ", "")
            if "opacity:0" in body and "opacity:0." not in body:
                self.assertIn(".js", m.group(1))

    def test_no_typing_effect(self):
        self.assertNotIn("typeRole", self.js)

    def test_js_sets_js_class(self):
        self.assertIn("classList.add('js')", self.js)

    def test_gitignore_has_claude(self):
        self.assertIn(".claude/", (ROOT / ".gitignore").read_text())


if __name__ == "__main__":
    unittest.main()
