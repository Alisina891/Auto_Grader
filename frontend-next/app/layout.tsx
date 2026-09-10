import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "سامانه نمره‌دهی | بال پرواز",
  description: "سامانه هوشمند نمره‌دهی پروژه‌های Excel",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}