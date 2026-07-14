export const unresolvedResolutions = new Set(["unresolved", "pending_human"]);

export function canApprove(tokens: { resolution: string }[]) {
  return tokens.length > 0 && tokens.every((token) => !unresolvedResolutions.has(token.resolution));
}

export const triggerLabels: Record<string, string> = {
  similar_product: "Similar formula, different product name",
  same_name_different_formula: "Same product name, different formula",
  divergent_list: "Divergent ingredient list",
  product_not_found: "Product not found",
  product_ingredient_list_missing: "Online ingredient list missing",
  product_source_untrusted: "Untrusted product source",
  unresolved_tokens: "Unresolved ingredients",
  source_disagreement: "Sources disagree on spelling",
  llm_unknown: "Ingredient judgment uncertain",
  submission_too_large: "Submission too large for automatic verification",
  product_name_resolved: "Product name matched from trusted source",
};

export function triggerLabel(trigger: string | null) {
  return trigger ? triggerLabels[trigger] || trigger.replaceAll("_", " ") : "Needs review";
}
