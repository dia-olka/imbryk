import type { NewspaperDisplay } from './newspaper-display';

interface NewspaperCardProps {
  paperName: string;
  tagline: string;
  display?: NewspaperDisplay;
}

/**
 * Splits a CSS border shorthand like "3px double" into its component parts.
 * Returns width and style; colour is applied separately.
 */
function parseBorderShorthand(shorthand: string): { width: string; style: string } {
  const parts = shorthand.trim().split(/\s+/);
  const style = parts.find((p) => ['solid', 'dashed', 'dotted', 'double'].includes(p)) ?? 'solid';
  const width = parts.find((p) => /^\d/.test(p)) ?? '2px';
  return { width, style };
}

export function NewspaperCard({ paperName, tagline, display }: NewspaperCardProps) {
  const primary = display?.primary ?? '#1a1a2e';
  const secondary = display?.secondary ?? '#f8f8f8';
  const { width: borderTopWidth, style: borderTopStyle } = parseBorderShorthand(
    display?.borderStyle ?? '2px solid'
  );

  return (
    <div
      className="rounded-md overflow-hidden"
      style={{
        backgroundColor: secondary,
        borderWidth: '1px',
        borderStyle: 'solid',
        borderColor: `${primary}30`,
        borderTopWidth,
        borderTopStyle: borderTopStyle as 'solid' | 'dashed' | 'dotted' | 'double',
        borderTopColor: primary,
      }}
    >
      <div className="px-4 py-3">
        <p className="font-semibold text-sm leading-tight font-sans" style={{ color: primary }}>
          {paperName}
        </p>
        <p className="text-xs italic mt-0.5" style={{ color: `${primary}99` }}>
          {tagline}
        </p>
      </div>
    </div>
  );
}
