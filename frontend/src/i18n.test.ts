import { describe, expect, it } from 'vitest'
import { CATALOGS, CATEGORIES, ROLES, UNITS, toPayload } from './catalog'
import { messages, translate } from './i18n'

describe('translations', () => {
  it('English and Arabic have the same keys, none empty', () => {
    expect(Object.keys(messages.ar).sort()).toEqual(Object.keys(messages.en).sort())
    for (const lang of ['en', 'ar'] as const) {
      for (const [key, text] of Object.entries(messages[lang])) {
        expect(text, `${lang} ${key}`).not.toBe('')
      }
    }
  })

  it('every label the catalog screens use exists', () => {
    const keys = new Set<string>()
    for (const c of CATALOGS) {
      keys.add(c.tab)
      keys.add(`field.${c.codeKey}`)
      c.fields.forEach((f) => keys.add(`field.${f.key}`))
      c.columns.forEach((col) => keys.add(`field.${col}`))
    }
    ROLES.forEach((r) => keys.add(`role.${r}`))
    CATEGORIES.forEach((r) => keys.add(`category.${r}`))
    UNITS.forEach((r) => keys.add(`unit.${r}`))
    for (const key of keys) {
      expect(key in messages.en, key).toBe(true)
    }
  })

  it('falls back to the key when a message is missing', () => {
    expect(translate('ar', 'missing.key')).toBe('missing.key')
  })
})

describe('toPayload', () => {
  const profiles = CATALOGS.find((c) => c.resource === 'profiles')!

  it('converts numbers, trims text and nulls empty optionals', () => {
    const payload = toPayload(profiles.fields, {
      system_id: '3',
      article_no: ' W70-101 ',
      name_en: 'Frame',
      name_ar: 'حلق',
      role: 'frame',
      width_mm: '70',
      height_mm: '55.5',
      weight_kg_per_m: '1.245',
      bar_length_mm: 6000,
      price_per_m: '',
    })
    expect(payload).toEqual({
      system_id: 3,
      article_no: 'W70-101',
      name_en: 'Frame',
      name_ar: 'حلق',
      role: 'frame',
      width_mm: 70,
      height_mm: 55.5,
      weight_kg_per_m: 1.245,
      bar_length_mm: 6000,
      price_per_m: null,
    })
  })
})
