# Runbook: Shared look (stemedplus-theme)

A runbook is a short card that lets someone who didn't build a board keep it running. This one covers the shared look, and also how every STEMEd+ board works. Each board has its own `RUNBOOK.md` that links back here.

## How every board works

Each board is a GitHub repository in the **stemedplus** organization, published with GitHub Pages at `stemedplus.github.io/<repo>`. A GitHub Actions workflow (in `.github/workflows/`) rebuilds it on a daily schedule, on every push, and whenever you press **Run workflow**. Each run:

1. **Refreshes the shared look**: clones `stemedplus-theme` and runs `apply.py`, which updates the STEMEd+ menu bar, footer, and styles. If the theme can't be reached, the board builds with its own copies.
2. **Refreshes the discipline list** from HuMeta (most boards).
3. **Runs the tests** and checks every listing file against its schema.
4. **Builds the site** into `output/` and publishes it to Pages.

**Adding listings.** People use the board's **Suggest** or **Add** link, which opens a GitHub issue form (or a prefilled email for people without GitHub). A maintainer turns the issue into a listing file and pushes it. Jobs is the exception: its form adds the job automatically.

**Who maintains them.** Julie Libarkin and Linnea Beckett, the stemedplus organization owners. Submission emails go to libarkin@msu.edu.

### Common fixes

| Problem | What to do |
|---|---|
| A board stopped updating | Open the repository's **Actions** tab, find the red run, and open the failed step. Fix the cause, then press **Run workflow**. |
| A listing file fails its check | The log names the file and field. Fix the YAML or JSON (a missing date, a bad URL, a typo in a field name) and push. |
| A test fails after a code change | Revert the change in Git, or fix it on a branch first. stemed-jobs requires a pull request with passing tests. |
| An outside feed or API is down | Usually nothing: the next daily run picks it up. If a source has moved for good, update its URL in `config/` and the Source and Permissions Log. |
| The menu or footer looks wrong | Fix it once in `stemedplus-theme` (`menu.json` or `sp_bar.py`), then re-run each board, or wait for the next daily run. |
| The site is down but the run is green | Check **Settings → Pages**: the source should be **GitHub Actions**. |
| A repository was deleted | Restore it within 90 days in the organization's settings (see the Backup Plan). |

**Running locally.** In any Python board: `pip install -r requirements.txt`, then `python -m unittest discover -s tests -t .`, then the build command on its card. Open `output/index.html` through a local web server.

**Home page shortcuts.** The "Shortcuts for you" box on the stemedplus.org home page links to boards with a filter already chosen, by putting the filter's value in the address (for example `stemed-funding/#kind=K-12%20and%20teachers`). If you rename or remove one of the values below, update its link in the home page's Custom HTML block, or the shortcut opens the board unfiltered.

| Board | Filter | Values the shortcuts use |
|---|---|---|
| Funding | `kind` | K-12 and teachers · Outreach and informal learning · Teaching and curriculum · Students and training · Research |
| Professional Development | `audience` | K-12 teachers · Informal educators · Faculty and instructors · Graduate students and postdocs |
| Awards | `level`, `recognizes` | K-12 · Informal and public (level); Teaching (recognizes) |
| Jobs | `aud` | teaching · postdocs |
| Conferences | `kind` | education |

## This repository

| | |
|---|---|
| **Repository** | stemedplus/stemedplus-theme |
| **What it holds** | `menu.json` (the menu), `sp_bar.py` (builds the bar and footer), `assets/` (styles), `apply.py` (what each board runs) |
| **Tests** | Run on every push and pull request, and weekly on Mondays at 12:23 UTC (`tests.yml`). The weekly run also checks that every HuMeta discipline term in use still exists and isn't deprecated. |

**Change the menu:** edit `menu.json`, push, and let tests pass. Each board picks it up on its next run; re-run a board to see it sooner.

**Add a new board to the shared look:** follow "Adding a site" in the README: copy the assets, add `.stemedplus-theme.json`, add the refresh step to the board's workflow, and add the board to `menu.json`.

**Remember the WordPress side:** the menu and footer on stemedplus.org and member sites are pasted in by hand from Build Your STEMEd+ Site, so a menu change here also needs the footer code updated there.

## Redirect repositories

| Repository | What it does |
|---|---|
| stemed-faculty-development | Sends visitors to Professional Development, keeping their filters; copies its calendar and RSS daily so old subscriptions keep working |
| stemed-professional-learning | The same, for the old K-12 and informal list |
| JLib271/jlib271.github.io | Forwards every old jlib271.github.io link to stemedplus.github.io, and serves old image addresses. **Keep it forever.** |

These need no routine work. If a redirect breaks, check its daily `redirect.yml` run.

_Written November 2026. Review with the yearly December review._
