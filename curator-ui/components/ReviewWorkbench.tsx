"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  approveSubmissionAction,
  rejectSubmissionAction,
  resolveTokenAction,
} from "@/app/actions";
import { canApprove, triggerLabel } from "@/lib/review";
import type { DetailData, SubmissionToken } from "@/lib/types";

type Ingredient = { id: string; inci_name: string; confidence?: number };

export function ReviewWorkbench({ initial, children }: { initial: DetailData; children: React.ReactNode }) {
  const router = useRouter();
  const [tokens, setTokens] = useState(initial.tokens);
  const [editing, setEditing] = useState<{ token: SubmissionToken; mode: string } | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approveConfirmed, setApproveConfirmed] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const verification = initial.submission.verification;
  const verdict = String(verification.verdict || "");
  const needsApproveWarning = ["divergent", "not_found", "untrusted_source", "no_list", "similar_product", "same_name_different_formula", "name_resolved"].includes(verdict);

  useEffect(() => {
    const poll = setInterval(async () => {
      if (document.visibilityState !== "visible") return;
      const response = await fetch(`/api/submissions/${initial.submission.id}`, { cache: "no-store" });
      if (response.ok) setTokens(((await response.json()) as DetailData).tokens);
    }, 10_000);
    return () => clearInterval(poll);
  }, [initial.submission.id]);

  async function resolve(token: SubmissionToken, resolution: "matched" | "new_ingredient" | "junk", extra: { ingredientId?: string; ingredientName?: string; canonicalName?: string } = {}) {
    const previous = tokens;
    setSaving(token.id);
    setError(null);
    setTokens((current) => current.map((row) => row.id === token.id ? { ...row, resolution, matched_ingredient_id: extra.ingredientId || null, matched_name: extra.ingredientName || null, canonical_name: extra.canonicalName || null } : row));
    const result = await resolveTokenAction({ tokenId: token.id, submissionId: initial.submission.id, resolution, ...extra });
    setSaving(null);
    if (!result.ok) {
      setTokens(previous);
      setError(result.error || "Could not save the token resolution.");
      return;
    }
    if (resolution === "matched") {
      setTokens((current) => current.map((row) => row.id === token.id ? {
        ...row,
        matched_ingredient_id: result.ingredientId || row.matched_ingredient_id,
        matched_name: result.ingredientName || row.matched_name,
      } : row));
    }
    setEditing(null);
  }

  async function approve() {
    if (needsApproveWarning && !approveConfirmed) { setApproveConfirmed(true); return; }
    setSaving("submission"); setError(null);
    const result = await approveSubmissionAction(initial.submission.id);
    setSaving(null);
    if (!result.ok) { setError(result.error || "Approval failed."); return; }
    if (result.result === "duplicate") {
      setError(`This submission duplicates an existing product${result.productId ? ` (${result.productId})` : ""}.`);
      return;
    }
    router.push("/"); router.refresh();
  }

  return (
    <>
      {error && <div className="error-banner" role="alert">{error}</div>}
      <header className="submission-header">
        {children}
        <div className="header-actions">
          <button className="primary" disabled={!canApprove(tokens) || saving === "submission"} title={!canApprove(tokens) ? `Resolve ${tokens.filter((t) => ["unresolved", "pending_human"].includes(t.resolution)).length} tokens first` : undefined} onClick={approve}>
            {saving === "submission" ? "Approving…" : approveConfirmed ? "Confirm approval" : "Approve"}
          </button>
          <button className="danger" onClick={() => setRejectOpen(true)}>Reject</button>
          {approveConfirmed && <p className="confirm-copy">{verdict === "similar_product" ? "This formula overlaps an existing product by at least 95%, but the product names differ. Approve it as a separate product?" : verdict === "name_resolved" ? `Approve the trusted product name “${String(verification.resolved_product_name)}” instead of the submitted name “${String(verification.submitted_product_name)}”?` : "The product wasn't verified against the online source. Approve anyway?"}</p>}
        </div>
      </header>

      {initial.similarProduct && (
        <section className="warning"><p className="eyebrow">Catalog similarity</p><h2>{initial.similarProduct.brand} — {initial.similarProduct.name}</h2><p>{verdict === "similar_product" ? "The formulas overlap by at least 95%, but the product names differ." : "This brand and product name already exist, but the submitted formula differs."}</p><code>{initial.similarProduct.id}</code></section>
      )}

      {verdict === "name_resolved" && (
        <section className="warning"><p className="eyebrow">Product name match</p><h2>{String(verification.resolved_product_name)}</h2><p>Submitted as “{String(verification.submitted_product_name)}”. The trusted ingredient list matches, but a curator must confirm the full published product name.</p></section>
      )}

      {verdict === "divergent" && <DivergentDiff submitted={initial.submission.raw_ingredient_text.split(/[,;\n]/).map((s) => s.trim()).filter(Boolean)} online={(verification.online_tokens as string[]) || []} />}

      <section className="tokens-section"><div className="section-heading"><div><p className="eyebrow">Ingredient decisions</p><h2>Submitted label</h2></div><p>{tokens.length} tokens</p></div>
        <div className="table-wrap"><table className="token-table"><thead><tr><th>#</th><th>Raw token</th><th>Normalized</th><th>Evidence</th><th>Candidate / escalation</th><th>Resolution</th><th>Action</th></tr></thead><tbody>
          {tokens.map((token) => <TokenRow key={token.id} token={token} saving={saving === token.id} editing={editing?.token.id === token.id ? editing.mode : null} onEdit={(mode) => setEditing({ token, mode })} onCancel={() => setEditing(null)} onResolve={resolve} />)}
        </tbody></table></div>
      </section>
      {editing?.mode === "matched" && <IngredientDialog token={editing.token} onCancel={() => setEditing(null)} onConfirm={(ingredient) => resolve(editing.token, "matched", { ingredientId: ingredient.id, ingredientName: ingredient.inci_name })} />}
      {rejectOpen && <RejectDialog onCancel={() => setRejectOpen(false)} onConfirm={async (reason) => { const result = await rejectSubmissionAction(initial.submission.id, reason); if (!result.ok) { setError(result.error || "Rejection failed."); return; } router.push("/"); router.refresh(); }} />}
    </>
  );
}

function TokenRow({ token, saving, editing, onEdit, onCancel, onResolve }: { token: SubmissionToken; saving: boolean; editing: string | null; onEdit: (mode: string) => void; onCancel: () => void; onResolve: (token: SubmissionToken, resolution: "new_ingredient" | "junk", extra?: { canonicalName?: string }) => void }) {
  const preferred = token.evidence.find((ev) => ["cosing", "incidecoder"].includes(ev.source) && ev.canonical)?.canonical || token.raw_token;
  const [name, setName] = useState(preferred);
  const [junkConfirmed, setJunkConfirmed] = useState(false);
  return <>
    <tr tabIndex={0} className={["unresolved", "pending_human"].includes(token.resolution) ? "needs-review" : token.resolution === "junk" ? "is-junk" : ""}>
      <td>{token.position}</td><td className="raw">{token.raw_token}</td><td><code>{token.normalized_token}</code></td>
      <td><div className="badges">{token.evidence.filter((ev) => ev.found).map((ev) => <span className="badge" key={`${ev.source}-${ev.canonical}`}>{ev.source}: {ev.canonical} {ev.confidence ? `${Math.round(ev.confidence * 100)}%` : ""}</span>)}</div></td>
      <td>{token.matched_name ? <>{token.matched_name} {token.match_confidence && <small>{Math.round(token.match_confidence * 100)}%</small>}</> : token.escalation ? triggerLabel(token.escalation) : "—"}</td>
      <td><span className={`resolution resolution-${token.resolution}`}>{saving ? "Saving…" : token.resolution.replaceAll("_", " ")}</span></td>
      <td><select aria-label={`Resolve ${token.raw_token}`} value="" disabled={saving} onChange={(event) => event.target.value && onEdit(event.target.value)}><option value="">Choose…</option><option value="matched">Matched</option><option value="new_ingredient">New ingredient</option><option value="junk">Junk</option></select></td>
    </tr>
    {editing === "new_ingredient" && <tr className="inline-action"><td colSpan={7}><label>Canonical name<input value={name} onChange={(e) => setName(e.target.value)} autoFocus /></label><p>This name will be used as-is. No spelling correction happens after this point.</p><button className="primary small" disabled={!name.trim()} onClick={() => onResolve(token, "new_ingredient", { canonicalName: name.trim() })}>Confirm new ingredient</button><button className="text-button" onClick={onCancel}>Cancel</button></td></tr>}
    {editing === "junk" && <tr className="inline-action"><td colSpan={7}><p>{token.position <= 3 && !junkConfirmed ? `This token is at position ${token.position}. Are you sure it isn't a major ingredient?` : "Drop this token from the product?"}</p><button className="danger small" onClick={() => token.position <= 3 && !junkConfirmed ? setJunkConfirmed(true) : onResolve(token, "junk")}>{token.position <= 3 && !junkConfirmed ? "Continue" : "Confirm drop"}</button><button className="text-button" onClick={onCancel}>Cancel</button></td></tr>}
  </>;
}

function IngredientDialog({ token, onCancel, onConfirm }: { token: SubmissionToken; onCancel: () => void; onConfirm: (ingredient: Ingredient) => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState(token.matched_name || token.raw_token);
  const [results, setResults] = useState<Ingredient[]>([]);
  const [selected, setSelected] = useState<Ingredient | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => { dialog.current?.showModal(); }, []);
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      setSelected(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/ingredients?q=${encodeURIComponent(trimmed)}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) return setResults([]);
        const matches = (await response.json()) as Ingredient[];
        setResults(matches);
        setSelected(matches.find((ingredient) => ingredient.inci_name.toLocaleLowerCase() === trimmed.toLocaleLowerCase()) || null);
      } catch {
        if (!controller.signal.aborted) setResults([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query]);
  const exactExistingMatch = selected?.inci_name.toLocaleLowerCase() === query.trim().toLocaleLowerCase();
  return <dialog ref={dialog} onCancel={onCancel} className="modal"><div className="modal-content"><p className="eyebrow">Match existing ingredient</p><h2>{token.raw_token}</h2><label>Search existing ingredients<input role="combobox" aria-expanded={results.length > 0} aria-controls="ingredient-matches" value={query} onChange={(e) => { setQuery(e.target.value); setSelected(null); }} autoFocus /></label><div id="ingredient-matches" role="listbox" className="search-results">{results.map((ingredient) => <button type="button" role="option" aria-selected={selected?.id === ingredient.id} key={ingredient.id} className={selected?.id === ingredient.id ? "selected" : ""} onClick={() => { setQuery(ingredient.inci_name); setSelected(ingredient); }}><span>{ingredient.inci_name}</span>{ingredient.confidence !== undefined && <small>{Math.round(ingredient.confidence * 100)}% match</small>}</button>)}</div>{loading && <p>Searching current ingredient database…</p>}{!loading && query.trim().length >= 2 && results.length === 0 && <p>No existing ingredients found.</p>}{selected && exactExistingMatch && <p>Link “{token.raw_token}” to “{selected.inci_name}”?</p>}<div className="modal-actions">{selected && exactExistingMatch && <button className="primary" onClick={() => onConfirm(selected)}>Confirm match</button>}<button onClick={onCancel}>Cancel</button></div></div></dialog>;
}

function RejectDialog({ onCancel, onConfirm }: { onCancel: () => void; onConfirm: (reason: string) => void }) {
  const dialog = useRef<HTMLDialogElement>(null); const [reason, setReason] = useState("");
  const chips = ["Not a real product", "Ingredient list is nonsense", "Duplicate of a rejected submission", "Test/spam submission"];
  useEffect(() => { dialog.current?.showModal(); }, []);
  return <dialog ref={dialog} onCancel={onCancel} className="modal"><div className="modal-content"><h2>Reject this submission?</h2><div className="chips">{chips.map((chip) => <button key={chip} onClick={() => setReason(chip)}>{chip}</button>)}</div><label>Reason<textarea value={reason} onChange={(e) => setReason(e.target.value)} autoFocus /></label><div className="modal-actions"><button className="danger" disabled={reason.trim().length < 10} onClick={() => onConfirm(reason)}>Confirm rejection</button><button onClick={onCancel}>Cancel</button></div></div></dialog>;
}

function DivergentDiff({ submitted, online }: { submitted: string[]; online: string[] }) {
  const normalizedOnline = useMemo(() => new Set(online.map((v) => v.toLowerCase().replace(/[^a-z0-9]/g, ""))), [online]);
  const normalizedSubmitted = useMemo(() => new Set(submitted.map((v) => v.toLowerCase().replace(/[^a-z0-9]/g, ""))), [submitted]);
  return <section className="diff-section"><div className="section-heading"><div><p className="eyebrow">Source comparison</p><h2>Divergent lists</h2></div></div><div className="diff-grid"><div><h3>Submitted</h3>{submitted.map((value, i) => <p key={`${value}-${i}`} className={normalizedOnline.has(value.toLowerCase().replace(/[^a-z0-9]/g, "")) ? "agree" : "missing"}>{normalizedOnline.has(value.toLowerCase().replace(/[^a-z0-9]/g, "")) ? "✓" : "−"} {value}</p>)}</div><div><h3>Online</h3>{online.map((value, i) => <p key={`${value}-${i}`} className={normalizedSubmitted.has(value.toLowerCase().replace(/[^a-z0-9]/g, "")) ? "agree" : "extra"}>{normalizedSubmitted.has(value.toLowerCase().replace(/[^a-z0-9]/g, "")) ? "✓" : "+"} {value}</p>)}</div></div></section>;
}
