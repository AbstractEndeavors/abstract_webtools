#!/usr/bin/env bash

WEBSITE="$1"           # e.g. https://example.com
DESTINATION_DIR="$2"   # e.g. /tmp/mywebsite

# 1) Create the directory if it doesn't exist
mkdir -p "$DESTINATION_DIR"
chmod 755 "$DESTINATION_DIR"

# 2) Use wget to recursively download the site
# Explanation of flags:
#  -r         : recursive
#  -p         : download all files necessary to display HTML (images, CSS, etc.)
#  -k         : convert links in downloaded pages so they work locally
#  -E         : adjust extension of HTML files to .html if needed
#  -np        : no parent (prevents going "above" the start site)
#  -nH        : don’t create host directories
#  --cut-dirs : skip creating extra directory levels
#  -P         : specify the directory where to save files
wget -r -p -k -E -np -nH --cut-dirs=0 -P "$DESTINATION_DIR" "$WEBSITE"

# optionally, you could add --user-agent or other headers if needed

