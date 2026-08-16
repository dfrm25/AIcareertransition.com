#!/bin/bash
# Main cPanel FTP user logs into /home/... so we cd into public_html first.
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
pwd;
cd public_html;
pwd;
put this-week.html;
put index.html;
ls this-week.html;
mirror -R --no-perms --no-umask --verbose --exclude-glob .git --exclude-glob .github --exclude-glob scripts --exclude-glob \"*.md\" --exclude-glob \"*.py\" --exclude-glob .cpanel.yml --exclude-glob .gitignore --exclude-glob requirements-automation.txt --exclude-glob ai-career-transition-deploy.zip --exclude-glob github-deploy-ok.txt .;
bye
"
