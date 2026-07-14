import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
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

import { resolveTokenAction } from "./actions";

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
