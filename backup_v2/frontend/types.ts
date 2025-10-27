export type DataNode = {
  id: string;
  name: string;
  schema: string;
  object_type: 'Table' | 'View' | 'Stored Procedure';
  description?: string;
  data_model_type?: 'Dimension' | 'Fact' | 'Lookup' | 'Other';
  inputs: string[];
  outputs:string[];
};

export type TraceConfig = {
  startNodeId: string | null;
  upstreamLevels: number;
  downstreamLevels: number;
  includedSchemas: Set<string>;
  exclusionPatterns: string[];
};

export type Notification = {
  id: number;
  text: string;
  type: 'info' | 'error';
};
