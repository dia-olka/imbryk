import markdownIt from 'markdown-it';

const md = markdownIt({ html: false, breaks: true, linkify: true });

export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy('src/css');
  // make logo and favicon icons available at site root
  eleventyConfig.addPassthroughCopy('src/favicon.svg');
  eleventyConfig.addPassthroughCopy('src/logo.svg');
  // TODO: create a 1200x630 og-gazette.png and place it in src/
  eleventyConfig.addPassthroughCopy('src/og-gazette.png');

  eleventyConfig.addFilter('dateDisplay', (value) => {
    if (!value) return '';
    const date = new Date(value);
    return date.toLocaleDateString('en-GB', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  });

  eleventyConfig.addFilter('dateISO', (value) => {
    if (!value) return '';
    return new Date(value).toISOString().split('T')[0];
  });

  eleventyConfig.addFilter('markdown', (value) => {
    if (!value) return '';
    return md.render(value);
  });

  eleventyConfig.addFilter('truncateWords', (value, count) => {
    if (!value) return '';
    const words = value.split(/\s+/);
    if (words.length <= count) return value;
    return words.slice(0, count).join(' ') + '…';
  });
  eleventyConfig.addFilter('truncateChars', (value, count) => {
    if (!value) return '';
    // Strip markdown formatting for clean meta descriptions
    const plain = value
      .replace(/[#*_~`>]/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/\n+/g, ' ')
      .trim();
    if (plain.length <= count) return plain;
    // Cut at last space before limit
    const truncated = plain.slice(0, count);
    const lastSpace = truncated.lastIndexOf(' ');
    return (
      (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + '\u2026'
    );
  });
  eleventyConfig.addFilter('head', (array, n) => {
    if (!Array.isArray(array)) return [];
    return array.slice(0, n);
  });

  eleventyConfig.addFilter('findPersona', (personas, newspaperId) => {
    return personas.find((p) => p.id === newspaperId);
  });

  eleventyConfig.addFilter('findCategory', (categories, categoryId) => {
    return categories.find((c) => c.id === categoryId);
  });

  eleventyConfig.addFilter('latestEdition', (editions) => {
    if (!editions || editions.length === 0) return null;
    return editions[0];
  });

  return {
    dir: {
      input: 'src',
      output: '../../dist/apps/gazette',
      includes: '_includes',
      data: '_data',
    },
    templateFormats: ['njk', 'md'],
    htmlTemplateEngine: 'njk',
    markdownTemplateEngine: 'njk',
  };
}
