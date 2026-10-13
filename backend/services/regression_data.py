# =====================================================
# REGRESSION DATA PREPARATION
# =====================================================
#
# This module is responsible for preparing the filtered
# analysis dataframe for regression.
#
# IMPORTANT
# ---------
#
# The USER selects:
#
#     - independent variables
#     - dependent variable
#     - antibiotic when required
#
# The USER does NOT select the regression model.
#
# The backend automatically determines the model from:
#
#     1. Dependent variable type
#     2. Observed outcome categories
#     3. Outcome ordering where applicable
#
# -----------------------------------------------------
#
# Automatic model selection
#
# culture_result
#     2 categories
#         -> Binary Logistic Regression
#
# organism_identification
#     2 categories
#         -> Binary Logistic Regression
#
#     >2 categories
#         -> Multinomial Logistic Regression
#
# antibiogram_susceptibility
#     2 categories
#         -> Binary Logistic Regression
#
#     >=3 ordered categories
#         -> Ordinal Logistic Regression
#
# age_group
#     2 categories
#         -> Binary Logistic Regression
#
#     >=3 ordered categories
#         -> Ordinal Logistic Regression
#
# -----------------------------------------------------
#
# This module does NOT fit a statistical model.
#
# Its responsibility is:
#
#     filtered dataframe
#             ↓
#     validate variables
#             ↓
#     apply outcome-specific restrictions
#             ↓
#     create standardized outcome if required
#             ↓
#     complete-case analysis
#             ↓
#     determine observed outcome categories
#             ↓
#     automatically select regression model
#             ↓
#     validate outcome
#             ↓
#     return regression-ready dataframe
#
# =====================================================


import pandas as pd


# =====================================================
# METADATA
# =====================================================

from services.regression_metadata import (
    get_regression_options,
    get_outcome_metadata,
    get_automatic_model
)


# =====================================================
# HELPERS
# =====================================================

from services.regression_helpers import (
    prepare_regression_dataframe,
    clean_regression_dataframe,
    get_outcome_distribution,
    validate_binary_outcome,
    validate_multinomial_outcome,
    validate_ordinal_outcome,
    get_predictor_levels,
    validate_predictors
)


# =====================================================
# CONSTANTS
# =====================================================

CULTURE_RESULT_COLUMN = (
    "culture_result"
)


ORGANISM_COLUMN = (
    "organism_identification"
)


ANTIBIOGRAM_COLUMN = (
    "antibiogram_susceptibility"
)


AGE_GROUP_COLUMN = (
    "age_group"
)


ANTIBIOTIC_METADATA_KEY = (
    "antibiotic_columns"
)


POSITIVE_CULTURE = (
    "positive"
)


ANTIBIOGRAM_ORDER = [

    "resistant",

    "intermediate",

    "susceptible"

]


SUPPORTED_DEPENDENT_VARIABLES = [

    CULTURE_RESULT_COLUMN,

    ORGANISM_COLUMN,

    ANTIBIOGRAM_COLUMN,

    AGE_GROUP_COLUMN

]


# =====================================================
# NORMALIZE SINGLE VALUE
# =====================================================

def _normalize_value(value):
    """
    Converts a single categorical value into the
    normalized representation used by the regression
    backend.

    Examples
    --------
    " Positive " -> "positive"
    "Male"       -> "male"
    None         -> None
    """

    if value is None:

        return None


    try:

        if pd.isna(value):

            return None

    except (TypeError, ValueError):

        pass


    value = str(
        value
    ).strip().lower()


    if value in {

        "",
        "nan",
        "none",
        "null",
        "<na>"

    }:

        return None


    return value


# =====================================================
# NORMALIZE COLUMN
# =====================================================

def _normalize_column(series):
    """
    Returns a normalized categorical Series.

    The original Series is not modified.
    """

    normalized = (

        series
        .astype("string")
        .str.strip()
        .str.lower()

    )


    normalized = normalized.replace({

        "": pd.NA,

        "nan": pd.NA,

        "none": pd.NA,

        "null": pd.NA,

        "<na>": pd.NA

    })


    return normalized


# =====================================================
# GET DEFAULT REGRESSION PREDICTORS
# =====================================================

def get_default_predictors():
    """
    Gets the available regression predictors from
    regression_metadata.py.

    This avoids duplicating the predictor list.
    """

    options = get_regression_options()


    return list(

        options.get(

            "independent_variables",

            []

        )

    )


# =====================================================
# CHECK PREDICTOR COLUMNS
# =====================================================

def _check_predictor_columns(
    df,
    independent_variables
):
    """
    Returns predictor columns that are missing from
    the dataframe.
    """

    if df is None:

        return list(
            independent_variables
        )


    return [

        column

        for column in independent_variables

        if column not in df.columns

    ]


# =====================================================
# GET ANTIBIOTIC COLUMNS
# =====================================================

def get_antibiotic_columns(df):
    """
    Returns antibiotic column names stored in:

        df.attrs["antibiotic_columns"]

    The function does not modify the dataframe.
    """

    if df is None:

        return []


    antibiotics = df.attrs.get(

        ANTIBIOTIC_METADATA_KEY,

        []

    )


    if antibiotics is None:

        return []


    if not isinstance(

        antibiotics,

        (list, tuple, set)

    ):

        return []


    cleaned = []


    for antibiotic in antibiotics:

        if antibiotic is None:

            continue


        antibiotic = str(
            antibiotic
        ).strip()


        if not antibiotic:

            continue


        cleaned.append(
            antibiotic
        )


    return sorted(
        list(
            set(cleaned)
        )
    )


# =====================================================
# FIND ANTIBIOTIC COLUMN
# =====================================================

def find_antibiotic_column(
    df,
    antibiotic
):
    """
    Finds the actual dataframe column corresponding to
    the selected antibiotic.

    Matching is:

        - case insensitive
        - whitespace insensitive
    """

    if df is None or df.empty:

        return None


    selected = _normalize_value(
        antibiotic
    )


    if selected is None:

        return None


    # -------------------------------------------------
    # Search metadata first
    # -------------------------------------------------

    antibiotic_columns = (
        get_antibiotic_columns(df)
    )


    for column in antibiotic_columns:

        normalized_column = (
            _normalize_value(column)
        )


        if normalized_column == selected:

            if column in df.columns:

                return column


    # -------------------------------------------------
    # Fallback: search dataframe columns
    # -------------------------------------------------

    for column in df.columns:

        normalized_column = (
            _normalize_value(column)
        )


        if normalized_column == selected:

            return column


    return None


# =====================================================
# FILTER POSITIVE CULTURES
# =====================================================

def filter_positive_cultures(df):
    """
    Restricts the dataframe to culture-positive records.

    Required for:

        - organism identification
        - antibiogram susceptibility
    """

    if df is None or df.empty:

        return df


    if CULTURE_RESULT_COLUMN not in df.columns:

        return pd.DataFrame(
            columns=df.columns
        )


    culture_values = _normalize_column(

        df[
            CULTURE_RESULT_COLUMN
        ]

    )


    return df.loc[
        culture_values == POSITIVE_CULTURE
    ].copy()


# =====================================================
# GET OUTCOME REQUIREMENTS
# =====================================================

def get_outcome_requirements(
    dependent_variable
):
    """
    Retrieves metadata describing the selected outcome.
    """

    dependent_variable = (
        _normalize_value(
            dependent_variable
        )
    )


    if dependent_variable is None:

        return None


    return get_outcome_metadata(
        dependent_variable
    )


# =====================================================
# GET MODEL FOR OUTCOME
# =====================================================

def get_model_for_outcome(
    dependent_variable,
    observed_categories=None
):
    """
    Automatically determines the regression model.

    IMPORTANT
    ---------
    The final model is determined using the observed
    outcome categories.

    Parameters
    ----------
    dependent_variable : str
        Selected dependent variable.

    observed_categories : list, optional
        Observed categories after filtering and
        complete-case analysis.

    Returns
    -------
    str or None
        Automatically selected model.
    """

    dependent_variable = (
        _normalize_value(
            dependent_variable
        )
    )


    if dependent_variable is None:

        return None


    # -------------------------------------------------
    # Categories are required for final automatic
    # model selection.
    # -------------------------------------------------

    if observed_categories is None:

        return None


    result = get_automatic_model(

        dependent_variable,

        observed_categories

    )


    if not result.get(
        "success",
        False
    ):

        return None


    return result.get(
        "model"
    )


# =====================================================
# DETERMINE AUTOMATIC MODEL
# =====================================================

def _determine_automatic_model(
    dependent_variable,
    observed_categories
):
    """
    Wrapper around get_automatic_model().

    Returns the complete model-selection result.
    """

    return get_automatic_model(

        dependent_variable,

        observed_categories

    )


# =====================================================
# GET OBSERVED OUTCOME CATEGORIES
# =====================================================

def _get_observed_categories(
    df,
    dependent_variable
):
    """
    Returns normalized, unique observed outcome
    categories from the dataframe.
    """

    if df is None:

        return []


    if dependent_variable not in df.columns:

        return []


    values = _normalize_column(

        df[
            dependent_variable
        ]

    )


    categories = [

        value

        for value in values.dropna().unique().tolist()

        if value is not None

    ]


    return categories


# =====================================================
# COMMON VALIDATION
# =====================================================

def _validate_common_inputs(
    df,
    independent_variables,
    dependent_variable
):
    """
    Performs validation common to all regression types.

    IMPORTANT
    ---------
    The regression model is NOT selected here because
    model selection requires the observed outcome
    categories after data preparation.
    """

    if df is None or df.empty:

        return {

            "valid": False,

            "error":
                "No data available for regression."

        }


    if not independent_variables:

        return {

            "valid": False,

            "error":
                "At least one independent variable "
                "must be selected."

        }


    if dependent_variable is None:

        return {

            "valid": False,

            "error":
                "A dependent variable must be selected."

        }


    dependent_variable = (
        _normalize_value(
            dependent_variable
        )
    )


    if dependent_variable not in (
        SUPPORTED_DEPENDENT_VARIABLES
    ):

        return {

            "valid": False,

            "error": (
                f"Unsupported dependent variable "
                f"'{dependent_variable}'."
            )

        }


    # -------------------------------------------------
    # Validate predictors
    # -------------------------------------------------

    predictor_validation = (
        validate_predictors(

            df,

            independent_variables

        )
    )


    if not predictor_validation["valid"]:

        return {

            "valid": False,

            "error":
                "One or more predictor columns are missing.",

            "missing_columns":
                predictor_validation[
                    "missing_variables"
                ]

        }


    # -------------------------------------------------
    # Dependent-variable validation
    #
    # antibiogram_susceptibility is generated later
    # from the selected antibiotic column.
    # -------------------------------------------------

    if (
        dependent_variable
        != ANTIBIOGRAM_COLUMN
        and
        dependent_variable not in df.columns
    ):

        return {

            "valid": False,

            "error":
                (
                    f"Dependent variable "
                    f"'{dependent_variable}' "
                    "is missing from the dataframe."
                )

        }


    return {

        "valid": True,

        "dependent_variable":
            dependent_variable

    }


# =====================================================
# BUILD SUCCESS RESPONSE
# =====================================================

def _build_success_response(
    regression_df,
    dependent_variable,
    model,
    independent_variables,
    outcome_validation
):
    """
    Builds the common response structure returned by
    all preparation functions.
    """

    outcome_distribution = (
        get_outcome_distribution(

            regression_df,

            dependent_variable

        )
    )


    predictor_levels = (
        get_predictor_levels(

            regression_df,

            independent_variables

        )
    )


    return {

        "success": True,

        "data":
            regression_df,

        "model":
            model,

        "dependent_variable":
            dependent_variable,

        "independent_variables":
            list(independent_variables),

        "outcome_categories":
            outcome_validation.get(
                "categories",
                []
            ),

        "outcome_distribution":
            outcome_distribution,

        "predictor_levels":
            predictor_levels,

        "initial_n":
            regression_df.attrs.get(
                "initial_n"
            ),

        "excluded_n":
            regression_df.attrs.get(
                "excluded_n"
            ),

        "final_n":
            regression_df.attrs.get(
                "final_n"
            )

    }


# =====================================================
# BUILD ERROR RESPONSE
# =====================================================

def _build_clean_error_response(
    dependent_variable,
    source_df,
    context=None
):
    """
    Builds a detailed error response when
    clean_regression_dataframe() returns None.

    This extracts diagnostic information from the
    source dataframe's attrs (which clean_regression_dataframe
    stores with _clean_ prefix).
    """

    error_response = {

        "success": False,

        "dependent_variable":
            dependent_variable,

        "error":
            "No complete observations are available "
            "for the selected regression variables."

    }

    # Extract diagnostic information from source_df.attrs
    if source_df is not None and hasattr(source_df, "attrs"):

        attrs = source_df.attrs

        # Check for _clean_ prefixed diagnostics
        if "_clean_missing_counts" in attrs:

            error_response["missing_counts"] = (
                attrs["_clean_missing_counts"]
            )

        if "_clean_missing_summary" in attrs:

            error_response["missing_summary"] = (
                attrs["_clean_missing_summary"]
            )

        if "_clean_initial_n" in attrs:

            error_response["initial_n"] = (
                attrs["_clean_initial_n"]
            )

        if "_clean_excluded_n" in attrs:

            error_response["excluded_n"] = (
                attrs["_clean_excluded_n"]
            )

        if "_clean_final_n" in attrs:

            error_response["final_n"] = (
                attrs["_clean_final_n"]
            )

        if "_clean_error" in attrs:

            error_response["details"] = (
                attrs["_clean_error"]
            )

        if "_clean_required_columns" in attrs:

            error_response["required_columns"] = (
                attrs["_clean_required_columns"]
            )

        # Also check for non-prefixed attrs (fallback)
        if "missing_counts" in attrs and "_clean_missing_counts" not in attrs:

            error_response["missing_counts"] = (
                attrs["missing_counts"]
            )

        if "initial_n" in attrs and "_clean_initial_n" not in attrs:

            error_response["initial_n"] = (
                attrs["initial_n"]
            )

        if "excluded_n" in attrs and "_clean_excluded_n" not in attrs:

            error_response["excluded_n"] = (
                attrs["excluded_n"]
            )

    if context:

        error_response["context"] = context

    return error_response


# =====================================================
# VALIDATE AUTOMATIC MODEL
# =====================================================

def _validate_selected_model_outcome(
    regression_df,
    dependent_variable,
    model,
    categories
):
    """
    Validates the outcome according to the model selected
    automatically from the observed categories.

    This is intentionally independent of the static
    default model in regression_metadata.py.
    """

    if len(categories) < 2:

        return {

            "valid": False,

            "error": (
                "At least two observed outcome "
                "categories are required for regression."
            ),

            "categories":
                categories

        }


    # =================================================
    # BINARY LOGISTIC
    # =================================================

    if model == "binary_logistic":

        validation = validate_binary_outcome(

            regression_df,

            dependent_variable

        )


        return validation


    # =================================================
    # MULTINOMIAL LOGISTIC
    # =================================================

    if model == "multinomial_logistic":

        validation = validate_multinomial_outcome(

            regression_df,

            dependent_variable

        )


        return validation


    # =================================================
    # ORDINAL LOGISTIC
    # =================================================

    if model == "ordinal_logistic":

        validation = validate_ordinal_outcome(

            regression_df,

            dependent_variable

        )


        return validation


    return {

        "valid": False,

        "error": (
            f"Unsupported automatically selected "
            f"model '{model}'."
        ),

        "categories":
            categories

    }


# =====================================================
# PREPARE CULTURE RESULT DATA
# =====================================================

def prepare_culture_result_data(
    df,
    independent_variables=None
):
    """
    Prepares data for:

        Binary Logistic Regression

    Outcome:

        culture_result

    Both positive and negative cultures are retained.
    """

    if independent_variables is None:

        independent_variables = (
            get_default_predictors()
        )


    validation = _validate_common_inputs(

        df,

        independent_variables,

        CULTURE_RESULT_COLUMN

    )


    if not validation["valid"]:

        return validation


    # -------------------------------------------------
    # Prepare dataframe
    # -------------------------------------------------

    prepared_df = (
        prepare_regression_dataframe(
            df
        )
    )


    # -------------------------------------------------
    # Complete-case analysis
    # -------------------------------------------------

    cleaned_df = clean_regression_dataframe(

        prepared_df,

        independent_variables,

        CULTURE_RESULT_COLUMN

    )


    if cleaned_df is None:

        # Return detailed error with diagnostic info
        # from prepared_df.attrs (populated by clean_regression_dataframe)
        return _build_clean_error_response(

            CULTURE_RESULT_COLUMN,

            prepared_df,  # Pass the source df with attrs

            context={
                "independent_variables":
                    independent_variables,
                "prepared_rows":
                    len(prepared_df)
            }

        )


    regression_df = cleaned_df


    # -------------------------------------------------
    # Normalize outcome
    # -------------------------------------------------

    regression_df = regression_df.copy()

    regression_df[
        CULTURE_RESULT_COLUMN
    ] = _normalize_column(

        regression_df[
            CULTURE_RESULT_COLUMN
        ]

    )


    # -------------------------------------------------
    # Get observed categories
    # -------------------------------------------------

    categories = _get_observed_categories(

        regression_df,

        CULTURE_RESULT_COLUMN

    )


    # -------------------------------------------------
    # Automatic model selection
    # -------------------------------------------------

    model_selection = _determine_automatic_model(

        CULTURE_RESULT_COLUMN,

        categories

    )


    if not model_selection["success"]:

        return {

            "success": False,

            "dependent_variable":
                CULTURE_RESULT_COLUMN,

            "error":
                model_selection["error"],

            "categories":
                categories

        }


    model = model_selection["model"]


    # -------------------------------------------------
    # Validate outcome
    # -------------------------------------------------

    outcome_validation = (
        _validate_selected_model_outcome(

            regression_df,

            CULTURE_RESULT_COLUMN,

            model,

            categories

        )
    )


    if not outcome_validation["valid"]:

        return {

            "success": False,

            "model":
                model,

            "dependent_variable":
                CULTURE_RESULT_COLUMN,

            "error":
                outcome_validation["error"],

            "categories":
                outcome_validation.get(
                    "categories",
                    categories
                )

        }


    return _build_success_response(

        regression_df,

        CULTURE_RESULT_COLUMN,

        model,

        independent_variables,

        outcome_validation

    )


# =====================================================
# PREPARE ORGANISM IDENTIFICATION DATA
# =====================================================

def prepare_organism_identification_data(
    df,
    independent_variables=None
):
    """
    Prepares data for automatically selected:

        Binary Logistic Regression
        OR
        Multinomial Logistic Regression

    Outcome:

        organism_identification

    Only culture-positive observations are retained.
    """

    if independent_variables is None:

        independent_variables = (
            get_default_predictors()
        )


    validation = _validate_common_inputs(

        df,

        independent_variables,

        ORGANISM_COLUMN

    )


    if not validation["valid"]:

        return validation


    # -------------------------------------------------
    # Prepare dataframe
    # -------------------------------------------------

    prepared_df = (
        prepare_regression_dataframe(
            df
        )
    )


    # -------------------------------------------------
    # Positive cultures only
    # -------------------------------------------------

    positive_df = (
        filter_positive_cultures(
            prepared_df
        )
    )


    if positive_df.empty:

        return {

            "success": False,

            "dependent_variable":
                ORGANISM_COLUMN,

            "error": (
                "No culture-positive observations "
                "are available for organism regression."
            )

        }


    # -------------------------------------------------
    # Complete cases
    # -------------------------------------------------

    cleaned_df = clean_regression_dataframe(

        positive_df,

        independent_variables,

        ORGANISM_COLUMN

    )


    if cleaned_df is None:

        return _build_clean_error_response(

            ORGANISM_COLUMN,

            positive_df,  # Pass the source df with attrs

            context={
                "independent_variables":
                    independent_variables,
                "positive_rows":
                    len(positive_df)
            }

        )


    regression_df = cleaned_df


    # -------------------------------------------------
    # Normalize outcome
    # -------------------------------------------------

    regression_df = regression_df.copy()

    regression_df[
        ORGANISM_COLUMN
    ] = _normalize_column(

        regression_df[
            ORGANISM_COLUMN
        ]

    )


    # -------------------------------------------------
    # Get observed categories
    # -------------------------------------------------

    categories = _get_observed_categories(

        regression_df,

        ORGANISM_COLUMN

    )


    # -------------------------------------------------
    # Automatic model selection
    # -------------------------------------------------

    model_selection = _determine_automatic_model(

        ORGANISM_COLUMN,

        categories

    )


    if not model_selection["success"]:

        return {

            "success": False,

            "dependent_variable":
                ORGANISM_COLUMN,

            "error":
                model_selection["error"],

            "categories":
                categories

        }


    model = model_selection["model"]


    # -------------------------------------------------
    # Validate outcome according to selected model
    # -------------------------------------------------

    outcome_validation = (
        _validate_selected_model_outcome(

            regression_df,

            ORGANISM_COLUMN,

            model,

            categories

        )
    )


    if not outcome_validation["valid"]:

        return {

            "success": False,

            "model":
                model,

            "dependent_variable":
                ORGANISM_COLUMN,

            "error":
                outcome_validation["error"],

            "categories":
                outcome_validation.get(
                    "categories",
                    categories
                )

        }


    return _build_success_response(

        regression_df,

        ORGANISM_COLUMN,

        model,

        independent_variables,

        outcome_validation

    )


# =====================================================
# PREPARE ORDINAL OUTCOME DATA
# =====================================================

def prepare_ordinal_outcome_data(
    df,
    independent_variables=None,
    ordered_categories=None
):
    """
    Prepares data for ordinal logistic regression.

    Outcome:
        age_group (or other ordinal outcome)

    Expected categories:
        Explicitly ordered categories.

    Parameters:
        df: Input dataframe
        independent_variables: List of predictors
        ordered_categories: Explicit list of ordered categories

    Returns:
        dict with regression-ready data
    """

    if independent_variables is None:

        independent_variables = (
            get_default_predictors()
        )


    # Determine which ordinal outcome column to use
    # Currently supports age_group
    outcome_column = "age_group"

    validation = _validate_common_inputs(

        df,

        independent_variables,

        outcome_column

    )


    if not validation["valid"]:

        return validation


    prepared_df = (
        prepare_regression_dataframe(
            df
        )
    )


    regression_df = (
        clean_regression_dataframe(

            prepared_df,

            independent_variables,

            outcome_column

        )
    )


    if regression_df is None:

        return {

            "success": False,

            "dependent_variable":
                outcome_column,

            "error": (
                "No complete observations are "
                "available for the selected "
                "ordinal regression."
            )

        }


    # Normalize outcome
    regression_df = regression_df.copy()

    regression_df[
        outcome_column
    ] = _normalize_column(

        regression_df[
            outcome_column
        ]

    )


    # Get observed categories
    categories = _get_observed_categories(

        regression_df,

        outcome_column

    )


    # Automatic model selection
    model_selection = _determine_automatic_model(

        outcome_column,

        categories

    )


    if not model_selection["success"]:

        return {

            "success": False,

            "dependent_variable":
                outcome_column,

            "error":
                model_selection["error"],

            "categories":
                categories

        }


    model = model_selection["model"]


    # Validate outcome according to selected model
    outcome_validation = (
        _validate_selected_model_outcome(

            regression_df,

            outcome_column,

            model,

            categories

        )
    )


    if not outcome_validation["valid"]:

        return {

            "success": False,

            "model":
                model,

            "dependent_variable":
                outcome_column,

            "error":
                outcome_validation["error"],

            "categories":
                outcome_validation.get(
                    "categories",
                    categories
                )

        }


    return _build_success_response(

        regression_df,

        outcome_column,

        model,

        independent_variables,

        outcome_validation

    )


# =====================================================
# PREPARE ANTIBIOGRAM DATA
# =====================================================

def prepare_antibiogram_data(
    df,
    antibiotic,
    independent_variables=None
):
    """
    Prepares data for automatically selected:

        Binary Logistic Regression
        OR
        Ordinal Logistic Regression

    Outcome:

        Selected antibiotic susceptibility.

    Expected susceptibility categories:

        resistant
        intermediate
        susceptible

    Only culture-positive observations are retained.

    IMPORTANT
    ---------
    The antibiotic determines which dataframe column
    becomes the standardized dependent variable.

    The number of observed susceptibility categories
    determines the final regression model.
    """

    if independent_variables is None:

        independent_variables = (
            get_default_predictors()
        )


    # -------------------------------------------------
    # Validate common inputs
    # -------------------------------------------------

    validation = _validate_common_inputs(

        df,

        independent_variables,

        ANTIBIOGRAM_COLUMN

    )


    if not validation["valid"]:

        return validation


    # -------------------------------------------------
    # Validate selected antibiotic
    # -------------------------------------------------

    selected_antibiotic = (
        _normalize_value(
            antibiotic
        )
    )


    if selected_antibiotic is None:

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error":
                (
                    "A specific antibiotic must be "
                    "selected for antibiogram regression."
                )

        }


    if selected_antibiotic == "all":

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error":
                (
                    "'All' cannot be used as the "
                    "antibiogram outcome. Select a "
                    "specific antibiotic."
                )

        }


    # -------------------------------------------------
    # Prepare dataframe
    # -------------------------------------------------

    prepared_df = (
        prepare_regression_dataframe(
            df
        )
    )


    # -------------------------------------------------
    # Positive cultures only
    # -------------------------------------------------

    positive_df = (
        filter_positive_cultures(
            prepared_df
        )
    )


    if positive_df.empty:

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error": (
                "No culture-positive observations "
                "are available for antibiogram regression."
            )

        }


    # -------------------------------------------------
    # Find selected antibiotic
    # -------------------------------------------------

    antibiotic_column = (
        find_antibiotic_column(

            positive_df,

            antibiotic

        )
    )


    if antibiotic_column is None:

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error": (
                f"Selected antibiotic '{antibiotic}' "
                "was not found in the analysis dataframe."
            ),

            "available_antibiotics":
                get_antibiotic_columns(
                    positive_df
                )

        }


    # -------------------------------------------------
    # Create standardized susceptibility outcome
    # -------------------------------------------------

    positive_df = positive_df.copy()


    positive_df[
        ANTIBIOGRAM_COLUMN
    ] = _normalize_column(

        positive_df[
            antibiotic_column
        ]

    )


    # -------------------------------------------------
    # Check raw susceptibility categories
    # -------------------------------------------------

    observed_values = (

        positive_df[
            ANTIBIOGRAM_COLUMN
        ]
        .dropna()
        .unique()
        .tolist()

    )


    unexpected_values = [

        value

        for value in observed_values

        if value not in ANTIBIOGRAM_ORDER

    ]


    if unexpected_values:

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error": (
                "Unexpected susceptibility "
                "category/categories found."
            ),

            "antibiotic":
                antibiotic,

            "antibiotic_column":
                antibiotic_column,

            "unexpected_categories":
                unexpected_values,

            "expected_categories":
                ANTIBIOGRAM_ORDER

        }


    # -------------------------------------------------
    # Complete-case analysis
    # -------------------------------------------------

    cleaned_df = clean_regression_dataframe(

        positive_df,

        independent_variables,

        ANTIBIOGRAM_COLUMN

    )


    if cleaned_df is None:

        return _build_clean_error_response(

            ANTIBIOGRAM_COLUMN,

            positive_df,  # Pass the source df with attrs

            context={
                "independent_variables":
                    independent_variables,
                "antibiotic":
                    antibiotic,
                "positive_rows":
                    len(positive_df)
            }

        )


    regression_df = cleaned_df


    # -------------------------------------------------
    # Normalize final outcome
    # -------------------------------------------------

    regression_df = regression_df.copy()

    regression_df[
        ANTIBIOGRAM_COLUMN
    ] = _normalize_column(

        regression_df[
            ANTIBIOGRAM_COLUMN
        ]

    )


    # -------------------------------------------------
    # Get observed categories AFTER complete-case
    # analysis
    # -------------------------------------------------

    categories = _get_observed_categories(

        regression_df,

        ANTIBIOGRAM_COLUMN

    )


    # -------------------------------------------------
    # Check susceptibility categories again after
    # complete-case analysis
    # -------------------------------------------------

    unexpected_final = [

        value

        for value in categories

        if value not in ANTIBIOGRAM_ORDER

    ]


    if unexpected_final:

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error": (
                "Unexpected susceptibility "
                "category/categories remain after "
                "complete-case analysis."
            ),

            "antibiotic":
                antibiotic,

            "antibiotic_column":
                antibiotic_column,

            "unexpected_categories":
                unexpected_final,

            "expected_categories":
                ANTIBIOGRAM_ORDER

        }


    # -------------------------------------------------
    # Automatic model selection
    # -------------------------------------------------

    model_selection = _determine_automatic_model(

        ANTIBIOGRAM_COLUMN,

        categories

    )


    if not model_selection["success"]:

        return {

            "success": False,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error":
                model_selection["error"],

            "categories":
                categories,

            "antibiotic":
                antibiotic,

            "antibiotic_column":
                antibiotic_column

        }


    model = model_selection["model"]


    # -------------------------------------------------
    # Validate outcome according to selected model
    # -------------------------------------------------

    outcome_validation = (
        _validate_selected_model_outcome(

            regression_df,

            ANTIBIOGRAM_COLUMN,

            model,

            categories

        )
    )


    if not outcome_validation["valid"]:

        return {

            "success": False,

            "model":
                model,

            "dependent_variable":
                ANTIBIOGRAM_COLUMN,

            "error":
                outcome_validation["error"],

            "categories":
                outcome_validation.get(
                    "categories",
                    categories
                ),

            "antibiotic":
                antibiotic,

            "antibiotic_column":
                antibiotic_column

        }


    result = _build_success_response(

        regression_df,

        ANTIBIOGRAM_COLUMN,

        model,

        independent_variables,

        outcome_validation

    )


    # -------------------------------------------------
    # Antibiotic-specific metadata
    # -------------------------------------------------

    result["antibiotic"] = antibiotic

    result["antibiotic_column"] = (
        antibiotic_column
    )

    result["category_order"] = [

        category

        for category
        in ANTIBIOGRAM_ORDER

        if category in categories

    ]


    # -------------------------------------------------
    # Explicit model-selection metadata
    # -------------------------------------------------

    result["model_selection"] = {

        "automatic":
            True,

        "observed_categories":
            categories,

        "number_categories":
            len(categories),

        "model":
            model

    }


    return result


# =====================================================
# AUTOMATIC REGRESSION DATA DISPATCHER
# =====================================================

def prepare_regression_data(
    df,
    dependent_variable,
    independent_variables=None,
    antibiotic=None
):
    """
    Main entry point for regression data preparation.

    IMPORTANT
    ---------
    The caller supplies the DEPENDENT VARIABLE.

    The caller does NOT supply the model.

    The model is automatically determined from the
    observed outcome categories after data preparation.

    Parameters
    ----------
    df:
        Filtered analysis dataframe.

    dependent_variable:
        Selected outcome.

    independent_variables:
        User-selected predictors.

    antibiotic:
        Required only when the dependent variable is
        antibiogram_susceptibility.

    Returns
    -------
    dict
        Regression-ready data and metadata.
    """

    # =================================================
    # NORMALIZE OUTCOME
    # =================================================

    dependent_variable = (
        _normalize_value(
            dependent_variable
        )
    )


    # =================================================
    # VALIDATE OUTCOME
    # =================================================

    if dependent_variable is None:

        return {

            "success": False,

            "error":
                "A dependent variable must be selected."

        }


    if dependent_variable not in (
        SUPPORTED_DEPENDENT_VARIABLES
    ):

        return {

            "success": False,

            "error": (
                f"Unsupported dependent variable "
                f"'{dependent_variable}'."
            )

        }


    # =================================================
    # DEFAULT PREDICTORS
    # =================================================

    if independent_variables is None:

        independent_variables = (
            get_default_predictors()
        )


    # -------------------------------------------------
    # Ensure predictor list is a list
    # -------------------------------------------------

    if isinstance(
        independent_variables,
        str
    ):

        independent_variables = [

            independent_variables

        ]

    else:

        independent_variables = list(
            independent_variables
        )


    # =================================================
    # DISPATCH BASED ON OUTCOME
    # =================================================

    if dependent_variable == (
        CULTURE_RESULT_COLUMN
    ):

        return prepare_culture_result_data(

            df,

            independent_variables

        )


    if dependent_variable == (
        ORGANISM_COLUMN
    ):

        return prepare_organism_identification_data(

            df,

            independent_variables

        )


    if dependent_variable == (
        ANTIBIOGRAM_COLUMN
    ):

        return prepare_antibiogram_data(

            df,

            antibiotic,

            independent_variables

        )


    if dependent_variable == (
        AGE_GROUP_COLUMN
    ):

        return prepare_ordinal_outcome_data(

            df,

            independent_variables

        )


    # =================================================
    # SAFETY FALLBACK
    # =================================================

    return {

        "success": False,

        "error": (
            f"No regression preparation method "
            f"is defined for '{dependent_variable}'."
        )

    }


# =====================================================
# DETERMINE REGRESSION MODEL
# =====================================================

def determine_regression_model(
    dependent_variable,
    observed_categories=None
):
    """
    Public helper used by routes and other backend
    services.

    The model is automatically selected from the
    observed outcome categories IF provided.
    Otherwise, the default model from metadata is used.

    Examples
    --------
    determine_regression_model(
        "culture_result",
        ["negative", "positive"]
    )
        -> binary_logistic

    determine_regression_model(
        "organism_identification",
        ["ecoli", "klebsiella", "pseudomonas"]
    )
        -> multinomial_logistic
    """

    normalized_outcome = (
        _normalize_value(
            dependent_variable
        )
    )


    if normalized_outcome is None:

        return {

            "success": False,

            "error":
                "A dependent variable must be selected."

        }


    if normalized_outcome not in (
        SUPPORTED_DEPENDENT_VARIABLES
    ):

        return {

            "success": False,

            "error": (
                f"Unsupported dependent variable "
                f"'{normalized_outcome}'."
            )

        }


    # =================================================
    # IF observed_categories is provided, use automatic
    # model selection based on observed categories.
    # =================================================

    if observed_categories is not None:

        # Normalize categories
        if not isinstance(
            observed_categories,
            (list, tuple, set)
        ):

            observed_categories = [
                observed_categories
            ]

        normalized_categories = []

        for category in observed_categories:

            value = _normalize_value(
                category
            )

            if (
                value is not None
                and
                value not in normalized_categories
            ):

                normalized_categories.append(
                    value
                )

        # Automatic model selection
        result = _determine_automatic_model(

            normalized_outcome,

            normalized_categories

        )

        if not result["success"]:

            return result

        return {

            "success": True,

            "dependent_variable":
                normalized_outcome,

            "outcome_type":
                result.get(
                    "outcome_type"
                ),

            "observed_categories":
                normalized_categories,

            "number_categories":
                len(normalized_categories),

            "model":
                result["model"],

            "label":
                result.get(
                    "label"
                ),

            "requires_positive_culture":
                result.get(
                    "requires_positive_culture",
                    False
                ),

            "requires_antibiotic":
                result.get(
                    "requires_antibiotic",
                    False
                )

        }


    # =================================================
    # If observed_categories is NOT provided, use the
    # default model from metadata.
    # =================================================

    from services.regression_metadata import (
        get_default_model,
        get_outcome_metadata
    )

    model = get_default_model(
        normalized_outcome
    )

    if not model:

        return {

            "success": False,

            "error": (
                f"No default model is configured for "
                f"'{normalized_outcome}'."
            )

        }

    metadata = get_outcome_metadata(
        normalized_outcome
    )

    return {

        "success": True,

        "dependent_variable":
            normalized_outcome,

        "outcome_type":
            metadata.get(
                "outcome_type"
            ) if metadata else None,

        "observed_categories":
            None,

        "number_categories":
            None,

        "model":
            model,

        "label":
            metadata.get(
                "model_label"
            ) if metadata else model,

        "requires_positive_culture":
            metadata.get(
                "requires_positive_culture",
                False
            ) if metadata else False,

        "requires_antibiotic":
            metadata.get(
                "requires_antibiotic",
                False
            ) if metadata else False

    }