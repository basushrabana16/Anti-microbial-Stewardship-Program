from services.data_loader import (
    load_analysis_dataframe,
    apply_filters
)


# =====================================================
# VALID SUSCEPTIBILITY RESULTS
# =====================================================

VALID_RESULTS = {

    "susceptible",
    "intermediate",
    "resistant"

}


# =====================================================
# ANTIBIOGRAM
# =====================================================

def get_antibiogram(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    antibiotics=None,
    from_month=None,      # <-- CHANGED: was start_date
    to_month=None         # <-- CHANGED: was end_date
):
    """
    Returns organism-wise antibiogram percentages.

    from_month / to_month: "YYYY-MM" strings (or None),
    applied to prescription_date.
    """

    # -------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------

    df = load_analysis_dataframe()

    df = apply_filters(
        df,
        district=district,
        block=block,
        sample_type=sample_type,
        organisms=organisms,
        from_month=from_month,     # <-- CHANGED
        to_month=to_month           # <-- CHANGED
    )

    if df.empty:
        return {}

    # -------------------------------------------------
    # POSITIVE CULTURES ONLY
    # -------------------------------------------------

    df = df[
        df["culture_result"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        ==
        "positive"
    ]

    if df.empty:
        return {}

    # -------------------------------------------------
    # CLEAN ORGANISM
    # -------------------------------------------------

    df["organism_clean"] = (

        df["organism_identification"]

        .fillna("")

        .astype(str)

        .str.strip()

    )

    df = df[
        df["organism_clean"] != ""
    ]

    if df.empty:
        return {}

    # -------------------------------------------------
    # ANTIBIOTIC COLUMNS
    # -------------------------------------------------

    antibiotic_columns = list(

        df.attrs.get(
            "antibiotic_columns",
            []
        )

    )

    # -------------------------------------------------
    # FILTER ANTIBIOTICS
    # -------------------------------------------------

    if antibiotics:

        selected = {

            str(a).strip().lower()

            for a in antibiotics

            if str(a).strip().lower() != "all"

        }

        if selected:

            antibiotic_columns = [

                col

                for col in antibiotic_columns

                if col.lower() in selected

            ]

    if not antibiotic_columns:
        return {}

    # -------------------------------------------------
    # BUILD RESULT
    # -------------------------------------------------

    result = {}

    for organism_name, organism_df in df.groupby(
        "organism_clean",
        sort=True
    ):

        organism_table = []

        for antibiotic in sorted(antibiotic_columns):

            if antibiotic not in organism_df.columns:
                continue

            values = (

                organism_df[antibiotic]

                .fillna("")

                .astype(str)

                .str.strip()

                .str.lower()

            )

            values = values[
                values.isin(VALID_RESULTS)
            ]

            total = len(values)

            if total == 0:
                continue

            susceptible = int(
                (values == "susceptible").sum()
            )

            intermediate = int(
                (values == "intermediate").sum()
            )

            resistant = int(
                (values == "resistant").sum()
            )

            organism_table.append({

                "Antibiotic": antibiotic,

                "Susceptible":
                    f"{susceptible} ({susceptible / total * 100:.1f}%)",

                "Intermediate":
                    f"{intermediate} ({intermediate / total * 100:.1f}%)",

                "Resistant":
                    f"{resistant} ({resistant / total * 100:.1f}%)",

                "Total":
                    f"{total} (100.0%)"

            })

        if organism_table:

            result[organism_name] = organism_table

    return result