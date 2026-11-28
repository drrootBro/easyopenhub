# EasyOpenHub

Curated, local-first open-source Mac apps with direct official `.dmg` downloads: https://easyopenhub.com

## How it works

| File | Who edits it | What it holds |
|---|---|---|
| `data/manual_apps.json` | Only you, by hand | Your own paid apps and featured picks (price, buy links, badge). No script touches it. |
| `data/github_apps.json` | You / the weekly update, by hand | The open-source list: `repo`, `alternative_to`, `pitch`, `group`, `video`, `status`, `rank`, plus the plain-language text. No script writes to it. |
| `data/releases.json` | Only `scripts/sync_releases.py` | Latest stable version, date and `.dmg` links per repo. |

`scripts/sync_releases.py` calls `GET /repos/{owner}/{repo}/releases/latest` for every Mac app (pre-releases skipped), keeps `.dmg` assets and labels them
**Download for Mac (Universal)**, **Download for Apple Silicon (M1–M4)** or **Download for Intel Mac**. No `.dmg`? The page shows the official site and **View on GitHub Releases** instead.

`scripts/build.py` turns the three files into plain static HTML (`/`, `/en/…`, `/zh/…`, alternatives pages, sitemap).

`.github/workflows/sync-releases.yml` runs both every day at 00:00 UTC, on the "Run workflow" button, and whenever `data/`, `scripts/` or `assets/` change, then commits and pushes only if something changed. GitHub Pages serves the result.

### Add an open-source app
Add an entry to `data/github_apps.json` with at least `slug`, `name`, `repo`, `status` (`priority` / `keep` / `retired`), `rank`, `group`, `alternative_to`, `pitch`, `platforms`, `official_url`, `category`, and `en` / `zh` text. Commit; the workflow does the rest.

### Add your own app
Add an entry to `data/manual_apps.json` (see the MedEar example). `home_position`: `top` (above the list) or `after_list`.
