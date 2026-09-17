import { hostedDemo } from "../demo";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { login, SESSION_EXPIRED_MESSAGE } from "../api";

export default function Login() {
  const [username, setUsername] = useState("auditor");
  const [password, setPassword] = useState("auditor123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      const from = location.state?.from;
      const destination = from?.pathname?.startsWith("/") && !from.pathname.startsWith("//") && from.pathname !== "/login"
        ? `${from.pathname}${from.search || ""}${from.hash || ""}` : "/dashboard";
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50">
      <div className="panel shadow-sm p-8 w-full max-w-sm">
        <Link to="/" className="text-xs text-accent">← Product overview</Link>
        <h1 className="text-lg font-semibold text-navy-900 mt-4">Sign in to the demo</h1>
        <p className="text-sm text-navy-700/70 mt-1 mb-4">Explore sample invoices, or upload your own receipt to read and check its details. The shared sample workspace uses made-up companies and records.</p>
        {hostedDemo && <p className="text-sm bg-amber-50 rounded p-3 mb-4">This public demo uses shared sample records. Changes are temporary and may reset. Use “Read a receipt” for your own uploads; those are kept out of the sample records.</p>}
        {location.state?.sessionExpired && <p role="status" className="text-sm bg-amber-50 border border-review/30 rounded p-3 mb-4">{SESSION_EXPIRED_MESSAGE}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-xs font-medium text-navy-700 mb-1">App username</label>
            <input
              id="username"
              autoComplete="username"
              required
              className="w-full border border-navy-900/20 rounded px-3 py-2 text-sm"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-xs font-medium text-navy-700 mb-1">App password</label>
            <input
              id="password"
              autoComplete="current-password"
              required
              type="password"
              className="w-full border border-navy-900/20 rounded px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p role="alert" className="text-sm text-fail">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-navy-900 text-white text-sm font-medium py-2 rounded hover:bg-navy-700 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <div className="mt-6 text-xs text-navy-700/60 space-y-1">
          <p className="font-medium text-navy-900">Start with auditor / auditor123 (already filled in).</p>
          <p>Auditor: explore records and try document changes.</p>
          <p>Reviewer: reviewer / reviewer123 — approve, reject, or ask for more documents.</p>
          <p>Admin: admin / admin123 — access both sets of actions.</p>
          <p className="pt-3">The POSTGRES settings connect the server to its database. SECRET_KEY protects sign-ins. Neither is an app login.</p>
          <Link className="inline-block pt-3 text-accent" to="/about-demo">New here? Read the simple guide →</Link>
        </div>
      </div>
    </div>
  );
}
