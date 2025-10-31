import React from 'react';
import { Button } from './ui/Button';

type InfoModalProps = {
    isOpen: boolean;
    onClose: () => void;
};

// SVG Icons for different sections
const GraphIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500"><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" /></svg>;
const NavIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500"><path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672 13.684 16.6m0 0-2.51 2.225.569-9.47 5.227 7.917-3.286-.672ZM12 2.25V4.5m0 13.5v2.25m0-15.75-1.383-.393a2.25 2.25 0 0 0-2.122 2.122L7.5 7.5m0 9 1.383.393a2.25 2.25 0 0 0 2.122-2.122L12 15.75m0-9-1.383.393a2.25 2.25 0 0 1-2.122-2.122L7.5 7.5m0 9 1.383-.393a2.25 2.25 0 0 1 2.122 2.122L12 15.75m0-15.75 1.383-.393a2.25 2.25 0 0 1 2.122 2.122L16.5 7.5m0 9-1.383.393a2.25 2.25 0 0 1-2.122-2.122L12 15.75m0 0 .569 9.47a2.25 2.25 0 0 1-2.122 2.122L10.5 21.75m2.816-16.5-2.225-2.512a2.25 2.25 0 0 0-2.122-2.122L7.5 4.5M12 15.75l2.225 2.512a2.25 2.25 0 0 0 2.122 2.122l.393 1.383M12 15.75l-2.225 2.512a2.25 2.25 0 0 1-2.122 2.122L6 21.75" /></svg>;
const ViewIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12a7.5 7.5 0 0 0 15 0m-15 0a7.5 7.5 0 1 1 15 0m-15 0H3m18 0h-1.5m-15 0a7.5 7.5 0 1 1 15 0m-15 0H3m18 0h-1.5m-15 0a7.5 7.5 0 1 1 15 0m-15 0H3m18 0h-1.5" /></svg>;
const FilterIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.572a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" /></svg>;
const TraceIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9.75v6.75m-4.5-3.5h9M3.75 12a9 9 0 0 1 18 0v.001a9 9 0 0 1-18 0V12Z" /></svg>;
const ImportExportIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-blue-500"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" /></svg>;

const Feature = ({ icon, title, children }: { icon: React.ReactNode, title: string, children: React.ReactNode }) => (
    <div className="flex items-start gap-4">
        <div className="flex-shrink-0 mt-1">{icon}</div>
        <div>
            <h3 className="text-lg font-bold text-gray-800">{title}</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{children}</p>
        </div>
    </div>
);

export const InfoModal = ({ isOpen, onClose }: InfoModalProps) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl h-auto max-h-[90vh] flex flex-col text-gray-800">
                <header className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-2xl font-bold">Welcome to the Data Lineage Visualizer!</h2>
                    <Button onClick={onClose} variant="icon">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                    </Button>
                </header>
                <main className="flex-grow p-6 overflow-y-auto space-y-6">
                    <p className="text-center text-gray-700 italic">This tool helps you explore and understand the relationships between your data assets.</p>
                    
                    <Feature icon={<GraphIcon />} title="Visualize Lineage">
                        See how data flows from source to destination. Each node represents a data object (like a table or view), and the lines show their connections. Nodes are color-coded by their database schema.
                    </Feature>

                    <Feature icon={<NavIcon />} title="Canvas Navigation">
                        Click and drag to pan across the canvas. Use your mouse wheel or the controls on the left to zoom in and out. Click an object to highlight it and its immediate neighbors, dimming everything else for focus.
                    </Feature>

                    <Feature icon={<ViewIcon />} title="Detail vs. Schema View">
                        Switch between a detailed, object-level graph (<strong>Detail View</strong>) and a high-level overview of dependencies between entire schemas (<strong>Schema View</strong>) using the toggle in the toolbar.
                    </Feature>

                    <Feature icon={<FilterIcon />} title="Search & Filter">
                        Use the toolbar to quickly find any object by name. You can also filter the canvas to show only the schemas or data model types you're interested in, simplifying complex diagrams.
                    </Feature>

                    <Feature icon={<TraceIcon />} title="Interactive Trace">
                        Perform powerful impact and root-cause analysis with the <strong>Start Trace</strong> feature. Select a starting node and trace its lineage upstream (ancestors) or downstream (descendants) to any depth.
                    </Feature>

                    <Feature icon={<ImportExportIcon />} title="Custom Data & Export">
                        Load your own data lineage by clicking the upload icon and providing a JSON file. Once you're happy with your visualization, export it as a clean SVG file for presentations or documentation.
                    </Feature>
                </main>
                <footer className="p-4 border-t flex items-center justify-end flex-shrink-0">
                    <Button onClick={onClose} variant="primary" className="px-6">Got it!</Button>
                </footer>
            </div>
        </div>
    );
};
