# =====================================================
# REGRESSION HELPERS
# =====================================================

import re

import numpy as np
import pandas as pd

from statsmodels.api import add_constant

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
)


# =====================================================
# NUMERIC-AWARE CATEGORY SORTING
# =====================================================
#
# Alphabetical sorting breaks numeric range labels:
#
#     sorted(["5-15", "16-25", "26-100"])
#         -> ["16-25", "26-100", "5-15"]
#
# That reverses the reference category for custom age
# bins like 5-15 / 16-25 / 26-100.
#
# _sort_categories() sorts numeric-looking labels by
# their numeric bounds while preserving alphabetical
# order for everything else.
# =====================================================

_RANGE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)$")
_LESS_THAN_RE = re.compile(r"^<\s*(\d+)$")
_GREATER_THAN_RE = re.compile(r"^>\s*(\d+)$")


def _numeric_aware_sort_key(category):
    """
    Sort key for a single category label.

    Numeric range labels sort by (min, max).
    <N labels sort as (0, N-1).
    >N labels sort as (N+1, +inf).
    Everything else sorts after numeric labels,
    alphabetically.
    """

    text = str(category).strip().lower()


    match = _RANGE_RE.match(text)

    if match:

        return (
            0,
            int(match.group(1)),
            int(match.group(2)),
            text
        )


    match = _LESS_THAN_RE.match(text)

    if match:

        n = int(match.group(1))

        return (
            0,
            0,
            max(n - 1, 0),
            text
        )


    match = _GREATER_THAN_RE.match(text)

    if match:

        n = int(match.group(1))

        return (
            0,
            n + 1,
            float("inf"),
            text
        )


    return (1, 0, 0, text)


def _sort_categories(categories):
    """
    Sorts categories with numeric awareness.

    Backward compatible with sorted() for non-numeric
    labels.
    """

    return sorted(
        categories,
        key=_numeric_aware_sort_key
    )


# =====================================================
# NORMALIZE CATEGORICAL VALUE
# =====================================================

def normalize_categorical_series(series):
    """
    Converts a pandas Series into a normalized
    categorical representation.

    Examples
    --------
    " Female " -> "female"
    "Male"     -> "male"

    Missing-like strings are converted to <NA>.
    """

    if series is None:

        return series


    normalized = (

        series
        .astype("string")
        .str.strip()
        .str.lower()

    )


    normalized = normalized.replace({

        "":
            pd.NA,

        "nan":
            pd.NA,

        "none":
            pd.NA,

        "<na>":
            pd.NA,

        "null":
            pd.NA

    })


    return normalized


# =====================================================
# NORMALIZE COLUMN NAMES
# =====================================================

def normalize_column_name(column):
    """
    Normalizes a column name for internal comparison.

    This does not rename dataframe columns.
    """

    if column is None:

        return None


    return (

        str(column)
        .strip()
        .lower()

    )


# =====================================================
# PREPARE REGRESSION DATAFRAME
# =====================================================

def prepare_regression_dataframe(df):
    """
    Performs common regression-specific preparation.

    Operations:

        1. Copy dataframe
        2. Coerce age_years to numeric (matches database schema)
        3. Calculate turnaround time when possible
        4. Normalize known categorical columns

    Predictor and outcome selection are NOT performed
    here.

    Positive-culture filtering and antibiotic-specific
    filtering are NOT performed here.

    Those operations belong to regression_data.py.
    """

    if df is None or df.empty:

        return pd.DataFrame()


    df = df.copy()


    # =================================================
    # AGE - Use age_years (matches database schema)
    # =================================================

    if "age_years" in df.columns:

        df["age_years"] = pd.to_numeric(

            df["age_years"],

            errors="coerce"

        )


    # =================================================
    # TURNAROUND TIME
    # =================================================

    if (
        "collection_date" in df.columns
        and
        "reporting_date" in df.columns
    ):

        collection_date = pd.to_datetime(

            df["collection_date"],

            errors="coerce"

        )

        reporting_date = pd.to_datetime(

            df["reporting_date"],

            errors="coerce"

        )


        df["turnaround_time_days"] = (

            reporting_date
            -
            collection_date

        ).dt.total_seconds() / 86400.0

    else:

        df["turnaround_time_days"] = np.nan


    # =================================================
    # NORMALIZE COMMON CATEGORICAL COLUMNS
    # =================================================

    categorical_columns = [

        "gender",
        "age_group",
        "district",
        "block",
        "sample_type",
        "referred_by",

        "culture_result",

        "organism_identification",

        "antibiogram_susceptibility",

        "collection_month",
        "collection_season"

    ]


    for column in categorical_columns:

        if column in df.columns:

            df[column] = normalize_categorical_series(

                df[column]

            )


    return df


# =====================================================
# VALIDATE PREDICTOR LIST
# =====================================================

def validate_predictors(
    df,
    independent_variables
):
    """
    Validates that all requested independent variables
    exist in the dataframe.

    Returns
    -------
    dict

        {
            "valid": True/False,
            "missing_variables": [...]
        }
    """

    if df is None:

        return {

            "valid":
                False,

            "missing_variables":
                list(
                    independent_variables
                    or []
                )

        }


    independent_variables = (

        list(
            independent_variables
            or []
        )

    )


    missing_variables = [

        variable

        for variable in independent_variables

        if variable not in df.columns

    ]


    if missing_variables:

        return {

            "valid":
                False,

            "missing_variables":
                missing_variables

        }


    return {

        "valid":
            True,

        "missing_variables":
            []

    }


# =====================================================
# VALIDATE DEPENDENT VARIABLE
# =====================================================

def validate_dependent_variable(
    df,
    dependent_variable
):
    """
    Validates that the requested dependent variable
    exists in the dataframe.
    """

    if df is None:

        return {

            "valid":
                False,

            "error":
                "Dataframe is unavailable."

        }


    if not dependent_variable:

        return {

            "valid":
                False,

            "error":
                "Dependent variable was not specified."

        }


    if dependent_variable not in df.columns:

        return {

            "valid":
                False,

            "error":
                (
                    f"Dependent variable "
                    f"'{dependent_variable}' "
                    f"was not found in the dataframe."
                )

        }


    return {

        "valid":
            True

    }


# =====================================================
# CLEAN REGRESSION DATAFRAME
# =====================================================

def clean_regression_dataframe(
    df,
    independent_variables,
    dependent_variable
):
    """
    Selects and cleans the variables required for the
    requested regression.

    Returns
    -------
    pandas.DataFrame or None
        Returns a DataFrame if successful.
        Returns None if no rows remain after complete-case
        analysis. Diagnostic information is stored in the
        original df's attrs.
    """

    if df is None or df.empty:

        return None


    independent_variables = (

        list(
            independent_variables
            or []
        )

    )


    if not independent_variables:

        return None


    dependent_validation = (
        validate_dependent_variable(

            df,

            dependent_variable

        )
    )


    if not dependent_validation["valid"]:

        return None


    predictor_validation = (
        validate_predictors(

            df,

            independent_variables

        )
    )


    if not predictor_validation["valid"]:

        return None


    required_columns = (

        independent_variables
        +
        [dependent_variable]

    )


    required_columns = list(
        dict.fromkeys(
            required_columns
        )
    )


    working_df = df[
        required_columns
    ].copy()


    for column in independent_variables:

        working_df[column] = (

            normalize_categorical_series(

                working_df[column]

            )

        )


    working_df[dependent_variable] = (

        normalize_categorical_series(

            working_df[dependent_variable]

        )

    )


    initial_n = len(
        working_df
    )


    missing_counts = {}

    for column in required_columns:

        missing_count = working_df[column].isna().sum()

        if missing_count > 0:

            missing_counts[column] = int(missing_count)


    working_df = working_df.dropna(

        subset=required_columns

    )


    final_n = len(
        working_df
    )


    excluded_n = (

        initial_n
        -
        final_n

    )


    if working_df.empty:

        missing_summary = []

        for column, count in missing_counts.items():

            percent = round(
                count / initial_n * 100,
                1
            )

            missing_summary.append(
                f"{column}: {count} missing ({percent}%)"
            )


        df.attrs[
            "_clean_error"
        ] = (
            "No complete observations remain after "
            "complete-case analysis."
        )

        df.attrs[
            "_clean_missing_counts"
        ] = missing_counts

        df.attrs[
            "_clean_initial_n"
        ] = int(initial_n)

        df.attrs[
            "_clean_excluded_n"
        ] = int(excluded_n)

        df.attrs[
            "_clean_final_n"
        ] = 0

        df.attrs[
            "_clean_missing_summary"
        ] = missing_summary

        df.attrs[
            "_clean_required_columns"
        ] = required_columns

        return None


    working_df = working_df.reset_index(
        drop=True
    )


    working_df.attrs[
        "initial_n"
    ] = int(initial_n)


    working_df.attrs[
        "excluded_n"
    ] = int(excluded_n)


    working_df.attrs[
        "final_n"
    ] = int(final_n)


    if missing_counts:

        working_df.attrs[
            "missing_counts"
        ] = missing_counts


    return working_df


# =====================================================
# GET OUTCOME CATEGORIES
# =====================================================

def get_outcome_categories(
    df,
    dependent_variable
):
    """
    Returns observed non-missing outcome categories.

    Categories are returned in numeric-aware sorted
    order (numeric ranges first, then alphabetical).

    For ordinal outcomes, use
    get_ordered_outcome_categories() instead.
    """

    if (
        df is None
        or df.empty
        or dependent_variable not in df.columns
    ):

        return []


    categories = (

        df[dependent_variable]
        .dropna()
        .astype("string")
        .str.strip()
        .str.lower()
        .unique()
        .tolist()

    )


    categories = [

        str(category)

        for category in categories

        if category is not None
        and str(category).strip() != ""

    ]


    return _sort_categories(
        categories
    )


# =====================================================
# GET ORDERED OUTCOME CATEGORIES
# =====================================================

def get_ordered_outcome_categories(
    df,
    dependent_variable,
    category_order
):
    """
    Returns observed outcome categories according to
    a predefined ordinal order.

    Example
    -------
    category_order =

        [
            "resistant",
            "intermediate",
            "susceptible"
        ]

    If only resistant and susceptible are observed,
    the returned order will be:

        [
            "resistant",
            "susceptible"
        ]
    """

    if (
        df is None
        or df.empty
        or dependent_variable not in df.columns
    ):

        return []


    observed = set(

        get_outcome_categories(

            df,

            dependent_variable

        )

    )


    return [

        category

        for category in category_order

        if category in observed

    ]


# =====================================================
# GET OUTCOME DISTRIBUTION
# =====================================================

def get_outcome_distribution(
    df,
    dependent_variable,
    category_order=None
):
    """
    Returns category frequencies and percentages.

    If category_order is supplied, the result follows
    that order. Otherwise categories are returned in
    descending frequency order.
    """

    if (
        df is None
        or df.empty
        or dependent_variable not in df.columns
    ):

        return []


    series = (

        df[dependent_variable]
        .dropna()
        .astype("string")
        .str.strip()
        .str.lower()

    )


    series = series[
        series.notna()
    ]


    if series.empty:

        return []


    counts = series.value_counts()

    total = counts.sum()


    if category_order is not None:

        ordered_categories = [

            category

            for category in category_order

            if category in counts.index

        ]

    else:

        ordered_categories = (

            counts.index
            .astype(str)
            .tolist()

        )


    results = []


    for category in ordered_categories:

        count = int(
            counts.get(
                category,
                0
            )
        )


        percentage = (

            (
                float(count)
                /
                float(total)
            )
            *
            100.0

            if total > 0

            else 0.0

        )


        results.append({

            "category":
                str(category),

            "n":
                count,

            "percentage":
                round(
                    percentage,
                    2
                )

        })


    return results


# =====================================================
# VALIDATE BINARY OUTCOME
# =====================================================

def validate_binary_outcome(
    df,
    dependent_variable,
    expected_categories=None
):
    """
    Validates a binary outcome.

    Requirement:

        Exactly 2 observed categories.

    If expected_categories is supplied, all observed
    categories must belong to that set.
    """

    if (
        df is None
        or df.empty
        or dependent_variable not in df.columns
    ):

        return {

            "valid":
                False,

            "error":
                "Dependent variable is unavailable."

        }


    categories = get_outcome_categories(

        df,

        dependent_variable

    )


    if expected_categories is not None:

        expected = {

            str(category)
            .strip()
            .lower()

            for category
            in expected_categories

        }


        unexpected = [

            category

            for category in categories

            if category not in expected

        ]


        if unexpected:

            return {

                "valid":
                    False,

                "error":
                    (
                        "The dependent variable contains "
                        "unexpected outcome category/categories."
                    ),

                "categories":
                    categories,

                "unexpected_categories":
                    unexpected

            }


    if len(categories) != 2:

        return {

            "valid":
                False,

            "error":
                (
                    "Binary logistic regression requires "
                    "exactly 2 observed outcome categories. "
                    f"Found {len(categories)}."
                ),

            "categories":
                categories

        }


    return {

        "valid":
            True,

        "categories":
            categories

    }


# =====================================================
# VALIDATE MULTINOMIAL OUTCOME
# =====================================================

def validate_multinomial_outcome(
    df,
    dependent_variable
):
    """
    Validates a nominal multinomial outcome.

    Requirement:

        At least 3 observed categories.
    """

    if (
        df is None
        or df.empty
        or dependent_variable not in df.columns
    ):

        return {

            "valid":
                False,

            "error":
                "Dependent variable is unavailable."

        }


    categories = get_outcome_categories(

        df,

        dependent_variable

    )


    if len(categories) < 3:

        return {

            "valid":
                False,

            "error":
                (
                    "Multinomial logistic regression "
                    "requires at least 3 observed outcome "
                    "categories."
                ),

            "categories":
                categories

        }


    return {

        "valid":
            True,

        "categories":
            categories

    }


# =====================================================
# VALIDATE ORDINAL OUTCOME
# =====================================================

def validate_ordinal_outcome(
    df,
    dependent_variable,
    category_order=None
):
    """
    Validates an ordinal outcome.

    Default ordering:

        resistant
        intermediate
        susceptible

    At least 2 observed ordered categories are required.

    Missing intermediate categories are allowed.
    """

    if (
        df is None
        or df.empty
        or dependent_variable not in df.columns
    ):

        return {

            "valid":
                False,

            "error":
                "Dependent variable is unavailable."

        }


    if category_order is None:

        category_order = [

            "resistant",

            "intermediate",

            "susceptible"

        ]


    normalized_order = [

        str(category)
        .strip()
        .lower()

        for category
        in category_order

    ]


    observed = get_outcome_categories(

        df,

        dependent_variable

    )


    unexpected_categories = [

        category

        for category in observed

        if category not in normalized_order

    ]


    if unexpected_categories:

        return {

            "valid":
                False,

            "error":
                (
                    "Unexpected ordinal outcome "
                    "category/categories."
                ),

            "unexpected_categories":
                unexpected_categories,

            "categories":
                observed

        }


    observed_ordered_categories = (

        get_ordered_outcome_categories(

            df,

            dependent_variable,

            normalized_order

        )

    )


    if len(observed_ordered_categories) < 2:

        return {

            "valid":
                False,

            "error":
                (
                    "Ordinal logistic regression "
                    "requires at least 2 observed "
                    "ordered outcome categories."
                ),

            "categories":
                observed_ordered_categories

        }


    return {

        "valid":
            True,

        "categories":
            observed_ordered_categories,

        "category_order":
            normalized_order

    }


# =====================================================
# BUILD DESIGN MATRIX
# =====================================================

def build_design_matrix(
    df,
    independent_variables
):
    """
    Builds a dummy-coded predictor matrix.

    All predictors are treated as categorical.

    For each predictor:

        - observed categories are identified
        - categories are sorted with numeric awareness
        - first category becomes the reference
        - remaining categories become dummy variables

    An intercept is added.

    If the design matrix is singular (perfect
    multicollinearity), redundant columns are removed
    automatically.

    Returns
    -------
    X : pandas.DataFrame

    reference_categories : dict
    """

    if df is None or df.empty:

        return (

            pd.DataFrame(
                index=(
                    df.index
                    if df is not None
                    else None
                )
            ),

            {}

        )


    independent_variables = (

        list(
            independent_variables
            or []
        )

    )


    reference_categories = {}

    encoded_frames = []


    for column in independent_variables:

        if column not in df.columns:

            continue


        # ---------------------------------------------
        # Normalize predictor
        # ---------------------------------------------

        series = normalize_categorical_series(

            df[column]

        )


        # ---------------------------------------------
        # Identify observed categories
        # ---------------------------------------------

        categories = (

            series
            .dropna()
            .astype(str)
            .unique()
            .tolist()

        )


        categories = _sort_categories(
            categories
        )


        if not categories:

            continue


        reference_category = categories[0]


        reference_categories[
            column
        ] = reference_category


        # ---------------------------------------------
        # Dummy encoding
        # ---------------------------------------------

        categorical_series = pd.Categorical(

            series,

            categories=categories,

            ordered=False

        )


        dummies = pd.get_dummies(

            categorical_series,

            prefix=column,

            drop_first=True,

            dtype=float

        )


        dummies.index = df.index


        if not dummies.empty:

            encoded_frames.append(
                dummies
            )


    # =================================================
    # COMBINE DUMMIES
    # =================================================

    if encoded_frames:

        X = pd.concat(

            encoded_frames,

            axis=1

        )

    else:

        X = pd.DataFrame(
            index=df.index
        )


    if not X.empty:

        X = X.astype(float)


    # =================================================
    # ADD INTERCEPT
    # =================================================

    X = add_constant(

        X,

        has_constant="add"

    )


    # =================================================
    # HANDLE SINGULAR MATRIX
    #
    # If the design matrix is singular (perfect
    # multicollinearity, e.g. district + block with
    # aligned categories), drop one redundant column
    # at a time until the matrix becomes full rank.
    #
    # Zero-variance columns are removed first (bulk
    # removal is faster than one-by-one).
    #
    # Silence on success: callers get a usable matrix
    # without console noise. If the matrix cannot be
    # repaired, it is returned as-is and downstream
    # rank checks will produce a user-facing error.
    # =================================================

    try:

        zero_var_cols = find_zero_variance_columns(X)

        if zero_var_cols:

            X = X.drop(columns=zero_var_cols)


        while X.shape[1] > 0:

            rank = np.linalg.matrix_rank(X.values)

            if rank >= X.shape[1]:

                break


            removed = False

            for col in list(X.columns):

                if col == "const":

                    continue

                temp = X.drop(columns=[col])

                if np.linalg.matrix_rank(temp.values) == rank:

                    X = temp

                    removed = True

                    break


            if not removed:

                break

    except Exception:

        pass


    return (

        X,

        reference_categories

    )


# =====================================================
# GET PREDICTOR LEVELS
# =====================================================

def get_predictor_levels(
    df,
    independent_variables
):
    """
    Returns observed levels for each predictor.
    """

    levels = {}


    if df is None or df.empty:

        return levels


    for column in independent_variables:

        if column not in df.columns:

            continue


        series = normalize_categorical_series(

            df[column]

        )


        categories = (

            series
            .dropna()
            .astype(str)
            .unique()
            .tolist()

        )


        levels[column] = _sort_categories(
            categories
        )


    return levels


# =====================================================
# FIND ZERO-VARIANCE COLUMNS
# =====================================================

def find_zero_variance_columns(X):
    """
    Identifies predictor/dummy columns with no
    variation.

    The intercept is ignored.
    """

    if X is None or X.empty:

        return []


    zero_variance_columns = []


    for column in X.columns:

        if column == "const":

            continue


        try:

            n_unique = X[column].nunique(
                dropna=False
            )

        except Exception:

            zero_variance_columns.append(
                column
            )

            continue


        if n_unique <= 1:

            zero_variance_columns.append(
                column
            )


    return zero_variance_columns


# =====================================================
# REMOVE ZERO-VARIANCE COLUMNS
# =====================================================

def remove_zero_variance_columns(X):
    """
    Removes zero-variance predictor/dummy columns.

    The intercept is retained.

    Returns
    -------
    X_clean : pandas.DataFrame

    removed_columns : list
    """

    if X is None or X.empty:

        return X, []


    zero_variance = (
        find_zero_variance_columns(
            X
        )
    )


    if not zero_variance:

        return X.copy(), []


    keep_columns = [

        column

        for column in X.columns

        if column not in zero_variance

    ]


    return (

        X[
            keep_columns
        ].copy(),

        zero_variance

    )


# =====================================================
# CALCULATE VIF
# =====================================================

def calculate_vif(X):
    """
    Calculates variance inflation factors.

    The intercept is excluded.

    Columns that have zero variance or cannot produce
    a finite VIF receive None.

    Returns
    -------
    list of dictionaries
    """

    if X is None or X.empty:

        return []


    predictor_columns = [

        column

        for column in X.columns

        if column != "const"

    ]


    if not predictor_columns:

        return []


    zero_variance_columns = set(

        find_zero_variance_columns(X)

    )


    variable_columns = [

        column

        for column in predictor_columns

        if column not in zero_variance_columns

    ]


    if len(variable_columns) < 2:

        return [

            {

                "variable":
                    column,

                "vif":
                    None

            }

            for column in predictor_columns

        ]


    predictors = X[
        variable_columns
    ].copy()


    try:

        predictors = predictors.astype(float)

    except Exception:

        return [

            {

                "variable":
                    column,

                "vif":
                    None

            }

            for column in predictor_columns

        ]


    vif_values = []


    for index, column in enumerate(
        variable_columns
    ):

        try:

            vif = variance_inflation_factor(

                predictors.values,

                index

            )

        except Exception:

            vif = None


        if (

            vif is not None

            and

            np.isfinite(vif)

        ):

            vif = round(

                float(vif),

                4

            )

        else:

            vif = None


        vif_values.append({

            "variable":
                column,

            "vif":
                vif

        })


    for column in predictor_columns:

        if column in zero_variance_columns:

            vif_values.append({

                "variable":
                    column,

                "vif":
                    None

            })


    vif_lookup = {

        item["variable"]:
            item["vif"]

        for item in vif_values

    }


    return [

        {

            "variable":
                column,

            "vif":
                vif_lookup.get(
                    column
                )

        }

        for column in predictor_columns

    ]


# =====================================================
# FIND RARE CATEGORIES
# =====================================================

def find_rare_categories(
    df,
    independent_variables,
    minimum_count=5
):
    """
    Identifies predictor categories with fewer than
    minimum_count observations.

    Rare categories are reported only.
    """

    if df is None or df.empty:

        return {}


    independent_variables = (

        list(
            independent_variables
            or []
        )

    )


    rare_categories = {}


    for column in independent_variables:

        if column not in df.columns:

            continue


        series = normalize_categorical_series(

            df[column]

        )


        counts = series.dropna().value_counts()


        rare = {

            str(category):
                int(count)

            for category, count
            in counts.items()

            if count < minimum_count

        }


        if rare:

            rare_categories[
                column
            ] = rare


    return rare_categories


# =====================================================
# GET REFERENCE CATEGORIES
# =====================================================

def get_reference_categories(
    df,
    independent_variables
):
    """
    Returns the reference category for each categorical
    predictor.

    The first observed category in numeric-aware sorted
    order is used as the reference category.

    This uses the same rule as build_design_matrix().
    """

    if df is None or df.empty:

        return {}


    _, reference_categories = build_design_matrix(

        df,

        independent_variables

    )


    return reference_categories


# =====================================================
# GET NUMBER OF PARAMETERS
# =====================================================

def get_number_of_parameters(X):
    """
    Returns the number of columns in the design matrix,
    including the intercept.
    """

    if X is None:

        return 0


    if not isinstance(
        X,
        pd.DataFrame
    ):

        return 0


    return int(
        X.shape[1]
    )


# =====================================================
# GET SAMPLE INFORMATION
# =====================================================

def get_sample_information(df):
    """
    Returns standardized sample-size information from
    a cleaned regression dataframe.
    """

    if df is None:

        return {

            "initial_n":
                0,

            "excluded_n":
                0,

            "n":
                0

        }


    initial_n = df.attrs.get(

        "initial_n",

        len(df)

    )


    excluded_n = df.attrs.get(

        "excluded_n",

        0

    )


    final_n = df.attrs.get(

        "final_n",

        len(df)

    )


    return {

        "initial_n":
            int(initial_n),

        "excluded_n":
            int(excluded_n),

        "n":
            int(final_n)

    }