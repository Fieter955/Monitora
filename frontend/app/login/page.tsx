"use client";

import {FormEvent, useEffect, useState} from "react";
import {useRouter} from "next/navigation";
import {api, ApiError} from "@/lib/api";
import type {User} from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api<User>("/auth/me").then(() => router.replace("/")).catch(() => undefined);
  }, [router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api<User>("/auth/login", {
        method: "POST",
        body: JSON.stringify({username, password}),
      });
      router.replace("/");
      router.refresh();
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Tidak dapat terhubung ke server");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-intro" aria-labelledby="product-title">
        <div className="login-brand">
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <strong>Pantau Infrastruktur</strong>
        </div>
        <div className="login-copy">
          <p>Layanan internal TI</p>
          <h1 id="product-title">Kondisi layanan, terlihat dalam satu tempat.</h1>
          <p>Pantau server, jaringan, dan layanan digital untuk membantu penanganan gangguan secara lebih cepat.</p>
        </div>
        <p className="login-footnote">Akses terbatas untuk petugas yang berwenang.</p>
      </section>

      <section className="login-form-wrap" aria-labelledby="login-title">
        <div className="login-card">
          <h2 id="login-title">Masuk ke portal</h2>
          <p>Gunakan akun internal yang diberikan administrator.</p>
          <form onSubmit={submit}>
            {error && <div className="form-error" role="alert">{error}</div>}
            <div className="field">
              <label htmlFor="username">Nama pengguna</label>
              <input id="username" name="username" autoComplete="username" required minLength={3} value={username} onChange={(event) => setUsername(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="password">Kata sandi</label>
              <input id="password" name="password" type="password" autoComplete="current-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <button className="button button-primary" type="submit" disabled={submitting}>
              {submitting ? "Memeriksa akun…" : "Masuk"}
            </button>
          </form>
          <p className="login-help">Hubungi administrator TI jika akun terkunci atau kata sandi perlu diatur ulang.</p>
        </div>
      </section>
    </main>
  );
}

