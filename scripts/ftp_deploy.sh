#!/bin/bash
# Upload the site into the FTP login directory (already public_html).
set -euo pipefail

if [[ -z "${FTP_USER:-}" || -z "${FTP_PASS:-}" ]]; then
  echo "FTP_USER and FTP_PASS must be set" >&2
  exit 1
fi

lftp -u "$FTP_USER","$FTP_PASS" aicareertransition.com -e "
set ssl:verify-certificate no;
set ftp:ssl-force true;
set ftp:ssl-protect-data true;
set net:max-retries 3;
set net:timeout 30;
set cmd:fail-exit yes;
pwd;
chmod 666 this-week.html;
put this-week.html;
chmod 644 this-week.html;
chmod 666 index.html;
put index.html;
chmod 644 index.html;
ls this-week.html;
bye
"
