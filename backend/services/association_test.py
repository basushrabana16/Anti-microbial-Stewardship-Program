import pandas as pd

from services.data_loader import (
    load_analysis_dataframe,
    apply_filters,
    validate_variables
)

from services.association_metadata import (
    apply_custom_age_groups
)

from services.association_helpers import (
    build_contingency_table,
    calculate_expected_frequencies,
    calculate_row_percentages,
    evaluate_assumptions,
    calculate_totals
)

from services.association_statistics import (
    run_chi_square_test,
    run_fisher_exact_test,
    run_fisher_freeman_halton_test
)


# =====================================================
# ALLOWED VARIABLES
# =====================================================

INDEPENDENT_VARIABLES = [

    "gender",
    "age_group",
    "district",
    "block",
    "sample_type",
    "referred_by",
    "collection_month",
    "collection_season"

]


DEPENDENT_VARIABLES = [

    "culture_result",
    "organism_identification",
    "antibiogram_susceptibility"

]


# =====================================================
# PIPELINE FOR ONE CROSSTAB
# =====================================================

def _evaluate_crosstab(df, indep_var, dep_col):
    """
    Runs the full association pipeline on a single dependent
    column: crosstab → expected frequencies → row % →
    assumptions → automatic test selection → statistics.

    Returns a dict with the full result, or
    {"error": "..."} if the crosstab cannot be built.
    """

    contingency_table = build_contingency_table(
        df=df,
        independent_variable=indep_var,
        dependent_variable=dep_col,
        is_antibiogram_susceptibility=False
    )

    if contingency_table is None:

        return {
            "error":
                "Unable to construct contingency table."
        }

    if (
        contingency_table.shape[0] < 2
        or
        contingency_table.shape[1] < 2
    ):

        return {
            "error":
                "At least two categories are required "
                "for both variables.",
            "contingency_table":
                contingency_table.to_dict()
        }

    expected_df = calculate_expected_frequencies(
        contingency_table
    )

    row_percentages = calculate_row_percentages(
        contingency_table
    )

    totals = calculate_totals(
        contingency_table
    )

    assumptions = evaluate_assumptions(
        expected_df
    )

    is_2x2 = (
        contingency_table.shape == (2, 2)
    )

    min_expected = assumptions[
        "minimum_expected_frequency"
    ]

    percent_below_5 = assumptions[
        "percent_cells_with_expected_below_5"
    ]

    if is_2x2:

        if min_expected >= 5:

            statistics = run_chi_square_test(
                contingency_table
            )

            decision = (
                "2x2 table with adequate expected "
                "frequencies. Chi-square test used."
            )

        else:

            statistics = run_fisher_exact_test(
                contingency_table
            )

            decision = (
                "2x2 table with low expected "
                "frequency. Fisher Exact test used."
            )

    else:

        if percent_below_5 < 20:

            statistics = run_chi_square_test(
                contingency_table
            )

            decision = (
                "Expected frequency assumption satisfied. "
                "Chi-square test used."
            )

        else:

            statistics = run_fisher_freeman_halton_test(
                contingency_table
            )

            decision = (
                "Many expected frequencies below 5. "
                "Fisher-Freeman-Halton test used."
            )

    return {

        "total_records":
            int(contingency_table.values.sum()),

        "table_shape":
            f"{contingency_table.shape[0]}x"
            f"{contingency_table.shape[1]}",

        "test":
            statistics.get("test"),

        "decision":
            decision,

        "test_statistic":
            statistics.get("test_statistic"),

        "degrees_of_freedom":
            statistics.get("degrees_of_freedom"),

        "p_value":
            statistics.get("p_value"),

        "warning":
            statistics.get("warning", ""),

        "contingency_table":
            contingency_table.to_dict(),

        "row_percentages":
            row_percentages.to_dict(),

        "expected_frequencies":
            expected_df.round(2).to_dict(),

        "row_totals":
            totals["row_totals"],

        "column_totals":
            totals["column_totals"],

        "grand_total":
            totals["grand_total"],

        "assumptions":
            assumptions

    }


# =====================================================
# POOLED ANTIBIOGRAM PIPELINE
# =====================================================

def _evaluate_pooled_antibiogram(
    df,
    indep_var,
    antibiotics
):
    """
    Pools all selected antibiotic columns into a long frame
    (one row per culture × antibiotic) and runs the standard
    crosstab pipeline on the pooled variable.

    NOTE: This table is descriptive — the same culture
    contributes once per antibiotic, so independence
    assumptions are violated. Per-antibiotic tables are
    the statistically sound ones.
    """

    frames = []

    for antibiotic in antibiotics:

        if antibiotic not in df.columns:
            continue

        sub = df[
            [indep_var, antibiotic]
        ].copy()

        sub = sub.rename(
            columns={antibiotic: "susceptibility"}
        )

        frames.append(sub)

    if not frames:

        return {
            "error":
                "No antibiotic columns available "
                "for pooling."
        }

    pooled = pd.concat(
        frames,
        ignore_index=True
    )

    # Mark the pooled column as an antibiogram column
    # so clean_test_dataframe() applies the S/I/R filter.
    pooled.attrs["antibiotic_columns"] = [
        "susceptibility"
    ]

    return _evaluate_crosstab(
        pooled,
        indep_var,
        "susceptibility"
    )


# =====================================================
# MAIN ASSOCIATION TEST
# =====================================================

def run_association_test(

    district="all",
    block="all",
    sample_type="all",
    organisms=None,

    independent_variable=None,
    dependent_variable=None,

    antibiotics=None,

    age_groups=None,

    from_month=None,
    to_month=None

):

    # =================================================
    # LOAD DATA
    # =================================================

    df = load_analysis_dataframe()

    if df is None or df.empty:
        return {"error": "No data available."}

    # =================================================
    # APPLY FILTERS
    # =================================================

    df = apply_filters(

        df,

        district=district,
        block=block,
        sample_type=sample_type,
        organisms=organisms or [],
        from_month=from_month,
        to_month=to_month

    )

    if df.empty:

        return {
            "error":
                "No records found after applying filters."
        }

    # =================================================
    # CUSTOM AGE GROUPS
    #
    # Only applied when the user customized the bins
    # AND age_group is the independent variable.
    # Replaces the default <30 / 30-60 / >60 column
    # produced by add_derived_columns().
    # =================================================

    if age_groups and independent_variable == "age_group":

        df, age_error = apply_custom_age_groups(
            df,
            age_groups
        )

        if age_error:

            return {
                "error": age_error
            }

    # =================================================
    # VARIABLE VALIDATION
    # =================================================

    validation = validate_variables(

        independent_variable,
        dependent_variable,
        INDEPENDENT_VARIABLES,
        DEPENDENT_VARIABLES

    )

    if validation:
        return validation

    # =================================================
    # ANTIBIOGRAM HANDLING
    # =================================================

    is_antibiogram = (
        dependent_variable ==
        "antibiogram_susceptibility"
    )

    if is_antibiogram:

        antibiotics = antibiotics or []

        selected = [

            str(a).strip().lower()

            for a in antibiotics

            if (
                str(a).strip()
                and
                str(a).strip().lower() != "all"
            )

        ]

        if not selected:

            return {
                "error":
                    "Please select at least one antibiotic."
            }

        for antibiotic in selected:

            if antibiotic not in df.columns:

                return {
                    "error":
                        f"Antibiotic '{antibiotic}' not found."
                }

        # ---------------------------------------------
        # SINGLE ANTIBIOTIC — current behaviour
        # ---------------------------------------------

        if len(selected) == 1:

            response = _evaluate_crosstab(
                df,
                independent_variable,
                selected[0]
            )

            if "error" in response:
                return response

            response["independent_variable"] = \
                independent_variable

            response["dependent_variable"] = \
                dependent_variable

            response["selected_antibiotic"] = \
                selected[0]

            response["selected_antibiotics"] = \
                selected

            response["antibiogram_mode"] = "single"

            return response

        # ---------------------------------------------
        # MULTIPLE ANTIBIOTICS — cumulative + per-antibiotic
        # ---------------------------------------------

        cumulative = _evaluate_pooled_antibiogram(
            df,
            independent_variable,
            selected
        )

        per_antibiotic = {}

        for antibiotic in selected:

            per_antibiotic[antibiotic] = _evaluate_crosstab(
                df,
                independent_variable,
                antibiotic
            )

        # If the pooled table itself failed, still return
        # the per-antibiotic results so the user can see them.

        if "error" in cumulative:

            return {

                "error":
                    cumulative["error"],

                "independent_variable":
                    independent_variable,

                "dependent_variable":
                    dependent_variable,

                "selected_antibiotics":
                    selected,

                "antibiotics":
                    per_antibiotic,

                "antibiogram_mode":
                    "multi"

            }

        cumulative["independent_variable"] = \
            independent_variable

        cumulative["dependent_variable"] = \
            dependent_variable

        cumulative["selected_antibiotics"] = \
            selected

        cumulative["antibiotics"] = \
            per_antibiotic

        cumulative["antibiogram_mode"] = \
            "multi"

        cumulative["pooled_warning"] = (
            "The cumulative table pools susceptibility "
            "results across all selected antibiotics. "
            "Because the same culture contributes once "
            "per antibiotic, independence assumptions are "
            "violated. Treat the cumulative table as "
            "descriptive; use the per-antibiotic tables "
            "for statistical inference."
        )

        return cumulative

    # =================================================
    # NON-ANTIBIOGRAM
    # =================================================

    response = _evaluate_crosstab(
        df,
        independent_variable,
        dependent_variable
    )

    if "error" in response:
        return response

    response["independent_variable"] = \
        independent_variable

    response["dependent_variable"] = \
        dependent_variable

    response["selected_antibiotic"] = None

    response["selected_antibiotics"] = []

    response["antibiogram_mode"] = "none"

    return response


# =====================================================
# ASSOCIATION SUMMARY (unchanged)
# =====================================================

def get_association_summary():

    return {

        "independent_variables":
            INDEPENDENT_VARIABLES,

        "dependent_variables":
            DEPENDENT_VARIABLES,

        "automatic_test_selection": {

            "2x2 with expected frequency <5":
                "Fisher Exact Test",

            "rxc with >=20% expected frequencies <5":
                "Fisher-Freeman-Halton Test",

            "otherwise":
                "Chi-square Test"

        }

    }