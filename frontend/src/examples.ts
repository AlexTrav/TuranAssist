import type { AppLocale } from './types'

// примеры вопросов: стартовые подсказки в пустом чате и карточки тем на главной
export const EXAMPLE_QUESTIONS: Record<AppLocale, string[]> = {
  ru: ['Сколько стоит обучение?', 'Какие предметы сдавать на ЕНТ на IT?', 'Есть ли общежитие?', 'Как взять академический отпуск?'],
  kk: ['Оқу ақысы қанша?', 'Жатақхана бар ма?', 'Магистратураға қалай түсуге болады?', 'Сессия қашан?'],
  en: ['How much is the tuition?', 'Is there a dormitory?', 'How do I apply for a master’s program?', 'When is the exam session?'],
}

// карточки групп тем на главной: пример вопроса для перехода сразу в чат
export const GROUP_EXAMPLES: Record<string, Record<AppLocale, string>> = {
  admission: { ru: 'Как поступить в Туран?', kk: 'Туранға қалай түсуге болады?', en: 'How do I apply to Turan?' },
  postgrad: { ru: 'Как поступить в магистратуру?', kk: 'Магистратураға қалай түсемін?', en: 'How to apply for a master’s?' },
  payment: { ru: 'Сколько стоит обучение?', kk: 'Оқу ақысы қанша?', en: 'How much is the tuition?' },
  grants: { ru: 'Какие скидки по баллам ЕНТ?', kk: 'ҰБТ балы бойынша жеңілдік бар ма?', en: 'Discounts for UNT scores?' },
  study: { ru: 'Когда зимняя сессия?', kk: 'Қысқы сессия қашан?', en: 'When is the winter session?' },
  student_life: { ru: 'Есть ли общежитие?', kk: 'Жатақхана бар ма?', en: 'Is there a dormitory?' },
  about: { ru: 'Телефон приёмной комиссии', kk: 'Қабылдау комиссиясының телефоны', en: 'Admissions office phone' },
}
