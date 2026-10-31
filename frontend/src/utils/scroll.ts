/** The element a page scrolls in: the app's content area, or else the document. */
export function scrollerOf(element: Element | null | undefined): Element | null {
  return element?.closest('.n-scrollbar-container') ?? document.scrollingElement
}
