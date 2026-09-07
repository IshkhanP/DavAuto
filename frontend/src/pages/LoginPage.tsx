import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "@/components/Logo";
import toast from "react-hot-toast";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const redirect = params.get("redirect") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      navigate(redirect);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Invalid email or password");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: "calc(100vh - 64px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "2rem 1rem",
    }}>
      <Helmet><title>Login — BlackSharkCars</title></Helmet>

      <div className="card" style={{ width: "100%", maxWidth: 420, padding: 28 }}>
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <Logo size={36} />
          <h2 style={{ marginTop: 12 }}>Welcome back</h2>
          <p className="text-sm muted">Login to continue.</p>
        </div>

        <form onSubmit={submit}>
          <div className="field">
            <label>Email</label>
            <input type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="text-sm" style={{ color: "var(--color-red)", marginBottom: 8 }}>{error}</p>}
          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-sm" style={{ textAlign: "center", marginTop: 16 }}>
          New here? <Link to="/register" style={{ color: "var(--color-blue)", fontWeight: 600 }}>Create an account</Link>
        </p>
        <p className="text-sm" style={{ textAlign: "center", marginTop: 4 }}>
          <Link to="/forgot-password" style={{ color: "var(--color-text-muted)" }}>Forgot password?</Link>
        </p>
      </div>
    </div>
  );
};