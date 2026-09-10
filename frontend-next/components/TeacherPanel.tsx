"use client";

import { useState } from "react";
import { createTeacherProject } from "../lib/api";

interface TeacherResult {
  success: boolean;
  message?: string;
  project_id?: string;
  filename?: string;
  google_drive?: {
    uploaded: boolean;
    file_id?: string;
    web_view_link?: string;
  };
}

export default function TeacherPanel() {
  const [projectId, setProjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<TeacherResult | null>(null);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setResult(null);

    if (!projectId.trim()) {
      setError("لطفاً شماره پروژه را وارد کنید.");
      return;
    }

    if (!file) {
      setError("لطفاً فایل اصلی Master Excel را انتخاب کنید.");
      return;
    }

    const fileName = file.name.toLowerCase();

    if (
      !fileName.endsWith(".xlsx") &&
      !fileName.endsWith(".xlsm")
    ) {
      setError(
        "فقط فایل‌های Excel با فرمت .xlsx یا .xlsm قابل قبول هستند."
      );
      return;
    }

    try {
      setLoading(true);

      const data = await createTeacherProject(
        projectId.trim(),
        file
      );

      setResult(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("در ایجاد پروژه مشکلی به وجود آمد.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      dir="rtl"
      className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 px-4 py-8 text-slate-100 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <header className="mb-8 text-center">
          <div className="mb-3 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/10 px-5 py-2 shadow-lg backdrop-blur-md">
            <span className="text-2xl">🪽</span>

            <span className="bg-gradient-to-r from-cyan-300 via-blue-300 to-indigo-300 bg-clip-text text-xl font-black tracking-wide text-transparent sm:text-2xl">
              Flying Wings
            </span>
          </div>

          <h1 className="mt-4 text-3xl font-black tracking-tight text-white sm:text-4xl">
            پنل استاد
          </h1>

          <p className="mt-3 text-sm text-slate-300 sm:text-base">
            مدیریت و ایجاد پروژه‌های نمره‌دهی
          </p>

          <div className="mx-auto mt-5 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-5 py-2 text-sm font-bold text-cyan-300">
            Master Project
          </div>
        </header>

        {/* Main Card */}
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.07] shadow-2xl backdrop-blur-xl">

          {/* Information */}
          <div className="border-b border-white/10 bg-white/[0.04] p-6 sm:p-8">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start">

              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-500/20 text-3xl">
                👨‍🏫
              </div>

              <div>
                <h2 className="text-xl font-extrabold text-white">
                  ایجاد پروژه جدید
                </h2>

                <p className="mt-2 leading-8 text-slate-300">
                  فایل اصلی Master Excel پروژه را ارسال کنید.
                  سیستم ساختار فایل را تحلیل کرده و قوانین
                  پروژه را برای نمره‌دهی دانش‌آموزان ذخیره می‌کند.
                </p>

                <div className="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm leading-7 text-cyan-200">
                  💡 فایل Master باید همان فایل اصلی و کامل
                  پروژه باشد.
                </div>
              </div>

            </div>
          </div>

          {/* Form */}
          <div className="p-6 sm:p-8 lg:p-10">

            <div className="mb-7">
              <h2 className="text-2xl font-black text-white">
                اطلاعات پروژه
              </h2>

              <div className="mt-2 h-1 w-20 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500" />
            </div>

            <form
              onSubmit={handleSubmit}
              className="space-y-6"
            >

              {/* Project ID */}
              <div>
                <label className="mb-2 block text-sm font-bold text-slate-200">
                  شماره پروژه
                </label>

                <input
                  type="text"
                  value={projectId}
                  onChange={(event) =>
                    setProjectId(event.target.value)
                  }
                  placeholder="مثلاً: excel-project-01"
                  disabled={loading}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-5 py-4 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-4 focus:ring-cyan-400/10 disabled:cursor-not-allowed disabled:opacity-50"
                />

                <p className="mt-2 text-xs text-slate-500">
                  این شناسه برای شناسایی قوانین Master Project
                  استفاده می‌شود.
                </p>
              </div>

              {/* Master File */}
              <div>
                <label className="mb-2 block text-sm font-bold text-slate-200">
                  فایل Master Excel
                </label>

                <label className="group flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/15 bg-slate-950/30 px-6 py-12 text-center transition hover:border-cyan-400/60 hover:bg-cyan-400/5">

                  <div className="mb-4 text-5xl transition-transform duration-300 group-hover:scale-110">
                    📊
                  </div>

                  <span className="font-bold text-white">
                    {file
                      ? file.name
                      : "فایل Master Excel را انتخاب کنید"}
                  </span>

                  <span className="mt-2 text-xs text-slate-500">
                    فرمت‌های مجاز: .xlsx و .xlsm
                  </span>

                  <input
                    type="file"
                    accept=".xlsx,.xlsm"
                    className="hidden"
                    disabled={loading}
                    onChange={(event) =>
                      setFile(
                        event.target.files?.[0] || null
                      )
                    }
                  />
                </label>
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-2xl border border-red-400/20 bg-red-500/10 px-5 py-4 text-sm font-bold leading-7 text-red-300">
                  ⚠️ {error}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full overflow-hidden rounded-2xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 px-6 py-4 text-base font-black text-white shadow-xl shadow-blue-900/30 transition duration-300 hover:-translate-y-0.5 hover:shadow-2xl hover:shadow-blue-900/50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <span className="relative z-10 flex items-center justify-center gap-3">

                  {loading ? (
                    <>
                      <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      در حال ایجاد پروژه...
                    </>
                  ) : (
                    <>
                      🚀
                      ایجاد Master Project
                    </>
                  )}

                </span>
              </button>

            </form>
          </div>
        </section>

        {/* Success Result */}
        {result && (
          <section className="mt-8 overflow-hidden rounded-3xl border border-emerald-400/20 bg-emerald-400/[0.06] shadow-2xl backdrop-blur-xl">

            <div className="p-6 text-center sm:p-8">

              <div className="mb-4 text-5xl">
                ✅
              </div>

              <h2 className="text-2xl font-black text-white">
                پروژه با موفقیت ایجاد شد
              </h2>

              <p className="mt-3 text-slate-300">
                قوانین Master Project با موفقیت استخراج و
                ذخیره شدند.
              </p>

            </div>

            <div className="grid gap-4 border-t border-white/10 p-6 sm:grid-cols-2 sm:p-8">

              <div className="rounded-2xl bg-slate-950/30 p-5">
                <p className="text-xs font-bold text-slate-500">
                  Project ID
                </p>

                <p className="mt-2 break-all font-bold text-cyan-300">
                  {result.project_id}
                </p>
              </div>

              <div className="rounded-2xl bg-slate-950/30 p-5">
                <p className="text-xs font-bold text-slate-500">
                  فایل
                </p>

                <p className="mt-2 break-all font-bold text-white">
                  {result.filename}
                </p>
              </div>

            </div>

            {result.google_drive?.uploaded &&
              result.google_drive.web_view_link && (
                <div className="px-6 pb-6 sm:px-8 sm:pb-8">

                  <a
                    href={result.google_drive.web_view_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-sm font-bold text-slate-200 transition hover:bg-white/10"
                  >
                    📁 مشاهده Master File در Google Drive
                  </a>

                </div>
              )}

          </section>
        )}

        {/* Footer */}
        <footer className="mt-8 pb-4 text-center">
          <p className="font-black tracking-wide text-slate-400">
            Flying Wings
          </p>

          <p className="mt-1 text-xs text-slate-600">
            سامانه هوشمند نمره‌دهی پروژه‌ها
          </p>
        </footer>

      </div>
    </main>
  );
}