export function Footer() {
  return (
    <footer
      role="contentinfo"
      className="border-t border-border py-4 px-4 md:px-8 mt-auto"
    >
      <div className="mx-auto max-w-3xl text-center text-sm text-text-muted font-sans">
        <p>&copy; {new Date().getFullYear()} Imbryk. All events are fictional.</p>
      </div>
    </footer>
  );
}
