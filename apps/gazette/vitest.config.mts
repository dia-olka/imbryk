import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    root: 'apps/gazette',
    include: ['src/**/*.spec.{js,ts}'],
  },
});
