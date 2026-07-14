import Link from "next/link";
import { getSubmissionDetail } from "@/lib/data";
import { triggerLabel } from "@/lib/review";
import { ReviewWorkbench } from "@/components/ReviewWorkbench";

export default async function SubmissionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const detail = await getSubmissionDetail(id);
  const verification = detail.submission.verification;
  return (
    <main className="page-shell detail-page">
      <Link className="back" href="/">← Review queue</Link>
      <ReviewWorkbench initial={detail}>
        <div className="submission-copy">
          <p className="eyebrow">{triggerLabel(detail.trigger)}</p>
          <h1>{detail.submission.product_name}</h1>
          <p className="brand-line">{detail.submission.brand_name}</p>
          <dl className="meta-grid">
            <div><dt>Status</dt><dd><span className="status">Pending human</span></dd></div>
            <div><dt>Submitted</dt><dd>{new Date(detail.submission.created_at).toLocaleString()}</dd></div>
            <div><dt>Submitter</dt><dd>{detail.submission.submitted_by || "Anonymous"}</dd></div>
            <div><dt>Product evidence</dt><dd>{verification.found ? "Exact page found" : "Not verified"}</dd></div>
            <div><dt>Submitted coverage</dt><dd>{Math.round(Number(verification.submitted_coverage || 0) * 100)}%</dd></div>
            <div><dt>Online coverage</dt><dd>{Math.round(Number(verification.online_coverage || 0) * 100)}%</dd></div>
          </dl>
          {Boolean(verification.source_url) && <a href={String(verification.source_url)} target="_blank" rel="noreferrer">Open verification source ↗</a>}
          {Boolean(verification.reason) && <p className="reason">{String(verification.reason)}</p>}
        </div>
      </ReviewWorkbench>
    </main>
  );
}
