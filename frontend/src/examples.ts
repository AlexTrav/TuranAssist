import type { AppLocale } from './types'

// примеры вопросов: стартовые подсказки в пустом чате
export const EXAMPLE_QUESTIONS: Record<AppLocale, string[]> = {
  ru: ['Сколько стоит ВТиПО?', 'Какие предметы сдавать на ЕНТ на IT?', 'Есть ли общежитие?', 'Как взять академический отпуск?', 'Гранты', 'ВТиПО цена'],
  kk: ['Оқу ақысы қанша?', 'Жатақхана бар ма?', 'Магистратураға қалай түсуге болады?', 'Сессия қашан?', 'Гранттар', 'ВТиПО бағасы'],
  en: ['How much is software engineering?', 'Is there a dormitory?', 'How do I apply for a master’s program?', 'When is the exam session?', 'Grants', 'Software engineering price'],
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

// живой пример на главной: настоящие ответы модели (сняты с бэкенда в docker-compose, октябрь 2026; ms – медиана
// пяти запросов) – токены с леммами, стоп-слова, подслова трансформера, три лучшие темы и начало ответа
export interface DemoToken {
  text: string
  lemma?: string
  stop?: boolean
}
export interface DemoExample {
  question: string
  tokens: DemoToken[]
  subwords: string[]
  top: { title: string; p: number }[]
  answerTitle: string
  answer: string
  confidence: number // итоговая уверенность ответа (для «ВТиПО» – сумма двух тем стоимости)
  ms: number
}

export const DEMO: Record<AppLocale, DemoExample[]> = {
  ru: [
    {
      question: 'Сколько стоит ВТиПО?',
      tokens: [{ text: 'сколько' }, { text: 'стоит', lemma: 'стоить' }, { text: 'втипо' }],
      subwords: ['▁Сколько', '▁стоит', '▁В', 'Ти', 'ПО', '?'],
      top: [
        { title: 'Стоимость бакалавриата', p: 0.508 },
        { title: 'Стоимость магистратуры и докторантуры', p: 0.213 },
        { title: 'Стипендия', p: 0.073 },
      ],
      answerTitle: 'Стоимость бакалавриата · ВТиПО',
      answer: 'Очная, 4 года: 1 476 600 тенге в год. После колледжа, 2 года: 1 925 100 тенге…',
      confidence: 0.72,
      ms: 6.2,
    },
    {
      question: 'Есть ли общежитие для иногородних?',
      tokens: [
        { text: 'есть' },
        { text: 'ли', stop: true },
        { text: 'общежитие' },
        { text: 'для', stop: true },
        { text: 'иногородних', lemma: 'иногородний' },
      ],
      subwords: ['▁Есть', '▁ли', '▁обще', 'жити', 'е', '▁для', '▁и', 'но', 'город', 'них', '?'],
      top: [
        { title: 'Общежитие', p: 0.996 },
        { title: 'Инклюзивное образование', p: 0.001 },
        { title: 'Специальности', p: 0.0 },
      ],
      answerTitle: 'Общежитие',
      answer: 'Места в Доме студентов выделяются приехавшим из отдалённых регионов Казахстана и иностранным гражданам…',
      confidence: 0.996,
      ms: 7.5,
    },
    {
      question: 'получил FX по статистике, что делать?',
      tokens: [
        { text: 'получил', lemma: 'получить' },
        { text: 'fx' },
        { text: 'по', stop: true },
        { text: 'статистике', lemma: 'статистика' },
        { text: 'что' },
        { text: 'делать' },
      ],
      subwords: ['▁получил', '▁', 'FX', '▁по', '▁статистик', 'е', ',', '▁что', '▁делать', '?'],
      top: [
        { title: 'Пересдача FX и Retake', p: 0.924 },
        { title: 'Оценки и GPA', p: 0.011 },
        { title: 'Академическая честность и ИИ', p: 0.011 },
      ],
      answerTitle: 'Пересдача FX и Retake',
      answer: 'FX (25–49 баллов) – можно платно пересдать экзамен без повторного изучения дисциплины…',
      confidence: 0.924,
      ms: 6.5,
    },
  ],
  kk: [
    {
      question: 'Жатақхана бар ма?',
      tokens: [{ text: 'жатақхана' }, { text: 'бар' }, { text: 'ма', stop: true }],
      subwords: ['▁Жа', 'т', 'ақ', 'хана', '▁бар', '▁ма', '?'],
      top: [
        { title: 'Жатақхана', p: 0.971 },
        { title: 'Мекенжай', p: 0.007 },
        { title: 'Студенттік клубтар', p: 0.002 },
      ],
      answerTitle: 'Жатақхана',
      answer: 'Студенттер үйіндегі орындар Қазақстанның шалғай өңірлерінен келгендерге және шетел азаматтарына беріледі…',
      confidence: 0.971,
      ms: 6.0,
    },
    {
      question: 'Магистратураға қалай түсуге болады?',
      tokens: [{ text: 'магистратураға' }, { text: 'қалай' }, { text: 'түсуге' }, { text: 'болады', stop: true }],
      subwords: ['▁Маг', 'ист', 'ратура', 'ға', '▁қалай', '▁түсу', 'ге', '▁болады', '?'],
      top: [
        { title: 'Магистратураға түсу', p: 0.924 },
        { title: 'Магистратура және MBA бағдарламалары', p: 0.025 },
        { title: 'Қалай түсуге болады', p: 0.01 },
      ],
      answerTitle: 'Магистратураға түсу',
      answer: 'Магистратураға түсу Ұлттық тестілеу орталығының кешенді тестілеуі (КТ) арқылы өтеді…',
      confidence: 0.924,
      ms: 7.7,
    },
    {
      question: 'Сессия қашан басталады?',
      tokens: [{ text: 'сессия' }, { text: 'қашан' }, { text: 'басталады' }],
      subwords: ['▁С', 'есс', 'ия', '▁қа', 'шан', '▁басталады', '?'],
      top: [
        { title: 'Академиялық күнтізбе', p: 0.984 },
        { title: 'Сабақ кестесі', p: 0.006 },
        { title: 'Қабылдау мерзімдері', p: 0.004 },
      ],
      answerTitle: 'Академиялық күнтізбе',
      answer: '2026–2027 оқу жылына бакалавриаттың академиялық күнтізбесі: сессиялар, демалыстар, қайта тапсыру…',
      confidence: 0.984,
      ms: 6.4,
    },
  ],
  en: [
    {
      question: 'How much is software engineering?',
      tokens: [{ text: 'how' }, { text: 'much' }, { text: 'is', stop: true }, { text: 'software' }, { text: 'engineering' }],
      subwords: ['▁How', '▁much', '▁is', '▁software', '▁engineering', '?'],
      top: [
        { title: 'Bachelor’s tuition', p: 0.549 },
        { title: 'Master’s and PhD tuition', p: 0.308 },
        { title: 'Academic mobility', p: 0.013 },
      ],
      answerTitle: 'Bachelor’s tuition · Software engineering',
      answer: 'Full-time, 4 years: 1,476,600 tenge per year. After college, 2 years: 1,925,100 tenge…',
      confidence: 0.857,
      ms: 6.4,
    },
    {
      question: 'Is there a dormitory?',
      tokens: [{ text: 'is', stop: true }, { text: 'there', stop: true }, { text: 'a', stop: true }, { text: 'dormitory' }],
      subwords: ['▁Is', '▁there', '▁a', '▁dormitor', 'y', '?'],
      top: [
        { title: 'Dormitory', p: 0.985 },
        { title: 'Medical center', p: 0.002 },
        { title: 'Address and location', p: 0.001 },
      ],
      answerTitle: 'Dormitory',
      answer: 'Places in the Student House are given to students from remote regions of Kazakhstan and international students…',
      confidence: 0.985,
      ms: 5.5,
    },
    {
      question: 'How do I apply for a master’s program?',
      tokens: [
        { text: 'how' },
        { text: 'do', stop: true },
        { text: 'i', stop: true },
        { text: 'apply' },
        { text: 'for', stop: true },
        { text: 'a', stop: true },
        { text: 'master' },
        { text: 'program' },
      ],
      subwords: ['▁How', '▁do', '▁I', '▁apply', '▁for', '▁a', '▁master', '’', 's', '▁program', '?'],
      top: [
        { title: 'Master’s admission', p: 0.911 },
        { title: 'Master’s and MBA programs', p: 0.019 },
        { title: 'How to apply', p: 0.019 },
      ],
      answerTitle: 'Master’s admission',
      answer: 'Master’s admission is based on the Comprehensive Test (CT) of the National Testing Center…',
      confidence: 0.911,
      ms: 6.6,
    },
  ],
}
