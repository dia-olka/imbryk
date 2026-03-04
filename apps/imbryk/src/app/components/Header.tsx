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
          <p className="text-text-muted text-sm mt-1 font-sans">
            Shape the world. One event at a time.
          </p>
        </div>
      </div>
    </header>
  );
}
