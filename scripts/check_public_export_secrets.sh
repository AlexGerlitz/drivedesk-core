#!/usr/bin/env bash
set -euo pipefail

ROOT="${PUBLIC_EXPORT_ROOT:-$(pwd)}"
cd "$ROOT"

risk=0

report() {
  echo "RISK: $1 in $2" >&2
  risk=1
}

while IFS= read -r -d '' file; do
  [[ -f "$file" ]] || continue
  [[ "$file" == ./.git/* ]] && continue
  [[ "$file" == ./scripts/check_public_export_secrets.sh ]] && continue

  if ! grep -Iq . "$file"; then
    continue
  fi

  if grep -Eq '[0-9]{8,10}:[A-Za-z0-9_-]{30,}' "$file"; then
    report "Telegram bot token pattern" "$file"
  fi

  private_patterns=(
    "auto""school"
    "land""vps"
    "duck""dns"
    "xr""ay"
    "vl""ess"
    "reality""Settings"
    "backup_""passphrase"
    "215""689"
    "185""\\.80\\."
    "152""\\.53\\."
  )
  for pattern in "${private_patterns[@]}"; do
    if grep -Eiq "$pattern" "$file"; then
      report "private infrastructure wording" "$file"
      break
    fi
  done

  if grep -Eq '^(BOT_TOKEN|ADMIN_PASSWORD|POSTGRES_PASSWORD|SECRET_KEY)=' "$file"; then
    report "secret-like env assignment" "$file"
  fi
done < <(find . -type f -print0)

if [[ "$risk" -ne 0 ]]; then
  echo "public export secret scan failed" >&2
  exit 1
fi

echo "public export secret scan ok"
