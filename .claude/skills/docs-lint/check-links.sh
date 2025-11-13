#!/bin/bash
# Link checker for documentation files
# Usage: ./check-links.sh part1.md part2.md ...

check_url() {
    local url="$1"
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 10 "$url" 2>/dev/null)

    if [ "$status_code" -eq 200 ] || [ "$status_code" -eq 301 ] || [ "$status_code" -eq 302 ]; then
        return 0
    else
        echo "  [✖] $url → Status: $status_code"
        return 1
    fi
}

dead_links=0

# Extract URLs from markdown files
for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "File not found: $file"
        continue
    fi

    echo ""
    echo "Checking links in $file..."

    # Extract URLs more carefully - stop at markdown delimiters
    grep -oE '\[.*\]\(https?://[^)]+\)' "$file" | \
    sed -E 's/.*\((https?:\/\/[^)]+)\).*/\1/' | \
    sort -u | while read -r url; do
        if ! check_url "$url"; then
            ((dead_links++))
        fi
    done
done

if [ $dead_links -gt 0 ]; then
    echo ""
    echo "ERROR: $dead_links dead links found!"
    exit 1
else
    echo ""
    echo "✓ All links are valid"
    exit 0
fi
