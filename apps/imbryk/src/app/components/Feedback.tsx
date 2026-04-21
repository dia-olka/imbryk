import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

const WEB3FORMS_ACCESS_KEY = '987c22b8-28cb-4780-bb51-795528fbe8e0';
const WEB3FORMS_ENDPOINT = 'https://api.web3forms.com/submit';

type Status =
  | { kind: 'idle' }
  | { kind: 'sending' }
  | { kind: 'success' }
  | { kind: 'error'; message: string };

const inputClass =
  'flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm ring-offset-bg placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';

export function Feedback() {
  const [status, setStatus] = useState<Status>({ kind: 'idle' });

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus({ kind: 'sending' });

    const form = event.currentTarget;
    const data = new FormData(form);
    const payload: Record<string, FormDataEntryValue> = {};
    data.forEach((value, key) => {
      payload[key] = value;
    });

    try {
      const response = await fetch(WEB3FORMS_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => ({ success: false }));
      if (response.ok && body.success) {
        setStatus({ kind: 'success' });
        form.reset();
      } else {
        setStatus({
          kind: 'error',
          message: body.message ?? 'Something went wrong. Please try again later.',
        });
      }
    } catch {
      setStatus({ kind: 'error', message: 'Network error. Please try again later.' });
    }
  };

  if (status.kind === 'success') {
    return (
      <Alert variant="success" className="max-w-md mx-auto">
        <AlertDescription>
          Thanks — your message is on its way. We read every one.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md mx-auto space-y-4 font-sans">
      <input type="hidden" name="access_key" value={WEB3FORMS_ACCESS_KEY} />
      <input type="hidden" name="from_name" value="Imbryk Whisper feedback" />
      <input type="hidden" name="subject" value="New feedback from Imbryk Whisper" />
      {/* Honeypot — bots fill this, humans don't see it. */}
      <input
        type="checkbox"
        name="botcheck"
        tabIndex={-1}
        autoComplete="off"
        className="hidden"
        aria-hidden="true"
      />

      <div className="space-y-1.5">
        <Label htmlFor="feedback-name">
          Your name <span className="text-text-muted font-normal">(optional)</span>
        </Label>
        <input
          type="text"
          id="feedback-name"
          name="name"
          autoComplete="name"
          maxLength={120}
          className={inputClass}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="feedback-email">
          Email <span className="text-text-muted font-normal">(optional — needed if you want a reply)</span>
        </Label>
        <input
          type="email"
          id="feedback-email"
          name="email"
          autoComplete="email"
          maxLength={200}
          className={inputClass}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="feedback-message">Message</Label>
        <Textarea
          id="feedback-message"
          name="message"
          required
          minLength={10}
          maxLength={4000}
          rows={6}
        />
      </div>

      {status.kind === 'error' && (
        <Alert variant="destructive">
          <AlertDescription>{status.message}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between gap-3">
        <Button type="submit" disabled={status.kind === 'sending'}>
          {status.kind === 'sending' ? 'Sending…' : 'Send feedback'}
        </Button>
        <p className="text-xs text-text-muted">
          Delivered via{' '}
          <a
            href="https://web3forms.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            web3forms
          </a>
        </p>
      </div>
    </form>
  );
}
