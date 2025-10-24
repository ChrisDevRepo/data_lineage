#!/usr/bin/env python3
"""
Data Lineage Diagram: BillableEfficiency FTE Aggregation Pipeline
Generated: 2025-10-24
Purpose: Visualize data flow and identify double-counting issues in FTE aggregation
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import Action, Delay, Preparation

# Define edge styles
normal_edge = Edge(color="black", style="solid")
problem_edge = Edge(color="red", style="dashed", penwidth="2.5")

# Graph attributes
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "splines": "ortho",
    "nodesep": "0.5",
    "ranksep": "1.0",
}

node_attr = {
    "fontsize": "10",
    "shape": "box",
    "style": "rounded,filled",
    "fillcolor": "lightblue",
}

edge_attr = {
    "fontsize": "9",
}

with Diagram(
    "Data Lineage: BillableEfficiency FTE Aggregation Pipeline",
    show=False,
    direction="LR",
    filename="billable_efficiency_fte_lineage",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):

    # Layer 0: Source Tables
    with Cluster("Layer 0: Sources"):
        full_dept_map = Action("Full_Departmental_Map\n(DBO)")
        hr_contract = Action("HrContractAttendance")
        dept_map_view = Delay("vFull_Departmental\n_Map_ActivePrima\n(VIEW)")
        dateranges = Action("DateRanges_PM")
        currency = Action("CURRENCY")
        cadence_budget_post = Action("CadenceBudgetData_Post")
        fact_labor_powerbi = Action("FactLaborCost\nForEarnedValue\n(POWERBI)")
        currency_rate = Action("MonthlyAverage\nCurrencyExchangeRate\n(PRIMA)")

    # Layer 1: FTE Aggregations (PROBLEMATIC)
    with Cluster("Layer 1: FTE Aggregations (PROBLEMATIC)"):
        sp_emp_util = Preparation("spLoadEmployee\nContractUtilization\n_Aggregations")
        emp_attendance = Action("EmployeeAttendance\nExpectedHours\nUtilization_Monthly")
        emp_fte_monthly = Action("EmployeeContract\nFTE_Monthly")
        avg_fte_monthly = Action("AverageContract\nFTE_Monthly")
        avg_fte_rank = Action("AverageContractFTE\n_Monthly_RankDetail")

    # Layer 2: Labor Cost Staging
    with Cluster("Layer 2: Labor Cost Staging"):
        sp_labor_post = Preparation("spLoadFactLaborCost\nForEarnedValue_Post")
        fact_labor_post = Action("FactLaborCost\nForEarnedValue_Post")

    # Layer 3: Budget Aggregations
    with Cluster("Layer 3: Budget Aggregations"):
        sp_budget_agg = Preparation("spLoadCadenceBudget\n_Aggregations")
        budget_rank = Action("CadenceBudgetData\n_BillableEfficiency\n_RankDetail")

    # Layer 4: Labor Cost & Productivity Aggregations
    with Cluster("Layer 4: Labor Cost & Productivity"):
        sp_labor_agg = Preparation("spLoadFactLaborCost\nForEarnedValue\n_Aggregations")
        fact_labor_rank = Action("FactLaborCost\nForEarnedValue\n_RankDetailAggregation")
        billable_prod_rank = Action("BillableEfficiency\n_Productivity\n_RankDetailAggregation")

    # Layer 5: Final Target
    with Cluster("Layer 5: Final Target (INFLATED FTE)"):
        final_target = Action("BillableEfficiency\n_Productivity_AverageFTE\n_Monthly_RankDetail\nAggregation\n(TARGET)")

    # Define relationships

    # Layer 0 -> Layer 1 relationships
    full_dept_map >> normal_edge >> dept_map_view
    hr_contract >> normal_edge >> sp_emp_util
    dept_map_view >> problem_edge >> sp_emp_util  # PROBLEMATIC - Department mapping issue
    dateranges >> normal_edge >> sp_emp_util

    # Layer 1 internal flows
    sp_emp_util >> normal_edge >> emp_attendance
    sp_emp_util >> problem_edge >> emp_fte_monthly  # PROBLEMATIC - Creates inflated FTE
    emp_fte_monthly >> normal_edge >> avg_fte_monthly
    avg_fte_monthly >> normal_edge >> avg_fte_rank
    dateranges >> normal_edge >> avg_fte_rank

    # Layer 0 -> Layer 2 relationships
    fact_labor_powerbi >> normal_edge >> sp_labor_post
    sp_labor_post >> normal_edge >> fact_labor_post

    # Layer 0 -> Layer 3 relationships
    cadence_budget_post >> normal_edge >> sp_budget_agg
    dateranges >> normal_edge >> sp_budget_agg
    sp_budget_agg >> normal_edge >> budget_rank

    # Layer 2,3 -> Layer 4 relationships
    fact_labor_post >> normal_edge >> sp_labor_agg
    dateranges >> normal_edge >> sp_labor_agg
    sp_labor_agg >> normal_edge >> fact_labor_rank
    sp_labor_agg >> normal_edge >> billable_prod_rank
    budget_rank >> normal_edge >> billable_prod_rank

    # Layer 4,1 -> Layer 5 relationships (final aggregation)
    billable_prod_rank >> normal_edge >> sp_emp_util
    avg_fte_rank >> problem_edge >> sp_emp_util  # PROBLEMATIC - Inflated FTE flows back
    currency >> normal_edge >> sp_emp_util
    sp_emp_util >> problem_edge >> final_target  # PROBLEMATIC - Final output includes inflated FTE

print("Diagram generated successfully!")
print("Output file: billable_efficiency_fte_lineage.png")
