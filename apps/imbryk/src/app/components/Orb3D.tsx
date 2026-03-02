import { useEffect, useCallback } from 'react';
import './orb.css';

interface Orb3DProps {
  isFlipped: boolean;
  isReleasing: boolean;
  onFlipBack: () => void;
  children: React.ReactNode;
}

export function Orb3D({
  isFlipped,
  isReleasing,
  onFlipBack,
  children,
}: Orb3DProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (isFlipped && e.key === 'Escape') {
        onFlipBack();
      }
    },
    [isFlipped, onFlipBack]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const bodyClasses = [
    'orb-body',
    isFlipped && 'orb-body--flipped',
    isReleasing && 'orb-body--releasing',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className="orb-scene"
      role="group"
      aria-label={isFlipped ? 'Quote result — click or press Escape to edit' : 'Prompt input'}
    >
      <div
        className={bodyClasses}
        onClick={isFlipped ? onFlipBack : undefined}
        tabIndex={isFlipped ? 0 : -1}
      >
        {children}
      </div>
    </div>
  );
}
