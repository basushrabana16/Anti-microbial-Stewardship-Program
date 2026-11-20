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
# BUILD ONE ANTIBIOGRAM TABLE   <-- NEW (shared helper)
# =====================================================

def _build_antibiogram_table(frame, antibiotic_columns):
    """
    Builds one antibiogram table (list of rows) from a
    dataframe of culture reports.

    The SAME function is used for every organism table and
    for the combined (all organisms pooled) table, so the
    two can never be calculated differently.

    One row per antibiotic:
        Antibiotic | Susceptible | Intermediate | Resistant | Total
    each value formatted as "n (x.x%)".
    """

    table = []

    for antibiotic in sorted(antibiotic_columns):

        if antibiotic not in frame.columns:
            continue

        values = (

            frame[antibiotic]

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

        table.append({

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

    return table


# =====================================================
# ANTIBIOGRAM
# =====================================================

def get_antibiogram(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    antibiotics=None,
    from_month=None,
    to_month=None
):
    """
    Returns the antibiogram.

    Response shape (CHANGED):

        {
            "combined":  [ ...rows... ],     # all organisms pooled
            "organisms": {
                "Escherichia coli": [ ...rows... ],
                "Klebsiella pneumoniae": [ ...rows... ]
            }
        }

    "combined" is an empty list unless two or more organisms
    are present (with a single organism it would only repeat
    that organism's table).

    An empty dict {} is returned when there is no data.

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
        from_month=from_month,
        to_month=to_month
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
    # ORGANISM-WISE TABLES
    # -------------------------------------------------

    organism_tables = {}

    for organism_name, organism_df in df.groupby(
        "organism_clean",
        sort=True
    ):

        organism_table = _build_antibiogram_table(
            organism_df,
            antibiotic_columns
        )

        if organism_table:

            organism_tables[organism_name] = organism_table

    if not organism_tables:
        return {}

    # -------------------------------------------------
    # COMBINED TABLE (NEW)
    #
    # All organisms that appear in the tables above,
    # pooled together. Only built when two or more
    # organism tables exist.
    # -------------------------------------------------

    combined_table = []

    if len(organism_tables) >= 2:

        combined_df = df[
            df["organism_clean"].isin(
                organism_tables.keys()
            )
        ]

        combined_table = _build_antibiogram_table(
            combined_df,
            antibiotic_columns
        )

    return {

        "combined":
            combined_table,

        "organisms":
            organism_tables

    }