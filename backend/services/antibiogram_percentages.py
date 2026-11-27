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
# BUILD ONE ANTIBIOGRAM TABLE (shared helper)
# =====================================================

def _build_antibiogram_table(frame, antibiotic_columns):
    """
    Builds one antibiogram table (list of rows) from a
    dataframe of culture reports.

    The SAME function is used for every organism table and
    for every combined (organisms pooled) table, so they can
    never be calculated differently.

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
# SPLIT BY SAMPLE TYPE   (NEW)
# =====================================================

UNSPECIFIED_SAMPLE_TYPE = "Unspecified sample type"


def _sample_groups(frame):
    """
    Splits a dataframe into one group per sample type.

    Returns a list of (display_name, sub_dataframe), sorted
    alphabetically (case-insensitive). Records with no sample
    type go into a final "Unspecified sample type" group so
    that the groups always add up to the full table.
    """

    keys = frame["sample_clean"].str.lower()

    groups = []

    for key, sub_frame in frame.groupby(keys, sort=False):

        if key == "":
            name = UNSPECIFIED_SAMPLE_TYPE
        else:
            name = sub_frame["sample_clean"].iloc[0]

        groups.append((name, sub_frame))

    groups.sort(
        key=lambda item: (
            item[0] == UNSPECIFIED_SAMPLE_TYPE,
            item[0].lower()
        )
    )

    return groups


# =====================================================
# BUILD ONE BLOCK OF TABLES   (NEW)
# =====================================================

def _build_block(frame, antibiotic_columns, title_prefix=""):
    """
    Builds the tables for one group of culture reports:

        - one table for each organism
        - one combined table (all organisms pooled), only when
          two or more organism tables exist

    Every table carries:
        title             - what the table shows
        samples_analysed  - number of positive culture reports
                            included in the table
        rows              - the antibiogram rows

    title_prefix is added in front of each title (used for the
    sample-type sections, e.g. "Blood — ").
    """

    organism_tables = []

    for organism_name, organism_df in frame.groupby(
        "organism_clean",
        sort=True
    ):

        rows = _build_antibiogram_table(
            organism_df,
            antibiotic_columns
        )

        if rows:

            organism_tables.append({

                "organism":
                    organism_name,

                "title":
                    f"{title_prefix}{organism_name}",

                "samples_analysed":
                    int(len(organism_df)),

                "rows":
                    rows

            })

    if not organism_tables:

        return None

    organism_names = [
        table["organism"]
        for table in organism_tables
    ]

    included = frame[
        frame["organism_clean"].isin(organism_names)
    ]

    combined = None

    if len(organism_tables) >= 2:

        combined_rows = _build_antibiogram_table(
            included,
            antibiotic_columns
        )

        if combined_rows:

            combined = {

                "title":
                    f"{title_prefix}All Selected Organisms (Combined)",

                "samples_analysed":
                    int(len(included)),

                "rows":
                    combined_rows

            }

    return {

        "samples_analysed":
            int(len(included)),

        "combined":
            combined,

        "organisms":
            organism_tables

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
    from_month=None,
    to_month=None
):
    """
    Returns the antibiogram.

    Response shape (CHANGED):

        {
            "overall": {                       # all selected sample
                "heading": "...",              # types pooled together
                "samples_analysed": 60,
                "combined": { "title", "samples_analysed", "rows" } | None,
                "organisms": [
                    { "organism", "title", "samples_analysed", "rows" },
                    ...
                ]
            },
            "sample_types": [                  # one section per sample
                {                              # type (same layout)
                    "sample_type": "blood",
                    "heading": "Sample Type: blood",
                    "samples_analysed": 33,
                    "combined": {...} | None,
                    "organisms": [ ... ]
                },
                ...
            ]
        }

    "combined" is None unless two or more organisms are present
    in that block (with one organism it would only repeat that
    organism's table).

    "sample_types" is empty when only one sample type is present,
    because its section would repeat the overall one.

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
    ].copy()

    if df.empty:
        return {}

    # -------------------------------------------------
    # CLEAN ORGANISM AND SAMPLE TYPE
    # -------------------------------------------------

    df["organism_clean"] = (

        df["organism_identification"]

        .fillna("")

        .astype(str)

        .str.strip()

    )

    if "sample_type" in df.columns:

        df["sample_clean"] = (

            df["sample_type"]

            .fillna("")

            .astype(str)

            .str.strip()

        )

    else:

        df["sample_clean"] = ""

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
    # SAMPLE-TYPE GROUPS
    # -------------------------------------------------

    groups = _sample_groups(df)

    # -------------------------------------------------
    # SECTION 1: ALL SELECTED SAMPLE TYPES POOLED
    # -------------------------------------------------

    overall = _build_block(
        df,
        antibiotic_columns
    )

    if overall is None:
        return {}

    if len(groups) >= 2:

        overall["heading"] = (
            "All Selected Sample Types (Pooled)"
        )

    else:

        overall["heading"] = (
            f"Sample Type: {groups[0][0]}"
        )

    # -------------------------------------------------
    # ONE SECTION PER SAMPLE TYPE
    #
    # Only when two or more sample types are present;
    # with one, the section would repeat the overall one.
    # -------------------------------------------------

    sample_sections = []

    if len(groups) >= 2:

        for sample_name, sample_frame in groups:

            block = _build_block(
                sample_frame,
                antibiotic_columns,
                title_prefix=f"{sample_name} \u2014 "
            )

            if block is None:
                continue

            block["sample_type"] = sample_name

            block["heading"] = f"Sample Type: {sample_name}"

            sample_sections.append(block)

    return {

        "overall":
            overall,

        "sample_types":
            sample_sections

    }