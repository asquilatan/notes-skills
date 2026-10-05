#!/usr/bin/env bash
# Extracts all questions and correct answers directly from module questions.md on demand.
# Usage: ./extract-questions.sh [MODULE_DIR]

set -e

MODULE_DIR="${1:-.}"
QUESTIONS_FILE="$MODULE_DIR/questions.md"

if [ ! -f "$QUESTIONS_FILE" ]; then
    echo "Error: $QUESTIONS_FILE not found." >&2
    exit 1
fi

DIR_NAME=$(basename "$(cd "$MODULE_DIR" && pwd)")

echo "================================================================="
echo " MODULE QUESTIONS REFERENCE: $DIR_NAME"
echo "================================================================="
echo ""

awk '
    /^##[[:space:]]+(.+)/ {
        section = $0
        sub(/^##[[:space:]]+/, "", section)
        if (section !~ /^(Diagnostic Test|Module Comprehensive)/) {
            if (q != "" && ans != "") {
                print "- **" q "**\n  - **Correct Answer**: " ans "\n"
            }
            q = ""
            ans = ""
            print "### " section "\n"
        }
        next
    }
    /^####[[:space:]]+(Q[0-9]*:[[:space:]].+)/ {
        if (q != "" && ans != "") {
            print "- **" q "**\n  - **Correct Answer**: " ans "\n"
        }
        sub(/^####[[:space:]]+/, "")
        q = $0
        ans = ""
        next
    }
    /^###[[:space:]]+(Q:[[:space:]].+)/ {
        if (q != "" && ans != "") {
            print "- **" q "**\n  - **Correct Answer**: " ans "\n"
        }
        sub(/^###[[:space:]]+/, "")
        q = $0
        ans = ""
        next
    }
    /^>?[[:space:]]*-[[:space:]]*\*\*Correct Answer\*\*:[[:space:]]*/ {
        sub(/^>?[[:space:]]*-[[:space:]]*\*\*Correct Answer\*\*:[[:space:]]*/, "")
        ans = $0
        next
    }
    q != "" && ans == "" && /^\*\*[^*]+\*\*$/ {
        gsub(/^\*\*|\*\*$/, "")
        ans = $0
        next
    }
    END {
        if (q != "" && ans != "") {
            print "- **" q "**\n  - **Correct Answer**: " ans "\n"
        }
    }
' "$QUESTIONS_FILE"
