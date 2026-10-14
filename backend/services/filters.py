from database.connection import get_connection
from services.query_builder import get_analysis_dataframe
import pandas as pd


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
# APPLY MONTH-YEAR RANGE FILTER   <-- REPLACES apply_date_filter
# =====================================================

def apply_month_filter(df, column, from_month=None, to_month=None):
    """
    Keeps rows whose `column` falls between from_month and
    to_month. Both months are inclusive (whole months).

    If both from_month and to_month are None / empty,
    no filtering is applied.

    from_month / to_month accepted as:
        "YYYY-MM" strings, or None

    Example:
        from_month="2025-01", to_month="2025-03"
        -> keeps 01 Jan 2025 up to and including 31 Mar 2025
    """

    if df.empty or column not in df.columns:
        return df

    from_month = str(from_month).strip() if from_month else ""
    to_month = str(to_month).strip() if to_month else ""

    if not from_month and not to_month:
        return df

    dates = pd.to_datetime(df[column], errors="coerce")

    mask = pd.Series(True, index=df.index)

    if from_month:
        start = pd.to_datetime(from_month + "-01", errors="coerce")

        if pd.notna(start):
            mask &= dates >= start

    if to_month:
        end = pd.to_datetime(to_month + "-01", errors="coerce")

        if pd.notna(end):
            # first day of the NEXT month (exclusive),
            # so the entire "to" month is included
            mask &= dates < (end + pd.offsets.MonthBegin(1))

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
    from_month=None,      # <-- CHANGED: was start_date
    to_month=None         # <-- CHANGED: was end_date
):
    """
    Applies the selected filters to the normalized dataframe.

    Filtering hierarchy:

        Time Duration (Month-Year, prescription_date)
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
    # TIME DURATION (MONTH-YEAR, prescription_date)
    # -------------------------------------------------

    df = apply_month_filter(
        df,
        "prescription_date",
        from_month,
        to_month
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
    from_month=None,      # <-- CHANGED: was start_date
    to_month=None         # <-- CHANGED: was end_date
):
    """
    Returns cascading filter options.

    Cascade:

        Time Duration (Month-Year, prescription_date)
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
            "date_range": {"min": None, "max": None},
            "districts": ["all"],
            "blocks": ["all"],
            "sample_types": ["all"],
            "organisms": ["all"],
            "antibiotics": ["all"]
        }

    # =================================================
    # 0. MONTH-YEAR RANGE OPTIONS
    # =================================================

    # The picker's selectable bounds must ALWAYS
    # reflect the full dataset, not the currently
    # selected range.
    #
    # Values are returned as "YYYY-MM" (what
    # <input type="month"> expects).

    if "prescription_date" in df.columns:
        valid_dates = pd.to_datetime(
            df["prescription_date"], errors="coerce"
        ).dropna()

        date_range = {
            "min": valid_dates.min().strftime("%Y-%m") if not valid_dates.empty else None,
            "max": valid_dates.max().strftime("%Y-%m") if not valid_dates.empty else None
        }
    else:
        date_range = {"min": None, "max": None}

    # =================================================
    # 1. DISTRICT OPTIONS
    # =================================================

    # District options respect the selected time
    # duration, since time is the top-level scope.

    date_scoped_df = apply_month_filter(
        df,
        "prescription_date",
        from_month,
        to_month
    )

    district_options = unique_values(
        date_scoped_df,
        "district"
    )

    # =================================================
    # 2. BLOCK OPTIONS
    # =================================================

    # Blocks depend ONLY on selected district(s)
    # (within the selected time duration).

    block_df = apply_multi_filter(
        date_scoped_df,
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
        date_scoped_df,
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
        date_scoped_df,
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
        from_month=from_month,
        to_month=to_month
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

        "date_range":
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