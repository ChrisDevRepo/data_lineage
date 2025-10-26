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
    const numNodes = 40;
    let nodes: DataNode[] = Array.from({ length: numNodes }, (_, i) => ({
        id: `node_${i}`,
        name: `${names[i % names.length]}_${i}`,
        schema: schemas[Math.floor(Math.random() * schemas.length)].toUpperCase(),
        object_type: types[Math.floor(Math.random() * types.length)],
        description: descriptions[i % descriptions.length],
        data_model_type: modelTypes[Math.floor(Math.random() * modelTypes.length)],
        inputs: [],
        outputs: []
    }));

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
