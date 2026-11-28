import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { IngredientReviews } from "./ingredient-reviews";

describe("IngredientReviews", () => {
  it("shows ingredient names, reasons, and the review count", () => {
    render(<IngredientReviews rows={[{
      ingredientId: "one", name: "Glycerin", reason: "enrichment_confidence_below_threshold",
    }]} />);
    expect(screen.getByText("Ingredients needing review (1)")).toBeTruthy();
    expect(screen.getByText("Glycerin")).toBeTruthy();
    expect(screen.getByText("enrichment confidence below threshold")).toBeTruthy();
  });
  it("does not render an empty queue", () => {
    const { container } = render(<IngredientReviews rows={[]} />);
    expect(container.innerHTML).toBe("");
  });
});
