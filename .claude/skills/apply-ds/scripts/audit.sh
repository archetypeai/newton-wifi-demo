#!/bin/bash
#
# Design System Audit Script
#
# Scans .svelte files for non-DS patterns that should be migrated:
# - Raw Tailwind color utilities (should be semantic tokens)
# - Native HTML elements (should be DS components)
# - Hardcoded inline color styles
# - Class string concatenation (should use cn())
#
# Usage: bash <skill-dir>/scripts/audit.sh
#

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════"
echo "  Design System Audit"
echo "═══════════════════════════════════════════════════"
echo ""

if [ ! -d "src" ]; then
    echo "✗ Error: No src/ directory found"
    echo "  Run this script from your project root directory"
    exit 1
fi

SVELTE_FILES=$(find src -name "*.svelte" -not -path "*/node_modules/*" -not -path "*/.svelte-kit/*" 2>/dev/null)

if [ -z "$SVELTE_FILES" ]; then
    echo "✗ No .svelte files found in src/"
    exit 1
fi

FILE_COUNT=$(echo "$SVELTE_FILES" | wc -l | tr -d ' ')
echo "Scanning $FILE_COUNT .svelte files..."
echo ""

ISSUES=0

# ─────────────────────────────────────────────────────────
# 1. Raw Tailwind color utilities
# ─────────────────────────────────────────────────────────

echo -e "${CYAN}── Raw Tailwind Colors ──${NC}"
echo ""

RAW_COLOR_PATTERN='\b(bg|text|border|ring|outline|shadow|from|to|via)-(red|blue|green|yellow|orange|purple|pink|indigo|violet|teal|cyan|emerald|amber|lime|rose|fuchsia|sky|stone|zinc|neutral|slate|gray|grey|white|black)-[0-9]'

RAW_MATCHES=$(grep -rn --include="*.svelte" -E "$RAW_COLOR_PATTERN" src/ 2>/dev/null || true)

if [ -n "$RAW_MATCHES" ]; then
    echo "$RAW_MATCHES" | while IFS= read -r line; do
        echo -e "  ${YELLOW}$line${NC}"
    done
    RAW_COUNT=$(echo "$RAW_MATCHES" | wc -l | tr -d ' ')
    ISSUES=$((ISSUES + RAW_COUNT))
    echo ""
    echo "  Found $RAW_COUNT raw color utilities → replace with semantic tokens"
else
    echo "  ✓ No raw Tailwind color utilities found"
fi

# Also check bg-white, bg-black, text-white, text-black without shade numbers
BW_PATTERN='\b(bg-white|bg-black|text-white|text-black)\b'
BW_MATCHES=$(grep -rn --include="*.svelte" -E "$BW_PATTERN" src/ 2>/dev/null || true)

if [ -n "$BW_MATCHES" ]; then
    echo ""
    echo "$BW_MATCHES" | while IFS= read -r line; do
        echo -e "  ${YELLOW}$line${NC}"
    done
    BW_COUNT=$(echo "$BW_MATCHES" | wc -l | tr -d ' ')
    echo ""
    echo "  Found $BW_COUNT black/white utilities → replace with bg-background, text-foreground, etc."
fi

echo ""

# ─────────────────────────────────────────────────────────
# 2. Native HTML elements with DS equivalents
# ─────────────────────────────────────────────────────────

echo -e "${CYAN}── Native HTML Elements ──${NC}"
echo ""

# Search in template sections only (outside <script> blocks)
NATIVE_ELEMENTS="<button[> ]|<input[> /]|<textarea[> /]|<select[> ]|<table[> ]|<dialog[> ]|<hr[> /]|<hr>"

NATIVE_MATCHES=$(grep -rn --include="*.svelte" -E "$NATIVE_ELEMENTS" src/ 2>/dev/null | grep -v '<script' | grep -v 'import ' || true)

if [ -n "$NATIVE_MATCHES" ]; then
    echo "$NATIVE_MATCHES" | while IFS= read -r line; do
        echo -e "  ${YELLOW}$line${NC}"
    done
    NATIVE_COUNT=$(echo "$NATIVE_MATCHES" | wc -l | tr -d ' ')
    ISSUES=$((ISSUES + NATIVE_COUNT))
    echo ""
    echo "  Found $NATIVE_COUNT native elements → replace with DS components"
else
    echo "  ✓ No native HTML elements with DS equivalents found"
fi

echo ""

# ─────────────────────────────────────────────────────────
# 3. Hardcoded inline color styles
# ─────────────────────────────────────────────────────────

echo -e "${CYAN}── Hardcoded Inline Colors ──${NC}"
echo ""

INLINE_PATTERN='style="[^"]*\b(color|background|background-color|border-color)\s*:'

INLINE_MATCHES=$(grep -rn --include="*.svelte" -E "$INLINE_PATTERN" src/ 2>/dev/null || true)

if [ -n "$INLINE_MATCHES" ]; then
    echo "$INLINE_MATCHES" | while IFS= read -r line; do
        echo -e "  ${YELLOW}$line${NC}"
    done
    INLINE_COUNT=$(echo "$INLINE_MATCHES" | wc -l | tr -d ' ')
    ISSUES=$((ISSUES + INLINE_COUNT))
    echo ""
    echo "  Found $INLINE_COUNT hardcoded inline colors → use semantic token classes"
else
    echo "  ✓ No hardcoded inline colors found"
fi

echo ""

# ─────────────────────────────────────────────────────────
# 4. Class string concatenation (should use cn())
# ─────────────────────────────────────────────────────────

echo -e "${CYAN}── Class Concatenation ──${NC}"
echo ""

# Look for class={`...`} or class={something + "..."} patterns
CONCAT_PATTERN='class=\{`|class=\{[^}]*\+'

CONCAT_MATCHES=$(grep -rn --include="*.svelte" -E "$CONCAT_PATTERN" src/ 2>/dev/null | grep -v 'cn(' || true)

if [ -n "$CONCAT_MATCHES" ]; then
    echo "$CONCAT_MATCHES" | while IFS= read -r line; do
        echo -e "  ${YELLOW}$line${NC}"
    done
    CONCAT_COUNT=$(echo "$CONCAT_MATCHES" | wc -l | tr -d ' ')
    ISSUES=$((ISSUES + CONCAT_COUNT))
    echo ""
    echo "  Found $CONCAT_COUNT class concatenations → use cn() from \$lib/utils.js"
else
    echo "  ✓ No class string concatenation found"
fi

echo ""

# ─────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════"
echo "  Audit Complete"
echo "═══════════════════════════════════════════════════"
echo ""
