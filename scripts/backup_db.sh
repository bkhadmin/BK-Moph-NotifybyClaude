#!/bin/bash
# backup_db.sh — backup MySQL database จาก Docker container
# Usage: bash scripts/backup_db.sh
# Cron (daily 02:00): 0 2 * * * cd /path/to/BK-Moph-NotifybyClaude && bash scripts/backup_db.sh >> /var/log/bk_backup.log 2>&1

set -e

COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
FILENAME="bk_moph_notify_${DATE}.sql.gz"

# โหลด .env เพื่อดึง MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup → ${BACKUP_DIR}/${FILENAME}"

docker compose -f "$COMPOSE_FILE" exec -T mysql \
  mysqldump \
    --user="${MYSQL_USER}" \
    --password="${MYSQL_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    --set-gtid-purged=OFF \
    "${MYSQL_DATABASE}" \
  | gzip > "${BACKUP_DIR}/${FILENAME}"

SIZE=$(du -sh "${BACKUP_DIR}/${FILENAME}" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done: ${FILENAME} (${SIZE})"

# ลบ backup เก่ากว่า 30 วัน
find "$BACKUP_DIR" -name "bk_moph_notify_*.sql.gz" -mtime +30 -delete
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Old backups cleaned (>30 days)"
