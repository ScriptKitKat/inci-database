"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import {
  clearCuratorSession,
  normalizeReviewerName,
  requireCuratorSession,
  setCuratorSession,
  verifyPassword,
} from "@/lib/auth";
import { remoteIngredientClient, serviceClient } from "@/lib/supabase";

type Result = {
  ok: boolean;
  error?: string;
  result?: string;
  productId?: string;
  ingredientId?: string;
  ingredientName?: string;
};
const failures = new Map<string, { count: number; resetAt: number }>();

export async function loginAction(_: Result, formData: FormData): Promise<Result> {
  const name = String(formData.get("name") || "");
  const password = String(formData.get("password") || "");
  const ip = (await headers()).get("x-forwarded-for")?.split(",")[0] || "local";
  const now = Date.now();
  const attempt = failures.get(ip);
  if (attempt && attempt.resetAt > now && attempt.count >= 5) {
    return { ok: false, error: "Too many attempts. Try again in a few minutes." };
  }
  const { data: reviewer } = await serviceClient()
    .from("curator_reviewers")
    .select("id, display_name, active")
    .eq("normalized_name", normalizeReviewerName(name))
    .maybeSingle();
  if (!reviewer?.active || !verifyPassword(password)) {
    failures.set(ip, {
      count: attempt && attempt.resetAt > now ? attempt.count + 1 : 1,
      resetAt: now + 5 * 60 * 1000,
    });
    return { ok: false, error: "Invalid reviewer name or password" };
  }
  failures.delete(ip);
  await setCuratorSession(reviewer.id, reviewer.display_name);
  redirect("/");
}

export async function logoutAction() {
  await clearCuratorSession();
  redirect("/login");
}

export async function resolveTokenAction(input: {
  tokenId: string;
  submissionId: string;
  resolution: "matched" | "new_ingredient" | "junk";
  ingredientId?: string;
  canonicalName?: string;
}): Promise<Result> {
  const session = await requireCuratorSession();
  const db = serviceClient();
  let ingredientId = input.ingredientId;
  let ingredientName: string | undefined;

  if (input.resolution === "matched") {
    if (!ingredientId) return { ok: false, error: "Choose an existing ingredient first." };
    const { data: remoteIngredient, error: remoteError } = await remoteIngredientClient()
      .from("ingredients")
      .select("id, inci_name, slug, normalized_name")
      .eq("id", ingredientId)
      .maybeSingle();
    if (remoteError || !remoteIngredient) {
      return { ok: false, error: remoteError?.message || "The selected ingredient no longer exists." };
    }

    const { data: syncedIngredientId, error: syncError } = await db.rpc(
      "sync_remote_catalog_ingredient",
      {
        p_id: remoteIngredient.id,
        p_inci_name: remoteIngredient.inci_name,
        p_slug: remoteIngredient.slug,
      },
    );
    if (syncError || !syncedIngredientId) {
      return { ok: false, error: syncError?.message || "Could not link the catalog ingredient." };
    }
    ingredientId = String(syncedIngredientId);
    ingredientName = remoteIngredient.inci_name;
  }

  const { error } = await db.rpc("resolve_submission_token", {
    p_token_id: input.tokenId,
    p_resolution: input.resolution,
    p_ingredient_id: ingredientId || null,
    p_canonical_name: input.canonicalName || null,
    p_actor: session.displayName,
  });
  if (error) return { ok: false, error: error.message };
  revalidatePath(`/submissions/${input.submissionId}`);
  return { ok: true, ingredientId, ingredientName };
}

export async function approveSubmissionAction(id: string): Promise<Result> {
  const session = await requireCuratorSession();
  const { data, error } = await serviceClient().rpc("apply_product_submission", {
    p_id: id,
    p_actor: session.displayName,
  });
  if (error) return { ok: false, error: error.message };
  if (String(data) === "duplicate") {
    const { data: submission } = await serviceClient()
      .from("product_submissions")
      .select("product_id")
      .eq("id", id)
      .single();
    return { ok: true, result: "duplicate", productId: submission?.product_id || undefined };
  }
  revalidatePath("/");
  return { ok: true, result: String(data) };
}

export async function rejectSubmissionAction(id: string, reason: string): Promise<Result> {
  const session = await requireCuratorSession();
  if (reason.trim().length < 10) return { ok: false, error: "Enter at least 10 characters." };
  const { error } = await serviceClient().rpc("reject_product_submission", {
    p_id: id,
    p_reason: reason.trim(),
    p_actor: session.displayName,
  });
  if (error) return { ok: false, error: error.message };
  revalidatePath("/");
  return { ok: true };
}
