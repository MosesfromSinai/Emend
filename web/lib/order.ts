// Mirrors latex/render.py's _reorder_by_key -- items whose key isn't in
// `order` keep their relative position, appended after the ordered ones,
// so a stale/partial order never drops an item.
export function reorderByKey<T>(items: T[], order: string[] | undefined, key: (item: T) => string): T[] {
  if (!order || order.length === 0) return items;
  const byKey = new Map<string, T>(items.map((item) => [key(item), item]));
  const seen = new Set(order);
  const ordered: T[] = [];
  for (const k of order) {
    const item = byKey.get(k);
    if (item !== undefined) ordered.push(item);
  }
  for (const item of items) {
    if (!seen.has(key(item))) ordered.push(item);
  }
  return ordered;
}
