export function sourceHostname(value: unknown): string | null {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.username || url.password) return null;
    return url.hostname.toLowerCase().replace(/^www\./, "") || null;
  } catch {
    return null;
  }
}

export function domainMatches(host: string, domain: string) {
  const normalized = domain.trim().toLowerCase().replace(/^www\./, "").replace(/\.$/, "");
  return Boolean(normalized) && (host === normalized || host.endsWith(`.${normalized}`));
}
