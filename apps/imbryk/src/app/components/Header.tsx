import { GAZETTE_URL } from '../constants';

export function Header() {
  return (
    <header role="banner" className="border-b-2 border-accent py-4 px-4 md:px-8">
      <div className="mx-auto flex max-w-3xl items-center">
        <img
          src="/logo.svg"
          alt="Imbryk logo"
          className="h-10 w-auto mr-3"
        />
        <div>
          <h1 className="font-serif text-3xl md:text-4xl font-bold tracking-tight text-text">
            Whisper
          </h1>
        </div>
        <nav className="ml-auto" aria-label="Gazette">
          <a
            href={GAZETTE_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open The Gazette in a new tab"
            className="inline-flex items-center gap-1 border border-accent text-accent text-xs font-sans px-3 py-1.5 rounded-full hover:bg-accent hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus transition-colors"
          >
            <span aria-hidden="true">📰</span>
            <span>The Gazette</span>
            <span aria-hidden="true" className="text-[10px]">↗</span>
          </a>
        </nav>
      </div>
    </header>
  );
}
