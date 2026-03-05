/**
 * Display metadata for each newspaper persona.
 * Source of truth: data/personas.json — keep in sync if persona names/taglines change.
 * We duplicate here because this runs in the browser where Node's createRequire is unavailable.
 */
export const NEWSPAPER_DISPLAY: Record<
  string,
  { paperName: string; tagline: string }
> = {
  sovereign: {
    paperName: 'The Sovereign',
    tagline: 'The view from the situation room',
  },
  aspirant: {
    paperName: 'The Aspirant',
    tagline: 'A better world is possible',
  },
  owner: { paperName: 'The Owner', tagline: 'The bottom line, above all' },
  moralist: { paperName: 'The Moralist', tagline: 'Decency still matters' },
  radical: {
    paperName: 'The Radical',
    tagline: "They don't want you to read this",
  },
  hedonist: {
    paperName: 'The Hedonist',
    tagline: 'Life is too short for boring news',
  },
};
