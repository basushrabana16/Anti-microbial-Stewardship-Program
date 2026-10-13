import pandas as pd
import numpy as np


# =====================================================
# VALID ANTIBIOGRAM SUSCEPTIBILITY VALUES
# =====================================================

VALID_SUSCEPTIBILITY_RESULTS = {
    "susceptible",
    "intermediate",
    "resistant"
}


# =====================================================
# CLEAN TEST DATAFRAME
# =====================================================

def clean_test_dataframe(
    df,
    independent_variable,
    dependent_variable
):

    if df is None or df.empty:
        return None

    if independent_variable not in df.columns:
        return None

    if dependent_variable not in df.columns:
        return None

    test_df = df[
        [independent_variable, dependent_variable]
    ].copy()

    # -----------------------------------------
    # CLEAN VARIABLES
    # -----------------------------------------

    for column in [
        independent_variable,
        dependent_variable
    ]:

        test_df[column] = (

            test_df[column]

            .fillna("")

            .astype(str)

            .str.strip()

            .str.lower()

        )

    # -----------------------------------------
    # REMOVE BLANKS
    # -----------------------------------------

    test_df = test_df[

        (~test_df[independent_variable].isin(
            ["", "nan", "none"]
        ))

        &

        (~test_df[dependent_variable].isin(
            ["", "nan", "none"]
        ))

    ]

    if test_df.empty:
        return None

    # -----------------------------------------
    # VALIDATE ANTIBIOTIC RESULTS
    # -----------------------------------------

    antibiotic_columns = df.attrs.get(
        "antibiotic_columns",
        []
    )

    if dependent_variable in antibiotic_columns:

        test_df = test_df[

            test_df[dependent_variable]

            .isin(
                VALID_SUSCEPTIBILITY_RESULTS
            )

        ]

        if test_df.empty:
            return None

    return test_df
# =====================================================
# BUILD CONTINGENCY TABLE
# =====================================================

def build_contingency_table(
    df,
    independent_variable,
    dependent_variable,
    is_antibiogram_susceptibility=False
):

    test_df = clean_test_dataframe(
        df=df,
        independent_variable=independent_variable,
        dependent_variable=dependent_variable,
    )

    if test_df is None or test_df.empty:
        return None

    table = pd.crosstab(
        test_df[independent_variable],
        test_df[dependent_variable]
    )

    if table is None or table.empty:
        return None

    return table


# =====================================================
# EXPECTED FREQUENCIES
# =====================================================

def calculate_expected_frequencies(contingency_table):

    if contingency_table is None or contingency_table.empty:
        return None

    total = contingency_table.values.sum()

    if total == 0:
        return None

    row_totals = (
        contingency_table
        .sum(axis=1)
        .values
        .reshape(-1, 1)
    )

    column_totals = (
        contingency_table
        .sum(axis=0)
        .values
        .reshape(1, -1)
    )

    expected = (
        row_totals @ column_totals
    ) / total

    return pd.DataFrame(
        expected,
        index=contingency_table.index,
        columns=contingency_table.columns
    )


# =====================================================
# ROW PERCENTAGES
# =====================================================

def calculate_row_percentages(contingency_table):

    if contingency_table is None or contingency_table.empty:
        return None

    row_totals = contingency_table.sum(axis=1)

    row_percentages = (
        contingency_table
        .div(row_totals, axis=0)
        .fillna(0)
        * 100
    )

    return row_percentages.round(2)


# =====================================================
# ASSUMPTION CHECKS
# =====================================================

def evaluate_assumptions(expected_df):

    if expected_df is None or expected_df.empty:
        return {
            "minimum_expected_frequency": 0,
            "cells_with_expected_below_5": 0,
            "percent_cells_with_expected_below_5": 100
        }

    min_expected = expected_df.min().min()

    if pd.isna(min_expected):
        min_expected = 0

    total_cells = expected_df.size

    cells_below_5 = int(
        (expected_df < 5).sum().sum()
    )

    percent_cells_below_5 = (
        (cells_below_5 / total_cells) * 100
        if total_cells > 0
        else 100
    )

    return {
        "minimum_expected_frequency": round(
            float(min_expected),
            4
        ),
        "cells_with_expected_below_5": cells_below_5,
        "percent_cells_with_expected_below_5": round(
            percent_cells_below_5,
            2
        )
    }


# =====================================================
# TABLE TOTALS
# =====================================================

def calculate_totals(contingency_table):

    if contingency_table is None or contingency_table.empty:
        return None

    row_totals = contingency_table.sum(axis=1)

    column_totals = contingency_table.sum(axis=0)

    return {
        "row_totals": row_totals.to_dict(),
        "column_totals": column_totals.to_dict(),
        "grand_total": int(
            contingency_table.values.sum()
        )
    }