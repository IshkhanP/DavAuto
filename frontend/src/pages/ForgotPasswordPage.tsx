import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Logo } from "@/components/Logo";
import { authService } from "@/services";
import toast from "react-hot-toast";

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await authService.forgotPassword(email);
      setDone(true);
    } catch {
      toast.error("Could not send reset email");
    }
  };

  return (
    <div style={{
      minHeight: "calc(100vh - 64px)",
      display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem 1rem",
    }}>
      <Helmet><title>Reset Password — BlackSharkCars</title></Helmet>
      <div className="card" style={{ width: "100%", maxWidth: 420, padding: 28 }}>
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <Logo size={36} />
          <h2 style={{ marginTop: 12 }}>Reset Password</h2>
          {done ? (
            <p className="text-sm muted">If that email exists, a reset link has been sent.</p>
          ) : (
            <p className="text-sm muted">Enter your email to receive a reset link.</p>
          )}
        </div>
        {!done && (
          <form onSubmit={submit}>
            <div className="field">
              <label>Email</label>
              <input type="email" className="input" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-block" type="submit">Send reset link</button>
          </form>
        )}
        <p className="text-sm" style={{ textAlign: "center", marginTop: 16 }}>
          <Link to="/login" style={{ color: "var(--color-blue)", fontWeight: 600 }}>Back to login</Link>
        </p>
      </div>
    </div>
  );
};