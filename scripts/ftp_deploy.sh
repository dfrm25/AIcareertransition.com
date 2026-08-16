#!/bin/bash
# Extra FTP account is already jailed to public_html.
set -euo pipefail

if [[ -z "${FTP_USER:-}" || -z "${FTP_PASS:-}" ]]; then
  echo "FTP_USER and FTP_PASS must be set" >&2
  exit 1
fi

lftp -u "$FTP_USER","$FTP_PASS" aicareertransition.com -e "
set ssl:verify-certificate no;
set ftp:ssl-force true;
set ftp:ssl-protect-data true;
set net:max-retries 2;
set net:timeout 20;
pwd;
rm this-week.html;
put this-week.html;
rm index.html;
put index.html;
ls this-week.html;
ls index.html;
bye
"
