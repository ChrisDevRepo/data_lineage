import React, { useState, useEffect, useMemo, useRef } from 'react';
import { DataNode } from '../types';

type ImportDataModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onImport: (data: DataNode[]) => void;
    currentData: DataNode[];
    defaultSampleData: DataNode[];
};

type ValidationResult = {
    errors: string[];
    warnings: string[];
};

const validateAndCleanData = (nodes: any[]): { data: DataNode[], errors: string[], warnings: string[] } => {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!Array.isArray(nodes)) {
        return { data: [], errors: ["Import failed: Data must be a JSON array."], warnings: [] };
    }

    const nodeMap = new Map<string, any>();
    nodes.forEach((node, index) => {
        if (typeof node !== 'object' || node === null) {
            warnings.push(`Item at index ${index} is not a valid object and was ignored.`);
            return;
        }
        if (!node.id || typeof node.id !== 'string') {
            warnings.push(`Item at index ${index} is missing a valid 'id' and was ignored.`);
            return;
        }
        if (nodeMap.has(node.id)) {
            warnings.push(`Duplicate node ID "${node.id}" found. Using last definition.`);
        }
        nodeMap.set(node.id, node);
    });

    const uniqueNodes = Array.from(nodeMap.values());
    const validNodeIds = new Set(uniqueNodes.map(n => n.id));
    const finalNodes: DataNode[] = [];

    uniqueNodes.forEach((node, index) => {
        const nodeId = `(ID: ${node.id})`;
        const requiredFields = ['name', 'schema', 'object_type', 'inputs', 'outputs'];
        const missingFields = requiredFields.filter(f => !(f in node));
        if (missingFields.length > 0) {
            errors.push(`Node ${nodeId} is missing required fields: ${missingFields.join(', ')}.`);
            return;
        }
        if (typeof node.name !== 'string' || typeof node.schema !== 'string' || typeof node.object_type !== 'string') {
            errors.push(`Node ${nodeId} has invalid data types for name, schema, or object_type.`);
        }
        if (!["Table", "View", "Stored Procedure"].includes(node.object_type)) {
            errors.push(`Node ${nodeId} has an invalid 'object_type': "${node.object_type}".`);
        }
        if (!Array.isArray(node.inputs) || !Array.isArray(node.outputs)) {
            errors.push(`Node ${nodeId} 'inputs' and 'outputs' must be arrays.`);
            return;
        }

        const cleanInputs = node.inputs.filter((id: any) => {
            const isValid = typeof id === 'string' && validNodeIds.has(id);
            if (!isValid) warnings.push(`Node ${nodeId} has an invalid or non-existent input ID "${id}". It was removed.`);
            return isValid;
        });
        const cleanOutputs = node.outputs.filter((id: any) => {
            const isValid = typeof id === 'string' && validNodeIds.has(id);
            if (!isValid) warnings.push(`Node ${nodeId} has an invalid or non-existent output ID "${id}". It was removed.`);
            return isValid;
        });

        finalNodes.push({ ...node, inputs: cleanInputs, outputs: cleanOutputs });
    });
    
    if (errors.length > 0) return { data: [], errors, warnings };

    const finalNodeMap = new Map<string, DataNode>(finalNodes.map(n => [n.id, n]));
    finalNodes.forEach(node => {
        node.outputs.forEach(outputId => {
            const targetNode = finalNodeMap.get(outputId);
            if (targetNode && !targetNode.inputs.includes(node.id)) {
                targetNode.inputs.push(node.id);
                warnings.push(`Auto-fixed: Added missing input from "${node.name}" to "${targetNode.name}".`);
            }
        });
        node.inputs.forEach(inputId => {
            const sourceNode = finalNodeMap.get(inputId);
            if (sourceNode && !sourceNode.outputs.includes(node.id)) {
                sourceNode.outputs.push(node.id);
                warnings.push(`Auto-fixed: Added missing output from "${sourceNode.name}" to "${node.name}".`);
            }
        });
    });

    return { data: Array.from(finalNodeMap.values()), errors, warnings };
};

export const ImportDataModal = ({ isOpen, onClose, onImport, currentData, defaultSampleData }: ImportDataModalProps) => {
    const [jsonText, setJsonText] = useState('');
    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [view, setView] = useState<'sample' | 'definition'>('sample');
    const importFileRef = useRef<HTMLInputElement>(null);
    const defaultSampleString = useMemo(() => JSON.stringify(defaultSampleData, null, 2), [defaultSampleData]);

    useEffect(() => {
        if (isOpen) {
            setJsonText(JSON.stringify(currentData, null, 2));
            setValidationResult(null);
        }
    }, [isOpen, currentData]);

    if (!isOpen) return null;

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => setJsonText(e.target?.result as string);
            reader.readAsText(file);
        }
    };
    
    const handleApply = () => {
        let parsedData;
        try {
            parsedData = JSON.parse(jsonText);
        } catch (err) {
            setValidationResult({ errors: ["Invalid JSON format. Please check for syntax errors."], warnings: [] });
            return;
        }

        const { data, errors, warnings } = validateAndCleanData(parsedData);
        setValidationResult({ errors, warnings });
        
        if (errors.length === 0) {
            onImport(data);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl h-[90vh] flex flex-col text-gray-800">
                <header className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-xl font-bold">Import & Edit Data</h2>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                    </button>
                </header>
                <main className="flex-grow p-4 grid grid-cols-1 md:grid-cols-2 gap-4 overflow-hidden">
                    <div className="flex flex-col gap-2">
                        <label className="font-semibold">Edit current data or paste new JSON:</label>
                        <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} className="w-full flex-grow border rounded-md p-2 font-mono text-sm bg-gray-50 resize-none" spellCheck="false" />
                        <div className="flex items-center gap-2">
                            <input type="file" ref={importFileRef} onChange={handleFileChange} accept=".json" className="hidden" />
                            <button onClick={() => importFileRef.current?.click()} className="px-3 py-1.5 text-sm font-semibold bg-gray-200 hover:bg-gray-300 rounded-md">Upload File</button>
                            <button onClick={() => setJsonText(defaultSampleString)} className="px-3 py-1.5 text-sm font-semibold bg-gray-200 hover:bg-gray-300 rounded-md">Load Sample Data</button>
                        </div>
                    </div>
                    <div className="flex flex-col gap-2 overflow-hidden">
                        <div className="flex items-center justify-between">
                            <label className="font-semibold">{view === 'sample' ? 'Default Sample Data (read-only):' : 'Data Contract Definition:'}</label>
                            <button onClick={() => setView(v => v === 'sample' ? 'definition' : 'sample')} className="px-3 py-1 text-sm font-semibold text-blue-600 hover:bg-blue-100 rounded-md">
                                {view === 'sample' ? 'Show Definition' : 'Show Sample Data'}
                            </button>
                        </div>
                        <div className="flex-grow bg-gray-100 rounded-md p-3 overflow-y-auto text-sm">
                            {view === 'sample' ? (
                                <pre className="font-mono whitespace-pre-wrap break-all"><code>{defaultSampleString}</code></pre>
                            ) : (
                                <div className="space-y-3 text-gray-700">
                                    <p className="text-gray-800 font-medium">The lineage data must be a JSON array of node objects. Each object represents a data asset and should conform to the structure below:</p>
                                    <ul className="space-y-2 list-none p-0 font-mono">
                                        <li><strong><code>id</code></strong>: <span className="text-red-600 font-semibold">string, required</span><br/><span className="pl-4 text-gray-600 font-sans">A unique identifier for the node.</span></li>
                                        <li><strong><code>name</code></strong>: <span className="text-red-600 font-semibold">string, required</span><br/><span className="pl-4 text-gray-600 font-sans">The display name of the object.</span></li>
                                        <li><strong><code>schema</code></strong>: <span className="text-red-600 font-semibold">string, required</span><br/><span className="pl-4 text-gray-600 font-sans">The database schema.</span></li>
                                        <li><strong><code>object_type</code></strong>: <span className="text-red-600 font-semibold">string, required</span><br/><span className="pl-4 text-gray-600 font-sans">Must be one of: <code>"Table"</code>, <code>"View"</code>, <code>"Stored Procedure"</code>.</span></li>
                                        <li><strong><code>description</code></strong>: <span className="text-green-600 font-semibold">string, optional</span><br/><span className="pl-4 text-gray-600 font-sans">A brief description of the node's purpose.</span></li>
                                        <li><strong><code>data_model_type</code></strong>: <span className="text-green-600 font-semibold">string, optional</span><br/><span className="pl-4 text-gray-600 font-sans">Role in the data model, e.g., <code>"Dimension"</code>, <code>"Fact"</code>, <code>"Lookup"</code>, <code>"Other"</code>.</span></li>
                                        <li><strong><code>inputs</code></strong>: <span className="text-red-600 font-semibold">array of strings, required</span><br/><span className="pl-4 text-gray-600 font-sans">An array of <code>id</code>s that are sources for this node.</span></li>
                                        <li><strong><code>outputs</code></strong>: <span className="text-red-600 font-semibold">array of strings, required</span><br/><span className="pl-4 text-gray-600 font-sans">An array of <code>id</code>s that are targets for this node.</span></li>
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                </main>
                {validationResult && (
                    <div className="flex-shrink-0 p-4 border-t max-h-48 overflow-y-auto">
                        <h3 className="font-bold text-lg mb-2">Validation Results</h3>
                        {validationResult.errors.length > 0 && (
                            <div className="mb-2">
                                <h4 className="font-semibold text-red-600">Errors (must be fixed to import):</h4>
                                <ul className="list-disc list-inside text-sm text-red-700 bg-red-50 p-2 rounded-md">
                                    {validationResult.errors.map((e, i) => <li key={`err-${i}`}>{e}</li>)}
                                </ul>
                            </div>
                        )}
                        {validationResult.warnings.length > 0 && (
                            <div>
                                <h4 className="font-semibold text-yellow-600">Warnings (auto-fixed):</h4>
                                <ul className="list-disc list-inside text-sm text-yellow-800 bg-yellow-50 p-2 rounded-md">
                                    {validationResult.warnings.map((w, i) => <li key={`warn-${i}`}>{w}</li>)}
                                </ul>
                            </div>
                        )}
                         {validationResult.errors.length === 0 && validationResult.warnings.length === 0 && (
                             <p className="text-sm text-green-700">Validation passed successfully!</p>
                         )}
                    </div>
                )}
                <footer className="p-4 border-t flex items-center justify-end flex-shrink-0">
                    <div className="flex items-center gap-2">
                        <button onClick={onClose} className="h-10 px-4 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-lg text-sm">Cancel</button>
                        <button onClick={handleApply} className="h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-sm">Apply Changes</button>
                    </div>
                </footer>
            </div>
        </div>
    );
};
