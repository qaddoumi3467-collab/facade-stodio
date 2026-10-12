// The element layout tree, matching the API: a field is one glazed opening,
// a split divides an area into columns (vertical, with mullions) or rows
// (horizontal, with transoms). A path is the list of child indexes from the
// root to a node.

export const OPENINGS = [
  'fixed',
  'turn_left',
  'turn_right',
  'tilt_turn_left',
  'tilt_turn_right',
  'tilt',
  'sliding_left',
  'sliding_right',
] as const

export type Opening = (typeof OPENINGS)[number]
export type Direction = 'vertical' | 'horizontal'
export type Path = number[]

export interface FieldNode {
  kind: 'field'
  opening: Opening
  glass_id?: number | null
}

export interface SplitNode {
  kind: 'split'
  direction: Direction
  /** Centre-line sizes in mm; null shares what is left. */
  sizes: (number | null)[]
  children: LayoutNode[]
}

export type LayoutNode = FieldNode | SplitNode

/** The most parts one split can have (the API's limit). */
export const MAX_PARTS = 20

export const newField = (): FieldNode => ({ kind: 'field', opening: 'fixed', glass_id: null })

export function pathKey(path: Path): string {
  return path.join('.')
}

export function getNode(root: LayoutNode, path: Path): LayoutNode {
  let node = root
  for (const i of path) {
    if (node.kind !== 'split' || !node.children[i]) throw new Error(`No node at ${pathKey(path)}`)
    node = node.children[i]
  }
  return node
}

/** A copy of the tree with the node at `path` replaced. */
export function replaceNode(root: LayoutNode, path: Path, next: LayoutNode): LayoutNode {
  if (path.length === 0) return next
  if (root.kind !== 'split') throw new Error(`No node at ${pathKey(path)}`)
  const [i, ...rest] = path
  const children = root.children.slice()
  children[i] = replaceNode(children[i], rest, next)
  return { ...root, children }
}

/** Split a field into `count` equal parts. Splitting a field that already
 *  sits in a split the same way adds parts to that split instead, so three
 *  columns stay one row of three rather than a column inside a column. */
export function splitField(root: LayoutNode, path: Path, direction: Direction, count: number): LayoutNode {
  const field = getNode(root, path)
  if (field.kind !== 'field') throw new Error('Only a field can be split')
  let parts = Math.max(2, Math.min(MAX_PARTS, Math.round(count)))
  if (path.length > 0) {
    const parentPath = path.slice(0, -1)
    const parent = getNode(root, parentPath) as SplitNode
    if (parent.direction === direction) {
      parts = Math.min(parts, MAX_PARTS - parent.children.length + 1)
      if (parts < 2) return root
      const at = path[path.length - 1]
      const copies = Array.from({ length: parts }, () => ({ ...field }))
      const sizes = parent.sizes.slice()
      sizes.splice(at, 1, ...Array<null>(parts).fill(null))
      const children = parent.children.slice()
      children.splice(at, 1, ...copies)
      return replaceNode(root, parentPath, { ...parent, sizes, children })
    }
  }
  return replaceNode(root, path, {
    kind: 'split',
    direction,
    sizes: Array<null>(parts).fill(null),
    children: Array.from({ length: parts }, () => ({ ...field })),
  })
}

/** Remove the dividers of the split at `path`; its first field takes its place. */
export function removeSplit(root: LayoutNode, path: Path): LayoutNode {
  const node = getNode(root, path)
  if (node.kind !== 'split') return root
  return replaceNode(root, path, firstField(node))
}

function firstField(node: LayoutNode): FieldNode {
  return node.kind === 'field' ? node : firstField(node.children[0])
}

export function updateField(root: LayoutNode, path: Path, change: Partial<FieldNode>): LayoutNode {
  const node = getNode(root, path)
  if (node.kind !== 'field') throw new Error('Not a field')
  return replaceNode(root, path, { ...node, ...change })
}

export function setSizes(root: LayoutNode, path: Path, sizes: (number | null)[]): LayoutNode {
  const node = getNode(root, path)
  if (node.kind !== 'split') throw new Error('Not a split')
  return replaceNode(root, path, { ...node, sizes })
}

/** Arabic-Indic digits (٠-٩, ۰-۹) and the Arabic decimal mark become plain
 *  digits and a point, so sizes can be typed on an Arabic keyboard. */
export function normalizeNumber(text: string): string {
  return text
    .trim()
    .replace(/[\u0660-\u0669]/g, (d) => String(d.charCodeAt(0) - 0x0660))
    .replace(/[\u06f0-\u06f9]/g, (d) => String(d.charCodeAt(0) - 0x06f0))
    .replace(/[\u066b,]/g, '.')
}

/** What the user typed in a size box as a number; blank or not a number
 *  gives null. */
export function parseSize(text: string): number | null {
  const clean = normalizeNumber(text)
  const value = Number(clean)
  return clean === '' || !Number.isFinite(value) ? null : value
}
