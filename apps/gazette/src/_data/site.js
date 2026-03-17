/**
 * Centralised site metadata for SEO, Open Graph, and structured data.
 *
 * Environment variables (set in Cloudflare Pages / GitHub Actions):
 *   GAZETTE_URL    — public URL of this Gazette site (e.g. https://gazette.imbryk.com)
 *   IMBRYK_APP_URL — public URL of the Imbryk submission app (e.g. https://app.imbryk.com)
 */
export default function () {
  // Extract the origin from R2_PUBLIC_URL for preconnect hints in templates
  let r2Origin = '';
  if (process.env.R2_PUBLIC_URL) {
    try {
      r2Origin = new URL(process.env.R2_PUBLIC_URL).origin;
    } catch { /* ignore malformed URLs */ }
  }

  return {
    url: process.env.GAZETTE_URL ?? 'https://imbryk.news',
    submitUrl: process.env.IMBRYK_APP_URL ?? 'https://whisper.imbryk.news',
    name: 'Imbryk Gazette',
    description:
      'AI-powered perspectives on how world events ripple through society, politics, and culture — six ideologically distinct newspapers, each driven by advanced AI systems.',
    locale: 'en_US',
    ogImageFallback: '/og-gazette.png',
    cfWebAnalyticsToken: process.env.CF_WEB_ANALYTICS_TOKEN ?? '',
    r2Origin,
  };
}
