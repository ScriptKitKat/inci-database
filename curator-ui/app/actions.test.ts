import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  localFrom: vi.fn(),
  localRpc: vi.fn(),
  remoteMaybeSingle: vi.fn(),
  revalidatePath: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  requireCuratorSession: vi.fn().mockResolvedValue({ displayName: "Priscilla" }),
  clearCuratorSession: vi.fn(),
  normalizeReviewerName: vi.fn((value: string) => value.toLowerCase()),
  setCuratorSession: vi.fn(),
  verifyPassword: vi.fn(),
}));
vi.mock("@/lib/supabase", () => ({
  serviceClient: () => ({
    from: mocks.localFrom,
    rpc: mocks.localRpc,
  }),
  remoteIngredientClient: () => ({
    from: () => ({
      select: () => ({ eq: () => ({ maybeSingle: mocks.remoteMaybeSingle }) }),
    }),
  }),
}));
vi.mock("next/cache", () => ({ revalidatePath: mocks.revalidatePath }));
vi.mock("next/headers", () => ({ headers: vi.fn() }));
vi.mock("next/navigation", () => ({ redirect: vi.fn() }));

import { approveProductSourceDomainAction, resolveTokenAction } from "./actions";

const remoteWater = {
  id: "11111111-1111-1111-1111-111111111111",
  inci_name: "Water",
  slug: "water",
  normalized_name: "water",
};

describe("resolveTokenAction existing ingredient matches", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.remoteMaybeSingle.mockResolvedValue({ data: remoteWater, error: null });
    mocks.localRpc
      .mockResolvedValueOnce({ data: remoteWater.id, error: null })
      .mockResolvedValueOnce({ error: null });
  });

  it("mirrors a selected remote catalog row before linking the token", async () => {
    const result = await resolveTokenAction({
      tokenId: "token-1",
      submissionId: "submission-1",
      resolution: "matched",
      ingredientId: remoteWater.id,
    });

    expect(mocks.localRpc).toHaveBeenNthCalledWith(1, "sync_remote_catalog_ingredient", {
      p_id: remoteWater.id,
      p_inci_name: "Water",
      p_slug: "water",
    });
    expect(mocks.localRpc).toHaveBeenNthCalledWith(2, "resolve_submission_token", expect.objectContaining({
      p_ingredient_id: remoteWater.id,
      p_resolution: "matched",
    }));
    expect(result).toEqual(expect.objectContaining({
      ok: true,
      ingredientId: remoteWater.id,
      ingredientName: "Water",
    }));
  });

  it("reuses an equivalent ingredient already present in the review database", async () => {
    mocks.localRpc
      .mockReset()
      .mockResolvedValueOnce({
        data: "22222222-2222-2222-2222-222222222222",
        error: null,
      })
      .mockResolvedValueOnce({ error: null });

    const result = await resolveTokenAction({
      tokenId: "token-1",
      submissionId: "submission-1",
      resolution: "matched",
      ingredientId: remoteWater.id,
    });

    expect(mocks.localRpc).toHaveBeenNthCalledWith(2, "resolve_submission_token", expect.objectContaining({
      p_ingredient_id: "22222222-2222-2222-2222-222222222222",
    }));
    expect(result.ingredientId).toBe("22222222-2222-2222-2222-222222222222");
  });
});

describe("approveProductSourceDomainAction", () => {
  it("approves the verified hostname only for the submission brand", async () => {
    const upsert = vi.fn().mockResolvedValue({ error: null });
    const insertAudit = vi.fn().mockResolvedValue({ error: null });
    mocks.localFrom.mockImplementation((table: string) => {
      if (table === "product_submissions") {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: vi.fn().mockResolvedValue({
                data: {
                  brand_name: "New Brand",
                  status: "pending_human",
                  verification: {
                    verdict: "untrusted_source",
                    source_url: "https://www.newbrand.example/products/serum",
                  },
                },
                error: null,
              }),
            }),
          }),
        };
      }
      if (table === "brand_product_domains") return { upsert };
      if (table === "submission_audit") return { insert: insertAudit };
      throw new Error(`Unexpected table: ${table}`);
    });

    const result = await approveProductSourceDomainAction("submission-1");

    expect(upsert).toHaveBeenCalledWith(
      { normalized_brand_name: "NEW BRAND", domain: "newbrand.example" },
      { onConflict: "normalized_brand_name,domain", ignoreDuplicates: true },
    );
    expect(insertAudit).toHaveBeenCalledWith(expect.objectContaining({
      submission_id: "submission-1",
      actor: "Priscilla",
      payload: expect.objectContaining({ domain: "newbrand.example" }),
    }));
    expect(result).toEqual({ ok: true, result: "newbrand.example" });
  });
});
