import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "@/components/Logo";
import toast from "react-hot-toast";

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: "", password: "", full_name: "", phone: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await register(form);
      toast.success("Account created");
      navigate("/dashboard");
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.response?.data?.message || "Registration failed";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
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
      <Helmet><title>Register — BlackSharkCars</title></Helmet>

      <div className="card" style={{ width: "100%", maxWidth: 460, padding: 28 }}>
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <Logo size={36} />
          <h2 style={{ marginTop: 12 }}>Create your account</h2>
          <p className="text-sm muted">Buy and sell cars on BlackSharkCars.</p>
        </div>

        <form onSubmit={submit}>
          <div className="field">
            <label>Full name</label>
            <input className="input" required value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" className="input" required value={form.email} onChange={(e) => set("email", e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" className="input" required minLength={8} value={form.password} onChange={(e) => set("password", e.target.value)} />
            <span className="hint">Must be at least 8 characters with letters and numbers.</span>
          </div>
          <div className="field">
            <label>Phone (optional)</label>
            <input className="input" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          </div>

          {error && <p className="text-sm" style={{ color: "var(--color-red)", marginBottom: 8 }}>{error}</p>}
          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? "Creating…" : "Create account"}
          </button>
        </form>

        <p className="text-sm" style={{ textAlign: "center", marginTop: 16 }}>
          Already have an account? <Link to="/login" style={{ color: "var(--color-blue)", fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
};