#!/bin/bash
#
# Design System Linting & Formatting Setup
#
# Installs and configures ESLint + Prettier for a SvelteKit project
# using the Archetype AI design system.
#
# Usage: bash <skill-dir>/scripts/setup.sh
#

set -e

echo "═══════════════════════════════════════════════════"
echo "  Linting & Formatting Setup"
echo "═══════════════════════════════════════════════════"
echo ""

if [ ! -f "package.json" ]; then
    echo "✗ Error: No package.json found"
    echo "  Run this script from your project root directory"
    exit 1
fi

# ─────────────────────────────────────────────────────────
# Install Dependencies
# ─────────────────────────────────────────────────────────

echo "Installing linting dependencies..."

npm i -D eslint prettier eslint-plugin-svelte eslint-config-prettier prettier-plugin-svelte prettier-plugin-tailwindcss globals 2>/dev/null || {
    echo "✗ Failed to install dependencies"
    exit 1
}
echo "  ✓ Dependencies installed"
echo ""

# ─────────────────────────────────────────────────────────
# Detect CSS file for Prettier Tailwind plugin
# ─────────────────────────────────────────────────────────

CSS_FILE=""
if [ -f "src/app.css" ]; then
    CSS_FILE="src/app.css"
elif [ -f "src/routes/layout.css" ]; then
    CSS_FILE="src/routes/layout.css"
elif [ -f "src/app.pcss" ]; then
    CSS_FILE="src/app.pcss"
fi

# ─────────────────────────────────────────────────────────
# Create eslint.config.js
# ─────────────────────────────────────────────────────────

if [ ! -f "eslint.config.js" ]; then
    cat > eslint.config.js << 'ESLINT_EOF'
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import svelteConfig from './svelte.config.js';

export default [
	js.configs.recommended,
	...svelte.configs.recommended,
	...svelte.configs['flat/prettier'],
	{
		languageOptions: {
			globals: { ...globals.browser, ...globals.node }
		}
	},
	{
		files: ['**/*.svelte', '**/*.svelte.js'],
		languageOptions: {
			parserOptions: { svelteConfig }
		}
	},
	{
		ignores: ['.svelte-kit/', 'build/', 'dist/', 'node_modules/']
	}
];
ESLINT_EOF
    echo "  ✓ eslint.config.js created"
else
    echo "  → eslint.config.js exists, skipping"
fi

# ─────────────────────────────────────────────────────────
# Create .prettierrc
# ─────────────────────────────────────────────────────────

if [ ! -f ".prettierrc" ]; then
    if [ -n "$CSS_FILE" ]; then
        cat > .prettierrc << PRETTIER_EOF
{
	"useTabs": true,
	"singleQuote": true,
	"trailingComma": "none",
	"printWidth": 100,
	"plugins": ["prettier-plugin-svelte", "prettier-plugin-tailwindcss"],
	"tailwindStylesheet": "./$CSS_FILE"
}
PRETTIER_EOF
    else
        cat > .prettierrc << 'PRETTIER_EOF'
{
	"useTabs": true,
	"singleQuote": true,
	"trailingComma": "none",
	"printWidth": 100,
	"plugins": ["prettier-plugin-svelte", "prettier-plugin-tailwindcss"]
}
PRETTIER_EOF
    fi
    echo "  ✓ .prettierrc created"
else
    echo "  → .prettierrc exists, skipping"
fi

# ─────────────────────────────────────────────────────────
# Create .prettierignore
# ─────────────────────────────────────────────────────────

if [ ! -f ".prettierignore" ]; then
    cat > .prettierignore << 'IGNORE_EOF'
.svelte-kit
.claude
.cursor
build
dist
node_modules
package-lock.json
IGNORE_EOF
    echo "  ✓ .prettierignore created"
else
    echo "  → .prettierignore exists, skipping"
fi

# ─────────────────────────────────────────────────────────
# Add scripts to package.json
# ─────────────────────────────────────────────────────────

npm pkg set scripts.lint="eslint ." 2>/dev/null || true
npm pkg set scripts.lint:fix="eslint . --fix" 2>/dev/null || true
npm pkg set scripts.format="prettier --write ." 2>/dev/null || true
npm pkg set scripts.format:check="prettier --check ." 2>/dev/null || true
echo "  ✓ Lint/format scripts added to package.json"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Setup Complete"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Run: npm run lint:fix && npm run format"
echo ""
