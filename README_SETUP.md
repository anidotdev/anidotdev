# Setup

1. Create a repo named exactly `animeshhq` (same as your username), public. Push these files.
2. Create a fine-grained PAT (Settings > Developer settings > Fine-grained tokens): All repositories,
   read-only for Contents, Metadata, Pull requests, Issues. Add it as repo secret `ACCESS_TOKEN`.
   Add secret `USER_NAME` = `animeshhq`.
3. Edit `BIRTHDAY` in `today.py` (it drives the Uptime line).
4. Edit INFO in `make_svg.py`, then `python make_svg.py`.
5. Actions tab > "Update profile card" > Run workflow. It then refreshes daily.
Local test: `ACCESS_TOKEN=... USER_NAME=animeshhq python today.py`
