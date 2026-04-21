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
