# Curator UI

Private review UI for `pending_human` product submissions.

Submission review reads and writes use `SUPABASE_URL` and
`SUPABASE_SERVICE_ROLE_KEY`. Ingredient autocomplete reads the remote catalog
configured by `REMOTE_SUPABASE_URL` and `REMOTE_SUPABASE_PUBLISHABLE_KEY`.

## Local setup

1. Start Supabase and apply migrations from the repository root.
2. Copy `.env.example` to `.env.local` and fill in the local service-role key.
3. Generate the supplied shared password's hash with `node scripts/hash-password.mjs <shared-password>` and set `CURATOR_PASSWORD_HASH` to its output.
4. Set a random `CURATOR_SESSION_SECRET` of at least 32 characters.
5. Run `pnpm install && pnpm dev`.

The migration allowlists reviewer **Priscilla**. Only the supplied password's
scrypt hash belongs in configuration. Rotate it by generating a new hash. Add,
rename, or disable reviewers directly in the
private `curator_reviewers` table.

The browser never receives Supabase credentials. All reads and mutations run
on the server after checking the signed session and the reviewer's active flag.
