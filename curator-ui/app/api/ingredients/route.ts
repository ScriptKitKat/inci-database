import { NextRequest, NextResponse } from "next/server";
import { requireCuratorSession } from "@/lib/auth";
import { remoteIngredientClient } from "@/lib/supabase";
import {
  rankIngredientMatches,
  type SearchableIngredient,
} from "@/lib/ingredient-search";

const PAGE_SIZE = 1_000;
const CACHE_MS = 60_000;
let catalog: { expiresAt: number; rows: SearchableIngredient[] } | null = null;
let catalogRequest: Promise<SearchableIngredient[]> | null = null;

async function remoteIngredientCatalog() {
  if (catalog && catalog.expiresAt > Date.now()) return catalog.rows;
  if (catalogRequest) return catalogRequest;
  catalogRequest = (async () => {
    const db = remoteIngredientClient();
    const rows: SearchableIngredient[] = [];
    for (let from = 0; ; from += PAGE_SIZE) {
      const { data, error } = await db
        .from("ingredients")
        .select("id, inci_name, normalized_name")
        .order("normalized_name")
        .range(from, from + PAGE_SIZE - 1);
      if (error) throw error;
      rows.push(...((data || []) as SearchableIngredient[]));
      if (!data || data.length < PAGE_SIZE) break;
    }
    catalog = { expiresAt: Date.now() + CACHE_MS, rows };
    return rows;
  })();
  try {
    return await catalogRequest;
  } finally {
    catalogRequest = null;
  }
}

export async function GET(request: NextRequest) {
  await requireCuratorSession();
  const query = request.nextUrl.searchParams.get("q")?.trim() || "";
  if (query.length < 2) {
    return NextResponse.json([], { headers: { "Cache-Control": "no-store" } });
  }
  try {
    const data = rankIngredientMatches(await remoteIngredientCatalog(), query);
    return NextResponse.json(data, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Remote ingredient search failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
