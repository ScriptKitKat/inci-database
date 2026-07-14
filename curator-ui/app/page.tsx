import Link from "next/link";
import { logoutAction } from "@/app/actions";
import { requireCuratorSession } from "@/lib/auth";
import { getQueue } from "@/lib/data";
import { triggerLabel } from "@/lib/review";

function age(iso: string) {
  const hours = Math.floor((Date.now() - new Date(iso).getTime()) / 3_600_000);
  return hours < 1 ? "< 1 hour" : hours < 24 ? `${hours} hours` : `${Math.floor(hours / 24)} days`;
}

export default async function QueuePage({ searchParams }: { searchParams: Promise<{ trigger?: string; age?: string }> }) {
  const [session, queue, filters] = await Promise.all([
    requireCuratorSession(),
    getQueue(),
    searchParams,
  ]);
  const triggers = [...new Set(queue.map((row) => row.trigger).filter(Boolean))] as string[];
  const filtered = queue.filter((row) => {
    if (filters.trigger && row.trigger !== filters.trigger) return false;
    if (filters.age === "24h" && Date.now() - new Date(row.created_at).getTime() < 86_400_000) return false;
    return true;
  });
  return (
    <main className="page-shell">
      <header className="topbar">
        <div><p className="eyebrow">INCI database</p><h1>Review queue</h1></div>
        <div className="reviewer"><span>{session.displayName}</span><form action={logoutAction}><button className="text-button">Log out</button></form></div>
      </header>
      <form className="filters">
        <label>Trigger<select name="trigger" defaultValue={filters.trigger || ""}><option value="">All triggers</option>{triggers.map((trigger) => <option key={trigger} value={trigger}>{triggerLabel(trigger)}</option>)}</select></label>
        <label>Age<select name="age" defaultValue={filters.age || "all"}><option value="all">Any age</option><option value="24h">Older than 24 hours</option></select></label>
        <button>Apply filters</button><Link className="button-link" href="/">Refresh</Link>
      </form>
      {filtered.length ? (
        <div className="table-wrap"><table><thead><tr><th>Brand</th><th>Product</th><th>Age</th><th>Trigger</th><th>Unresolved</th></tr></thead><tbody>
          {filtered.map((row) => <tr key={row.id}><td><Link href={`/submissions/${row.id}`}>{row.brand_name}</Link></td><td>{row.product_name}</td><td>{age(row.created_at)}</td><td>{triggerLabel(row.trigger)}</td><td><span className="count">{row.unresolved}</span></td></tr>)}
        </tbody></table></div>
      ) : <section className="empty"><h2>{queue.length ? "No submissions match these filters." : "No submissions need review right now."}</h2>{queue.length > 0 && <Link href="/">Clear filters</Link>}</section>}
    </main>
  );
}
