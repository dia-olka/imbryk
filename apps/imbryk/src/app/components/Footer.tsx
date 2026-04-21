import { useState } from 'react';
import { Feedback } from './Feedback';

export function Footer() {
  const [open, setOpen] = useState(false);

  return (
    <footer
      role="contentinfo"
      className="border-t border-border py-4 px-4 md:px-8 mt-auto"
    >
      <div className="mx-auto max-w-3xl text-sm text-text-muted font-sans space-y-4">
        <div className="flex flex-col items-center gap-1 text-center sm:flex-row sm:justify-between sm:text-left">
          <p>&copy; {new Date().getFullYear()} Imbryk. Shape the world.</p>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="feedback-panel"
            className="underline underline-offset-2 hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus rounded"
          >
            {open ? 'Close feedback' : 'Send feedback'}
          </button>
        </div>
        {open && (
          <div id="feedback-panel" className="pt-2">
            <Feedback />
          </div>
        )}
      </div>
    </footer>
  );
}
