import nextEslint from 'eslint-config-next';

/** @type {import('eslint').Linter.Config[]} */
const config = [
  ...nextEslint,
  {
    rules: {
      'react/no-unescaped-entities': 'off',
      '@next/next/no-page-custom-font': 'off',
      '@next/next/no-html-link-for-pages': 'off',
      // Regras experimentais do react-hooks que geram muitos falsos positivos neste codebase
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/refs': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/preserve-manual-memoization': 'off',
      'react-hooks/static-components': 'off',
      'react-hooks/use-memo': 'off',
    },
  },
];

export default config;
