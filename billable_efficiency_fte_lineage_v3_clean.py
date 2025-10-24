#!/usr/bin/env python3
"""
Data Lineage Diagram: BillableEfficiency FTE Pipeline (Clean Layout)
Generated: 2025-10-24
Target: CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation

CRITICAL STYLING:
- NO blue boxes around object types (no "Tables", "Views", "Stored Procedures" clusters)
- NO outer layer boxes (no "Source Layer", "Transform Layer", "Consumption Layer" clusters)
- ONLY schema-based clusters (DBO, CONSUMPTION_ClinOpsFinance, CONSUMPTION_POWERBI, CONSUMPTION_PRIMA)
- Object names INSIDE the shapes (not as separate labels)
- Objects directly in schema clusters - no nested groupings
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import Action, Delay, Preparation

# Schema color mapping
SCHEMA_COLORS = {
    "DBO": "#EA4335",
    "CONSUMPTION_ClinOpsFinance": "#4285F4",
    "CONSUMPTION_POWERBI": "#34A853",
    "CONSUMPTION_PRIMA": "#FBBC04",
}

# Graph attributes
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.2",
}

node_attr = {
    "fontsize": "11",
    "fontname": "Arial",
    "style": "filled",
    "shape": "box",
}

edge_attr = {
    "fontsize": "9",
    "fontname": "Arial",
}

with Diagram(
    "Data Lineage: BillableEfficiency FTE Pipeline (Clean Layout)",
    show=False,
    direction="LR",
    filename="billable_efficiency_fte_lineage_v3_clean",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    outformat="png",
):

    # ========================================
    # DBO Schema (Source)
    # ========================================
    with Cluster("DBO", graph_attr={"bgcolor": "#FEE", "style": "rounded"}):
        dbo_full_dept_map = Action("Full_Departmental_Map")

    # ========================================
    # CONSUMPTION_PRIMA Schema (Source)
    # ========================================
    with Cluster("CONSUMPTION_PRIMA", graph_attr={"bgcolor": "#FFF9E6", "style": "rounded"}):
        prima_currency = Action("MonthlyAverage\nCurrencyExchangeRate")

    # ========================================
    # CONSUMPTION_POWERBI Schema (Source)
    # ========================================
    with Cluster("CONSUMPTION_POWERBI", graph_attr={"bgcolor": "#E8F5E9", "style": "rounded"}):
        powerbi_labor_cost = Action("FactLaborCostFor\nEarnedValue")

    # ========================================
    # CONSUMPTION_ClinOpsFinance Schema (Transform & Target)
    # All objects directly in schema cluster - NO nested groupings
    # ========================================
    with Cluster("CONSUMPTION_ClinOpsFinance", graph_attr={"bgcolor": "#E3F2FD", "style": "rounded"}):
        # Source tables
        clinops_hr_contract = Action("HrContractAttendance")
        clinops_date_ranges = Action("DateRanges_PM")
        clinops_currency = Action("CURRENCY")
        clinops_cadence_post = Action("CadenceBudgetData_Post")

        # View
        clinops_dept_map_view = Delay("vFull_Departmental\n_Map_ActivePrima")

        # First stored procedure + outputs
        clinops_sp_util = Preparation("spLoadEmployee\nContractUtilization\n_Aggregations")
        clinops_attendance_util = Action("EmployeeAttendance\nExpectedHours\nUtilization_Monthly")
        clinops_employee_fte = Action("EmployeeContract\nFTE_Monthly")

        # FTE aggregation chain
        clinops_avg_fte = Action("AverageContract\nFTE_Monthly")
        clinops_avg_fte_rank = Action("AverageContract\nFTE_Monthly_RankDetail")

        # Labor cost processing
        clinops_sp_labor_post = Preparation("spLoadFactLaborCost\nForEarnedValue_Post")
        clinops_labor_post = Action("FactLaborCostFor\nEarnedValue_Post")

        # Cadence budget processing
        clinops_sp_cadence_agg = Preparation("spLoadCadenceBudget\n_Aggregations")
        clinops_cadence_rank = Action("CadenceBudgetData\n_BillableEfficiency\n_RankDetail")

        # Labor cost aggregations
        clinops_sp_labor_agg = Preparation("spLoadFactLaborCost\nForEarnedValue\n_Aggregations")
        clinops_labor_rank = Action("FactLaborCostFor\nEarnedValue_RankDetail\nlAggregation")

        # Productivity aggregation
        clinops_productivity = Action("BillableEfficiency\n_Productivity\n_RankDetailAggregation")

        # FINAL TARGET
        clinops_final_target = Action("BillableEfficiency\n_Productivity_AverageFTE\n_Monthly_RankDetail\nAggregation")

    # ========================================
    # DATA FLOW RELATIONSHIPS
    # All edges defined outside clusters
    # ========================================

    # DBO -> View
    dbo_full_dept_map >> clinops_dept_map_view

    # Sources -> spLoadEmployeeContractUtilization_Aggregations
    clinops_hr_contract >> clinops_sp_util
    clinops_dept_map_view >> Edge(color="red", style="dashed", penwidth="2.0") >> clinops_sp_util  # Problematic
    clinops_date_ranges >> clinops_sp_util

    # spLoadEmployeeContractUtilization_Aggregations -> Outputs
    clinops_sp_util >> clinops_attendance_util
    clinops_sp_util >> Edge(color="red", style="dashed", penwidth="2.0") >> clinops_employee_fte  # Problematic

    # FTE aggregation chain
    clinops_employee_fte >> clinops_avg_fte
    clinops_avg_fte >> clinops_avg_fte_rank
    clinops_date_ranges >> clinops_avg_fte_rank

    # Labor cost post processing
    powerbi_labor_cost >> clinops_sp_labor_post
    clinops_sp_labor_post >> clinops_labor_post

    # Cadence budget aggregations
    clinops_cadence_post >> clinops_sp_cadence_agg
    clinops_date_ranges >> clinops_sp_cadence_agg
    clinops_sp_cadence_agg >> clinops_cadence_rank

    # Labor cost aggregations
    clinops_labor_post >> clinops_sp_labor_agg
    clinops_date_ranges >> clinops_sp_labor_agg
    clinops_sp_labor_agg >> clinops_labor_rank
    clinops_sp_labor_agg >> clinops_productivity

    # Productivity aggregation
    clinops_cadence_rank >> clinops_productivity

    # Final aggregation inputs -> spLoadEmployeeContractUtilization_Aggregations
    clinops_productivity >> clinops_sp_util
    clinops_avg_fte_rank >> clinops_sp_util
    clinops_currency >> clinops_sp_util

    # Final output
    clinops_sp_util >> clinops_final_target

print("✓ Diagram generated successfully!")
print("✓ Output: billable_efficiency_fte_lineage_v3_clean.png")
print("✓ Styling: FLAT schema clusters with objects directly inside (no type/layer groupings)")
print("✓ Object names: Displayed INSIDE node shapes")
print("✓ Problematic flows: Highlighted with RED DASHED edges")
