# Lumen production snapshot

This repository is a sanitized source and deployment snapshot of the Lumen production websites, captured from the server on 2026-10-31 (Asia/Singapore).

## Contents

- `main-site/` — `lumstrat.com` website, bilingual generated pages, application API and administration console.
- `simulator/` — `lumstratai.com` bilingual investment simulator source and production build.
- `deployment/nginx/` — active Nginx virtual-host configuration for both domains.
- `deployment/systemd/` — application receiver and database-backup service definitions.
- `deployment/admin.env.example` — required administrator environment variables with placeholders only.

## Production versions represented

- Main site: `/var/www/lumen/releases/20261031103532-admin-console`
- Simulator: `/var/www/lumen-simulator/releases/20261029-bilingual`

## Security exclusions

This public repository intentionally excludes runtime secrets and private data:

- SSH and administrator passwords
- `LUMEN_ADMIN_SECRET` and production password hashes
- TLS private keys and certificates
- SQLite databases and submitted visitor data
- Python virtual environments, package caches and server logs

The live application database is stored separately at `/var/lib/lumen/applications.sqlite3` and is backed up on the server by `lumen-form-backup.timer`. Do not commit a production database to this repository.

## Basic restore outline

1. Restore `main-site/` and `simulator/` into versioned release directories.
2. Create the Python virtual environment from `main-site/selfhost/requirements.txt`.
3. Configure `/etc/lumen/admin.env` from `deployment/admin.env.example` using new secret values.
4. Restore the Nginx and systemd definitions after reviewing paths and certificates for the target server.
5. Restore the SQLite database from a private encrypted backup, then start `lumen-form.service` and reload Nginx.

Review `main-site/SELFHOST-部署说明.md` for additional deployment details.
