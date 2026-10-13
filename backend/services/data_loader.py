from database.connection import get_connection

from services.query_builder import get_analysis_dataframe

from services.association_metadata import (
    add_derived_columns,
    clean_organism_list
)

import pandas as pd  # <-- ADDED: needed for date parsing/comparison


# =====================================================
# LOAD COMPLETE ANALYSIS DATASET
# =====================================================

def load_analysis_dataframe():
    """
    Loads the complete analysis dataset.

    Workflow:

        Database
            ↓
        query_builder
            ↓
        normalize_prescriptions
            ↓
        add_derived_columns
    """

    conn = get_connection()

    try:

        analysis_df = get_analysis_dataframe(conn)

    finally:

        conn.close()


    if analysis_df.empty:
        return analysis_df


    analysis_df = add_derived_columns(
        analysis_df
    )


    return analysis_df


# =====================================================
# NORMALIZE FILTER VALUES
# =====================================================

def normalize_filter_values(value):
    """
    Converts a filter value into a list.

    Examples:

        "all"
            → []

        None
            → []

        "Udupi"
            → ["udupi"]

        ["Udupi", "Dakshina Kannada"]
            → ["udupi", "dakshina kannada"]

        ["all"]
            → []

    Empty list means:
        no restriction / ALL
    """

    if value is None:
        return []


    # -------------------------------------------------
    # Single string
    # -------------------------------------------------

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return []

        if value.lower() == "all":
            return []

        return [
            value.lower()
        ]


    # -------------------------------------------------
    # Multiple values
    # -------------------------------------------------

    if isinstance(value, (list, tuple, set)):

        cleaned = []

        for item in value:

            if item is None:
                continue

            item = str(item).strip()

            if not item:
                continue

            if item.lower() == "all":
                continue

            cleaned.append(
                item.lower()
            )

        return cleaned


    # -------------------------------------------------
    # Unsupported type
    # -------------------------------------------------

    return []


# =====================================================
# NORMALIZE DATE FILTER VALUES   <-- ADDED: new function
# =====================================================

def normalize_date_value(value):
    """
    Converts a date filter value into a pandas Timestamp,
    or None if not provided / invalid.

    Accepted inputs:
        "YYYY-MM-DD" string
        None
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed


# =====================================================
# APPLY COMMON FILTERS
# =====================================================

def apply_filters(
    df,
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    start_date=None,      # <-- ADDED
    end_date=None          # <-- ADDED
):
    """
    Applies the common cascading filters.

    Supports:

        - ALL
        - single selection
        - multiple selections

    Filter hierarchy:

        Time Duration      <-- ADDED
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


    # =================================================
    # NORMALIZE FILTERS
    # =================================================

    districts = normalize_filter_values(
        district
    )

    blocks = normalize_filter_values(
        block
    )

    sample_types = normalize_filter_values(
        sample_type
    )

    organism_values = normalize_filter_values(
        organisms
    )

    start_date_value = normalize_date_value(   # <-- ADDED
        start_date
    )

    end_date_value = normalize_date_value(     # <-- ADDED
        end_date
    )


    # =================================================
    # TIME DURATION   <-- ADDED
    # =================================================

    if start_date_value is not None or end_date_value is not None:

        if "collection_date" in df.columns:

            date_values = pd.to_datetime(
                df["collection_date"],
                errors="coerce"
            )

            mask = pd.Series(True, index=df.index)

            if start_date_value is not None:
                mask &= date_values >= start_date_value

            if end_date_value is not None:
                mask &= date_values <= end_date_value

            df = df[mask]


    if df.empty:
        return df


    # =================================================
    # DISTRICT
    # =================================================

    if districts:

        district_values = (

            df["district"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()

        )

        df = df[
            district_values.isin(
                districts
            )
        ]


    if df.empty:
        return df


    # =================================================
    # BLOCK
    # =================================================

    if blocks:

        block_values = (

            df["block"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()

        )

        df = df[
            block_values.isin(
                blocks
            )
        ]


    if df.empty:
        return df


    # =================================================
    # SAMPLE TYPE
    # =================================================

    if sample_types:

        sample_type_values = (

            df["sample_type"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()

        )

        df = df[
            sample_type_values.isin(
                sample_types
            )
        ]


    if df.empty:
        return df


    # =================================================
    # ORGANISMS
    # =================================================

    if organism_values:

        # -------------------------------------------------
        # Only positive cultures have organisms
        # -------------------------------------------------

        culture_values = (

            df["culture_result"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()

        )

        df = df[
            culture_values == "positive"
        ]


        if df.empty:
            return df


        # -------------------------------------------------
        # Match selected organisms
        # -------------------------------------------------

        organism_column = (

            df["organism_identification"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()

        )


        df = df[
            organism_column.isin(
                organism_values
            )
        ]


    return df


# =====================================================
# VARIABLE VALIDATION
# =====================================================

def validate_variables(
    independent_variable,
    dependent_variable,
    independent_variables,
    dependent_variables
):

    if independent_variable not in independent_variables:

        return {
            "error":
            f"Invalid independent variable '{independent_variable}'."
        }


    if dependent_variable not in dependent_variables:

        return {
            "error":
            f"Invalid dependent variable '{dependent_variable}'."
        }


    return None