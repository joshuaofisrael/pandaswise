#!/usr/bin/env bash
# Ping IndexNow (Bing, Yandex, Seznam, Naver...) for PandaWise.
# Usage: ./indexnow.sh URL [URL...]   (no args = every URL in the live sitemap.xml)
# BASE_URL and the key are read from build.py / .indexnow_key, so this keeps working after a domain switch.
cd "$(dirname "$0")"
BASE=$(python3 -c 'import re;print(re.search(r"^BASE_URL = \"([^\"]+)\"",open("build.py").read(),re.M).group(1))')
KEY=$(cat .indexnow_key)
HOST=$(echo "$BASE" | sed -E 's#^https?://([^/]+).*#\1#')
if [ $# -eq 0 ]; then set -- $(curl -s "${BASE}sitemap.xml" | grep -o '<loc>[^<]*' | sed 's/<loc>//'); fi
LIST=$(printf '%s\n' "$@" | python3 -c 'import sys,json;print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')
curl -s -o /dev/null -w "IndexNow HTTP %{http_code} ($# URLs)\n" -X POST https://api.indexnow.org/indexnow \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d "{\"host\":\"$HOST\",\"key\":\"$KEY\",\"keyLocation\":\"${BASE}${KEY}.txt\",\"urlList\":$LIST}"
