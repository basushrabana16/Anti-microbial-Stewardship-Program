# =====================================================
# REGRESSION HELPERS
# =====================================================
#
# Common utility functions used by:
#
#     regression_data.py
#     binary_logistic.py
#     multinomial_logistic.py
#     ordinal_logistic.py
#     regression_diagnostics.py
#
# This module is responsible for:
#
#     - categorical normalization
#     - regression dataframe preparation
#     - complete-case cleaning
#     - outcome validation
#     - outcome distributions
#     - category ordering
#     - design-matrix construction
#     - reference-category identification
#     - predictor-level identification
#     - VIF calculation
#     - zero-variance detection
#     - rare-category detection
#
# This module DOES NOT:
#
#     - select the regression model
#     - filter positive cultures
#     - select antibiotics
#     - fit a regression model
#     - calculate regression coefficients
#     - perform model diagnostics
#
# Model selection is handled by:
#
#     regression_data.py
#
# using:
#
#     regression_metadata.py
#
# =====================================================


import numpy as np
import pandas as pd

from statsmodels.api import add_constant

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
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
    #
    # Includes derived columns from association_metadata.py:
    #   - age_group (derived from age_years)
    #   - collection_month (derived from collection_date)
    #   - collection_season (derived from collection_month)
    #
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

        # Derived columns from association_metadata.py
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

    Operations:

        1. Validate requested variables
        2. Select required columns
        3. Normalize predictors
        4. Normalize outcome
        5. Remove incomplete observations
        6. Store sample-size information in attrs

    Returns
    -------
    pandas.DataFrame or None
        Returns a DataFrame if successful.
        Returns None if no rows remain after complete-case analysis.
        Diagnostic information is stored in the original df's attrs.

    NOTE
    ----
    This function does NOT:

        - filter positive cultures
        - select an antibiotic
        - select a regression model
        - remove rare categories
        - combine categories

    Those decisions belong to the data/model layers.
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


    # =================================================
    # VALIDATE DEPENDENT VARIABLE
    # =================================================

    dependent_validation = (
        validate_dependent_variable(

            df,

            dependent_variable

        )
    )


    if not dependent_validation["valid"]:

        return None


    # =================================================
    # VALIDATE PREDICTORS
    # =================================================

    predictor_validation = (
        validate_predictors(

            df,

            independent_variables

        )
    )


    if not predictor_validation["valid"]:

        return None


    # =================================================
    # REQUIRED COLUMNS
    # =================================================

    required_columns = (

        independent_variables
        +
        [dependent_variable]

    )


    # Remove duplicates while preserving order

    required_columns = list(
        dict.fromkeys(
            required_columns
        )
    )


    # =================================================
    # SELECT REQUIRED DATA
    # =================================================

    working_df = df[
        required_columns
    ].copy()


    # =================================================
    # NORMALIZE PREDICTORS
    # =================================================

    for column in independent_variables:

        working_df[column] = (

            normalize_categorical_series(

                working_df[column]

            )

        )


    # =================================================
    # NORMALIZE DEPENDENT VARIABLE
    # =================================================

    working_df[dependent_variable] = (

        normalize_categorical_series(

            working_df[dependent_variable]

        )

    )


    # =================================================
    # SAMPLE SIZE BEFORE COMPLETE-CASE ANALYSIS
    # =================================================

    initial_n = len(
        working_df
    )


    # =================================================
    # CHECK FOR MISSING DATA BEFORE DROPPING
    # =================================================
    #
    # This provides detailed diagnostic information
    # for debugging when no rows remain.
    #
    # =================================================

    missing_counts = {}

    for column in required_columns:

        missing_count = working_df[column].isna().sum()

        if missing_count > 0:

            missing_counts[column] = int(missing_count)


    # =================================================
    # COMPLETE-CASE ANALYSIS
    # =================================================

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


    # =================================================
    # HANDLE EMPTY DATAFRAME
    # =================================================
    #
    # If no rows remain, store diagnostic information
    # in the original dataframe's attrs and return None.
    #
    # The caller can access:
    #
    #     df.attrs.get("_clean_error")
    #     df.attrs.get("_clean_missing_counts")
    #     df.attrs.get("_clean_initial_n")
    #     df.attrs.get("_clean_excluded_n")
    #
    # =================================================

    if working_df.empty:

        # Store diagnostic information on the original df
        # so the caller can access it.

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


    # =================================================
    # RESET INDEX
    # =================================================

    working_df = working_df.reset_index(
        drop=True
    )


    # =================================================
    # STORE SAMPLE INFORMATION
    # =================================================

    working_df.attrs[
        "initial_n"
    ] = int(
        initial_n
    )


    working_df.attrs[
        "excluded_n"
    ] = int(
        excluded_n
    )


    working_df.attrs[
        "final_n"
    ] = int(
        final_n
    )


    # Store missing information for debugging

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

    Categories are returned in sorted order.

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


    return sorted(
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

    This allows regression_data.py to enforce the
    metadata-defined categories:

        negative
        positive
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

    A two-category outcome should be handled by binary
    logistic regression instead.
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

    Example:

        resistant
        susceptible

    remains a valid two-level ordered outcome.
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
        - categories are sorted
        - first category becomes the reference
        - remaining categories become dummy variables

    An intercept is added.

    If the design matrix is singular (perfect multicollinearity),
    redundant columns are removed automatically.

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


        categories = sorted(
            categories
        )


        # ---------------------------------------------
        # No usable categories
        # ---------------------------------------------

        if not categories:

            continue


        # ---------------------------------------------
        # Reference category
        # ---------------------------------------------

        reference_category = categories[0]


        reference_categories[
            column
        ] = reference_category


        # ---------------------------------------------
        # Convert to categorical
        # ---------------------------------------------

        categorical_series = pd.Categorical(

            series,

            categories=categories,

            ordered=False

        )


        # ---------------------------------------------
        # Dummy encoding
        # ---------------------------------------------

        dummies = pd.get_dummies(

            categorical_series,

            prefix=column,

            drop_first=True,

            dtype=float

        )


        # Preserve original dataframe index

        dummies.index = df.index


        # ---------------------------------------------
        # Add only if dummy columns exist
        # ---------------------------------------------

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


    # =================================================
    # ENSURE NUMERIC MATRIX
    # =================================================

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
    # =================================================
    #
    # If the design matrix is singular, remove columns
    # one by one until it becomes full rank.
    #
    # This typically happens when there is perfect
    # multicollinearity (e.g., district + block).
    #
    # =================================================

    # Try to get a full rank matrix
    try:

        # Check if matrix is singular
        rank = np.linalg.matrix_rank(X.values)
        cols = X.shape[1]

        if rank < cols:

            print(f"WARNING: Design matrix is singular (rank={rank}, columns={cols})")
            print(f"Removing redundant columns to achieve full rank...")

            # Remove columns with zero variance first
            zero_var_cols = find_zero_variance_columns(X)
            if zero_var_cols:
                X = X.drop(columns=zero_var_cols)
                print(f"Removed zero-variance columns: {zero_var_cols}")

            # If still singular, use QR decomposition to find rank-deficient columns
            rank = np.linalg.matrix_rank(X.values)
            cols = X.shape[1]

            if rank < cols:
                # Use QR decomposition to identify redundant columns
                # This is a simple approach: check each column's contribution
                columns_to_drop = []
                for i, col in enumerate(X.columns):
                    if col == "const":
                        continue
                    # Test if column can be expressed as linear combination of others
                    temp_X = X.drop(columns=[col]).values
                    temp_rank = np.linalg.matrix_rank(temp_X)
                    full_rank = np.linalg.matrix_rank(X.drop(columns=[col]).values)
                    # If dropping the column doesn't change the rank, it's redundant
                    # Actually, we need a simpler approach

                # Simpler approach: remove columns one by one until full rank
                temp_X = X.copy()
                cols_to_remove = []
                for col in X.columns:
                    if col == "const":
                        continue
                    temp_rank = np.linalg.matrix_rank(temp_X.drop(columns=[col]).values)
                    if temp_rank == np.linalg.matrix_rank(temp_X.values):
                        cols_to_remove.append(col)
                        temp_X = temp_X.drop(columns=[col])

                if cols_to_remove:
                    X = X.drop(columns=cols_to_remove)
                    print(f"Removed redundant columns: {cols_to_remove}")

    except Exception as e:
        print(f"Warning: Could not automatically fix singular matrix: {e}")

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


        levels[column] = sorted(
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

    VIF is calculated on the dummy-coded predictor
    matrix.

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


    # -------------------------------------------------
    # Fewer than two varying predictors
    # -------------------------------------------------

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


    # -------------------------------------------------
    # Ensure numeric values
    # -------------------------------------------------

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


    # -------------------------------------------------
    # Add zero-variance columns
    # -------------------------------------------------

    for column in predictor_columns:

        if column in zero_variance_columns:

            vif_values.append({

                "variable":
                    column,

                "vif":
                    None

            })


    # -------------------------------------------------
    # Preserve original predictor order
    # -------------------------------------------------

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

    They are NOT automatically removed or combined.
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

    The first observed category in sorted order is
    used as the reference category.

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