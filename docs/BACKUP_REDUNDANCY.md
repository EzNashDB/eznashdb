# Database Backup Redundancy

## Overview

Database backups are stored in two locations for redundancy:

1. **Google Drive** (primary) - Daily backups from production database
2. **Backblaze B2** (secondary) - Daily copies from Google Drive

This protects against Google Drive account compromise, accidental deletion, or service outages.

## How It Works

```
                Daily 11am Israel time
┌─────────────┐    (pg_dump)           ┌──────────────┐
│ PostgreSQL  │───────────────────────▶│ Google Drive │
│  Database   │                        │   (Primary)  │
└─────────────┘                        └──────┬───────┘
                                              │
                                              │ Daily 12pm Israel time
                                              │ (rclone copy - latest only)
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │ Backblaze B2 │
                                       │ (Secondary)  │
                                       └──────────────┘
```

**Daily Workflow:**

1. **11:00 AM Israel time:** Fly.io worker creates backup from database, uploads to Google Drive
2. **12:00 PM Israel time:** GitHub Actions copies the latest backup from Google Drive to B2
3. **Retention policy:** Both locations keep ~30 backups (7 daily, 4 weekly, 12 monthly, yearly)

**Key Design:**
- Uses `rclone copy` (not `sync`) - if Google Drive is deleted, B2 keeps all existing backups
- Only copies the latest backup each day (not all backups)
- Retention policy runs independently on B2

## Restoring from Backup

### Option 1: From Google Drive (Preferred)

**Via web interface:**
1. Log into Django admin
2. Go to Admin Dashboard
3. Click "Restore Backup"
4. Select backup and confirm

**Via command line:**
```bash
flyctl ssh console -a eznashdb
python manage.py restore_db backup_20241222_110000.sql.gz
```

### Option 2: From Backblaze B2 (If Google Drive Unavailable)

1. **Download backup from B2:**
   ```bash
   # Configure rclone with B2 credentials (one time setup)
   rclone config

   # List available backups
   rclone lsf b2:ezrat-nashim-db-backups/prod/

   # Download the backup you want
   rclone copy b2:ezrat-nashim-db-backups/prod/backup_20241222_110000.sql.gz /tmp/
   ```

2. **Decompress:**
   ```bash
   gunzip /tmp/backup_20241222_110000.sql.gz
   ```

3. **Restore to database:**
   ```bash
   # Get database connection info from DATABASE_URL
   flyctl ssh console -a eznashdb
   echo $DATABASE_URL
   # Format: postgres://USER:PASSWORD@HOST:PORT/NAME

   # Restore
   psql -h HOST -U USER -d NAME -f /tmp/backup_20241222_110000.sql
   ```

## Monitoring

**Check backup status:**
- GitHub repo → Actions tab → "Backup to Backblaze B2"
- Should run daily and show green checkmark
- Email notification on failure

**Monthly checks:**
1. Log into Backblaze B2 dashboard
2. Verify storage is ~1GB (under 10GB free tier)
3. Check billing shows $0.00

## Troubleshooting

### Workflow failing

1. Go to GitHub Actions → Click failed run
2. Check error message in logs
3. Common fixes:
   - Invalid credentials: Update GitHub secrets
   - No backups in Google Drive: Check primary backup is running

### Manually trigger workflow

1. GitHub repo → Actions tab
2. Click "Backup to Backblaze B2"
3. Click "Run workflow" → "Run workflow"

### Test sync script locally

```bash
# Configure rclone with Google Drive and B2 credentials first
python scripts/sync_to_b2.py gdrive:db-backups/prod/ b2:ezrat-nashim-db-backups/prod/
```

## GitHub Secrets Required

| Secret Name | Value | Where to Get |
|-------------|-------|--------------|
| `B2_APPLICATION_KEY_ID` | B2 app key ID | Backblaze dashboard → App Keys |
| `B2_APPLICATION_KEY` | B2 app key | Backblaze dashboard → App Keys |
| `B2_BUCKET_NAME` | `ezrat-nashim-db-backups` | Your B2 bucket name |
| `RCLONE_CONFIG_CONTENT` | Google Drive rclone config | `flyctl secrets list -a eznashdb-worker` |

## Files

- `/.github/workflows/backup-b2.yml` - GitHub Actions workflow
- `/app/scripts/sync_to_b2.py` - Backup sync script (with tests)
- `/app/app/management/commands/backup_db.py` - Primary backup command
- `/app/app/backups.py` - Shared backup utilities and retention policy

## Cost

**Backblaze B2:** $0/month (under 10GB free tier)
**GitHub Actions:** $0/month (under 2000 min/month free tier)

With retention policy keeping ~30 backups at ~30MB each = ~1GB total storage.
