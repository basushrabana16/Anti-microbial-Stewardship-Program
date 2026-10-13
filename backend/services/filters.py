from database.connection import get_connection
from services.query_builder import get_analysis_dataframe
import pandas as pd  # <-- ADDED: needed for pd.to_datetime


# =====================================================
# LOAD NORMALIZED DATASET
# =====================================================

def load_dataframe():
    """
    Loads the canonical analysis dataframe.
    """

    conn = get_connection()

    try:
        return get_analysis_dataframe(conn)

    finally:
        conn.close()


# =====================================================
# NORMALIZE FILTER SELECTION
# =====================================================

def normalize_selection(selection):
    """
    Converts a filter selection into a clean list.

    Accepted inputs:
        "all"
        "Udupi"
        ["Udupi", "Dakshina Kannada"]
        ["all"]

    Returns:
        []       -> means ALL
        [values] -> means selected values
    """

    if selection is None:
        return []

    # Single string
    if isinstance(selection, str):
        selection = [selection]

    # Convert to list
    selection = list(selection)

    cleaned = []

    for value in selection:

        if value is None:
            continue

        value = str(value).strip()

        if not value:
            continue

        # "all" means no restriction
        if value.lower() == "all":
            return []

        cleaned.append(value)

    return cleaned


# =====================================================
# SAFE UNIQUE VALUES
# =====================================================

def unique_values(df, column):
    """
    Returns sorted unique values for a column,
    prefixed with 'all'.
    """

    if df.empty or column not in df.columns:
        return ["all"]

    values = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    values = values[
        values != ""
    ]

    values = sorted(
        values.unique().tolist()
    )

    return ["all"] + values


# =====================================================
# APPLY MULTI-VALUE FILTER
# =====================================================

def apply_multi_filter(df, column, selection):
    """
    Applies a multi-select filter to a dataframe.

    If selection is:
        "all"
        None
        []
        ["all"]

    then no filtering is applied.

    Otherwise, rows matching ANY selected value
    are retained.
    """

    if df.empty or column not in df.columns:
        return df

    selected = normalize_selection(selection)

    # No selected values = ALL
    if not selected:
        return df

    selected = {
        str(value).strip().lower()
        for value in selected
    }

    column_values = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return df[
        column_values.isin(selected)
    ]


# =====================================================
# APPLY DATE RANGE FILTER   <-- ADDED: new function
# =====================================================

def apply_date_filter(df, column, start_date=None, end_date=None):
    """
    Applies a date-range filter to a dataframe.

    If both start_date and end_date are None,
    no filtering is applied.

    start_date / end_date accepted as:
        "YYYY-MM-DD" strings, or None
    """

    if df.empty or column not in df.columns:
        return df

    if not start_date and not end_date:
        return df

    dates = pd.to_datetime(df[column], errors="coerce")

    mask = pd.Series(True, index=df.index)

    if start_date:
        mask &= dates >= pd.to_datetime(start_date)

    if end_date:
        mask &= dates <= pd.to_datetime(end_date)

    return df[mask]


# =====================================================
# APPLY FILTERS
# =====================================================

def filter_dataframe(
    df,
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    start_date=None,      # <-- ADDED
    end_date=None         # <-- ADDED
):
    """
    Applies the selected filters to the normalized dataframe.

    Filtering hierarchy:

        Time Duration        <-- ADDED
            ↓
        District
            ↓
        Block
            ↓
        Sample Type
            ↓
        Organism
    """

    if df.empty:
        return df

    # -------------------------------------------------
    # TIME DURATION   <-- ADDED
    # -------------------------------------------------

    df = apply_date_filter(
        df,
        "collection_date",   # change this if your normalized column is named differently
        start_date,
        end_date
    )

    # -------------------------------------------------
    # DISTRICT
    # -------------------------------------------------

    df = apply_multi_filter(
        df,
        "district",
        district
    )

    # -------------------------------------------------
    # BLOCK
    # -------------------------------------------------

    df = apply_multi_filter(
        df,
        "block",
        block
    )

    # -------------------------------------------------
    # SAMPLE TYPE
    # -------------------------------------------------

    df = apply_multi_filter(
        df,
        "sample_type",
        sample_type
    )

    # -------------------------------------------------
    # ORGANISM
    # -------------------------------------------------

    selected_organisms = normalize_selection(
        organisms
    )

    if selected_organisms:

        # Only positive cultures have organisms
        if "culture_result" in df.columns:

            culture_result = (
                df["culture_result"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            df = df[
                culture_result == "positive"
            ]

        df = apply_multi_filter(
            df,
            "organism_identification",
            selected_organisms
        )

    return df


# =====================================================
# FILTER OPTIONS
# =====================================================

def get_antibiogram_options(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    start_date=None,      # <-- ADDED
    end_date=None         # <-- ADDED
):
    """
    Returns cascading filter options.

    Cascade:

        Time Duration    <-- ADDED
            ↓
        District
            ↓
        Block
            ↓
        Sample Type
            ↓
        Organism
            ↓
        Antibiotic
    """

    df = load_dataframe()

    if df.empty:
        return {
            "date_range": {"min": None, "max": None},  # <-- ADDED
            "districts": ["all"],
            "blocks": ["all"],
            "sample_types": ["all"],
            "organisms": ["all"],
            "antibiotics": ["all"]
        }

    # =================================================
    # 0. DATE RANGE OPTIONS   <-- ADDED
    # =================================================

    # The date picker's selectable bounds must ALWAYS
    # reflect the full dataset, not the currently
    # selected range — same logic as district_options
    # below always showing all districts.

    if "collection_date" in df.columns:
        valid_dates = pd.to_datetime(
            df["collection_date"], errors="coerce"
        ).dropna()

        date_range = {
            "min": valid_dates.min().strftime("%Y-%m-%d") if not valid_dates.empty else None,
            "max": valid_dates.max().strftime("%Y-%m-%d") if not valid_dates.empty else None
        }
    else:
        date_range = {"min": None, "max": None}

    # =================================================
    # 1. DISTRICT OPTIONS
    # =================================================

    # District dropdown must ALWAYS show all districts
    # because district is the first-level filter.
    # NOTE: district options should still respect the
    # selected time duration, since date is now the
    # top-level scope.

    date_scoped_df = apply_date_filter(     # <-- ADDED
        df,
        "collection_date",
        start_date,
        end_date
    )

    district_options = unique_values(
        date_scoped_df,     # <-- MODIFIED: was `df`
        "district"
    )

    # =================================================
    # 2. BLOCK OPTIONS
    # =================================================

    # Blocks depend ONLY on selected district(s)
    # (within the selected time duration).

    block_df = apply_multi_filter(
        date_scoped_df,     # <-- MODIFIED: was `df`
        "district",
        district
    )

    block_options = unique_values(
        block_df,
        "block"
    )

    # =================================================
    # 3. SAMPLE TYPE OPTIONS
    # =================================================

    # Sample types depend on:
    # time duration + district + block

    sample_type_df = apply_multi_filter(
        date_scoped_df,     # <-- MODIFIED: was `df`
        "district",
        district
    )

    sample_type_df = apply_multi_filter(
        sample_type_df,
        "block",
        block
    )

    sample_type_options = unique_values(
        sample_type_df,
        "sample_type"
    )

    # =================================================
    # 4. ORGANISM OPTIONS
    # =================================================

    # Organisms depend on:
    # time duration + district + block + sample type
    #
    # IMPORTANT:
    # Do NOT apply the currently selected organisms here.
    #
    # Otherwise selecting one organism would remove the
    # other organisms from the dropdown.

    organism_df = apply_multi_filter(
        date_scoped_df,     # <-- MODIFIED: was `df`
        "district",
        district
    )

    organism_df = apply_multi_filter(
        organism_df,
        "block",
        block
    )

    organism_df = apply_multi_filter(
        organism_df,
        "sample_type",
        sample_type
    )

    # Only positive cultures can have organisms
    if "culture_result" in organism_df.columns:

        culture_result = (
            organism_df["culture_result"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        organism_df = organism_df[
            culture_result == "positive"
        ]

    organism_options = unique_values(
        organism_df,
        "organism_identification"
    )

    # =================================================
    # 5. ANTIBIOTIC OPTIONS
    # =================================================

    # Antibiotics depend on:
    #
    # time duration
    # + district
    # + block
    # + sample type
    # + selected organism(s)

    antibiotic_df = filter_dataframe(
        df,
        district=district,
        block=block,
        sample_type=sample_type,
        organisms=organisms,
        start_date=start_date,      # <-- ADDED
        end_date=end_date            # <-- ADDED
    )

    # Get antibiotic column metadata from the ORIGINAL
    # dataframe rather than relying on filtered_df.attrs.

    antibiotics = sorted(
        df.attrs.get(
            "antibiotic_columns",
            []
        )
    )

    # If antibiotic_columns metadata is unavailable,
    # return only "all".
    antibiotic_options = (
        ["all"] + antibiotics
    )

    # =================================================
    # RETURN
    # =================================================

    return {

        "date_range":       # <-- ADDED
            date_range,

        "districts":
            district_options,

        "blocks":
            block_options,

        "sample_types":
            sample_type_options,

        "organisms":
            organism_options,

        "antibiotics":
            antibiotic_options

    }