#!/usr/bin/env python3
"""
Data Lineage Diagram: BillableEfficiency FTE Aggregation Pipeline (Version 2)
Generated: 2025-10-24
Purpose: Visualize data flow with improved layout and clear problematic flow highlighting
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.flowchart import Action, Delay, Preparation

# Define edge styles
normal_edge = Edge(color="black", style="solid")
problem_edge = Edge(color="red", style="dashed", penwidth="3.0")

# Graph attributes - improved spacing
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "splines": "spline",  # Changed to spline for smoother curves
    "nodesep": "0.8",
    "ranksep": "1.5",
    "compound": "true",
}

node_attr = {
    "fontsize": "10",
    "shape": "box",
    "style": "rounded,filled",
    "fillcolor": "lightblue",
    "margin": "0.2",
}

edge_attr = {
    "fontsize": "9",
}

with Diagram(
    "Data Lineage: BillableEfficiency FTE Aggregation Pipeline (v2)",
    show=False,
    direction="LR",
    filename="billable_efficiency_fte_lineage_v2",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):

    # SOURCE LAYER - Separated by schema
    with Cluster("SOURCE LAYER"):

        with Cluster("DBO Schema"):
            full_dept_map = Action("Full_Departmental\n_Map")

        with Cluster("ClinOpsFinance Sources"):
            hr_contract = Action("HrContractAttendance")
            dept_map_view = Delay("vFull_Departmental\n_Map_ActivePrima")
            dateranges = Action("DateRanges_PM")
            currency = Action("CURRENCY")
            cadence_budget_post = Action("CadenceBudgetData\n_Post")

        with Cluster("Other Sources"):
            fact_labor_powerbi = Action("FactLaborCost\nForEarnedValue\n(POWERBI)")
            currency_rate = Action("Currency\nExchangeRate\n(PRIMA)")

    # TRANSFORMATION LAYER 1: FTE Processing (PROBLEMATIC PATH)
    with Cluster("FTE PROCESSING (PROBLEMATIC)", graph_attr={"bgcolor": "#ffe6e6"}):
        sp_emp_util_1 = Preparation("spLoadEmployee\nContractUtilization\n_Aggregations\n(Creates FTE)")

        with Cluster("FTE Tables"):
            emp_attendance = Action("EmployeeAttendance\nExpectedHours\nUtilization_Monthly")
            emp_fte_monthly = Action("EmployeeContract\nFTE_Monthly\n[INFLATED]")
            avg_fte_monthly = Action("AverageContract\nFTE_Monthly\n[INFLATED]")
            avg_fte_rank = Action("AverageContractFTE\n_Monthly_RankDetail\n[INFLATED]")

    # TRANSFORMATION LAYER 2: Labor Cost (CLEAN PATH)
    with Cluster("LABOR COST PROCESSING (CLEAN)", graph_attr={"bgcolor": "#e6ffe6"}):
        sp_labor_post = Preparation("spLoadFactLaborCost\nForEarnedValue_Post")
        fact_labor_post = Action("FactLaborCost\nForEarnedValue_Post")

    # TRANSFORMATION LAYER 3: Budget Processing (CLEAN PATH)
    with Cluster("BUDGET PROCESSING (CLEAN)", graph_attr={"bgcolor": "#e6f7ff"}):
        sp_budget_agg = Preparation("spLoadCadenceBudget\n_Aggregations")
        budget_rank = Action("CadenceBudgetData\n_BillableEfficiency\n_RankDetail")

    # AGGREGATION LAYER 4
    with Cluster("AGGREGATION LAYER"):
        sp_labor_agg = Preparation("spLoadFactLaborCost\nForEarnedValue\n_Aggregations")

        with Cluster("Aggregated Tables"):
            fact_labor_rank = Action("FactLaborCost\nForEarnedValue\n_RankDetailAggregation\n[CLEAN]")
            billable_prod_rank = Action("BillableEfficiency\n_Productivity\n_RankDetailAggregation\n[CLEAN]")

    # FINAL LAYER
    with Cluster("FINAL TARGET", graph_attr={"bgcolor": "#fff0e6"}):
        sp_emp_util_2 = Preparation("spLoadEmployee\nContractUtilization\n_Aggregations\n(Final Join)")
        final_target = Action("BillableEfficiency\n_Productivity_AverageFTE\n_Monthly_RankDetail\nAggregation\n\n[MIXED: Clean Labor Cost\n+ Inflated FTE]")

    # DEFINE RELATIONSHIPS - Clean sources to department mapping
    full_dept_map >> normal_edge >> dept_map_view

    # PROBLEMATIC PATH: Department mapping to FTE processing
    hr_contract >> normal_edge >> sp_emp_util_1
    dept_map_view >> problem_edge >> sp_emp_util_1  # ROOT CAUSE: 1:M mapping without division
    dateranges >> normal_edge >> sp_emp_util_1

    # FTE processing internal flow (carries inflation forward)
    sp_emp_util_1 >> normal_edge >> emp_attendance
    sp_emp_util_1 >> problem_edge >> emp_fte_monthly  # Creates inflated FTE values
    emp_fte_monthly >> problem_edge >> avg_fte_monthly
    avg_fte_monthly >> problem_edge >> avg_fte_rank
    dateranges >> normal_edge >> avg_fte_rank

    # CLEAN PATH: Labor Cost processing
    fact_labor_powerbi >> normal_edge >> sp_labor_post
    sp_labor_post >> normal_edge >> fact_labor_post

    # CLEAN PATH: Budget processing
    cadence_budget_post >> normal_edge >> sp_budget_agg
    dateranges >> normal_edge >> sp_budget_agg
    sp_budget_agg >> normal_edge >> budget_rank

    # Aggregation layer (clean sources)
    fact_labor_post >> normal_edge >> sp_labor_agg
    dateranges >> normal_edge >> sp_labor_agg
    budget_rank >> normal_edge >> sp_labor_agg
    sp_labor_agg >> normal_edge >> fact_labor_rank
    sp_labor_agg >> normal_edge >> billable_prod_rank
    budget_rank >> normal_edge >> billable_prod_rank

    # Final join: Clean data + Inflated FTE
    billable_prod_rank >> normal_edge >> sp_emp_util_2  # Clean labor cost
    avg_fte_rank >> problem_edge >> sp_emp_util_2  # Inflated FTE values
    currency >> normal_edge >> sp_emp_util_2
    sp_emp_util_2 >> problem_edge >> final_target  # Final table contains mixed data

print("Diagram v2 generated successfully!")
print("Output file: billable_efficiency_fte_lineage_v2.png")
