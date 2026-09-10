"use client";

import { useState, type FormEvent } from "react";
import { gradeStudentExcel } from "../lib/api";

interface StudentGraderProps {
  grade: string;
}

interface GradeResult {
  success: boolean;
  student_name: string;
  attendance_number: string;
  email?: string;
  grade: string;
  filename: string;
  project_id: string;
  score: number;
  max_score: number;
  status: string;
  passed: boolean;

  checks?: {
    passed: number;
    total: number;
  };

  score_details?: unknown;
  errors?: unknown[];
  student_feedback?: unknown[];
  ai_feedback?: unknown;
  summary?: string;

  google_drive?: {
    uploaded: boolean;
    file_id?: string;
    file_name?: string;
    web_view_link?: string;
  };
}

const TOP_BACKGROUND_IMAGE =
  "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=2000&q=85";

export default function StudentGrader({
  grade,
}: StudentGraderProps) {
  const [studentName, setStudentName] = useState("");
  const [attendanceNumber, setAttendanceNumber] = useState("");
  const [email, setEmail] = useState("");
  const [projectId, setProjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<GradeResult | null>(null);

  function getAIFeedback(data: GradeResult): string {
    if (!data.ai_feedback) {
      return "";
    }

    if (typeof data.ai_feedback === "string") {
      return data.ai_feedback;
    }

    if (
      typeof data.ai_feedback === "object" &&
      data.ai_feedback !== null
    ) {
      const feedback =
        data.ai_feedback as Record<string, unknown>;

      const fields = [
        "message",
        "feedback",
        "text",
        "content",
        "output_text",
      ];

      for (const field of fields) {
        if (typeof feedback[field] === "string") {
          return feedback[field] as string;
        }
      }
    }

    return "";
  }

  function getStudentFeedback(data: GradeResult): string {
    if (!Array.isArray(data.student_feedback)) {
      return "";
    }

    return data.student_feedback
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (
          typeof item === "object" &&
          item !== null
        ) {
          const obj =
            item as Record<string, unknown>;

          if (typeof obj.message === "string") {
            return obj.message;
          }
        }

        return "";
      })
      .filter(Boolean)
      .join("\n");
  }

  function getFriendlyErrorMessage(message: string): string {
    const lowerMessage = message.toLowerCase();

    const duplicateEmail =
      lowerMessage.includes("email") &&
      (
        lowerMessage.includes("already") ||
        lowerMessage.includes("exist") ||
        lowerMessage.includes("duplicate") ||
        lowerMessage.includes("registered") ||
        lowerMessage.includes("submitted")
      );

    if (duplicateEmail) {
      return "شما قبلاً ثبت کرده‌اید؛ دیگر اجازه ارسال پروژه ندارید.";
    }

    const duplicateSubmission =
      lowerMessage.includes("already submitted") ||
      lowerMessage.includes("already graded") ||
      lowerMessage.includes("duplicate submission");

    if (duplicateSubmission) {
      return (
        "این پروژه قبلاً با مشخصات شما ثبت شده است و " +
        "دیگر اجازه ارسال مجدد ندارید."
      );
    }

    return (
      "در هنگام بررسی پروژه مشکلی به وجود آمد. " +
      "لطفاً کمی بعد دوباره تلاش کنید."
    );
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setResult(null);

    if (!studentName.trim()) {
      setError(
        "لطفاً نام و تخلص خود را وارد کنید."
      );
      return;
    }

    if (!attendanceNumber.trim()) {
      setError(
        "لطفاً شماره حاضری خود را وارد کنید."
      );
      return;
    }

    if (!email.trim()) {
      setError(
        "لطفاً ایمیل خود را وارد کنید."
      );
      return;
    }

    const emailPattern =
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email.trim())) {
      setError(
        "لطفاً یک آدرس ایمیل معتبر وارد کنید."
      );
      return;
    }

    if (!projectId.trim()) {
      setError(
        "لطفاً شماره پروژه را وارد کنید."
      );
      return;
    }

    if (!file) {
      setError(
        "لطفاً فایل Excel پروژه را انتخاب کنید."
      );
      return;
    }

    const fileName =
      file.name.toLowerCase();

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

      const data = await gradeStudentExcel(
        grade,
        projectId.trim(),
        studentName.trim(),
        attendanceNumber.trim(),
        email.trim(),
        file
      );

      setResult(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(
          getFriendlyErrorMessage(err.message)
        );
      } else {
        setError(
          "در هنگام بررسی پروژه مشکلی به وجود آمد. لطفاً کمی بعد دوباره تلاش کنید."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  const aiFeedback = result
    ? getAIFeedback(result)
    : "";

  const studentFeedback = result
    ? getStudentFeedback(result)
    : "";

  const feedback =
    aiFeedback ||
    studentFeedback ||
    result?.summary ||
    "برای این پروژه بازخوردی ثبت نشده است.";

  const scorePercentage =
    result && result.max_score > 0
      ? Math.round(
          (result.score / result.max_score) * 100
        )
      : 0;

  return (
    <main
      dir="rtl"
      className="relative min-h-screen overflow-hidden bg-slate-50 text-slate-800"
    >
      {/* =====================================================
          BACKGROUND
      ====================================================== */}

      <div className="pointer-events-none absolute inset-x-0 top-0 h-[680px] overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url("${TOP_BACKGROUND_IMAGE}")`,
          }}
        />

        <div className="absolute inset-0 bg-slate-950/50" />

        <div className="absolute inset-0 bg-gradient-to-br from-blue-950/75 via-blue-900/40 to-indigo-900/65" />

        <div className="absolute inset-x-0 bottom-0 h-80 bg-gradient-to-t from-slate-50 via-slate-50/85 to-transparent" />
      </div>

      {/* =====================================================
          DECORATIVE BACKGROUND
      ====================================================== */}

      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -right-32 top-[420px] h-80 w-80 rounded-full bg-cyan-300/20 blur-3xl" />

        <div className="absolute -left-32 top-[520px] h-96 w-96 rounded-full bg-indigo-300/20 blur-3xl" />

        <div className="absolute right-1/3 top-[700px] h-64 w-64 rounded-full bg-blue-200/20 blur-3xl" />

        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(15,23,42,1) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,1) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
      </div>

      {/* =====================================================
          MAIN CONTAINER
      ====================================================== */}

      <div className="relative z-10 mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">

        {/* ===================================================
            HEADER
        ==================================================== */}

        <header className="mb-8 text-center">
          <div className="mx-auto max-w-3xl">

            <div className="mb-5 flex justify-center">
              <div className="group relative">

                <div className="absolute inset-0 rounded-3xl bg-cyan-400/30 blur-2xl transition-all duration-500 group-hover:bg-cyan-300/50" />

                <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl border border-white/30 bg-white/15 shadow-2xl backdrop-blur-xl">
                  <span className="text-5xl drop-shadow-lg">
                    🪽
                  </span>
                </div>

              </div>
            </div>

            <div className="mb-3">
              <span className="text-sm font-semibold uppercase tracking-[0.35em] text-cyan-200 drop-shadow">
                Flying Wings
              </span>
            </div>

            <h1 className="text-3xl font-black tracking-tight text-white drop-shadow-lg sm:text-4xl lg:text-5xl">
              سامانه نمره‌دهی خودکار
            </h1>

            <p className="mx-auto mt-4 max-w-2xl text-sm leading-8 text-white/90 sm:text-base">
              فایل پروژه Excel خود را ارسال کنید تا سیستم به‌صورت
              خودکار پروژه شما را بررسی، نمره‌دهی و نتیجه را نمایش دهد.
            </p>

            <div className="mt-6 flex justify-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/15 px-5 py-2 text-sm font-bold text-white shadow-lg backdrop-blur-xl">
                <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
                صنف {grade}
              </div>
            </div>

          </div>
        </header>

        {/* ===================================================
            STARTUP NOTICE
        ==================================================== */}

        <section className="mb-6 overflow-hidden rounded-3xl border border-amber-200/80 bg-amber-50/95 p-5 shadow-xl shadow-amber-200/20 backdrop-blur-xl sm:p-6">

          <div className="flex items-start gap-4">

            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-2xl">
              ⏳
            </div>

            <div>
              <h2 className="font-black text-amber-900">
                لطفاً کمی صبر کنید
              </h2>

              <p className="mt-2 text-sm leading-7 text-amber-800">
                ممکن است سیستم در اولین درخواست تا حدود یک دقیقه
                زمان نیاز داشته باشد تا آماده شود و پروژه شما را
                بررسی کند.
              </p>

              <p className="mt-2 text-sm font-bold leading-7 text-amber-900">
                اگر در حال حاضر خطایی دریافت کردید، لطفاً کمی بعد
                دوباره تلاش کنید.
              </p>
            </div>

          </div>
        </section>

        {/* ===================================================
            INSTRUCTIONS
        ==================================================== */}

        <section className="mb-6 rounded-3xl border border-white/70 bg-white/90 p-5 shadow-xl shadow-slate-300/30 backdrop-blur-xl sm:p-6">

          <div className="flex items-start gap-4">

            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-2xl">
              📋
            </div>

            <div>
              <h2 className="text-lg font-extrabold text-slate-900">
                قبل از ارسال پروژه
              </h2>

              <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-600">

                <li>
                  • فایل اصلی Excel پروژه را ارسال کنید.
                </li>

                <li>
                  • عکس یا فایل PDF قابل قبول نیست.
                </li>

                <li>
                  • فایل باید با فرمت <b dir="ltr">.xlsx</b> یا{" "}
                  <b dir="ltr">.xlsm</b> باشد.
                </li>

                <li>
                  • شماره پروژه را مطابق پروژه‌ای که انجام داده‌اید
                  وارد کنید.
                </li>

                <li>
                  • ایمیل معتبر خود را وارد کنید.
                </li>

                <li>
                  • هر ایمیل فقط برای یک ارسال پروژه قابل استفاده است.
                </li>

              </ul>
            </div>

          </div>
        </section>

        {/* ===================================================
            FORM
        ==================================================== */}

        <section className="rounded-[2rem] border border-slate-200/80 bg-white/95 p-5 shadow-2xl shadow-slate-300/40 backdrop-blur-xl sm:p-8">

          <div className="mb-8">
            <h2 className="text-2xl font-black text-slate-900">
              ارسال پروژه
            </h2>

            <p className="mt-2 text-sm leading-7 text-slate-500">
              معلومات خود را وارد کرده و فایل Excel پروژه را انتخاب کنید.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-6"
          >

            {/* Student Name */}

            <div>
              <label
                htmlFor="studentName"
                className="mb-2 block text-sm font-bold text-slate-700"
              >
                نام و تخلص
              </label>

              <input
                id="studentName"
                type="text"
                value={studentName}
                onChange={(e) =>
                  setStudentName(e.target.value)
                }
                placeholder="نام و تخلص خود را وارد کنید"
                autoComplete="name"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
              />
            </div>

            {/* Attendance Number */}

            <div>
              <label
                htmlFor="attendanceNumber"
                className="mb-2 block text-sm font-bold text-slate-700"
              >
                شماره حاضری
              </label>

              <input
                id="attendanceNumber"
                type="text"
                value={attendanceNumber}
                onChange={(e) =>
                  setAttendanceNumber(e.target.value)
                }
                placeholder="شماره حاضری خود را وارد کنید"
                inputMode="numeric"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
              />
            </div>

            {/* Email */}

            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-bold text-slate-700"
              >
                ایمیل
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) =>
                  setEmail(e.target.value)
                }
                placeholder="مثلاً student@gmail.com"
                autoComplete="email"
                dir="ltr"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-left text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
              />

              <p className="mt-2 text-xs leading-6 text-slate-400">
                هر ایمیل فقط یک بار برای ارسال پروژه قابل استفاده است.
              </p>
            </div>

            {/* Project ID */}

            <div>
              <label
                htmlFor="projectId"
                className="mb-2 block text-sm font-bold text-slate-700"
              >
                شماره پروژه
              </label>

              <input
                id="projectId"
                type="text"
                value={projectId}
                onChange={(e) =>
                  setProjectId(e.target.value)
                }
                placeholder="مثلاً ۱"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
              />
            </div>

            {/* Excel File */}

            <div>
              <label
                htmlFor="excelFile"
                className="mb-2 block text-sm font-bold text-slate-700"
              >
                فایل پروژه Excel
              </label>

              <label
                htmlFor="excelFile"
                className="group flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center transition-all hover:border-blue-400 hover:bg-blue-50/50"
              >

                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 text-3xl transition-transform duration-300 group-hover:scale-110">
                  📊
                </div>

                <p className="font-bold text-slate-800">
                  {file
                    ? file.name
                    : "برای انتخاب فایل کلیک کنید"}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  فقط فایل‌های Excel با فرمت .xlsx و .xlsm
                </p>

                <input
                  id="excelFile"
                  type="file"
                  accept=".xlsx,.xlsm"
                  className="hidden"
                  onChange={(e) => {
                    setFile(
                      e.target.files?.[0] || null
                    );

                    setError("");
                  }}
                />

              </label>
            </div>

            {/* Error */}

            {error && (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-semibold leading-7 text-red-700">

                <div className="flex items-start gap-3">

                  <span className="text-xl">
                    ⚠️
                  </span>

                  <span>
                    {error}
                  </span>

                </div>

              </div>
            )}

            {/* Submit */}

            <button
              type="submit"
              disabled={loading}
              className="group relative w-full overflow-hidden rounded-2xl bg-gradient-to-l from-blue-700 via-blue-600 to-indigo-600 px-6 py-4 font-black text-white shadow-xl shadow-blue-500/25 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-blue-500/30 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            >

              <span className="relative z-10 flex items-center justify-center gap-3">

                {loading ? (
                  <>
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />

                    در حال بررسی پروژه...
                  </>
                ) : (
                  <>
                    <span className="text-xl">
                      🚀
                    </span>

                    بررسی و نمره‌دهی پروژه
                  </>
                )}

              </span>

              <span className="absolute inset-0 -translate-x-full bg-white/10 transition-transform duration-700 group-hover:translate-x-full" />

            </button>

          </form>
        </section>

        {/* ===================================================
            RESULT
        ==================================================== */}

        {result && (
          <section className="mt-8 overflow-hidden rounded-[2rem] border border-white/80 bg-white/95 shadow-2xl shadow-slate-300/40 backdrop-blur-xl">

            {/* Result Header */}

            <div className="relative overflow-hidden bg-gradient-to-l from-slate-950 via-blue-950 to-indigo-900 px-6 py-8 text-center text-white sm:px-10">

              <div className="absolute -right-20 -top-20 h-48 w-48 rounded-full bg-cyan-400/20 blur-3xl" />

              <div className="absolute -bottom-20 -left-20 h-48 w-48 rounded-full bg-indigo-400/20 blur-3xl" />

              <div className="relative">

                <div className="mb-3 text-4xl">
                  {result.passed ? "🎉" : "📘"}
                </div>

                <h2 className="text-2xl font-black sm:text-3xl">
                  نتیجه پروژه
                </h2>

                <p className="mt-2 text-sm text-white/70">
                  {result.student_name}
                </p>

              </div>
            </div>

            <div className="p-5 sm:p-8">

              {/* Score Cards */}

              <div className="grid gap-5 sm:grid-cols-3">

                {/* Score */}

                <div className="rounded-3xl border border-blue-100 bg-blue-50 p-6 text-center">

                  <p className="text-sm font-bold text-blue-700">
                    نمره
                  </p>

                  <div className="mt-3 text-5xl font-black text-blue-900">
                    {result.score}

                    <span className="mx-1 text-2xl text-blue-400">
                      /
                    </span>

                    {result.max_score}
                  </div>

                  <p className="mt-2 text-sm font-semibold text-blue-600">
                    از {result.max_score} نمره
                  </p>

                </div>

                {/* Percentage */}

                <div className="rounded-3xl border border-emerald-100 bg-emerald-50 p-6 text-center">

                  <p className="text-sm font-bold text-emerald-700">
                    درصد موفقیت
                  </p>

                  <div className="mt-3 text-5xl font-black text-emerald-900">
                    {scorePercentage}%
                  </div>

                  <div className="mx-auto mt-4 h-2 max-w-[180px] overflow-hidden rounded-full bg-emerald-200">

                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all duration-1000"
                      style={{
                        width: `${Math.min(
                          scorePercentage,
                          100
                        )}%`,
                      }}
                    />

                  </div>

                </div>

                {/* Status */}

                <div className="rounded-3xl border border-indigo-100 bg-indigo-50 p-6 text-center">

                  <p className="text-sm font-bold text-indigo-700">
                    وضعیت
                  </p>

                  <div className="mt-5">

                    <span
                      className={`inline-flex items-center rounded-full px-5 py-2 text-sm font-black ${
                        result.passed
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {result.passed
                        ? "✓ موفق"
                        : "نیاز به اصلاح"}
                    </span>

                  </div>

                  <p className="mt-4 text-xs text-slate-500">
                    {result.status}
                  </p>

                </div>

              </div>

              {/* Checks */}

              {result.checks && (
                <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-6">

                  <div className="flex items-center justify-between gap-4">

                    <div>
                      <h3 className="font-black text-slate-900">
                        بررسی‌های انجام‌شده
                      </h3>

                      <p className="mt-1 text-xs text-slate-500">
                        تعداد موارد بررسی‌شده توسط سیستم
                      </p>
                    </div>

                    <div className="shrink-0 rounded-2xl bg-white px-5 py-3 text-center shadow-sm">

                      <span className="text-2xl font-black text-slate-900">
                        {result.checks.passed}
                      </span>

                      <span className="mx-1 text-slate-400">
                        /
                      </span>

                      <span className="font-bold text-slate-500">
                        {result.checks.total}
                      </span>

                    </div>

                  </div>

                </div>
              )}

              {/* Feedback */}

              <div className="mt-6 rounded-3xl border border-violet-100 bg-gradient-to-br from-violet-50 to-blue-50 p-6">

                <div className="flex items-center gap-3">

                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-100 text-xl">
                    🤖
                  </div>

                  <div>
                    <h3 className="font-black text-slate-900">
                      بازخورد سیستم
                    </h3>

                    <p className="text-xs text-slate-500">
                      پیشنهادها و نتیجه بررسی پروژه
                    </p>
                  </div>

                </div>

                <div className="mt-5 whitespace-pre-line rounded-2xl bg-white/80 p-5 text-sm leading-8 text-slate-700">
                  {feedback}
                </div>

              </div>

              {/* Google Drive */}

              {result.google_drive?.uploaded && (
                <div className="mt-6 rounded-3xl border border-emerald-200 bg-emerald-50 p-5">

                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

                    <div className="flex items-center gap-3">

                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-100 text-xl">
                        ☁️
                      </div>

                      <div>

                        <h3 className="font-black text-emerald-900">
                          فایل ذخیره شد
                        </h3>

                        <p className="mt-1 text-xs text-emerald-700">
                          پروژه شما با موفقیت در Google Drive ذخیره شد.
                        </p>

                      </div>

                    </div>

                    {result.google_drive.web_view_link && (
                      <a
                        href={
                          result.google_drive.web_view_link
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-xl bg-emerald-600 px-5 py-3 text-center text-sm font-bold text-white transition hover:bg-emerald-700"
                      >
                        مشاهده فایل
                      </a>
                    )}

                  </div>

                </div>
              )}

            </div>
          </section>
        )}

        {/* ===================================================
            FOOTER
        ==================================================== */}

        <footer className="py-10 text-center">

          <div className="mb-3 text-2xl">
            🪽
          </div>

          <p className="text-sm font-bold text-slate-600">
            Flying Wings
          </p>

          <p className="mt-1 text-xs text-slate-400">
            سامانه هوشمند نمره‌دهی پروژه‌های Excel
          </p>

          <div className="mx-auto mt-5 h-px max-w-xs bg-gradient-to-r from-transparent via-slate-300 to-transparent" />

          <p className="mt-5 text-xs text-slate-400">
            © {new Date().getFullYear()} Flying Wings
          </p>

        </footer>

      </div>

      {/* =====================================================
          GLOBAL STYLES
      ====================================================== */}

      <style jsx global>{`
        html {
          scroll-behavior: smooth;
        }

        body {
          margin: 0;
          font-family: Tahoma, Arial, sans-serif;
          background: #f8fafc;
        }

        * {
          box-sizing: border-box;
        }

        ::selection {
          background: rgba(59, 130, 246, 0.25);
          color: #0f172a;
        }

        @keyframes float {
          0%,
          100% {
            transform: translateY(0);
          }

          50% {
            transform: translateY(-8px);
          }
        }

        .float-animation {
          animation: float 4s ease-in-out infinite;
        }
      `}</style>
    </main>
  );
}