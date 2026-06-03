/**
 * [lang] Route Segment Layout
 *
 * This layout wraps all language-specific routes.
 * Phase 2 will add:
 *   - Server-side locale validation (fa | en | ar)
 *   - dir="rtl" | dir="ltr" on the html element
 *   - Dictionary loading via getDictionary(lang)
 *   - Cookie-based locale persistence
 *
 * For Phase 1: skeleton only. Renders children directly.
 */
import type { Metadata } from "next";

type Props = {
  children: React.ReactNode;
  params: Promise<{ lang: string }>;
};

export async function generateStaticParams() {
  // Phase 2 will expand this to support all locales.
  // Returning empty array for now allows dynamic rendering in dev.
  return [];
}

export const metadata: Metadata = {
  title: "Diet Coach Agent",
};

export default async function LangLayout({ children, params }: Props) {
  const { lang } = await params;

  return <div data-lang={lang}>{children}</div>;
}
