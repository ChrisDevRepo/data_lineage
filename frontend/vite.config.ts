import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
        origin: 'http://localhost:3000',
        cors: true,
        warmup: {
          // Pre-warm frequently used files
          clientFiles: ['./index.tsx', './App.tsx', './config.ts'],
        },
      },
      build: {
        rollupOptions: {
          output: {
            manualChunks: {
              'graph-libs': ['graphology', 'graphology-traversal'],
              'layout-lib': ['dagre'],
              'flow-lib': ['reactflow']
            }
          }
        }
      },
      optimizeDeps: {
        // Pre-bundle these dependencies to speed up initial load
        include: [
          'react',
          'react-dom',
          'react-dom/client',
          'reactflow',
          'dagre',
          'graphology',
        ],
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
