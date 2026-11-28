import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import apply  # noqa: E402
import sp_bar  # noqa: E402

FUNDING = "https://stemedplus.github.io/stemed-funding/"
OLD_BAND = ('<div class="sp-bar"><div class="sp-in"><a class="sp-logo" href="https://stemedplus.org/">old</a>'
            '<nav class="sp-nav">old menu</nav><a class="sp-login" href="x">Log In</a></div></div>')


def make_site(tmp: Path, config: dict, page: str = None) -> Path:
    site = tmp / "site-repo"
    (site / "site").mkdir(parents=True)
    (site / "site" / "index.html").write_text(page or f"<html><body>{OLD_BAND}<main>Hi</main></body></html>")
    (site / "site" / "stemedplus-theme.css").write_text("/* old */")
    (site / apply.CONFIG).write_text(json.dumps(config))
    return site


class MenuTests(unittest.TestCase):
    def test_menu_is_valid_and_lists_every_site(self):
        menu = sp_bar.load_menu()
        urls = [s["url"] for item in menu["items"] for s in item.get("submenu", [])]
        urls += [s["url"] for item in menu["items"] for g in item.get("groups", []) for s in g["links"]]
        for site in ("stemed-funding", "STEMEd-Digest", "stemed-deadlines", "stemed-professional-development",
                     "stemed-collaborators", "stemed-conferences", "stem-ed-research-programs"):
            self.assertTrue(any(site in u for u in urls), site)

    def test_band_marks_the_current_site(self):
        band = sp_bar.bar(FUNDING)
        self.assertIn(f'href="{FUNDING}" aria-current="page"', band)
        self.assertIn('sp-here"', band)
        self.assertEqual(band.count('aria-current="page"'), 1)

    def test_find_is_one_grouped_panel(self):
        band = sp_bar.bar(FUNDING)
        self.assertIn('class="sp-has sp-has-mega sp-here"', band)
        self.assertIn('<button type="button" class="sp-label" aria-haspopup="true">Find</button>', band)
        for heading in ("Careers &amp; Learning", "Research &amp; Funding", "People &amp; Communities", "Library"):
            self.assertIn(f'<p class="sp-head">{heading}</p>', band)
        self.assertIn('<li class="sp-btn"><a href="https://stemedplus.org/join-stemed/">Join STEMEd+</a></li>', band)

    def test_group_without_heading_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "menu.json"
            menu = sp_bar.load_menu()
            menu["items"] = [{"label": "Find", "groups": [{"links": [{"label": "A", "url": "https://a.org/"}]}]}]
            bad.write_text(json.dumps(menu))
            with self.assertRaises(ValueError):
                sp_bar.load_menu(bad)

    def test_bad_menu_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "menu.json"
            bad.write_text(json.dumps({"login": "https://x", "items": [{"label": "A", "url": "http://insecure"}]}))
            with self.assertRaises(ValueError):
                sp_bar.load_menu(bad)


class ApplyTests(unittest.TestCase):
    def test_updates_band_and_existing_assets_only(self):
        with tempfile.TemporaryDirectory() as d:
            site = make_site(Path(d), {"asset_dirs": ["site"], "bars": [{"file": "site/index.html", "current": FUNDING}]})
            self.assertEqual(apply.main(["apply.py", str(site)]), 0)
            page = (site / "site" / "index.html").read_text()
            self.assertIn(sp_bar.bar(FUNDING), page)
            self.assertIn("<main>Hi</main>", page)
            self.assertEqual((site / "site" / "stemedplus-theme.css").read_bytes(),
                             (apply.ASSETS / "stemedplus-theme.css").read_bytes())
            self.assertFalse((site / "site" / "manrope.woff").exists())

    def test_custom_logo_path(self):
        with tempfile.TemporaryDirectory() as d:
            site = make_site(Path(d), {"bars": [{"file": "site/index.html", "logo": "{root}assets/logo.png"}]})
            apply.main(["apply.py", str(site)])
            self.assertIn('src="{root}assets/logo.png"', (site / "site" / "index.html").read_text())

    def test_problem_changes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            site = make_site(Path(d), {"asset_dirs": ["site"],
                                       "bars": [{"file": "site/index.html"}, {"file": "site/missing.html"}]})
            before = (site / "site" / "index.html").read_text()
            self.assertEqual(apply.main(["apply.py", str(site)]), 1)
            self.assertEqual((site / "site" / "index.html").read_text(), before)
            self.assertEqual((site / "site" / "stemedplus-theme.css").read_text(), "/* old */")

    def test_file_without_band_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            site = make_site(Path(d), {"bars": [{"file": "site/index.html"}]}, page="<html>no band</html>")
            self.assertEqual(apply.main(["apply.py", str(site)]), 1)

    def test_runs_as_a_script(self):
        with tempfile.TemporaryDirectory() as d:
            site = make_site(Path(d), {"bars": [{"file": "site/index.html"}]})
            run = subprocess.run([sys.executable, str(ROOT / "apply.py"), str(site)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("updated site/index.html", run.stdout)


class FooterTests(unittest.TestCase):
    def test_footer_matches_stemedplus_org(self):
        foot = sp_bar.footer()
        self.assertTrue(foot.startswith('<footer class="sp-footer">'))
        for text in ("Knowledge Commons", "OAC-2226271", "DRL-2321946", "OAC-2531819", "Jenison Fund"):
            self.assertIn(text, foot)

    def test_footer_counts_visits_once(self):
        foot = sp_bar.footer()
        self.assertEqual(foot.count("stemedplus.goatcounter.com/count"), 1)
        self.assertTrue(foot.endswith("</script></footer>"))
        for ch in "{}`'\\":
            self.assertNotIn(ch, foot)

    def test_footer_is_added_once_below_the_page_and_then_refreshed(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = f"<html><body>{OLD_BAND}<main>Hi</main><footer>Site footer</footer></body></html>"
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html", "current": FUNDING}]}, page)
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            html = (site / "site" / "index.html").read_text()
            self.assertEqual(html.count('class="sp-footer"'), 1)
            self.assertLess(html.index("Site footer"), html.index('class="sp-footer"'))
            self.assertLess(html.index('class="sp-footer"'), html.index("</body>"))

    def test_footer_can_be_left_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html", "current": FUNDING, "footer": False}]})
            apply.main(["apply", str(site)])
            self.assertNotIn("sp-footer", (site / "site" / "index.html").read_text())

    def test_page_without_body_end_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html", "current": FUNDING}]},
                             f"<html><body>{OLD_BAND}<main>Hi</main>")
            before = (site / "site" / "index.html").read_text()
            self.assertEqual(apply.main(["apply", str(site)]), 1)
            self.assertEqual((site / "site" / "index.html").read_text(), before)

    def test_python_template_that_would_break_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "build.py", "current": FUNDING}]})
            src = f"BAR = '{OLD_BAND}'\nPAGE = [\"<main>\", \"</body>\"]\n"
            (site / "build.py").write_text(src)
            self.assertEqual(apply.main(["apply", str(site)]), 1)
            self.assertEqual((site / "build.py").read_text(), src)

    def test_python_template_footer_slot_is_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "build.py", "current": FUNDING}]})
            (site / "build.py").write_text(f"BAR = '{OLD_BAND}'\nFOOT = '<footer class=\"sp-footer\"></footer>'\n"
                                           "PAGE = [\"<main>\", FOOT, \"</body>\"]\n")
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            namespace = {}
            exec((site / "build.py").read_text(), namespace)
            self.assertIn("OAC-2226271", namespace["FOOT"])



class LoginSpellingTests(unittest.TestCase):
    def test_band_is_found_with_either_login_spelling(self):
        import apply
        for label in ("Log in", "Log In"):
            page = f'<div class="sp-bar"><div class="sp-in">x</nav><a class="sp-login" href="y">{label}</a></div></div>'
            self.assertTrue(apply.BAND.search(page), label)

if __name__ == "__main__":
    unittest.main()


class IconTests(unittest.TestCase):
    def test_icon_is_added_once_to_the_head_and_then_refreshed(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = f"<html><head><title>T</title></head><body>{OLD_BAND}<main>Hi</main></body></html>"
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html", "current": FUNDING}]}, page)
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            html = (site / "site" / "index.html").read_text()
            self.assertEqual(html.count('rel="icon"'), 1)
            self.assertLess(html.index('rel="icon"'), html.index("</head>"))
            self.assertIn("data:image/png;base64,", html)

    def test_old_icon_is_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = f'<html><head><link rel="icon" href="old.ico"></head><body>{OLD_BAND}</body></html>'
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html"}]}, page)
            apply.main(["apply", str(site)])
            html = (site / "site" / "index.html").read_text()
            self.assertNotIn("old.ico", html)
            self.assertEqual(html.count('rel="icon"'), 1)

    def test_page_without_head_is_left_without_icon(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html"}]})
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            self.assertNotIn('rel="icon"', (site / "site" / "index.html").read_text())

    def test_icon_files_get_the_icon(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html"}], "icon_files": ["site/board.html"]})
            (site / "site" / "board.html").write_text("<html><head><title>B</title></head><body></body></html>")
            self.assertEqual(apply.main(["apply", str(site)]), 0)
            self.assertEqual((site / "site" / "board.html").read_text().count('rel="icon"'), 1)

    def test_icon_file_without_head_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = make_site(Path(tmp), {"bars": [{"file": "site/index.html"}], "icon_files": ["site/board.html"]})
            (site / "site" / "board.html").write_text("<p>no head</p>")
            before = (site / "site" / "index.html").read_text()
            self.assertEqual(apply.main(["apply", str(site)]), 1)
            self.assertEqual((site / "site" / "index.html").read_text(), before)

    def test_icon_tag_fits_in_code_templates(self):
        tag = sp_bar.icon()
        for ch in "{}`'\\":
            self.assertNotIn(ch, tag)

