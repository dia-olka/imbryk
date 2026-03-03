const PLACEHOLDER_PATTERN = /\{\{([A-Z_][A-Z0-9_]*)\}\}/g;

export function interpolateTemplate(
  template: string,
  values: Record<string, string>
): string {
  const missingKeys: string[] = [];

  const result = template.replace(PLACEHOLDER_PATTERN, (match, key: string) => {
    if (key in values) {
      return values[key];
    }
    missingKeys.push(key);
    return match;
  });

  if (missingKeys.length > 0) {
    throw new Error(
      `Missing values for template placeholders: ${missingKeys.join(', ')}`
    );
  }

  return result;
}
