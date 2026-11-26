import re

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
# AGE GROUP ORDERING
#
# crosstab() sorts labels as TEXT, which puts
# "30-60" before "<30" and ">60", and "10-19" before
# "5-9". Age groups must be ordered by their lower
# bound instead:
#
#     "<30"    -> first   (open lower end)
#     "30-60"  -> by its first number (30)
#     "61-80"  -> by its first number (61)
#     ">60"    -> last    (open upper end)
#
# Works for the default bins (<30 / 30-60 / >60) and
# for custom bins ("0-17", "18-40", "41-65", ...).
# =====================================================

AGE_GROUP_COLUMN = "age_group"


def _age_label_sort_key(label):

    text = str(label).strip().lower()

    match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

    number = float(match.group()) if match else 0.0

    # Open lower end: "<30", "<=29"
    if text.startswith("<"):
        return (0, number, text)

    # Open upper end: ">60", ">=61"
    if text.startswith(">") or text.startswith("\u2265"):
        return (2, number, text)

    # Closed range or single value: "30-60", "60+"
    if match:
        return (1, number, text)

    # Anything that is not recognisable goes last
    return (3, 0.0, text)


def order_age_group_labels(labels):
    """
    Returns the age-group labels sorted by lower bound.
    """

    return sorted(
        list(labels),
        key=_age_label_sort_key
    )


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

    # -------------------------------------------------
    # AGE GROUP: order rows by lower bound, not
    # alphabetically. Expected frequencies, row
    # percentages and totals are all derived from this
    # table, so they inherit the same order.
    # -------------------------------------------------

    if independent_variable == AGE_GROUP_COLUMN:

        table = table.reindex(
            order_age_group_labels(
                table.index.tolist()
            )
        )

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