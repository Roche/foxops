import { searchBy } from '.'

test('searchBy', () => {
  const search = searchBy('john', ['name', 'lastName'])
  expect(search({ name: 'John', lastName: 'Doe' })).toBe(true)
  expect(search({ name: 'Jane', lastName: 'Doe' })).toBe(false)
  expect(search({})).toBe(false)
})
