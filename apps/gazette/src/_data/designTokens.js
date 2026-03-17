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
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Source+Sans+3:wght@400;600;700&display=swap',
  },
  aspirant: {
    primary: '#0d6b5f',
    accent: '#2980b9',
    secondary: '#eaf6f4',
    fontHeading: "'Libre Franklin', sans-serif",
    fontBody: "'Merriweather Sans', sans-serif",
    borderStyle: '2px solid',
    borderStyleName: 'clean',
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;600;700&family=Merriweather+Sans:wght@400;700&display=swap',
  },
  owner: {
    primary: '#2c3e50',
    accent: '#8e6f3e',
    secondary: '#f5f0e8',
    fontHeading: "'Playfair Display', serif",
    fontBody: "'Lora', serif",
    borderStyle: '1px solid',
    borderStyleName: 'rule',
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,700;1,400&display=swap',
  },
  sovereign: {
    primary: '#1b4332',
    accent: '#495057',
    secondary: '#f0f4f1',
    fontHeading: "'Cormorant Garamond', serif",
    fontBody: "'Source Serif 4', serif",
    borderStyle: '3px double',
    borderStyleName: 'ornate',
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400&family=Source+Serif+4:ital,wght@0,400;0,700;1,400&display=swap',
  },
  moralist: {
    primary: '#6c3483',
    accent: '#943126',
    secondary: '#f5eef8',
    fontHeading: "'Vollkorn', serif",
    fontBody: "'Nunito', sans-serif",
    borderStyle: '2px dashed',
    borderStyleName: 'traditional',
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Vollkorn:ital,wght@0,400;0,700;1,400&family=Nunito:wght@400;700&display=swap',
  },
  hedonist: {
    primary: '#7a5f00',
    accent: '#e74c8b',
    secondary: '#fef9e7',
    fontHeading: "'Poppins', sans-serif",
    fontBody: "'Inter', sans-serif",
    borderStyle: '2px dotted',
    borderStyleName: 'playful',
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Inter:wght@400;600;700&display=swap',
  },
  curator: {
    primary: '#34495e',
    accent: '#7f8c8d',
    secondary: '#f2f3f4',
    fontHeading: "'Inter', sans-serif",
    fontBody: "'Inter', sans-serif",
    borderStyle: '1px solid',
    borderStyleName: 'neutral',
    googleFontsUrl:
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap',
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
