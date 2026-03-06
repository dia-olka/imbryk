/**
 * Display metadata for each newspaper persona.
 * Source of truth: data/personas.json and apps/gazette/src/_data/designTokens.js
 * — keep in sync if persona names/taglines/colours change.
 * We duplicate here because this runs in the browser where Node's createRequire is unavailable.
 */
export interface NewspaperDisplay {
  paperName: string;
  tagline: string;
  /** CSS colour for titles, borders, and primary UI accent. */
  primary: string;
  /** Complementary accent colour. */
  accent: string;
  /** Light tinted background colour for the card. */
  secondary: string;
  /** CSS border shorthand for the masthead accent strip, e.g. '3px double'. */
  borderStyle: string;
}

export const NEWSPAPER_DISPLAY: Record<string, NewspaperDisplay> = {
  sovereign: {
    paperName: 'The Sovereign',
    tagline: 'The view from the situation room',
    primary: '#1b4332',
    accent: '#495057',
    secondary: '#f0f4f1',
    borderStyle: '3px double',
  },
  aspirant: {
    paperName: 'The Aspirant',
    tagline: 'A better world is possible',
    primary: '#1a8a7d',
    accent: '#2980b9',
    secondary: '#eaf6f4',
    borderStyle: '2px solid',
  },
  owner: {
    paperName: 'The Owner',
    tagline: 'The bottom line, above all',
    primary: '#2c3e50',
    accent: '#8e6f3e',
    secondary: '#f5f0e8',
    borderStyle: '1px solid',
  },
  moralist: {
    paperName: 'The Moralist',
    tagline: 'Decency still matters',
    primary: '#6c3483',
    accent: '#943126',
    secondary: '#f5eef8',
    borderStyle: '2px dashed',
  },
  radical: {
    paperName: 'The Radical',
    tagline: "They don't want you to read this",
    primary: '#c0392b',
    accent: '#e67e22',
    secondary: '#fdf2e9',
    borderStyle: '4px solid',
  },
  hedonist: {
    paperName: 'The Hedonist',
    tagline: 'Life is too short for boring news',
    primary: '#d4ac0d',
    accent: '#e74c8b',
    secondary: '#fef9e7',
    borderStyle: '2px dotted',
  },
};
