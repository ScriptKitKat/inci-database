import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="login-shell">
      <section className="login-panel">
        <p className="eyebrow">INCI database</p>
        <h1>Curator review</h1>
        <p className="lede">Sign in with your reviewer name and the shared curator password.</p>
        <LoginForm />
      </section>
    </main>
  );
}
