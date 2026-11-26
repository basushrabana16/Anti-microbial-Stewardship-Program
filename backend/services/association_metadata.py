import pandas as pd

from services.filters import get_antibiogram_options


# =====================================================
# DERIVED VARIABLES
# =====================================================

def add_derived_columns(df):

    df = df.copy()

    # =================================================
    # AGE GROUP
    # =================================================

    if "age_years" in df.columns:

        df["age_years"] = pd.to_numeric(
            df["age_years"],
            errors="coerce"
        )

    else:

        df["age_years"] = pd.Series(
            [float("nan")] * len(df),
            index=df.index
        )

    df["age_group"] = pd.cut(

        df["age_years"],

        bins=[
            -float("inf"),
            29,
            60,
            float("inf")
        ],

        labels=[
            "<30",
            "30-60",
            ">60"
        ]

    ).astype("string")

    # =================================================
    # COLLECTION DATE
    # =================================================

    if "collection_date" in df.columns:

        df["collection_date"] = pd.to_datetime(
            df["collection_date"],
            errors="coerce"
        )

    else:

        df["collection_date"] = pd.Series(
            [pd.NaT] * len(df),
            index=df.index
        )

    df["collection_month"] = (

        df["collection_date"]
        .dt.month
        .astype("Int64")

    )

    # =================================================
    # COLLECTION SEASON
    # =================================================

    def get_season(month):

        if pd.isna(month):
            return None

        month = int(month)

        if month in (12, 1, 2):
            return "winter"

        if month in (3, 4, 5):
            return "spring"

        if month in (6, 7, 8):
            return "summer"

        return "fall"

    df["collection_season"] = (

        df["collection_month"]
        .apply(get_season)

    )

    return df


# =====================================================
# NORMALIZE ORGANISM LIST
# =====================================================

def clean_organism_list(organisms):

    if not organisms:
        return []

    if isinstance(organisms, str):
        organisms = [organisms]

    return [

        str(org).strip()

        for org in organisms

        if (
            str(org).strip()
            and
            str(org).strip().lower() != "all"
        )

    ]


# =====================================================
# CUSTOM AGE GROUPS
# =====================================================

def apply_custom_age_groups(df, age_groups):
    """
    Replaces the default age_group column with user-defined bins.

    age_groups: list of {"min": int, "max": int} dicts, or None.

    Validation rules (B1 — reject gaps and overlaps):
        - at least 2 and at most 5 groups
        - every group: 0 <= min < max
        - every pair of consecutive groups must be contiguous:
              group[i].max + 1 == group[i+1].min

    Returns (df, error_message). error_message is None on success.
    """

    if not age_groups:
        return df, None

    if not isinstance(age_groups, list):
        return df, "age_groups must be a list."

    if len(age_groups) < 2:
        return df, "At least 2 age groups are required."

    if len(age_groups) > 5:
        return df, "At most 5 age groups are allowed."

    parsed = []

    for index, group in enumerate(age_groups):

        if not isinstance(group, dict):
            return df, f"Age group {index + 1} must be an object."

        try:
            lo = int(group.get("min"))
            hi = int(group.get("max"))
        except (TypeError, ValueError):
            return df, f"Age group {index + 1}: min and max must be integers."

        if lo < 0:
            return df, f"Age group {index + 1}: minimum cannot be negative."

        if lo >= hi:
            return df, f"Age group {index + 1}: minimum must be less than maximum."

        parsed.append((lo, hi))

    for index in range(len(parsed) - 1):

        if parsed[index][1] + 1 != parsed[index + 1][0]:

            return df, (
                f"Age groups must be contiguous. "
                f"Group {index + 1} ends at {parsed[index][1]}, "
                f"but group {index + 2} starts at {parsed[index + 1][0]}."
            )

    df = df.copy()

    if "age_years" not in df.columns:

        df["age_years"] = pd.Series(
            [float("nan")] * len(df),
            index=df.index
        )

    else:

        df["age_years"] = pd.to_numeric(
            df["age_years"],
            errors="coerce"
        )

    labels = [
        f"{lo}-{hi}"
        for lo, hi in parsed
    ]

    edges = [parsed[0][0] - 0.5]

    for _, hi in parsed:
        edges.append(hi + 0.5)

    df["age_group"] = pd.cut(
        df["age_years"],
        bins=edges,
        labels=labels
    ).astype("string")

    return df, None


# =====================================================
# ASSOCIATION OPTIONS
# =====================================================

def get_association_options(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    from_month=None,
    to_month=None
):

    organisms = clean_organism_list(
        organisms
    )

    options = get_antibiogram_options(
        district=district,
        block=block,
        sample_type=sample_type,
        organisms=organisms,
        from_month=from_month,
        to_month=to_month
    )

    options["independent_variables"] = [

        "gender",
        "age_group",
        "district",
        "block",
        "sample_type",

    ]

    options["dependent_variables"] = [

        "culture_result",
        "organism_identification",
        "antibiogram_susceptibility"

    ]

    options["statistical_tests"] = [

        "auto"

    ]

    return options