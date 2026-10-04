set shell := ["bash", "-euo", "pipefail", "-c"]

# list recipes
default:
    @just --list

# new entry: just new cpp "Signed modulo by two is not free"
new topic title:
    #!/usr/bin/env bash
    set -euo pipefail
    slug=$(echo "{{title}}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
    file="{{topic}}/${slug}.md"
    mkdir -p "{{topic}}"
    if [[ -e "$file" ]]; then echo "$file already exists"; exit 1; fi
    printf -- '---\ntitle: "%s"\ndate: %s\n---\n\n' "{{title}}" "$(date +%F)" > "$file"
    "${EDITOR:-nvim}" "$file"

# rebuild the README index
readme:
    python3 scripts/build_readme.py

# drafts waiting for review
drafts:
    @grep -rl --include='*.md' '^draft: true' . || echo "no drafts"

# commit new and changed entries, then push
ship: readme
    #!/usr/bin/env bash
    set -euo pipefail
    git add -A
    # drafts stay local until you flip them to draft: false
    git diff --cached --name-only -- '*/*.md' | xargs -r grep -l '^draft: true' | xargs -r git reset -q --
    if git diff --cached --quiet; then echo "nothing to ship"; exit 0; fi
    titles=$(git diff --cached --name-only --diff-filter=A -- '*/*.md' \
        | xargs -r grep -h '^title:' | sed -E 's/^title: *"?//; s/"$//' | paste -sd ',' | sed 's/,/, /g')
    git commit -m "til: ${titles:-update}"
    git push
