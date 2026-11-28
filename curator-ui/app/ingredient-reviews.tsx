import { triggerLabel } from "@/lib/review";
import type { IngredientReview } from "@/lib/types";

export function IngredientReviews({ rows }: { rows: IngredientReview[] }) {
  if (!rows.length) return null;
  return (
    <section aria-label="Ingredient enrichment reviews">
      <h2>Ingredients needing review ({rows.length})</h2>
      <p>Enrichment is paused for these ingredients pending curator review.</p>
      <div className="table-wrap"><table>
        <thead><tr><th>Ingredient</th><th>Reason</th></tr></thead>
        <tbody>{rows.map((row) => (
          <tr key={row.ingredientId}><td>{row.name}</td><td>{triggerLabel(row.reason)}</td></tr>
        ))}</tbody>
      </table></div>
    </section>
  );
}
