"use client";

import { useState } from "react";
import TeacherPanel from "./TeacherPanel";

const TEMP_TEACHER_PASSWORD = "FW-Teacher-2026";

export default function TeacherLogin() {
  const [password, setPassword] = useState("");
  const [authenticated, setAuthenticated] =
    useState(false);
  const [error, setError] = useState("");

  function handleLogin(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");

    if (password === TEMP_TEACHER_PASSWORD) {
      setAuthenticated(true);
      return;
    }

    setError("رمز عبور اشتباه است.");
    setPassword("");
  }

  function handleLogout() {
    setAuthenticated(false);
    setPassword("");
    setError("");
  }

  if (authenticated) {
    return (
      <TeacherPanel
        teacherToken="temporary-frontend-token"
        onLogout={handleLogout}
      />
    );
  }

  return (
    <main
      dir="rtl"
      className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 px-4"
    >
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="mb-8 text-center">

          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-3xl border border-white/10 bg-white/10 text-5xl shadow-2xl backdrop-blur-xl">
            🪽
          </div>

          <h1 className="text-3xl font-black text-white">
            Flying Wings
          </h1>

          <p className="mt-2 text-slate-400">
            Teacher Access
          </p>

        </div>

        {/* Login Card */}
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.07] shadow-2xl backdrop-blur-xl">

          <div className="p-6 sm:p-8">

            <div className="mb-7 text-center">

              <div className="mb-4 text-4xl">
                🔐
              </div>

              <h2 className="text-2xl font-black text-white">
                ورود استاد
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                برای دسترسی به بخش مدیریت پروژه رمز عبور را وارد کنید.
              </p>

            </div>

            <form
              onSubmit={handleLogin}
              className="space-y-5"
            >

              <div>

                <label className="mb-2 block text-sm font-bold text-slate-200">
                  رمز عبور
                </label>

                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="رمز عبور را وارد کنید"
                  autoFocus
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/50 px-5 py-4 text-left text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400 focus:ring-4 focus:ring-cyan-400/10"
                />

              </div>

              {error && (
                <div className="rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm font-bold text-red-300">
                  ⚠️ {error}
                </div>
              )}

              <button
                type="submit"
                className="w-full rounded-2xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 px-6 py-4 font-black text-white shadow-xl transition duration-300 hover:-translate-y-0.5 hover:shadow-2xl"
              >
                🔓 ورود به پنل استاد
              </button>

            </form>

          </div>

          <div className="border-t border-white/10 bg-white/[0.03] px-6 py-4 text-center">
            <p className="text-xs text-slate-500">
              Teacher Access • Flying Wings
            </p>
          </div>

        </section>

      </div>
    </main>
  );
}