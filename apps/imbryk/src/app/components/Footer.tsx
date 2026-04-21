import { useState } from 'react';
import { Drawer } from '@/components/ui/drawer';
import { Feedback } from './Feedback';

export function Footer() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <footer
        role="contentinfo"
        className="border-t border-border py-4 px-4 md:px-8 mt-auto"
      >
        <div className="mx-auto max-w-3xl flex flex-col items-center gap-2 text-center text-sm text-text-muted font-sans sm:flex-row sm:justify-between sm:text-left">
          <p>&copy; {new Date().getFullYear()} Imbryk. Shape the world.</p>
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="inline-flex items-center justify-center min-h-11 min-w-11 px-3 underline underline-offset-2 hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus rounded cursor-pointer"
          >
            Send feedback
          </button>
        </div>
      </footer>
      <Drawer
        open={open}
        onOpenChange={setOpen}
        title="Send feedback"
        description="Questions, bugs, ideas — we read every note."
      >
        <Feedback />
      </Drawer>
    </>
  );
}
