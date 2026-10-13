# Setup

This repository contains a custom isometric motherboard illustration for the `animeshhq` GitHub profile README, with live GitHub statistics written into the SVGs by Python.

## Files

- `README.md` embeds the light- and dark-mode SVGs.
- `dark_mode.svg` and `light_mode.svg` contain the illustration and identifiable statistic text elements.
- `today.py` fetches statistics from the GitHub GraphQL API and updates those text elements.
- `.github/workflows/update-readme.yml` runs the updater on pushes to `main`, daily, or manually.

## Configure

1. Put these files in the public profile repository named `animeshhq`.
2. Create a GitHub token that can read your account and repository data. Add it to the repository under **Settings → Secrets and variables → Actions** with the name `ACCESS_TOKEN`.
3. The workflow sets `USER_NAME=animeshhq`. Change it in `.github/workflows/update-readme.yml` if you use a different GitHub username.
4. Ensure GitHub Actions is enabled and the workflow has permission to write repository contents. The workflow requests `contents: write` for committing updated SVGs.

## Statistics and SVG IDs

The updater writes these fields into both SVG variants:

| Statistic | SVG element ID |
|---|---|
| Owned repositories | `stat-repositories` |
| Stars across owned repositories | `stat-stars` |
| Commit contributions this calendar year | `stat-commits` |
| Total contributions this calendar year | `stat-contributions` |
| Followers | `stat-followers` |

Repository stars are summed across all pages of owned repositories. Commit and contribution counts use the current calendar year (January 1 through the time of the update). The updater changes only these five text elements; the illustration and its CSS animation rules remain intact.

## Test locally

Install dependencies with:

```bash
python -m pip install -r cache/requirements.txt
```

To check SVG text replacement without an API call, run:

```bash
python today.py --sample
```

That command replaces the SVG values with clearly marked sample data. Restore the original SVGs from version control afterward with `git checkout -- dark_mode.svg light_mode.svg`, then run the normal updater using a valid token:

```bash
# PowerShell
$env:ACCESS_TOKEN = "your_token"
$env:USER_NAME = "anidotdev"
python today.py
```

Do not commit or publish a sample-data run as your live statistics.
