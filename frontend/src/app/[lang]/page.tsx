/**
 * Skeleton home page for [lang] route.
 *
 * Phase 1: Renders a plain coming-soon shell with no features.
 * Phase 2: Replaced with proper i18n-aware landing page.
 * Phase 3: Replaced with auth-gated home or redirect to login.
 */
type Props = {
  params: Promise<{ lang: string }>;
};

export default async function HomePage({ params }: Props) {
  const { lang } = await params;

  return (
    <main className="min-h-dvh flex items-center justify-center">
      <div className="text-center p-8">
        <h1 className="text-2xl font-semibold mb-4">Diet Coach Agent</h1>
        <p className="text-sm text-gray-500">Phase 1 skeleton - lang: {lang}</p>
      </div>
    </main>
  );
}
