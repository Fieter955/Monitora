#!/usr/bin/env sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
backup_dir="$project_dir/backups/$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$backup_dir"
cd "$project_dir"

docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "$backup_dir/postgres.sql"

docker compose exec -T librenms-db sh -c \
  'mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" --single-transaction "$MARIADB_DATABASE"' \
  > "$backup_dir/librenms.sql"

docker run --rm \
  -v pantau-infrastruktur_prometheus_data:/source:ro \
  -v "$backup_dir":/backup \
  alpine:3.22 \
  tar -czf /backup/prometheus-data.tar.gz -C /source .

docker run --rm \
  -v pantau-infrastruktur_grafana_data:/source:ro \
  -v "$backup_dir":/backup \
  alpine:3.22 \
  tar -czf /backup/grafana-data.tar.gz -C /source .

docker run --rm \
  -v pantau-infrastruktur_librenms_data:/source:ro \
  -v "$backup_dir":/backup \
  alpine:3.22 \
  tar -czf /backup/librenms-config.tar.gz -C /source .

docker run --rm \
  -v pantau-infrastruktur_librenms_rrd_data:/source:ro \
  -v "$backup_dir":/backup \
  alpine:3.22 \
  tar -czf /backup/librenms-rrd.tar.gz -C /source .

cp .env "$backup_dir/environment.env"
chmod 600 "$backup_dir/environment.env"

printf 'Backup selesai: %s\n' "$backup_dir"
