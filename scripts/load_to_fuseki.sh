#!/usr/bin/env bash
set -euo pipefail

FUSEKI_URL=${FUSEKI_URL:-"http://localhost:3030"}
DATASET=${DATASET:-"vn"}
FILE=${1:-"./data/merged.ttl"}

# Mặc định user/pass là admin/admin
FUSEKI_USER="admin"
FUSEKI_PASSWORD="admin"

if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE" 1>&2
  exit 1
fi

TARGET_URL="$FUSEKI_URL/$DATASET/data?default"

echo "Uploading $FILE to $TARGET_URL"

curl --fail -sS -X PUT \
  -u "${FUSEKI_USER}:${FUSEKI_PASSWORD}" \
  -H "Content-Type: text/turtle" \
  --data-binary "@${FILE}" \
  "$TARGET_URL" >/dev/null

echo "Done."
