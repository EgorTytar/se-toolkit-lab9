import { StrictMode, Component, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';

// Error boundary to catch and display errors
class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white p-8">
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-8 max-w-2xl">
            <h1 className="text-2xl font-bold mb-4">❌ App Error</h1>
            <pre className="bg-gray-800 p-4 rounded text-sm overflow-auto max-h-96 whitespace-pre-wrap">
              {this.state.error?.toString()}
            </pre>
            <p className="mt-4 text-gray-400 text-sm">
              If you see this, React IS loading but crashing.
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

console.log('[F1 App] React starting...');
console.log('[F1 App] window.location.origin =', window.location.origin);
console.log('[F1 App] window.location.href =', window.location.href);
console.log('[F1 App] protocol =', window.location.protocol);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
