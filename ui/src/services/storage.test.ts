import { createStorageKey } from './storage'

it('should create a storage key', () => {
  expect(createStorageKey('foo')).toBe('foxops-store-foo')
})
