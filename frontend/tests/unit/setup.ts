import '@testing-library/jest-dom/vitest'

// jsdom does not lay out pages, so it has no scrollIntoView (used for links to a page part).
if (!('scrollIntoView' in Element.prototype)) {
  Object.defineProperty(Element.prototype, 'scrollIntoView', { value: () => undefined })
}
