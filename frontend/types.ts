export type DataNode = {
  id: string;
  name: string;
  schema: string;
  object_type: 'Table' | 'View' | 'Stored Procedure' | 'Function';
  description?: string;
  data_model_type?: 'Dimension' | 'Fact' | 'Lookup' | 'Other';
  inputs: string[];
  outputs: string[];
  bidirectional_with?: string[]; // v4.4.0: Pre-computed bidirectional pairs from DuckDB
  ddl_text?: string | null; // SQL definition for Views and Stored Procedures (v3.0 SQL Viewer feature)
  node_symbol?: 'circle' | 'diamond' | 'square' | 'question_mark';
  // Note: confidence scoring removed in v4.3.6 (was circular logic with regex-only parsing)
};

export type TraceConfig = {
  startNodeId: string | null;
  endNodeId?: string | null; // Optional: if provided, trace path between start and end
  upstreamLevels: number;
  downstreamLevels: number;
  includedSchemas: Set<string>;
  includedTypes: Set<string>;
  exclusionPatterns: string[];
};

export type Notification = {
  id: number;
  text: string;
  type: 'info' | 'error';
};
