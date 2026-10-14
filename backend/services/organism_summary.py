from services.data_loader import (
    load_analysis_dataframe,
    apply_filters
)

# =====================================================
# ORGANISM SUMMARY
# =====================================================

def get_organism_summary(
    district="all",
    block="all",
    sample_type="all",
    from_month=None,      # <-- CHANGED: was start_date
    to_month=None         # <-- CHANGED: was end_date
):
    """
    Returns:

    1. Culture positivity summary
    2. Organism distribution among positive cultures

    Supports multiple values for:
        - district
        - block
        - sample_type

    Supports month-year range filtering via:
        - from_month   ("YYYY-MM")
        - to_month     ("YYYY-MM")
    """

    # -------------------------------------------------
    # LOAD ANALYSIS DATA
    # -------------------------------------------------

    df = load_analysis_dataframe()

    if df.empty:
        return {
            "culture_positivity": [],
            "organism_distribution": []
        }

    # -------------------------------------------------
    # APPLY FILTERS
    #
    # apply_filters() handles both:
    #
    #   "all"
    #   ["all"]
    #   "Udupi"
    #   ["Udupi", "Dakshina Kannada"]
    #
    # and uses OR within each filter and
    # AND between different filters.
    #
    # Also applies time duration filtering via
    # from_month / to_month on prescription_date.
    # -------------------------------------------------

    df = apply_filters(
        df,
        district=district,
        block=block,
        sample_type=sample_type,
        from_month=from_month,     # <-- CHANGED
        to_month=to_month           # <-- CHANGED
    )

    if df.empty:
        return {
            "culture_positivity": [],
            "organism_distribution": []
        }

    # =================================================
    # CLEAN CULTURE RESULT
    # =================================================

    df["culture_result_clean"] = (
        df["culture_result"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # =================================================
    # TABLE A: CULTURE POSITIVITY
    # =================================================

    total_samples = len(df)

    positive_count = int(
        (
            df["culture_result_clean"]
            == "positive"
        ).sum()
    )

    nogrowth_count = int(
        (
            df["culture_result_clean"]
            == "no growth"
        ).sum()
    )

    table_a = [

        {
            "Result": "Positive",

            "Count": positive_count,

            "Percentage": round(
                positive_count * 100 / total_samples,
                2
            ) if total_samples else 0
        },

        {
            "Result": "No Growth",

            "Count": nogrowth_count,

            "Percentage": round(
                nogrowth_count * 100 / total_samples,
                2
            ) if total_samples else 0
        }

    ]

    # =================================================
    # TABLE B: ORGANISM DISTRIBUTION
    # =================================================

    # Only positive cultures are considered
    # for organism distribution.

    positive_df = df[
        df["culture_result_clean"]
        == "positive"
    ].copy()

    if positive_df.empty:
        return {
            "culture_positivity": table_a,
            "organism_distribution": []
        }

    # -------------------------------------------------
    # CLEAN ORGANISM NAMES
    # -------------------------------------------------

    positive_df["organism_clean"] = (

        positive_df["organism_identification"]

        .fillna("")

        .astype(str)

        .str.strip()

    )

    # Remove records without organism identification

    positive_df = positive_df[
        positive_df["organism_clean"] != ""
    ]

    if positive_df.empty:
        table_b = []

    else:

        # -------------------------------------------------
        # COUNT ORGANISMS
        # -------------------------------------------------

        organism_counts = (

            positive_df["organism_clean"]

            .value_counts()

            .sort_values(
                ascending=False
            )

        )

        total_positive = int(
            organism_counts.sum()
        )

        # -------------------------------------------------
        # BUILD ORGANISM TABLE
        # -------------------------------------------------

        table_b = []

        for organism, count in organism_counts.items():

            count = int(count)

            percentage = (

                round(
                    count * 100 / total_positive,
                    2
                )

                if total_positive

                else 0

            )

            table_b.append({

                "Organism": organism,

                "Count": count,

                "Percentage": percentage

            })

    # =================================================
    # RETURN RESULT
    # =================================================

    return {

        "culture_positivity": table_a,

        "organism_distribution": table_b

    }