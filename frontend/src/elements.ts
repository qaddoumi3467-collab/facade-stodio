// Element defaults: which catalog profiles fit each place in an element,
// and what a new element starts as.

import type { ElementData, Row } from './api'
import { newField } from './layout'

export type ProfileKey =
  | 'frame_profile_id'
  | 'mullion_profile_id'
  | 'transom_profile_id'
  | 'sash_profile_id'
  | 'bead_profile_id'

// Which catalog roles fit each profile choice (mullion and transom profiles
// are often the same extrusion, so either fits both).
export const PROFILE_CHOICES: { key: ProfileKey; label: string; roles: string[]; optional?: boolean }[] = [
  { key: 'frame_profile_id', label: 'designer.frame', roles: ['frame'] },
  { key: 'mullion_profile_id', label: 'designer.mullion', roles: ['mullion', 'transom'], optional: true },
  { key: 'transom_profile_id', label: 'designer.transom', roles: ['transom', 'mullion'], optional: true },
  { key: 'sash_profile_id', label: 'designer.sash', roles: ['sash'], optional: true },
  { key: 'bead_profile_id', label: 'designer.bead', roles: ['glazing_bead'], optional: true },
]

export interface Catalog {
  systems: Row[]
  profiles: Row[]
  glass: Row[]
}

/** Profile choices for a system: the first profile of each fitting role. */
export function defaultProfiles(profiles: Row[], systemId: number): Record<ProfileKey, number | null> {
  const out = {} as Record<ProfileKey, number | null>
  for (const choice of PROFILE_CHOICES) {
    const match = choice.roles
      .map((role) => profiles.find((p) => p.system_id === systemId && p.role === role))
      .find(Boolean)
    out[choice.key] = match ? match.id : null
  }
  return out
}

/** A new single-field element in the given system (or the first one). */
export function newElement(catalog: Catalog, name: string, systemId?: number): ElementData | null {
  const system = catalog.systems.find((s) => s.id === systemId) ?? catalog.systems[0]
  const glass = catalog.glass[0]
  if (!system || !glass) return null
  const profiles = defaultProfiles(catalog.profiles, system.id)
  if (profiles.frame_profile_id === null) return null
  return {
    position: '',
    name,
    quantity: 1,
    system_id: system.id,
    width_mm: 1200,
    height_mm: 1400,
    ...profiles,
    frame_profile_id: profiles.frame_profile_id,
    glass_id: glass.id,
    layout: newField(),
  }
}
