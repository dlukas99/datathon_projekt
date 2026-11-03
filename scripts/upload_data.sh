#!/usr/bin/env sh
# Copy processed data (and the OSM extract for Valhalla) to the server.
# Usage: scripts/upload_data.sh user@server /opt/prije-potpisa
set -eu
if [ $# -ne 2 ]; then
  echo "Upotreba: $0 korisnik@posluzitelj /putanja/do/repozitorija" >&2
  exit 2
fi
TARGET="$1"
DIR="$2"
ssh "$TARGET" "mkdir -p '$DIR/data/processed' '$DIR/data/raw/osm'"
rsync -avz --progress --delete data/processed/ "$TARGET:$DIR/data/processed/"
rsync -avz --progress data/raw/osm/croatia-latest.osm.pbf "$TARGET:$DIR/data/raw/osm/"
echo "Gotovo. Na poslužitelju: cd $DIR && DOMAIN=… docker compose -f deploy/docker-compose.yml up -d --build"
