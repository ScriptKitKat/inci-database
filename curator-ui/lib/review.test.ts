import { describe, expect, it } from "vitest";
import { canApprove, triggerLabel } from "./review";

describe("canApprove", () => {
  it.each(["unresolved", "pending_human"])("blocks %s tokens", (resolution) => {
    expect(canApprove([{ resolution: "matched" }, { resolution }])).toBe(false);
  });

  it("accepts exactly the three curator resolutions", () => {
    expect(canApprove([
      { resolution: "matched" },
      { resolution: "new_ingredient" },
      { resolution: "junk" },
    ])).toBe(true);
  });

  it("does not approve an empty submission", () => {
    expect(canApprove([])).toBe(false);
  });
});

describe("triggerLabel", () => {
  it("uses the specific similar-product copy", () => {
    expect(triggerLabel("similar_product")).toBe("Similar formula, different product name");
  });
});
