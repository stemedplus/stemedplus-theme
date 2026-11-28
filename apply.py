"""Bring a STEMEd+ site up to date with the shared look.

Run from a site's repository (its build workflow does this before building):

    python /path/to/stemedplus-theme/apply.py [site-repo-dir]

The site lists what to update in `.stemedplus-theme.json` at its root:

    {
      "asset_dirs": ["site"],
      "bars": [
        {"file": "site/index.html", "current": "https://stemedplus.github.io/stemed-funding/"}
      ]
    }

- `asset_dirs`: folders that hold copies of the theme files. Each theme file already in the
  folder is replaced with the current one; files the site does not use are not added.
- `bars`: files that contain the green band. Each band is rebuilt from menu.json, with the
  site's own menu item (`current`) marked. `logo` is the image path written into the band
  (default `stemedplus-commons-logo-white.png`). The same page also gets the STEMEd+ Commons
  footer, as on stemedplus.org: it is refreshed if the file has one, and otherwise added just
  before the first `</body>` after the band (below the site's own footer). Set `"footer": false`
  on a bar to leave its page without one. In a Python file, if adding it there would break the
  code (the page is built from short strings), put an empty slot,
  `<footer class="sp-footer"></footer>`, where the footer belongs; it is filled in from then on.
- `icon_files` (optional): pages whose `<head>` is not in a `bars` file. Every `bars` file with a
  `</head>`, and every file listed here, gets the STEMEd+ browser-tab icon (`icon/` in this
  repository): an existing `<link rel="icon">` is replaced, otherwise one is added before `</head>`.

Nothing is written unless every file can be updated, so a problem leaves the site's own copies
as they were. Exit status 1 means nothing changed.
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sp_bar  # noqa: E402

ASSETS = HERE / "assets"
CONFIG = ".stemedplus-theme.json"
FOOTER = re.compile(r'<footer class="sp-footer">.*?</footer>', re.S)
ICON = re.compile(r'<link rel="icon"[^>]*>')
BAND = re.compile(r'<div class="sp-bar"><div class="sp-in">.*?</nav>(?:<a class="sp-login"[^>]*>Log [iI]n</a>)?</div></div>',
                  re.S)


def with_footer(text: str, foot: str, name: str) -> str:
    """Refresh the STEMEd+ footer, or add it before the first </body> after the band."""
    new, n = FOOTER.subn(lambda m: foot, text)
    if n:
        return new
    band = BAND.search(text)
    end = text.find("</body>", band.end())
    if end == -1:
        raise ValueError(f"{name}: no </body> after the STEMEd+ band to put the footer before")
    return text[:end] + foot + "\n" + text[end:]


def with_icon(text: str, tag: str) -> str:
    """Refresh the browser-tab icon, or add it before </head>. A file with neither is left as it is."""
    new, n = ICON.subn(lambda m: tag, text)
    if n:
        return new
    end = text.find("</head>")
    return text if end == -1 else text[:end] + tag + text[end:]


def check_python(path: Path, text: str, name: str) -> None:
    if path.suffix == ".py":
        try:
            compile(text, str(path), "exec")
        except SyntaxError as exc:
            raise ValueError(f"{name}: would no longer be valid Python ({exc.msg}, line {exc.lineno}); "
                             "give its page a footer slot, '<footer class=\"sp-footer\"></footer>'") from exc


def plan(site: Path) -> tuple:
    """Work out every change without writing anything. Returns (text_updates, copies)."""
    config = json.loads((site / CONFIG).read_text(encoding="utf-8"))
    menu = sp_bar.load_menu()
    tag = sp_bar.icon()
    texts = {}
    for b in config.get("bars", []):
        path = site / b["file"]
        text = texts.get(path) or path.read_text(encoding="utf-8")
        band = sp_bar.bar(b.get("current", ""), b.get("logo", "stemedplus-commons-logo-white.png"), menu)
        new, n = BAND.subn(lambda m: band, text)
        if n == 0:
            raise ValueError(f"{b['file']}: no STEMEd+ band found")
        if b.get("footer", True):
            new = with_footer(new, sp_bar.footer(menu), b["file"])
        new = with_icon(new, tag)
        check_python(path, new, b["file"])
        texts[path] = new
    for f in config.get("icon_files", []):
        path = site / f
        text = texts.get(path) or path.read_text(encoding="utf-8")
        if "</head>" not in text and not ICON.search(text):
            raise ValueError(f"{f}: no </head> to put the icon before")
        new = with_icon(text, tag)
        check_python(path, new, f)
        texts[path] = new
    copies = []
    for d in config.get("asset_dirs", []):
        folder = site / d
        if not folder.is_dir():
            raise ValueError(f"{d}: not a folder")
        copies += [(src, folder / src.name) for src in sorted(ASSETS.iterdir()) if (folder / src.name).exists()]
    return texts, copies


def main(argv) -> int:
    site = Path(argv[1] if len(argv) > 1 else ".").resolve()
    try:
        texts, copies = plan(site)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"stemedplus-theme: nothing changed: {exc}", file=sys.stderr)
        return 1
    changed = []
    for path, text in texts.items():
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            changed.append(path)
    for src, dest in copies:
        if src.read_bytes() != dest.read_bytes():
            shutil.copyfile(src, dest)
            changed.append(dest)
    for path in changed:
        print(f"stemedplus-theme: updated {path.relative_to(site)}")
    if not changed:
        print("stemedplus-theme: already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
