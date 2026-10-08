// jsdom не реализует IntersectionObserver (директива v-reveal) и scrollIntoView (прокрутка чата)
if (!('IntersectionObserver' in window)) {
  class IntersectionObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  Object.assign(window, { IntersectionObserver: IntersectionObserverStub })
}
Element.prototype.scrollIntoView = Element.prototype.scrollIntoView ?? function () {}

// jsdom не реализует matchMedia, а useTheme.ts вызывает его при определении темы по умолчанию
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList
}
