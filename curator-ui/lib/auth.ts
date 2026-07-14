import "server-only";
import { createHmac, scryptSync, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { serviceClient } from "@/lib/supabase";

const COOKIE = "curator_session";
const MAX_AGE = 8 * 60 * 60;

export type CuratorSession = { reviewerId: string; displayName: string; expiresAt: number };

export function normalizeReviewerName(value: string) {
  return value.trim().toLocaleLowerCase().replace(/\s+/g, " ");
}

function secret() {
  const value = process.env.CURATOR_SESSION_SECRET;
  if (!value || value.length < 32) throw new Error("CURATOR_SESSION_SECRET must be at least 32 characters");
  return value;
}

function sign(payload: string) {
  return createHmac("sha256", secret()).update(payload).digest("base64url");
}

export function encodeSession(session: CuratorSession) {
  const payload = Buffer.from(JSON.stringify(session)).toString("base64url");
  return `${payload}.${sign(payload)}`;
}

export function decodeSession(value?: string): CuratorSession | null {
  if (!value) return null;
  const [payload, signature] = value.split(".");
  if (!payload || !signature) return null;
  const expected = sign(payload);
  if (signature.length !== expected.length || !timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return null;
  }
  try {
    const session = JSON.parse(Buffer.from(payload, "base64url").toString()) as CuratorSession;
    return session.expiresAt > Date.now() ? session : null;
  } catch {
    return null;
  }
}

export function verifyPassword(password: string) {
  const encoded = process.env.CURATOR_PASSWORD_HASH || "";
  const [saltHex, hashHex] = encoded.split(":");
  if (!saltHex || !hashHex) return false;
  const actual = scryptSync(password, Buffer.from(saltHex, "hex"), 64);
  const expected = Buffer.from(hashHex, "hex");
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

export async function setCuratorSession(reviewerId: string, displayName: string) {
  const expiresAt = Date.now() + MAX_AGE * 1000;
  (await cookies()).set(COOKIE, encodeSession({ reviewerId, displayName, expiresAt }), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: MAX_AGE,
  });
}

export async function clearCuratorSession() {
  (await cookies()).delete(COOKIE);
}

export async function requireCuratorSession(): Promise<CuratorSession> {
  const session = decodeSession((await cookies()).get(COOKIE)?.value);
  if (!session) redirect("/login");
  const { data } = await serviceClient()
    .from("curator_reviewers")
    .select("id, display_name, active")
    .eq("id", session.reviewerId)
    .maybeSingle();
  if (!data?.active || data.display_name !== session.displayName) {
    await clearCuratorSession();
    redirect("/login");
  }
  return session;
}
