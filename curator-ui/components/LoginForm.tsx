"use client";

import { useActionState } from "react";
import { loginAction } from "@/app/actions";

export function LoginForm() {
  const [state, action, pending] = useActionState(loginAction, { ok: false });
  return (
    <form action={action} className="form-stack">
      <label>
        Reviewer name
        <input name="name" autoComplete="username" required autoFocus />
      </label>
      <label>
        Password
        <input name="password" type="password" autoComplete="current-password" required />
      </label>
      {state.error && <p className="error" role="alert">{state.error}</p>}
      <button className="primary" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</button>
    </form>
  );
}
