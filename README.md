# STEMEd+ shared look

The look shared by the STEMEd+ Commons sites on GitHub Pages, matching https://stemedplus.org:
a green band with the white STEMEd+ Commons logo and the stemedplus.org menu, the Manrope
typeface, green accents, and rounded buttons.

This is the one place to change it. Each site keeps its own copy of these files, so it always
builds even if this repository can't be reached. Each site's build workflow runs `apply.py` first,
which replaces those copies with the current ones here. **A change merged here appears on every
site at its next build** (most sites build daily).

## What's here

| File | What it is |
|---|---|
| `menu.json` | The STEMEd+ Commons menu: Start here, Find (one wide panel of headed groups), Build, Share, About, and a Join button, plus the Log in link. An item can be a link, a link or label with a `submenu`, a label with `groups` (each a `heading` and `links`), or a link with `"button": true`. Every site picks up changes on its next build. |
| `sp_bar.py` | Builds the green band's HTML from `menu.json`, marking the current site's menu item. Needs no JavaScript. `python sp_bar.py <site-url>` prints it. |
| `apply.py` | Updates a site's copies: rebuilds each band and refreshes each theme file the site already has. |
| `assets/stemedplus-theme.css` | Load after a site's own styles. Colors, fonts, buttons, the join box, and the green band. |
| `assets/stemedplus-commons-logo-white.png` | The logo in white, for the green band. |
| `assets/stemedplus-commons-logo.png` | The logo in color. |
| `assets/manrope.woff` | Manrope (Latin subset), by the Manrope Project Authors, under the SIL Open Font License (`assets/manrope-OFL.txt`). |

## Sites that use it

| Site | Repository |
|---|---|
| STEMEd+ Jobs | [stemed-jobs](https://github.com/stemedplus/stemed-jobs) |
| Find Funding | [stemed-funding](https://github.com/stemedplus/stemed-funding) |
| STEMEd+ Awards | [stemed-awards](https://github.com/stemedplus/stemed-awards) |
| STEMEd+ Digest | [STEMEd-Digest](https://github.com/stemedplus/STEMEd-Digest) |
| Graduate Programs | [stem-ed-research-programs](https://github.com/stemedplus/stem-ed-research-programs) |
| Conferences | [stemed-conferences](https://github.com/stemedplus/stemed-conferences) |
| Professional Development | [stemed-professional-development](https://github.com/stemedplus/stemed-professional-development) |
| Deadlines | [stemed-deadlines](https://github.com/stemedplus/stemed-deadlines) |
| Find Collaborators | [stemed-collaborators](https://github.com/stemedplus/stemed-collaborators) |
| HuMeta Library | [humeta-library](https://github.com/stemedplus/humeta-library) |

## Adding a site

1. Copy the files in `assets/` that the site uses next to its pages, and put the band in each
   page: `python sp_bar.py https://your-site-url/`.
2. Add `.stemedplus-theme.json` at the site's root, listing the folders with theme files and the
   files with a band:

   ```json
   {
     "asset_dirs": ["site"],
     "bars": [{"file": "site/index.html", "current": "https://stemedplus.github.io/your-site/"}]
   }
   ```

   `current` is the site's address as it appears in `menu.json`, so its menu item is marked. Leave it
   out for a site that isn't in the menu. `logo` sets the band's image path, if it isn't
   `stemedplus-commons-logo-white.png`.
3. Add this step to the site's build workflow, before the build:

   ```yaml
   - name: Refresh the shared STEMEd+ look
     continue-on-error: true
     run: |
       git clone --depth 1 https://github.com/stemedplus/stemedplus-theme.git "$RUNNER_TEMP/stemedplus-theme"
       python "$RUNNER_TEMP/stemedplus-theme/apply.py" .
   ```

   If this repository can't be reached, or a file can't be updated, the step changes nothing and
   the site builds with its own copies.
4. Add the site to the menu in `menu.json` and to the table above.

## Checking a change

```bash
python -m unittest discover -s tests -v
python sp_bar.py https://stemedplus.github.io/stemed-funding/
```

This repository was split out of [HuMeta](https://github.com/stemedplus/HuMeta), where it lived in
`standard/stemedplus_theme/`.

## Shared discipline list

`stemedplus_disciplines.json` is the master copy of the STEMEd+ disciplines used by every board
(Jobs, Funding, Conferences, Professional Development, Awards, Digest, and Graduate Programs). Each
board keeps a copy and refreshes it from here when it builds, keeping its own copy if the download
fails or this one is older. Change the disciplines here, raise `version`, and copy the file into
each board.

Each discipline lists the ANZSRC 2020 Fields of Research it corresponds to (`humeta_disciplines`,
as HuMeta terms; HuMeta maps each to the OECD Fields of Science used by DataCite and to the ERIC
Thesaurus). Version 7 follows ANZSRC in giving Astronomy & Space Science (5101, 5109),
Environmental Science (41), and Computing (46) their own disciplines. The list was first kept in
[humeta-profile](https://github.com/stemedplus/humeta-profile), which now keeps a copy of this
file; its Check workflow fails when the copy differs, so update it there after a change here.

The list and HuMeta are checked in both directions. `check_humeta_terms.py` (run by the Tests
workflow on every pull request and once a week) fails if a term the list uses is missing or
deprecated in humeta-profile's `vocabularies.json`.

## Publishing rule for every STEMEd+ site

Each site's GitHub Pages workflow builds first and publishes later, in two jobs:

1. **build**: build the site, refresh the shared look, and upload it with `actions/upload-pages-artifact`.
2. **publish** (`needs: build`): only `actions/deploy-pages`, with `pages: write` and `id-token: write`.

Never upload and publish in the same job. Publishing right after the upload sometimes finds no upload
yet, and re-running such a job uploads a second copy, which the publish step then refuses. With two jobs,
"Re-run failed jobs" just publishes the same build again. If the workflow already has a top-level
`concurrency: group: pages`, do not repeat that group on the publish job: it would wait on itself.
