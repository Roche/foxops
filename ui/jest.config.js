/** @type {import('ts-jest/dist/types').InitialOptionsTsJest} */
// eslint-disable-next-line no-undef
module.exports = {
  rootDir: 'src',
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: [
    '<rootDir>/support/setup-tests.ts'
  ],
  coverageDirectory: '<rootDir>/../coverage'
}
