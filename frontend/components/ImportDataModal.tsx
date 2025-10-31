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

type UploadMode = 'json' | 'parquet';

type JobStatus = {
    job_id: string;
    status: 'processing' | 'completed' | 'error' | 'failed' | 'not_found';
    progress: number;
    message: string;
    started_at?: string;
    completed_at?: string;
    elapsed_seconds?: number;
    errors?: string[];
    warnings?: string[];
    stats?: {
        total_objects: number;
        high_confidence: number;
        medium_confidence: number;
        low_confidence: number;
    };
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
    // JSON import state
    const [jsonText, setJsonText] = useState('');
    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [view, setView] = useState<'sample' | 'definition'>('sample');
    const importFileRef = useRef<HTMLInputElement>(null);
    const defaultSampleString = useMemo(() => JSON.stringify(defaultSampleData, null, 2), [defaultSampleData]);

    // Parquet upload state
    const [uploadMode, setUploadMode] = useState<UploadMode>('json');
    const [isProcessing, setIsProcessing] = useState(false);
    const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
    const parquetFilesRef = useRef<HTMLInputElement>(null);

    // Metadata state
    const [lastUploadDate, setLastUploadDate] = useState<string | null>(null);
    const [isClearing, setIsClearing] = useState(false);

    // Incremental parsing state
    const [useIncremental, setUseIncremental] = useState(true);

    useEffect(() => {
        if (isOpen) {
            setJsonText(JSON.stringify(currentData, null, 2));
            setValidationResult(null);
            setJobStatus(null);
            // Fetch metadata when modal opens
            fetchMetadata();
        }
    }, [isOpen, currentData]);

    const fetchMetadata = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/metadata');
            const metadata = await response.json();
            if (metadata.available) {
                setLastUploadDate(metadata.upload_timestamp_human);
            } else {
                setLastUploadDate(null);
            }
        } catch (error) {
            console.error('Failed to fetch metadata:', error);
            setLastUploadDate(null);
        }
    };

    if (!isOpen) return null;

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file size (10MB limit for JSON)
            const fileSizeInMB = file.size / (1024 * 1024);
            if (fileSizeInMB > 10) {
                setValidationResult({
                    errors: [`JSON file too large (${fileSizeInMB.toFixed(1)}MB > 10MB). Use Parquet upload for large datasets.`],
                    warnings: []
                });
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => setJsonText(e.target?.result as string);
            reader.readAsText(file);
        }
    };

    const handleApply = async () => {
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
            // Auto-delete DuckDB workspace before importing JSON
            try {
                await fetch('http://localhost:8000/api/clear-data', { method: 'DELETE' });
            } catch (err) {
                console.warn('Failed to clear backend data:', err);
                // Continue anyway - JSON mode doesn't strictly need backend
            }

            onImport(data);
        }
    };

    // Parquet upload handler
    const handleParquetUpload = async () => {
        const files = parquetFilesRef.current?.files;

        if (!files || files.length === 0) {
            setJobStatus({
                job_id: '',
                status: 'error',
                progress: 0,
                message: 'Please select Parquet files to upload',
                errors: ['No files selected']
            });
            return;
        }

        setIsProcessing(true);
        setJobStatus({
            job_id: '',
            status: 'processing',
            progress: 0,
            message: 'Uploading files...'
        });

        try {
            // Upload all selected files with incremental flag
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }

            // Add incremental flag as query parameter
            const url = useIncremental
                ? 'http://localhost:8000/api/upload-parquet?incremental=true'
                : 'http://localhost:8000/api/upload-parquet?incremental=false';

            const uploadResponse = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (!uploadResponse.ok) {
                throw new Error(`Upload failed: ${uploadResponse.statusText}`);
            }

            const { job_id } = await uploadResponse.json();

            // Start polling for status
            await pollJobStatus(job_id);

        } catch (error) {
            setJobStatus({
                job_id: '',
                status: 'error',
                progress: 0,
                message: `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
                errors: [error instanceof Error ? error.message : 'Unknown error']
            });
            setIsProcessing(false);
        }
    };

    // Poll for job status
    const pollJobStatus = async (job_id: string) => {
        const startTime = Date.now();
        const pollInterval = 2000; // 2 seconds
        const maxDuration = 300000; // 5 minutes

        const poll = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/status/${job_id}`);
                const status: JobStatus = await response.json();

                // Calculate elapsed time
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const elapsedText = `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;

                setJobStatus({
                    ...status,
                    message: `${status.message} (${elapsedText})`
                });

                // Check if complete
                if (status.status === 'completed') {
                    // Fetch result
                    const resultResponse = await fetch(`http://localhost:8000/api/result/${job_id}`);
                    const result = await resultResponse.json();

                    // Extract data array from response
                    const lineageData: DataNode[] = result.data || result;

                    // Import data
                    onImport(lineageData);

                    // Refresh metadata after successful upload
                    await fetchMetadata();

                    // Close modal
                    setIsProcessing(false);
                    onClose();
                    return;
                }

                // Check if error or failed
                if (status.status === 'error' || status.status === 'failed') {
                    // Show the error to user
                    setJobStatus({
                        ...status,
                        errors: status.errors || [status.message]
                    });
                    setIsProcessing(false);
                    return;
                }

                // Check timeout
                if (Date.now() - startTime > maxDuration) {
                    setJobStatus({
                        job_id,
                        status: 'error',
                        progress: status.progress,
                        message: 'Processing timeout (>5 minutes)',
                        errors: ['The job took too long to complete. Please try again with a smaller dataset.']
                    });
                    setIsProcessing(false);
                    return;
                }

                // Continue polling
                setTimeout(poll, pollInterval);

            } catch (error) {
                setJobStatus({
                    job_id,
                    status: 'error',
                    progress: 0,
                    message: `Polling error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                    errors: [error instanceof Error ? error.message : 'Unknown error']
                });
                setIsProcessing(false);
            }
        };

        // Start polling
        poll();
    };

    // Clear all data handler
    const handleClearData = async () => {
        if (!confirm('Are you sure you want to clear all data? This will delete all DuckDB workspaces and JSON files. This action cannot be undone.')) {
            return;
        }

        setIsClearing(true);

        try {
            const response = await fetch('http://localhost:8000/api/clear-data', {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Clear failed: ${response.statusText}`);
            }

            const result = await response.json();

            alert(`Success: ${result.message}\n\nCleared items:\n- ${result.items_cleared.join('\n- ')}`);

            // Reset metadata
            setLastUploadDate(null);

            // Clear current data in the app
            onImport([]);

        } catch (error) {
            alert(`Failed to clear data: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setIsClearing(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl h-[90vh] flex flex-col text-gray-800">
                <header className="p-4 border-b">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-xl font-bold">Import Data</h2>
                        <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200" disabled={isProcessing}>
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                    {/* Tab selector */}
                    <div className="flex gap-2">
                        <button
                            className={`px-4 py-2 font-semibold rounded-lg transition-colors ${
                                uploadMode === 'json'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                            onClick={() => setUploadMode('json')}
                            disabled={isProcessing}
                        >
                            Import JSON
                        </button>
                        <button
                            className={`px-4 py-2 font-semibold rounded-lg transition-colors ${
                                uploadMode === 'parquet'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                            onClick={() => setUploadMode('parquet')}
                            disabled={isProcessing}
                        >
                            Upload Parquet Files
                        </button>
                    </div>
                </header>

                {/* Content area - conditionally render based on upload mode */}
                {uploadMode === 'json' ? (
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
                ) : (
                    <main className="flex-grow p-4 overflow-y-auto">
                        <div className="max-w-2xl mx-auto space-y-4">
                            {/* Last upload info banner */}
                            {lastUploadDate && (
                                <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-green-900">Data Available</p>
                                        <p className="text-xs text-green-700">Last upload: {lastUploadDate}</p>
                                    </div>
                                    <button
                                        onClick={handleClearData}
                                        disabled={isClearing || isProcessing}
                                        className={`px-3 py-1.5 text-sm font-semibold rounded-lg transition-colors ${
                                            isClearing || isProcessing
                                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                : 'bg-red-600 text-white hover:bg-red-700'
                                        }`}
                                    >
                                        {isClearing ? 'Clearing...' : 'Clear All Data'}
                                    </button>
                                </div>
                            )}

                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h3 className="font-semibold text-blue-900 mb-3">Upload Parquet Files</h3>
                                <p className="text-sm text-blue-800 mb-3">
                                    Upload Parquet files generated by the PySpark DMV Extractor notebook.
                                </p>
                                <div className="text-xs text-blue-800 mb-2">
                                    <strong>Required DMV queries to execute:</strong>
                                    <ul className="list-disc list-inside mt-1 ml-2 space-y-0.5">
                                        <li>sys.objects - Database object metadata</li>
                                        <li>sys.sql_expression_dependencies - View/function dependencies</li>
                                        <li>sys.sql_modules - Object DDL definitions</li>
                                    </ul>
                                </div>
                                <div className="text-xs text-blue-700">
                                    <strong>Optional (recommended):</strong>
                                    <ul className="list-disc list-inside mt-1 ml-2 space-y-0.5">
                                        <li>Query execution logs - For validation (0.85 → 0.95 confidence boost)</li>
                                        <li>sys.columns + sys.types - For table structure visualization</li>
                                    </ul>
                                </div>
                            </div>

                            {/* Incremental parsing option */}
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <label className="flex items-start gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={useIncremental}
                                        onChange={(e) => setUseIncremental(e.target.checked)}
                                        disabled={isProcessing}
                                        className="mt-1 w-4 h-4 text-green-600 rounded focus:ring-green-500"
                                    />
                                    <div className="flex-1">
                                        <div className="font-semibold text-green-900">
                                            Incremental Parsing (Recommended)
                                        </div>
                                        <p className="text-sm text-green-800 mt-1">
                                            Only re-parse objects that have been modified since the last upload. This is much faster for small updates.
                                        </p>
                                        <p className="text-xs text-green-700 mt-2">
                                            <strong>How it works:</strong> Compares modification dates and only processes changed stored procedures, new tables, or low-confidence objects. First upload always processes everything.
                                        </p>
                                    </div>
                                </label>
                            </div>

                            {/* Note about mode */}
                            {!useIncremental && (
                                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                    <p className="text-sm text-yellow-900">
                                        <strong>Full Refresh Mode:</strong> All objects will be re-parsed regardless of modification status. This may take longer but ensures complete re-analysis.
                                    </p>
                                </div>
                            )}

                            {/* Single multi-file input */}
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors">
                                <input
                                    type="file"
                                    ref={parquetFilesRef}
                                    accept=".parquet"
                                    multiple
                                    disabled={isProcessing}
                                    className="w-full"
                                />
                                <p className="text-sm text-gray-600 mt-2">
                                    Select 3-5 Parquet files (Ctrl/Cmd+Click to select multiple)
                                </p>
                            </div>

                            {/* Upload button */}
                            <button
                                onClick={handleParquetUpload}
                                disabled={isProcessing}
                                className={`w-full py-3 px-4 font-semibold rounded-lg transition-colors ${
                                    isProcessing
                                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                        : 'bg-blue-600 text-white hover:bg-blue-700'
                                }`}
                            >
                                {isProcessing ? 'Processing...' : 'Upload & Parse'}
                            </button>

                            {/* Processing status */}
                            {isProcessing && jobStatus && (
                                <div className="border rounded-lg p-4 bg-gray-50">
                                    <div className="mb-3">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="font-semibold">Progress</span>
                                            <span className="text-sm font-mono">{jobStatus.progress}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                                            <div
                                                className="bg-blue-600 h-3 transition-all duration-300 rounded-full"
                                                style={{ width: `${jobStatus.progress}%` }}
                                            />
                                        </div>
                                    </div>
                                    <p className="text-sm text-gray-700">{jobStatus.message}</p>
                                    {jobStatus.stats && (
                                        <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                                            <div className="bg-green-100 rounded p-2 text-center">
                                                <div className="font-bold text-green-800">{jobStatus.stats.high_confidence}</div>
                                                <div className="text-green-700">High Confidence</div>
                                            </div>
                                            <div className="bg-yellow-100 rounded p-2 text-center">
                                                <div className="font-bold text-yellow-800">{jobStatus.stats.medium_confidence}</div>
                                                <div className="text-yellow-700">Medium</div>
                                            </div>
                                            <div className="bg-orange-100 rounded p-2 text-center">
                                                <div className="font-bold text-orange-800">{jobStatus.stats.low_confidence}</div>
                                                <div className="text-orange-700">Low</div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Errors */}
                            {jobStatus && jobStatus.errors && jobStatus.errors.length > 0 && (
                                <div className="border border-red-200 rounded-lg p-4 bg-red-50">
                                    <h4 className="font-semibold text-red-900 mb-2">❌ Errors:</h4>
                                    <ul className="list-disc list-inside text-sm text-red-800 space-y-1">
                                        {jobStatus.errors.map((err, i) => (
                                            <li key={i}>{err}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Warnings */}
                            {jobStatus && jobStatus.warnings && jobStatus.warnings.length > 0 && (
                                <div className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
                                    <h4 className="font-semibold text-yellow-900 mb-2">⚠️ Warnings:</h4>
                                    <ul className="list-disc list-inside text-sm text-yellow-800 space-y-1">
                                        {jobStatus.warnings.map((warn, i) => (
                                            <li key={i}>{warn}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </main>
                )}

                {/* Validation results - only show in JSON mode */}
                {uploadMode === 'json' && validationResult && (
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

                {/* Footer - only show for JSON mode */}
                {uploadMode === 'json' && (
                    <footer className="p-4 border-t flex items-center justify-end flex-shrink-0">
                        <div className="flex items-center gap-2">
                            <button onClick={onClose} className="h-10 px-4 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-lg text-sm">Cancel</button>
                            <button onClick={handleApply} className="h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-sm">Apply Changes</button>
                        </div>
                    </footer>
                )}
            </div>
        </div>
    );
};
