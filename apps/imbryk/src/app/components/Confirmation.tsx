import { useEffect, useRef } from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { QuoteResponse } from '../api/types';
import { NEWSPAPER_DISPLAY } from './newspaper-display';
import { GAZETTE_URL } from '../constants';

interface ConfirmationProps {
  quote: QuoteResponse;
  onReset: () => void;
}

export function Confirmation({ quote, onReset }: ConfirmationProps) {
  const alertRef = useRef<HTMLDivElement>(null);

  // Move focus to the success alert when confirmation mounts (state transition: payment → confirmed)
  useEffect(() => {
    alertRef.current?.focus();
  }, []);

  return (
    <div
      className="w-full max-w-md mx-auto space-y-4"
      role="status"
      aria-live="polite"
    >
      <Alert
        ref={alertRef}
        variant="success"
        tabIndex={-1}
        className="focus-visible:outline-none"
      >
        <AlertTitle>Your event has been sent into the world</AlertTitle>
        <AlertDescription>
          It will appear in tomorrow morning&apos;s edition. Each newspaper will
          cover it from their own angle.{' '}
          <a
            href={GAZETTE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="underline font-semibold"
          >
            Read it in The Gazette ↗
          </a>
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-sans">
            Newspapers covering your event
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {quote.newspapers.map((n) => {
              const display = NEWSPAPER_DISPLAY[n.newspaper_id];
              return (
                <li key={n.newspaper_id} className="font-sans">
                  <a
                    href={`${GAZETTE_URL}/edition/${new Date(Date.now() + 86400000).toISOString().split('T')[0]}/${n.newspaper_id}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-semibold underline-offset-2 hover:underline"
                  >
                    {display?.paperName ?? n.newspaper_id}
                  </a>
                  {display?.tagline && (
                    <span className="text-text-muted text-sm ml-2 italic">
                      — {display.tagline}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>

      <div className="text-center">
        <Button onClick={onReset} variant="outline" size="lg">
          Submit another event
        </Button>
      </div>
    </div>
  );
}
