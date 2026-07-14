import "@testing-library/jest-dom/vitest";
import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { ReviewWorkbench } from "./ReviewWorkbench";
import type { DetailData } from "@/lib/types";

const actions = vi.hoisted(() => ({
  approveDomain: vi.fn().mockResolvedValue({ ok: true, result: "brand.example" }),
  resolve: vi.fn().mockResolvedValue({ ok: true }),
  approve: vi.fn().mockResolvedValue({ ok: true, result: "approved" }),
  reject: vi.fn().mockResolvedValue({ ok: true }),
}));

vi.mock("@/app/actions", () => ({
  approveProductSourceDomainAction: actions.approveDomain,
  resolveTokenAction: actions.resolve,
  approveSubmissionAction: actions.approve,
  rejectSubmissionAction: actions.reject,
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  });
});
afterEach(() => { cleanup(); vi.clearAllMocks(); vi.unstubAllGlobals(); });

function detail(position = 1): DetailData {
  return {
    submission: {
      id: "submission-1",
      brand_name: "Example",
      product_name: "Serum",
      submitted_by: null,
      raw_ingredient_text: "Directions",
      status: "pending_human",
      verification: { verdict: "not_found" },
      created_at: new Date().toISOString(),
    },
    tokens: [{
      id: "token-1",
      position,
      raw_token: "Directions",
      normalized_token: "directions",
      matched_ingredient_id: null,
      match_type: null,
      match_confidence: null,
      resolution: "pending_human",
      canonical_name: null,
      evidence: [],
    }],
    trigger: "junk_at_top_positions",
    approvedSourceDomain: null,
    similarProduct: null,
  };
}

describe("ReviewWorkbench token controls", () => {
  it("adds the verified website to the brand allowlist without approving the product", async () => {
    const initial = detail();
    initial.submission.verification = {
      verdict: "untrusted_source",
      source_url: "https://www.brand.example/products/serum",
    };
    render(<ReviewWorkbench initial={initial}><div>Header</div></ReviewWorkbench>);

    fireEvent.click(screen.getByRole("button", { name: "Add website to approved list" }));

    await waitFor(() => expect(actions.approveDomain).toHaveBeenCalledWith("submission-1"));
    expect(screen.getByText("Website approved for this brand")).toBeInTheDocument();
    expect(actions.approve).not.toHaveBeenCalled();
  });

  it("offers only the three supported curator resolutions", () => {
    render(<ReviewWorkbench initial={detail()}><div>Header</div></ReviewWorkbench>);
    expect(screen.getByRole("option", { name: "Matched" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "New ingredient" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Junk" })).toBeInTheDocument();
    expect(screen.queryByText("unmatched_keep")).not.toBeInTheDocument();
  });

  it("requires two confirmations before dropping a top-position token", async () => {
    render(<ReviewWorkbench initial={detail(1)}><div>Header</div></ReviewWorkbench>);
    fireEvent.change(screen.getByLabelText("Resolve Directions"), { target: { value: "junk" } });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(actions.resolve).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm drop" }));
    await waitFor(() => expect(actions.resolve).toHaveBeenCalledWith(expect.objectContaining({
      tokenId: "token-1",
      resolution: "junk",
    })));
  });

  it("drops a later junk token with one confirmation and enables approval", async () => {
    render(<ReviewWorkbench initial={detail(29)}><div>Header</div></ReviewWorkbench>);
    const approve = screen.getByRole("button", { name: "Approve" });
    expect(approve).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Resolve Directions"), {
      target: { value: "junk" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirm drop" }));

    await waitFor(() => expect(actions.resolve).toHaveBeenCalledWith(
      expect.objectContaining({ tokenId: "token-1", resolution: "junk" }),
    ));
    expect(approve).toBeEnabled();
  });

  it("autocompletes live database matches and only then shows confirm match", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ id: "ingredient-1", inci_name: "Glycerin", confidence: 0.91 }],
    }));
    render(<ReviewWorkbench initial={detail(29)}><div>Header</div></ReviewWorkbench>);

    fireEvent.change(screen.getByLabelText("Resolve Directions"), {
      target: { value: "matched" },
    });
    const search = screen.getByRole("combobox", { name: "Search existing ingredients" });
    fireEvent.change(search, { target: { value: "Gly" } });

    expect(screen.queryByRole("button", { name: "Confirm match" })).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole("option", { name: "Glycerin 91% match" }));
    expect(search).toHaveValue("Glycerin");
    fireEvent.click(screen.getByRole("button", { name: "Confirm match" }));

    await waitFor(() => expect(actions.resolve).toHaveBeenCalledWith(
      expect.objectContaining({
        tokenId: "token-1",
        resolution: "matched",
        ingredientId: "ingredient-1",
        ingredientName: "Glycerin",
      }),
    ));
    expect(screen.getByText("Glycerin")).toBeInTheDocument();
    expect(screen.getByText("matched")).toBeInTheDocument();
  });
});
