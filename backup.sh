#!/bin/bash
BACKUP_DIR="/opt/lwk-erp/backups"
mkdir -p $BACKUP_DIR
FILENAME="lwk_$(date +%Y%m%d_%H%M%S).dump"
docker compose -f /opt/lwk-erp/docker-compose.prod.yml exec -T postgres pg_dump -U lwk -Fc lwk > "$BACKUP_DIR/$FILENAME"
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
echo "Backup: $FILENAME ($(du -h $BACKUP_DIR/$FILENAME | cut -f1))"
