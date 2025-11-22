import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ErrorBoundary } from './components/ErrorBoundary';
import 'reactflow/dist/style.css';
import './index.css';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);

// Only wrap in StrictMode in development for error checking
// In development, StrictMode double-renders components which causes React Flow nodeTypes warning
const AppWithBoundary = (
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

if (import.meta.env.DEV) {
  root.render(
    <React.StrictMode>
      {AppWithBoundary}
    </React.StrictMode>
  );
} else {
  root.render(AppWithBoundary);
}
