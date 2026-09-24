#!/usr/bin/env bash
# legends grant controlled self-test: no-key federal lanes only.
# Usage: bash bin/lg-selftest.sh
set -u
PASS=0
FAIL=0
ok() { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1"; }

G=$(curl -s -m 25 -X POST https://api.grants.gov/v1/api/search2 \
  -H 'Content-Type: application/json' \
  -d '{"keyword":"small business","oppStatuses":"posted","rows":3}')
echo "$G" | grep -q '"errorcode":0' && ok "search2 errorcode 0" || bad "search2 errorcode 0"
echo "$G" | grep -q '"oppHits"' && ok "search2 oppHits present" || bad "search2 oppHits present"
ID=$(echo "$G" | grep -o '"id":"[0-9]*"' | head -1 | grep -o '[0-9]*')
if [ -n "${ID:-}" ]; then
  ok "search2 yields numeric id ($ID)"
  D=$(curl -s -m 25 -X POST https://api.grants.gov/v1/api/fetchOpportunity \
    -H 'Content-Type: application/json' -d "{\"opportunityId\": $ID}")
  echo "$D" | grep -q '"errorcode":0' && ok "fetchOpportunity errorcode 0" || bad "fetchOpportunity errorcode 0"
else
  bad "search2 yields numeric id"
fi

N=$(curl -s -m 25 'https://search.grants.nih.gov/guide/api/data?searchText=small+business&from=0&size=1')
echo "$N" | grep -qi 'error\|hits\|data' && ok "NIH Guide reachable" || bad "NIH Guide reachable"

U=$(curl -s -m 25 -X POST https://api.usaspending.gov/api/v2/search/spending_by_award \
  -H 'Content-Type: application/json' \
  -d '{"filters":{"award_type_codes":["02","03"]},"fields":["Award ID"],"limit":1}')
echo "$U" | grep -q 'results' && ok "USAspending reachable" || bad "USAspending reachable"

echo "---"
echo "pass=$PASS fail=$FAIL"
[ "$FAIL" -eq 0 ]
