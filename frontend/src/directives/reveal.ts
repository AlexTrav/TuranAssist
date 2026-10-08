import type { Directive } from 'vue'

// один общий наблюдатель на все элементы с v-reveal – экономнее, чем создавать по одному на элемент
const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.setAttribute('data-reveal', 'visible') // включает CSS-переход в style.css
        observer.unobserve(entry.target) // анимация проигрывается один раз
      }
    }
  },
  { threshold: 0.15 },
)

// директива v-reveal: элемент плавно появляется, когда попадает в область видимости при скролле
export const vReveal: Directive = {
  mounted(el: HTMLElement) {
    el.setAttribute('data-reveal', '')
    observer.observe(el)
  },
  unmounted(el: HTMLElement) {
    observer.unobserve(el)
  },
}
