export type DataNode = {
  id: string;
  name: string;
  schema: string;
  object_type: 'Table' | 'View' | 'Stored Procedure' | 'Function';
  description?: string;
  data_model_type?: 'Dimension' | 'Fact' | 'Lookup' | 'Other';
  inputs: string[];
  outputs: string[];
  ddl_text?: string | null;  // SQL definition for Views and Stored Procedures (v3.0 SQL Viewer feature)
  node_symbol?: 'circle' | 'diamond' | 'square' | 'question_mark';  // v4.3.0 Phantom Objects
  is_phantom?: boolean;  // v4.3.0 Phantom Objects
  phantom_reason?: string;  // v4.3.0 Phantom Objects
  // Note: confidence scoring removed in v4.3.6 (was circular logic with regex-only parsing)
};

export type TraceConfig = {
  startNodeId: string | null;
  endNodeId?: string | null;  // Optional: if provided, trace path between start and end
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
