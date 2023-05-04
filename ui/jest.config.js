/** @type {import('ts-jest/dist/types').InitialOptionsTsJest} */
// eslint-disable-next-line no-undef
module.exports = {
  rootDir: 'src',
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: [
    '<rootDir>/support/setup-tests.tsx'
  ],
  coverageDirectory: '<rootDir>/../coverage',
  moduleNameMapper: {
    '\\.(css|less|scss)$': '<rootDir>/support/style-mock.ts',
    '^support/(.*)$': '<rootDir>/support/$1',
    '^interfaces/(.*)$': '<rootDir>/interfaces/$1'
  }
}
