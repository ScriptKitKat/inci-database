import "server-only";
import { notFound } from "next/navigation";
import { requireCuratorSession } from "@/lib/auth";
import { serviceClient } from "@/lib/supabase";
import type { DetailData, SubmissionToken } from "@/lib/types";

export async function getQueue() {
  await requireCuratorSession();
  const db = serviceClient();
  const { data: submissions, error } = await db
    .from("product_submissions")
    .select("id, brand_name, product_name, created_at, verification")
    .eq("status", "pending_human")
    .order("created_at");
  if (error) throw error;
  const ids = (submissions || []).map((row) => row.id);
  if (!ids.length) return [];
  const [{ data: tokens }, { data: audits }] = await Promise.all([
    db.from("submission_tokens").select("submission_id, resolution").in("submission_id", ids),
    db
      .from("submission_audit")
      .select("submission_id, payload, created_at")
      .in("submission_id", ids)
      .order("created_at", { ascending: false }),
  ]);
  return (submissions || []).map((row) => ({
    ...row,
    trigger:
      (audits || []).find(
        (audit) => audit.submission_id === row.id && (audit.payload as { trigger?: string })?.trigger,
      )?.payload?.trigger || (row.verification as { verdict?: string })?.verdict || null,
    unresolved: (tokens || []).filter(
      (token) =>
        token.submission_id === row.id &&
        ["unresolved", "pending_human"].includes(token.resolution),
    ).length,
  }));
}

export async function getSubmissionDetail(id: string): Promise<DetailData> {
  await requireCuratorSession();
  const db = serviceClient();
  const [{ data: submission }, { data: rawTokens }, { data: audits }] = await Promise.all([
    db.from("product_submissions").select("*").eq("id", id).maybeSingle(),
    db.from("submission_tokens").select("*").eq("submission_id", id).order("position"),
    db
      .from("submission_audit")
      .select("action, payload, created_at")
      .eq("submission_id", id)
      .order("created_at", { ascending: false }),
  ]);
  if (!submission) notFound();
  const ingredientIds = [...new Set((rawTokens || []).map((t) => t.matched_ingredient_id).filter(Boolean))];
  const { data: ingredients } = ingredientIds.length
    ? await db.from("ingredients").select("id, inci_name").in("id", ingredientIds)
    : { data: [] as { id: string; inci_name: string }[] };
  const tokens: SubmissionToken[] = (rawTokens || []).map((token) => ({
    ...token,
    matched_name: ingredients?.find((ingredient) => ingredient.id === token.matched_ingredient_id)?.inci_name,
    escalation:
      (audits || []).find(
        (audit) => audit.payload?.token_id === token.id && audit.payload?.trigger,
      )?.payload?.trigger || null,
  }));
  const verification = submission.verification as Record<string, unknown>;
  const similar = (verification.similar_product || verification.existing_product) as
    | { product_id?: string }
    | undefined;
  let similarProduct = null;
  if (similar?.product_id) {
    const { data } = await db
      .from("products")
      .select("id, name, brands(name)")
      .eq("id", similar.product_id)
      .maybeSingle();
    if (data) {
      const brand = data.brands as unknown as { name?: string } | null;
      similarProduct = { id: data.id, name: data.name, brand: brand?.name || "Unknown brand" };
    }
  }
  const trigger =
    (audits || []).find((audit) => audit.payload?.trigger)?.payload?.trigger ||
    (verification.verdict as string | undefined) ||
    null;
  return { submission, tokens, trigger, similarProduct } as DetailData;
}
