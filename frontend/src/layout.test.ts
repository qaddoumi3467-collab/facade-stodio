import { describe, expect, it } from 'vitest'
import type { Row } from './api'
import { defaultProfiles, newElement, PROFILE_CHOICES } from './elements'
import { messages } from './i18n'
import {
  getNode,
  newField,
  normalizeNumber,
  OPENINGS,
  parseSize,
  removeSplit,
  setSizes,
  splitField,
  updateField,
  type LayoutNode,
  type SplitNode,
} from './layout'

const columns = (n: number): LayoutNode => splitField(newField(), [], 'vertical', n)

describe('layout tree', () => {
  it('splits a field into equal columns', () => {
    const layout = columns(3) as SplitNode
    expect(layout.kind).toBe('split')
    expect(layout.direction).toBe('vertical')
    expect(layout.sizes).toEqual([null, null, null])
    expect(layout.children).toHaveLength(3)
  })

  it('splitting a column into columns adds to the same row', () => {
    const layout = splitField(columns(2), [1], 'vertical', 2) as SplitNode
    expect(layout.children).toHaveLength(3)
    expect(layout.sizes).toEqual([null, null, null])
  })

  it('keeps the other sizes when adding columns', () => {
    const sized = setSizes(columns(2), [], [600, null])
    const layout = splitField(sized, [1], 'vertical', 3) as SplitNode
    expect(layout.sizes).toEqual([600, null, null, null])
  })

  it('splitting a column into rows nests a split', () => {
    const layout = splitField(columns(2), [0], 'horizontal', 2)
    const nested = getNode(layout, [0]) as SplitNode
    expect(nested.direction).toBe('horizontal')
    expect(getNode(layout, [0, 1])).toEqual(newField())
    expect(getNode(layout, [1])).toEqual(newField())
  })

  it('never makes more than 20 parts in one split', () => {
    const layout = splitField(columns(19), [0], 'vertical', 5) as SplitNode
    expect(layout.children).toHaveLength(20)
    expect(layout.sizes).toHaveLength(20)
    expect(splitField(layout, [0], 'vertical', 2)).toBe(layout)
  })

  it('a split field keeps its opening and glass in each part', () => {
    const field = updateField(newField(), [], { opening: 'turn_left', glass_id: 7 })
    const layout = splitField(field, [], 'horizontal', 2) as SplitNode
    expect(layout.children.every((c) => c.kind === 'field' && c.opening === 'turn_left' && c.glass_id === 7)).toBe(true)
  })

  it('removing dividers leaves the first field', () => {
    let layout = columns(2)
    layout = updateField(layout, [0], { opening: 'tilt' })
    expect(removeSplit(layout, [])).toEqual({ ...newField(), opening: 'tilt' })
  })

  it('changes never touch the original tree', () => {
    const original = columns(2)
    const copy = structuredClone(original)
    updateField(original, [1], { opening: 'tilt' })
    setSizes(original, [], [500, null])
    splitField(original, [0], 'horizontal', 2)
    expect(original).toEqual(copy)
  })

  it('refuses paths that do not exist', () => {
    expect(() => getNode(newField(), [0])).toThrow()
    expect(() => updateField(columns(2), [], { opening: 'tilt' })).toThrow()
  })
})

describe('size boxes', () => {
  it('reads plain and Arabic digits', () => {
    expect(parseSize('900')).toBe(900)
    expect(parseSize(' 912.5 ')).toBe(912.5)
    expect(parseSize('٩٠٠')).toBe(900)
    expect(parseSize('۱۲۰۰')).toBe(1200)
    expect(parseSize('٩١٢٫٥')).toBe(912.5)
    expect(parseSize('912,5')).toBe(912.5)
    expect(normalizeNumber('١٢٣')).toBe('123')
  })

  it('blank or nonsense gives no size', () => {
    expect(parseSize('')).toBeNull()
    expect(parseSize('   ')).toBeNull()
    expect(parseSize('abc')).toBeNull()
  })
})

describe('new elements', () => {
  const profiles = [
    { id: 1, system_id: 1, role: 'frame' },
    { id: 2, system_id: 1, role: 'mullion' },
    { id: 3, system_id: 1, role: 'sash' },
    { id: 4, system_id: 2, role: 'frame' },
    { id: 5, system_id: 2, role: 'transom' },
  ] as Row[]

  it('picks the first fitting profile of the system for each place', () => {
    expect(defaultProfiles(profiles, 1)).toEqual({
      frame_profile_id: 1,
      mullion_profile_id: 2,
      transom_profile_id: 2,
      sash_profile_id: 3,
      bead_profile_id: null,
    })
    expect(defaultProfiles(profiles, 2)).toMatchObject({ mullion_profile_id: 5, transom_profile_id: 5, sash_profile_id: null })
  })

  it('needs a system, a frame profile and a glass type', () => {
    const systems = [{ id: 1 }] as Row[]
    const glass = [{ id: 9 }] as Row[]
    expect(newElement({ systems, profiles, glass }, 'W')).toMatchObject({ system_id: 1, frame_profile_id: 1, glass_id: 9 })
    expect(newElement({ systems: [{ id: 2 }, ...systems] as Row[], profiles, glass }, 'W', 1)).toMatchObject({
      system_id: 1,
    })
    expect(newElement({ systems, profiles, glass: [] }, 'W')).toBeNull()
    expect(newElement({ systems: [], profiles, glass }, 'W')).toBeNull()
    expect(newElement({ systems, profiles: [], glass }, 'W')).toBeNull()
  })
})

describe('designer labels', () => {
  it('every opening, profile place and error code has a label', () => {
    const keys = [
      ...OPENINGS.map((o) => `opening.${o}`),
      ...PROFILE_CHOICES.map((c) => c.label),
      // Codes the API sends for designs it cannot build.
      ...[
        'unknown_system', 'unknown_profile', 'profile_wrong_system', 'profile_wrong_role', 'unknown_glass',
        'size_not_positive', 'sizes_mismatch', 'sizes_too_big', 'element_too_small', 'field_too_small',
        'sash_too_small', 'mullion_missing', 'transom_missing', 'sash_missing',
      ].map((c) => `error.${c}`),
    ]
    for (const key of keys) expect(key in messages.en, key).toBe(true)
  })
})
