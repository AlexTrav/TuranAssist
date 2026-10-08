// разметка ответа из базы знаний: абзацы, списки «- …», ссылки, телефоны и почта.
// разбирается в структуру и рисуется шаблоном Vue – без v-html, поэтому XSS невозможен

export type Inline =
  | { type: 'text'; value: string }
  | { type: 'link'; href: string; label: string }

export type Block = { type: 'p'; content: Inline[] } | { type: 'list'; items: Inline[][] }

// ссылка, телефон Казахстана (+7 727 …, 8 (727) …) или почта
const TOKEN_RE =
  /(https?:\/\/[^\s<>«»"]+)|((?:\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})|([\w.+-]+@[\w-]+(?:\.[\w-]+)+)/g
const TRAILING_PUNCT_RE = /[.,;:!?)»]+$/

export function parseInline(text: string): Inline[] {
  const out: Inline[] = []
  let last = 0
  for (const m of text.matchAll(TOKEN_RE)) {
    let token = m[0]
    let tail = ''
    if (m[1]) {
      // точка или скобка в конце предложения – не часть адреса
      const trail = token.match(TRAILING_PUNCT_RE)
      if (trail) {
        tail = trail[0]
        token = token.slice(0, -tail.length)
      }
    }
    const start = m.index ?? 0
    if (start > last) out.push({ type: 'text', value: text.slice(last, start) })
    if (m[1]) out.push({ type: 'link', href: token, label: token.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '') })
    else if (m[2]) out.push({ type: 'link', href: `tel:${token.replace(/[^\d+]/g, '')}`, label: token })
    else out.push({ type: 'link', href: `mailto:${token}`, label: token })
    if (tail) out.push({ type: 'text', value: tail })
    last = start + m[0].length
  }
  if (last < text.length) out.push({ type: 'text', value: text.slice(last) })
  return out
}

export function parseRichText(text: string): Block[] {
  const blocks: Block[] = []
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    const item = line.match(/^[-•*]\s+(.*)$/)
    const prev = blocks[blocks.length - 1]
    if (item) {
      if (prev?.type === 'list') prev.items.push(parseInline(item[1]))
      else blocks.push({ type: 'list', items: [parseInline(item[1])] })
    } else {
      blocks.push({ type: 'p', content: parseInline(line) })
    }
  }
  return blocks
}
