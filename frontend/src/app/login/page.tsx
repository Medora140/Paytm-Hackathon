"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, Mail, ArrowRight, AlertCircle, CheckCircle2 } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setLoading(true);

    try {
      // 1. Sign in with Supabase client
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email: trimmedEmail,
        password,
      });

      if (signInError) {
        // Fallback: Check with backend login route
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${apiBaseUrl}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: trimmedEmail, password }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || signInError.message || "Invalid email or password.");
        }

        const backendAuth = await res.json();
        if (backendAuth.access_token) {
          await supabase.auth.setSession({
            access_token: backendAuth.access_token,
            refresh_token: backendAuth.refresh_token || "",
          });
        }
      }

      router.push("/documents");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4 sm:px-6 animate-fade-in">
      <div className="bg-canvas rounded-3xl p-8 border border-ink/10 shadow-xs space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-black text-ink tracking-tight">Log In</h1>
          <p className="text-body text-sm">
            Sign in to access your decoded documents, red flags, and chat history.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 rounded-2xl bg-negative-soft border border-negative/20 text-negative-deep text-sm font-semibold">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-ink uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-mute absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full pl-10 pr-4 py-3 rounded-2xl border border-ink/15 bg-canvas text-ink text-sm focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-ink uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-mute absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                className="w-full pl-10 pr-4 py-3 rounded-2xl border border-ink/15 bg-canvas text-ink text-sm focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-2xl bg-primary hover:bg-primary-active text-ink font-extrabold text-sm transition-all shadow-xs active:scale-98 disabled:opacity-50"
          >
            {loading ? <span>Authenticating...</span> : (
              <>
                <span>Log In</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-2 text-xs text-body">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-primary-deep font-bold hover:underline">
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
}
