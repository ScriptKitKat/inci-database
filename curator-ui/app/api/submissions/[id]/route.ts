import { NextResponse } from "next/server";
import { getSubmissionDetail } from "@/lib/data";

export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return NextResponse.json(await getSubmissionDetail(id));
}
