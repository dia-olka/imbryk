import { SkipLink } from './components/SkipLink';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PromptFlow } from './components/PromptFlow';

export function App() {
  return (
    <div className="flex flex-col min-h-screen">
      <SkipLink />
      <Header />
      <main id="main-content" className="flex-1 px-4 py-8 md:py-12">
        <ErrorBoundary>
          <PromptFlow />
        </ErrorBoundary>
      </main>
      <Footer />
    </div>
  );
}

export default App;
