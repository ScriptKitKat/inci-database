export type SearchableIngredient = {
  id: string;
  inci_name: string;
  normalized_name: string;
};

export type IngredientSuggestion = {
  id: string;
  inci_name: string;
  confidence: number;
};

export function normalizeIngredientQuery(value: string) {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase()
    .replace(/[^a-z0-9 ]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function fuzzyIngredientScore(query: string, candidate: string): number | null {
  const needle = normalizeIngredientQuery(query);
  const haystack = normalizeIngredientQuery(candidate);
  if (!needle || !haystack) return null;
  if (needle === haystack) return 1;
  if (haystack.startsWith(needle)) return 0.95;
  if (haystack.includes(needle)) return 0.9;

  const positions: number[] = [];
  let cursor = 0;
  for (const character of needle) {
    const position = haystack.indexOf(character, cursor);
    if (position === -1) return null;
    positions.push(position);
    cursor = position + 1;
  }
  const span = positions.at(-1)! - positions[0] + 1;
  const density = needle.length / span;
  const lengthFit = needle.length / haystack.length;
  const startsAtBoundary = positions[0] === 0 || haystack[positions[0] - 1] === " ";
  return Math.min(0.89, 0.45 + density * 0.25 + lengthFit * 0.1 + (startsAtBoundary ? 0.08 : 0));
}

export function rankIngredientMatches(
  ingredients: SearchableIngredient[],
  query: string,
  limit = 12,
): IngredientSuggestion[] {
  return ingredients
    .map((ingredient) => ({
      id: ingredient.id,
      inci_name: ingredient.inci_name,
      confidence: fuzzyIngredientScore(query, ingredient.normalized_name),
    }))
    .filter((ingredient): ingredient is IngredientSuggestion => ingredient.confidence !== null)
    .sort((left, right) => right.confidence - left.confidence || left.inci_name.localeCompare(right.inci_name))
    .slice(0, limit);
}
