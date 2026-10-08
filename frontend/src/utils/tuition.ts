import type { Level, TuitionCatalog, TuitionPlan, TuitionPrice, TuitionProgram } from '../types'

// срок обучения по форме, лет – для оценки стоимости за весь срок; null – срок на сайте не уточнён
export const PLAN_YEARS: Record<string, number | null> = {
  bachelor_4y: 4,
  bachelor_school_3y: 3,
  bachelor_college_3y: 3,
  bachelor_college_2y: 2,
  bachelor_distance_college_3y: 3,
  bachelor_distance_college_2y: 2,
  bachelor_distance_university: null,
  master_research_2y: 2,
  master_professional_1y: 1,
  phd: 3,
}

export interface PlanOption {
  plan: TuitionPlan
  price: TuitionPrice
}

// уровни, на которых у программы есть цены (клиническая психология – только магистратура)
export function levelsOf(program: TuitionProgram, catalog: TuitionCatalog): Level[] {
  const levels = new Set(program.prices.map((p) => catalog.plans.find((pl) => pl.id === p.plan)?.level))
  return (['bachelor', 'postgrad'] as Level[]).filter((l) => levels.has(l))
}

// формы обучения программы на уровне в порядке справочника
export function optionsOf(program: TuitionProgram, level: Level, catalog: TuitionCatalog): PlanOption[] {
  return catalog.plans
    .filter((plan) => plan.level === level)
    .flatMap((plan) => {
      const price = program.prices.find((p) => p.plan === plan.id)
      return price ? [{ plan, price }] : []
    })
}

export function priceOf(option: PlanOption, english: boolean): number {
  return english && option.price.english ? option.price.english : option.price.main
}

// стоимость за весь срок при неизменной цене; null – срок неизвестен
export function totalOf(option: PlanOption, english: boolean): number | null {
  const years = PLAN_YEARS[option.plan.id]
  return years ? years * priceOf(option, english) : null
}
