import React from 'react';
import { Button } from './ui/Button';

type InfoModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onOpenDeveloperPanel?: () => void;
};

// Simple icon components with subtle styling
const GraphIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" /></svg>
    </div>
);
const NavIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" /></svg>
    </div>
);
const SearchIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" /></svg>
    </div>
);
const FilterIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" /></svg>
    </div>
);
const TraceIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" /></svg>
    </div>
);
const ImportExportIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" /></svg>
    </div>
);
const DeveloperIcon = () => (
    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-gray-600"><path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" /></svg>
    </div>
);

const Feature = ({ icon, title, children }: { icon: React.ReactNode, title: string, children: React.ReactNode }) => (
    <div className="flex items-start gap-4 p-4 rounded-lg hover:bg-gray-50 transition-colors">
        <div className="flex-shrink-0">{icon}</div>
        <div>
            <h3 className="text-base font-semibold text-gray-800 mb-1">{title}</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{children}</p>
        </div>
    </div>
);

export const InfoModal = ({ isOpen, onClose, onOpenDeveloperPanel }: InfoModalProps) => {
    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div className="fixed inset-0 bg-black/50 z-50" onClick={onClose} />

            {/* Modal */}
            <div className="fixed inset-0 z-[51] flex items-center justify-center p-4 pointer-events-none">
                <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl h-auto max-h-[90vh] flex flex-col text-gray-800 pointer-events-auto" onClick={(e) => e.stopPropagation()}>
                    {/* Header with logo and colorful accent */}
                    <div>
                        <div className="flex items-center justify-between px-4 py-2 bg-white rounded-t-lg">
                            <img src="/logo.png" alt="Data Lineage Visualizer" className="h-10" />
                            <button
                                onClick={onClose}
                                className="w-9 h-9 flex items-center justify-center hover:bg-gray-100 text-gray-600 rounded transition-colors"
                                title="Close (ESC)"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        {/* Colorful accent bar matching logo theme */}
                        <div className="h-1 bg-gradient-to-r from-blue-500 via-teal-400 to-orange-400"></div>
                    </div>

                    {/* Title section */}
                    <header className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-2xl font-bold text-gray-800">Welcome to the Data Lineage Visualizer!</h2>
                        <p className="mt-2 text-sm text-gray-600 italic">Explore and understand the relationships between your data assets</p>
                    </header>

                    {/* Content */}
                    <main className="flex-grow px-6 py-5 overflow-y-auto">
                        <div className="space-y-4">
                            <Feature icon={<GraphIcon />} title="Visualize Data Lineage">
                                See how data flows from source to destination. Each node represents a database object (table, view, or stored procedure), and arrows show dependencies. Nodes are color-coded by schema for easy identification.
                            </Feature>

                            <Feature icon={<NavIcon />} title="Navigate the Canvas">
                                Click and drag to pan, scroll to zoom, or use the controls in the bottom-left corner. Click any node to highlight its immediate connections. Toggle layout between top-down or left-right orientation.
                            </Feature>

                            <Feature icon={<SearchIcon />} title="Advanced Search">
                                Use <strong>Detail Search</strong> to search across all DDL definitions with full-text search. Filter by schema and object type, then view SQL code in a Monaco editor with syntax highlighting.
                            </Feature>

                            <Feature icon={<FilterIcon />} title="Filter & Focus">
                                Filter the canvas by schemas or object types. Click the <strong>⭐ star icon</strong> next to schemas to designate them as <strong>focus schemas</strong> (master/anchor). When enabled, extended schemas show only nodes connected to focus schemas. Use <strong>Hide Isolated Nodes</strong> to remove nodes with no connections, and pattern-based exclusions to hide temporary or backup objects.
                            </Feature>

                            <Feature icon={<TraceIcon />} title="Interactive Trace">
                                Perform impact analysis with <strong>Interactive Trace</strong>. Select a starting node and trace upstream (dependencies) or downstream (dependents) to any depth, or find the shortest path between two objects.
                            </Feature>

                            <Feature icon={<ImportExportIcon />} title="Import & Export">
                                Load your own lineage data from JSON files or Parquet snapshots. Export your current view as SVG for presentations and documentation. All data stays local in your browser.
                            </Feature>

                            <div className="pt-4 mt-4 border-t border-gray-200">
                                <div className="flex items-start gap-4 p-4 rounded-lg bg-gray-50">
                                    <div className="flex-shrink-0"><DeveloperIcon /></div>
                                    <div className="flex-1">
                                        <h3 className="text-base font-semibold text-gray-800 mb-2">For Developers</h3>
                                        <div className="text-sm text-gray-600 leading-relaxed space-y-2">
                                            <p>
                                                <strong>Parsing Process:</strong> The application extracts data lineage from stored procedures using a two-phase approach. First, <strong>regex patterns</strong> provide a guaranteed baseline by scanning DDL for table references. Then, <strong>SQLGlot</strong> (a SQL abstract syntax tree parser) enhances coverage by parsing DML statements when possible.
                                            </p>
                                            <p>
                                                <strong>YAML Rule Engine:</strong> Database-specific syntax that prevents SQLGlot parsing is preprocessed using <strong>YAML-based cleaning rules</strong>. These declarative rules remove dialect-specific constructs (like T-SQL's GO statements or Snowflake's LANGUAGE JAVASCRIPT) while preserving the core lineage information. Power users can extend support to new databases by creating custom YAML rules without writing Python code.
                                            </p>
                                            {onOpenDeveloperPanel && (
                                                <div className="mt-3 pt-3 border-t border-gray-300">
                                                    <button
                                                        onClick={() => {
                                                            onOpenDeveloperPanel();
                                                            onClose();
                                                        }}
                                                        className="inline-flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-800 transition-colors text-sm font-medium"
                                                    >
                                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0021 18V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v12a2.25 2.25 0 002.25 2.25z" />
                                                        </svg>
                                                        <span>Open Developer Panel</span>
                                                    </button>
                                                    <p className="mt-2 text-xs text-gray-500">
                                                        View debug logs, browse YAML rules, and reset rules to defaults
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </main>

                    {/* Footer */}
                    <footer className="px-6 py-4 border-t border-gray-200 flex items-center justify-between flex-shrink-0 bg-gray-50 rounded-b-lg">
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                            <div className="flex items-center gap-1.5">
                                <span>Created by</span>
                                <a
                                    href="https://at.linkedin.com/in/christian-wagner-11aa8614b/de"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 hover:underline font-medium"
                                >
                                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                                    </svg>
                                    Christian Wagner
                                </a>
                            </div>
                            <span className="text-gray-400">•</span>
                            <div className="flex items-center gap-1.5">
                                <span>Built with</span>
                                <a
                                    href="https://claude.ai/code"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 hover:underline font-medium"
                                    title="Claude Code - AI-powered coding assistant"
                                >
                                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" opacity="0.8"/>
                                        <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                    Claude Code
                                </a>
                            </div>
                        </div>
                        <Button onClick={onClose} variant="primary" className="px-6">Got it!</Button>
                    </footer>
                </div>
            </div>
        </>
    );
};
