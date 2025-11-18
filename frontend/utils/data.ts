import { DataNode } from '../types';

export const generateSampleData = (): DataNode[] => {
    const schemas = ["Sales", "Marketing", "Reporting", "Staging", "Finance", "HR", "Operations", "IT_Support", "Data_Warehouse", "Legacy_System"];
    const types: DataNode['object_type'][] = ["Table", "View", "Stored Procedure"];
    const names = ["DimCustomers", "FactOrders", "v_DimProducts", "spLoadFactCampaigns", "FactLeads", "DailySummary", "WeeklyReport", "spLoadDim_Geography", "EmployeeDetails", "Tickets_TEMP_"];
    const modelTypes: DataNode['data_model_type'][] = ["Dimension", "Fact", "Lookup", "Other"];
    const descriptions = [
        "Contains customer information.", "Transactional order data.", "Product details lookup.",
        "Aggregated campaign performance.", "Marketing lead data.", "Daily sales summary.",
        "Weekly reporting table.", "Geographical dimension data.", "HR employee records.",
        "Temporary IT support tickets."
    ];
    const numNodes = 200; // Doubled to 200 nodes for comprehensive testing
    let nodes: DataNode[] = Array.from({ length: numNodes }, (_, i) => {
        const objectType = types[Math.floor(Math.random() * types.length)];
        const nodeName = `${names[i % names.length]}_${i}`;

        // Add sample DDL for Stored Procedures and Views (for SQL Viewer testing)
        let ddlText: string | null = null;
        if (objectType === 'Stored Procedure') {
            ddlText = `CREATE PROCEDURE [dbo].[${nodeName}]\nAS\nBEGIN\n    -- Sample stored procedure for testing\n    SET NOCOUNT ON;\n    \n    INSERT INTO TargetTable\n    SELECT \n        col1,\n        col2,\n        col3\n    FROM SourceTable\n    WHERE status = 'Active';\n    \n    -- Update statistics\n    UPDATE STATISTICS TargetTable;\nEND`;
        } else if (objectType === 'View') {
            ddlText = `CREATE VIEW [dbo].[${nodeName}]\nAS\n    SELECT \n        t1.id,\n        t1.name,\n        t2.description,\n        t3.category\n    FROM Table1 t1\n    LEFT JOIN Table2 t2 ON t1.id = t2.id\n    LEFT JOIN Table3 t3 ON t1.category_id = t3.id\n    WHERE t1.is_active = 1`;
        }
        // Tables don't have DDL (ddlText remains null)

        return {
            id: `node_${i}`,
            name: nodeName,
            schema: schemas[Math.floor(Math.random() * schemas.length)].toUpperCase(),
            object_type: objectType,
            description: descriptions[i % descriptions.length],
            data_model_type: modelTypes[Math.floor(Math.random() * modelTypes.length)],
            inputs: [],
            outputs: [],
            ddl_text: ddlText
        };
    });

    // Create more realistic lineage chains
    for (let i = 0; i < numNodes * 1.5; i++) {
        const sourceIndex = Math.floor(Math.random() * numNodes);
        const targetIndex = Math.floor(Math.random() * numNodes);

        if (sourceIndex !== targetIndex) {
            const sourceNode = nodes[sourceIndex];
            const targetNode = nodes[targetIndex];
            if (!sourceNode.outputs.includes(targetNode.id) && !targetNode.inputs.includes(sourceNode.id)) {
                sourceNode.outputs.push(targetNode.id);
                targetNode.inputs.push(sourceNode.id);
            }
        }
    }
    return nodes;
};
