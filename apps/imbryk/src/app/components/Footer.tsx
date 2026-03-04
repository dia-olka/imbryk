export function Footer() {
  return (
    <footer
      role="contentinfo"
      className="border-t border-border py-4 px-4 md:px-8 mt-auto"
    >
      <div className="mx-auto max-w-3xl text-center text-sm text-text-muted font-sans">
        <p>
          &copy; {new Date().getFullYear()} Imbryk. All events are fictional.
        </p>
        <p className="mt-1">
          <a
            href="https://imbryk-gazette.pages.dev"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-text"
          >
            Read the Gazette →
          </a>
        </p>
      </div>
    </footer>
  );
}
