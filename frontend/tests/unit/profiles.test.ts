import { focusList, orderByFocus } from '../../src/lib/profiles'

test('profile focus moves categories first without dropping any', () => {
  const ids = ['flood', 'air', 'green', 'noise', 'solar']
  const ordered = orderByFocus(ids, (x) => x, focusList('rad-od-kuce', null))
  expect(ordered.slice(0, 3)).toEqual(['noise', 'green', 'solar'])
  expect([...ordered].sort()).toEqual([...ids].sort())
})

test('custom profile reads ids from the URL value', () => {
  expect(focusList('vlastiti', 'school,flood')).toEqual(['school', 'flood'])
  expect(focusList('opci', 'school')).toEqual([])
})
