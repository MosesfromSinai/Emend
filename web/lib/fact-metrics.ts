// Client-side, ephemeral heuristic for "does this fact carry a metric" --
// drives the Confirm screen's chips/filters. Never persisted: purely a
// review aid, not a schema field.

const METRIC_PATTERNS = [
  /\d+\+\s*[a-z]+/gi, // "25+ tests", "20+ components"
  /[+\-−]\s?\d+(\.\d+)?%/g, // "+35%", "-80%", "−80%"
  /\b\d+(\.\d+)?%/g, // bare "80%"
];

export function extractMetrics(text: string): string[] {
  const found = new Set<string>();
  for (const pattern of METRIC_PATTERNS) {
    for (const match of text.matchAll(pattern)) {
      found.add(match[0].trim());
    }
  }
  return [...found];
}

export function hasMetric(text: string): boolean {
  return extractMetrics(text).length > 0;
}
