/* eslint-disable-next-line */
module.exports = {
  env: {
    browser: true,
    es2021: true
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/jsx-runtime'
  ],
  overrides: [
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: [
    'react',
    '@typescript-eslint'
  ],
  settings: {
    react: {
      version: 'detect'
    }
  },
  rules: {
    indent: [
      'error',
      2,
      {
        SwitchCase: 1
      }
    ],
    'linebreak-style': [
      'error',
      'unix'
    ],
    quotes: [
      'error',
      'single'
    ],
    semi: [
      'error',
      'never'
    ],
    'array-callback-return': [
      'error'
    ],
    'no-await-in-loop': 'error',
    'no-constant-binary-expression': 'error',
    'no-constructor-return': 'error',
    'no-duplicate-imports': 'error',
    'no-promise-executor-return': 'error',
    'no-self-compare': 'error',
    'no-template-curly-in-string': 'error',
    'no-unmodified-loop-condition': 'error',
    'no-unreachable-loop': 'error',
    'require-atomic-updates': 'error',
    'arrow-body-style': [
      'error'
    ],
    'array-bracket-spacing': [
      'error',
      'never'
    ],
    'arrow-parens': [
      'error',
      'as-needed'
    ],
    'arrow-spacing': 'error',
    'block-spacing': 'error',
    'brace-style': 'error',
    'comma-dangle': [
      'error',
      'never'
    ],
    'comma-spacing': [
      'error',
      {
        before: false,
        after: true
      }
    ],
    'comma-style': [
      'error',
      'last'
    ],
    'computed-property-spacing': [
      'error',
      'never'
    ],
    'eol-last': 'error',
    'func-call-spacing': 'error',
    'function-call-argument-newline': [
      'error',
      'consistent'
    ],
    'implicit-arrow-linebreak': [
      'error'
    ],
    'jsx-quotes': [
      'error',
      'prefer-double'
    ],
    'key-spacing': 'error',
    'keyword-spacing': 'error',
    'lines-between-class-members': 'error',
    'max-statements-per-line': [
      'error',
      {
        max: 2
      }
    ],
    'new-parens': 'error',
    'no-multi-spaces': [
      'error',
      {
        ignoreEOLComments: true
      }
    ],
    'no-multiple-empty-lines': [
      'error',
      {
        max: 1
      }
    ],
    'no-trailing-spaces': [
      'error',
      {
        ignoreComments: true
      }
    ],
    'no-whitespace-before-property': 'error',
    'nonblock-statement-body-position': [
      'error',
      'beside'
    ],
    'object-curly-spacing': [
      'error',
      'always'
    ],
    'operator-linebreak': [
      'error',
      'before'
    ],
    'padded-blocks': [
      'error',
      'never'
    ],
    'rest-spread-spacing': [
      'error',
      'never'
    ],
    'semi-spacing': 'error',
    'semi-style': [
      'error',
      'last'
    ],
    'space-before-blocks': 'error',
    'space-before-function-paren': [
      'error',
      {
        anonymous: 'always',
        named: 'never',
        asyncArrow: 'always'
      }
    ],
    'space-in-parens': [
      'error',
      'never'
    ],
    'space-infix-ops': 'error',
    'space-unary-ops': 'error',
    'switch-colon-spacing': 'error',
    'template-curly-spacing': 'error',
    'template-tag-spacing': 'error',
    'wrap-iife': [
      'error',
      'inside'
    ],
    'quote-props': ['error', 'as-needed'],
    'object-shorthand': 'error',
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off'
  }
}
