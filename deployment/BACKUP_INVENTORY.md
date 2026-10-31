# Backup inventory

Snapshot date: 2026-10-31 (Asia/Singapore)

| Component | Production location | Repository path |
| --- | --- | --- |
| Main website and backend | `/var/www/lumen/current` | `main-site/` |
| Simulator | `/var/www/lumen-simulator/current` | `simulator/` |
| Main Nginx host | `/etc/nginx/sites-available/lumstrat.com` | `deployment/nginx/lumstrat.com` |
| Simulator Nginx host | `/etc/nginx/sites-available/lumstratai.com` | `deployment/nginx/lumstratai.com` |
| Form receiver service | `/etc/systemd/system/lumen-form.service` | `deployment/systemd/lumen-form.service` |
| Database backup timer | `/etc/systemd/system/lumen-form-backup.timer` | `deployment/systemd/lumen-form-backup.timer` |

Not included: `/etc/lumen/admin.env`, `/var/lib/lumen/applications.sqlite3`, `/etc/letsencrypt`, logs, virtual environments and deprecated releases.
