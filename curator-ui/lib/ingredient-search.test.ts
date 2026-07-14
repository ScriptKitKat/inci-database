import { describe, expect, it } from "vitest";
import {
  fuzzyIngredientScore,
  normalizeIngredientQuery,
  rankIngredientMatches,
} from "./ingredient-search";

const ingredients = [
  { id: "water", inci_name: "Water", normalized_name: "water" },
  { id: "watermelon", inci_name: "Watermelon Seed Oil", normalized_name: "watermelon seed oil" },
  { id: "wax", inci_name: "Candelilla Wax", normalized_name: "candelilla wax" },
];

describe("fzf-style ingredient ranking", () => {
  it("normalizes punctuation and accents like the catalog search field", () => {
    expect(normalizeIngredientQuery("  Água / WATER™  ")).toBe("agua watertm");
  });

  it("ranks exact and prefix matches before broader matches", () => {
    expect(rankIngredientMatches(ingredients, "water").map((row) => row.id)).toEqual([
      "water",
      "watermelon",
    ]);
  });

  it("supports ordered subsequence typo searches", () => {
    expect(fuzzyIngredientScore("watr", "water")).toBeGreaterThan(0.7);
    expect(rankIngredientMatches(ingredients, "watr")[0].id).toBe("water");
  });

  it("does not suggest candidates whose characters do not match in order", () => {
    expect(fuzzyIngredientScore("water", "candelilla wax")).toBeNull();
  });
});
