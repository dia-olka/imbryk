/**
 * Design token system mapping persona IDs to visual identity tokens.
 * Each newspaper gets distinct colors, fonts, and decorative styles
 * derived from their ideological persona.
 */

const PERSONA_DESIGN_MAP = {
  radical: {
    primary: '#c0392b',
    accent: '#e67e22',
    secondary: '#fdf2e9',
    fontHeading: "'Oswald', sans-serif",
    fontBody: "'Source Sans 3', sans-serif",
    borderStyle: '4px solid',
    borderStyleName: 'geometric',
  },
  aspirant: {
    primary: '#1a8a7d',
    accent: '#2980b9',
    secondary: '#eaf6f4',
    fontHeading: "'Libre Franklin', sans-serif",
    fontBody: "'Merriweather Sans', sans-serif",
    borderStyle: '2px solid',
    borderStyleName: 'clean',
  },
  owner: {
    primary: '#2c3e50',
    accent: '#8e6f3e',
    secondary: '#f5f0e8',
    fontHeading: "'Playfair Display', serif",
    fontBody: "'Lora', serif",
    borderStyle: '1px solid',
    borderStyleName: 'rule',
  },
  sovereign: {
    primary: '#1b4332',
    accent: '#495057',
    secondary: '#f0f4f1',
    fontHeading: "'Cormorant Garamond', serif",
    fontBody: "'Source Serif 4', serif",
    borderStyle: '3px double',
    borderStyleName: 'ornate',
  },
  moralist: {
    primary: '#6c3483',
    accent: '#943126',
    secondary: '#f5eef8',
    fontHeading: "'Vollkorn', serif",
    fontBody: "'Nunito', sans-serif",
    borderStyle: '2px dashed',
    borderStyleName: 'traditional',
  },
  hedonist: {
    primary: '#d4ac0d',
    accent: '#e74c8b',
    secondary: '#fef9e7',
    fontHeading: "'Poppins', sans-serif",
    fontBody: "'Inter', sans-serif",
    borderStyle: '2px dotted',
    borderStyleName: 'playful',
  },
  curator: {
    primary: '#34495e',
    accent: '#7f8c8d',
    secondary: '#f2f3f4',
    fontHeading: "'Inter', sans-serif",
    fontBody: "'Inter', sans-serif",
    borderStyle: '1px solid',
    borderStyleName: 'neutral',
  },
};

/**
 * Get design tokens for a persona by ID.
 * @param {string} personaId - e.g. 'sovereign', 'radical'
 * @returns {object|null} design token object or null if unknown persona
 */
export function getDesignTokens(personaId) {
  return PERSONA_DESIGN_MAP[personaId] ?? null;
}

/**
 * Convert design tokens to a CSS inline style string of custom properties.
 * Used in templates: <div class="newspaper" style="{{ tokens | toCSSVars }}">
 * @param {object} tokens - design token object from getDesignTokens
 * @returns {string} CSS custom properties for inline style attribute
 */
export function toCSSCustomProperties(tokens) {
  if (!tokens) return '';
  return [
    `--np-primary: ${tokens.primary}`,
    `--np-accent: ${tokens.accent}`,
    `--np-secondary: ${tokens.secondary}`,
    `--np-font-heading: ${tokens.fontHeading}`,
    `--np-font-body: ${tokens.fontBody}`,
    `--np-border-style: ${tokens.borderStyle}`,
  ].join('; ');
}

export { PERSONA_DESIGN_MAP };
