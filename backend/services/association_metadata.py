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
# ASSOCIATION OPTIONS
# =====================================================

def get_association_options(
    district="all",
    block="all",
    sample_type="all",
    organisms=None
):

    organisms = clean_organism_list(
        organisms
    )

    options = get_antibiogram_options(
        district=district,
        block=block,
        sample_type=sample_type,
        organisms=organisms
    )

    options["independent_variables"] = [

        "gender",
        "age_group",
        "district",
        "block",
        "sample_type",
        "referred_by",
        "collection_month",
        "collection_season"

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