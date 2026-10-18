#!/usr/bin/env bash
# action "Reset theme": back to the default look. Removes the theme and the
# logo from the addon's data; the running studio picks that up at once.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
rm -f "$DATA/theme.json" "$DATA/theme.json.tmp" "$DATA"/logo.svg "$DATA"/logo.png "$DATA"/logo.webp "$DATA"/logo.jpg "$DATA/logo.json"
echo "theme reset: every screen is back to the default look"
