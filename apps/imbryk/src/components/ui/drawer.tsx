import { Drawer as Vaul } from 'vaul';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function Drawer({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
}: DrawerProps) {
  return (
    <Vaul.Root open={open} onOpenChange={onOpenChange}>
      <Vaul.Portal>
        <Vaul.Overlay className="fixed inset-0 z-50 bg-black/45 backdrop-blur-[2px] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out data-[state=open]:fade-in" />
        <Vaul.Content
          aria-describedby={description ? 'drawer-description' : undefined}
          className={cn(
            // Shared: fixed drawer panel with rounded top corners (bottom-sheet feel on mobile).
            'fixed z-50 flex flex-col bg-surface shadow-2xl focus:outline-none',
            // Mobile: bottom sheet — full width, up to 90% of viewport height.
            'inset-x-0 bottom-0 max-h-[90dvh] rounded-t-2xl',
            // Desktop (≥sm): right-side sheet — full height, 28rem wide, flush to the right edge.
            'sm:inset-y-0 sm:right-0 sm:left-auto sm:top-0 sm:bottom-0 sm:h-full sm:max-h-none sm:w-[28rem] sm:rounded-t-none sm:rounded-l-2xl',
            className,
          )}
        >
          {/* Drag handle — visible only on mobile bottom-sheet form factor. */}
          <div
            aria-hidden="true"
            className="mx-auto mt-2 mb-1 h-1.5 w-10 rounded-full bg-border sm:hidden"
          />
          <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
            <div className="min-w-0">
              <Vaul.Title className="font-sans text-lg font-semibold text-text">
                {title}
              </Vaul.Title>
              {description && (
                <Vaul.Description
                  id="drawer-description"
                  className="font-sans text-sm text-text-muted mt-1"
                >
                  {description}
                </Vaul.Description>
              )}
            </div>
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              aria-label="Close"
              className="shrink-0 rounded-md p-1.5 text-text-muted hover:bg-bg hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus cursor-pointer"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </header>
          <div className="flex-1 overflow-y-auto px-5 py-5">{children}</div>
        </Vaul.Content>
      </Vaul.Portal>
    </Vaul.Root>
  );
}
