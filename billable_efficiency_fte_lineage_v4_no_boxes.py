#!/usr/bin/env python3
"""
Data Lineage Diagram: FTE Pipeline (Clean Layout)
Generated: 2025-10-24
Target: CONSUMPTION_ClinOpsFinance.BillableEfficiency_Productivity_AverageFTE_Monthly_RankDetailAggregation
"""

from diagrams import Diagram, Edge
from diagrams.programming.flowchart import Action, Delay, Preparation

# Graph attributes for clean appearance
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "nodesep": "0.8",
    "ranksep": "1.2",
}

node_attr = {
    "fontsize": "11",
    "height": "0.8",
    "width": "1.5",
}

edge_attr = {
    "fontsize": "9",
}

with Diagram(
    "Data Lineage: FTE Pipeline (Clean Layout)",
    show=False,
    direction="LR",
    filename="billable_efficiency_fte_lineage_v4_no_boxes",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):

    # ========================================
    # ALL NODES AT ROOT LEVEL - NO CLUSTERS
    # ========================================

    # DBO Schema Objects
    dbo_dept = Action("Full_Departmental\n_Map")

    # CONSUMPTION_PRIMA Schema Objects
    prima_currency = Action("MonthlyAverage\nCurrencyExchange\nRate")

    # CONSUMPTION_POWERBI Schema Objects
    powerbi_labor = Action("FactLaborCost\nForEarnedValue")

    # CONSUMPTION_ClinOpsFinance Schema Objects (21 objects)
    clinops_hr = Action("HrContract\nAttendance")
    clinops_view = Delay("vFull_Departmental\n_Map_ActivePrima")
    clinops_dateranges = Action("DateRanges_PM")
    clinops_currency = Action("CURRENCY")
    clinops_cadence_post = Action("CadenceBudget\nData_Post")

    # Stored Procedures
    clinops_sp1 = Preparation("spLoadEmployee\nContractUtilization\n_Aggregations")
    clinops_sp2 = Preparation("spLoadFactLaborCost\nForEarnedValue_Post")
    clinops_sp3 = Preparation("spLoadCadence\nBudget_Aggregations")
    clinops_sp4 = Preparation("spLoadFactLaborCost\nForEarnedValue\n_Aggregations")

    # Tables - Employee Utilization Pipeline
    clinops_emp_attendance = Action("EmployeeAttendance\nExpectedHours\nUtilization_Monthly")
    clinops_emp_fte = Action("EmployeeContract\nFTE_Monthly")
    clinops_avg_fte = Action("AverageContract\nFTE_Monthly")
    clinops_avg_fte_rank = Action("AverageContract\nFTE_Monthly\n_RankDetail")

    # Tables - Labor Cost Pipeline
    clinops_labor_post = Action("FactLaborCost\nForEarnedValue_Post")
    clinops_labor_rank = Action("FactLaborCost\nForEarnedValue\n_RankDetaillAggregation")

    # Tables - Cadence Budget Pipeline
    clinops_cadence_rank = Action("CadenceBudgetData\n_BillableEfficiency\n_RankDetail")

    # Tables - Final Aggregations
    clinops_billable_rank = Action("BillableEfficiency\n_Productivity\n_RankDetailAggregation")
    clinops_target = Action("BillableEfficiency\n_Productivity\n_AverageFTE_Monthly\n_RankDetailAggregation")

    # ========================================
    # DATA FLOW RELATIONSHIPS WITH COLORED EDGES
    # ========================================

    # --- FLOW 1: DBO to ClinOps View ---
    dbo_dept >> Edge(color="firebrick", label="DBO") >> clinops_view

    # --- FLOW 2: Employee Utilization Pipeline ---
    # Multiple sources to SP1
    clinops_hr >> Edge(color="darkblue") >> clinops_sp1
    clinops_dateranges >> Edge(color="darkblue") >> clinops_sp1

    # PROBLEMATIC FLOW 1: View to SP1
    clinops_view >> Edge(color="red", style="dashed", penwidth="2.5", label="ISSUE") >> clinops_sp1

    # SP1 outputs
    clinops_sp1 >> Edge(color="darkblue") >> clinops_emp_attendance

    # PROBLEMATIC FLOW 2: SP1 to EmployeeContractFTE_Monthly
    clinops_sp1 >> Edge(color="red", style="dashed", penwidth="2.5", label="ISSUE") >> clinops_emp_fte

    # EmployeeContractFTE_Monthly to Average FTE pipeline
    clinops_emp_fte >> Edge(color="darkblue") >> clinops_avg_fte
    clinops_avg_fte >> Edge(color="darkblue") >> clinops_avg_fte_rank

    # --- FLOW 3: Labor Cost Pipeline ---
    # PowerBI source to SP2
    powerbi_labor >> Edge(color="darkgreen", label="POWERBI") >> clinops_sp2

    # Prima currency to SP2
    prima_currency >> Edge(color="darkorange", label="PRIMA") >> clinops_sp2

    # SP2 output
    clinops_sp2 >> Edge(color="darkblue") >> clinops_labor_post

    # Labor Post to SP4
    clinops_labor_post >> Edge(color="darkblue") >> clinops_sp4

    # SP4 output
    clinops_sp4 >> Edge(color="darkblue") >> clinops_labor_rank

    # --- FLOW 4: Cadence Budget Pipeline ---
    # Cadence Post to SP3
    clinops_cadence_post >> Edge(color="darkblue") >> clinops_sp3

    # Currency to SP3
    clinops_currency >> Edge(color="darkblue") >> clinops_sp3

    # SP3 output
    clinops_sp3 >> Edge(color="darkblue") >> clinops_cadence_rank

    # --- FLOW 5: Final Aggregation to Target ---
    # Three ranked tables converge to BillableEfficiency aggregation
    clinops_labor_rank >> Edge(color="darkblue") >> clinops_billable_rank
    clinops_cadence_rank >> Edge(color="darkblue") >> clinops_billable_rank
    clinops_avg_fte_rank >> Edge(color="darkblue") >> clinops_billable_rank

    # Final flow to target
    clinops_billable_rank >> Edge(color="darkblue", penwidth="2.5") >> clinops_target

print("✓ Diagram generated successfully!")
print("✓ Output: billable_efficiency_fte_lineage_v4_no_boxes.png")
print("✓ Layout: Clean (no cluster boxes)")
print("✓ Total objects: 26")
print("✓ Schemas represented: 4 (DBO, CONSUMPTION_PRIMA, CONSUMPTION_POWERBI, CONSUMPTION_ClinOpsFinance)")
print("✓ Problematic flows highlighted: 2 (red dashed edges)")
