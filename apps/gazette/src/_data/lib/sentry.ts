/**
 * Sentry utility wrapper for the gazette data pipeline.
 *
 * Provides helpers for capturing Zod validation failures and generic load
 * errors during Eleventy builds. All reports include the full source URL so
 * operators can locate and inspect the offending R2 file or local fixture.
 *
 * If SENTRY_DSN is not set, all helpers degrade gracefully to console.warn only.
 */

import type { ZodError } from 'zod';

const SENTRY_DSN = process.env.SENTRY_DSN || '';

let sentryInitialised = false;

async function getSentry() {
  if (!SENTRY_DSN) return null;
  if (sentryInitialised) {
    // Already initialised — return the module
    const mod = await import('@sentry/node');
    return mod;
  }
  try {
    const mod = await import('@sentry/node');
    mod.init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV || 'production',
      // Disable performance tracing for build-time use
      tracesSampleRate: 0,
    });
    sentryInitialised = true;
    return mod;
  } catch {
    console.warn(
      'Gazette: @sentry/node could not be loaded; Sentry reporting disabled.'
    );
    return null;
  }
}

export interface ValidationContext {
  /**
   * Full URL of the file that failed (R2 URL or absolute local path).
   * Included in every Sentry event so operators can fetch and inspect the file.
   */
  sourceUrl: string;
  /** Human-readable label, e.g. "index entry yz-d2-001" or "newspaper sovereign". */
  label: string;
  /** The raw data that did not pass validation. */
  offendingData: unknown;
}

/**
 * Report a Zod validation failure to console and Sentry.
 *
 * Always includes the full `sourceUrl` so operators can locate the offending
 * file in R2 or the local fixture directory.
 */
export async function captureValidationError(
  ctx: ValidationContext,
  zodError: ZodError
): Promise<void> {
  const message = `Gazette validation failure [${ctx.label}] — ${ctx.sourceUrl}`;
  console.warn(message);
  console.warn('Validation issues:', JSON.stringify(zodError.flatten(), null, 2));

  const sentry = await getSentry();
  if (!sentry) return;

  sentry.withScope((scope) => {
    scope.setLevel('warning');
    scope.setExtra('sourceUrl', ctx.sourceUrl);
    scope.setExtra('label', ctx.label);
    scope.setExtra('zodErrors', zodError.flatten());
    scope.setExtra('offendingData', ctx.offendingData);
    sentry.captureMessage(message, 'warning');
  });
}

/**
 * Report a generic load/parse error to console and Sentry.
 *
 * Use this for non-Zod errors such as failed fetch responses or JSON.parse
 * failures. Always includes the full source URL.
 */
export async function captureLoadError(
  sourceUrl: string,
  label: string,
  error: unknown
): Promise<void> {
  const message = `Gazette load error [${label}] — ${sourceUrl}`;
  console.warn(message, error);

  const sentry = await getSentry();
  if (!sentry) return;

  const err = error instanceof Error ? error : new Error(String(error));
  sentry.withScope((scope) => {
    scope.setLevel('error');
    scope.setExtra('sourceUrl', sourceUrl);
    scope.setExtra('label', label);
    sentry.captureException(err);
  });
}
