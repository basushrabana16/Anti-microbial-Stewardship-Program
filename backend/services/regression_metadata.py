# =====================================================
# REGRESSION METADATA
# =====================================================
#
# Central metadata/configuration for the regression
# framework.
#
# Supported models:
#
#     1. Binary Logistic Regression
#     2. Multinomial Logistic Regression
#     3. Ordinal Logistic Regression
#
# IMPORTANT
# ---------
# The USER does NOT select the regression model.
#
# The BACKEND automatically determines the appropriate
# model from:
#
#     1. Dependent variable type
#     2. Number of observed outcome categories
#     3. Whether the outcome has a natural ordering
#
# General logic:
#
#     Binary outcome
#           ↓
#     Binary Logistic Regression
#
#     Nominal outcome with >2 categories
#           ↓
#     Multinomial Logistic Regression
#
#     Ordered outcome with >2 categories
#           ↓
#     Ordinal Logistic Regression
#
#     Ordered outcome with 2 categories
#           ↓
#     Binary Logistic Regression
#
# Actual data validation is performed by
# regression_data.py.
#
# =====================================================


# =====================================================
# INDEPENDENT VARIABLES
# =====================================================
#
# These match the columns available in the analysis
# dataframe after add_derived_columns() from
# association_metadata.py has been applied.
#
# =====================================================

INDEPENDENT_VARIABLES = [

    "gender",

    "age_group",

    "district",

    "block",

    "sample_type",

    "referred_by",

    "collection_month",

    "collection_season"

]


# =====================================================
# DEPENDENT VARIABLES
# =====================================================

DEPENDENT_VARIABLES = [

    "culture_result",

    "organism_identification",

    "antibiogram_susceptibility"

]


# =====================================================
# VARIABLE TYPES
# =====================================================
#
# These describe the ORIGINAL predictor variables.
#
# Design-matrix encoding is handled by
# regression_helpers.py / regression_data.py.
#
# =====================================================

VARIABLE_TYPES = {

    "gender":
        "categorical",

    "age_group":
        "categorical",

    "district":
        "categorical",

    "block":
        "categorical",

    "sample_type":
        "categorical",

    "referred_by":
        "categorical",

    "collection_month":
        "categorical",

    "collection_season":
        "categorical"

}


# =====================================================
# OUTCOME METADATA
# =====================================================

OUTCOME_METADATA = {


    # =================================================
    # CULTURE RESULT
    # =================================================

    "culture_result": {

        "outcome_type":
            "binary",

        "label":
            "Culture Result",

        "expected_categories": [

            "negative",

            "positive"

        ],

        "category_order":
            None,

        "requires_positive_culture":
            False,

        "requires_antibiotic":
            False,

        "default_model":
            "binary_logistic",

        "model_label":
            "Binary Logistic Regression"

    },


    # =================================================
    # ORGANISM IDENTIFICATION
    # =================================================
    #
    # Nominal outcome.
    #
    # Number of observed categories determines model:
    #
    #     2 categories
    #         → Binary Logistic Regression
    #
    #     >2 categories
    #         → Multinomial Logistic Regression
    #
    # =================================================

    "organism_identification": {

        "outcome_type":
            "nominal",

        "label":
            "Organism Identification",

        "expected_categories":
            None,

        "category_order":
            None,

        "requires_positive_culture":
            True,

        "requires_antibiotic":
            False,

        "default_model":
            "multinomial_logistic",

        "model_label":
            "Multinomial Logistic Regression"

    },


    # =================================================
    # ANTIBIOGRAM SUSCEPTIBILITY
    # =================================================
    #
    # Natural ordering:
    #
    #     Resistant
    #          <
    #     Intermediate
    #          <
    #     Susceptible
    #
    # The actual antibiotic must be supplied separately.
    #
    # Model selection:
    #
    #     2 observed categories
    #         → Binary Logistic Regression
    #
    #     >=3 observed ordered categories
    #         → Ordinal Logistic Regression
    #
    # =================================================

    "antibiogram_susceptibility": {

        "outcome_type":
            "ordinal",

        "label":
            "Antibiogram Susceptibility",

        "expected_categories": [

            "resistant",

            "intermediate",

            "susceptible"

        ],

        "category_order": [

            "resistant",

            "intermediate",

            "susceptible"

        ],

        "requires_positive_culture":
            True,

        "requires_antibiotic":
            True,

        "default_model":
            "ordinal_logistic",

        "model_label":
            "Ordinal Logistic Regression"

    }

}


# =====================================================
# MODEL METADATA
# =====================================================

MODEL_METADATA = {

    "binary_logistic": {

        "label":
            "Binary Logistic Regression",

        "outcome_type":
            "binary",

        "minimum_categories":
            2,

        "maximum_categories":
            2

    },

    "multinomial_logistic": {

        "label":
            "Multinomial Logistic Regression",

        "outcome_type":
            "nominal",

        "minimum_categories":
            3,

        "maximum_categories":
            None

    },

    "ordinal_logistic": {

        "label":
            "Ordinal Logistic Regression",

        "outcome_type":
            "ordinal",

        "minimum_categories":
            3,

        "maximum_categories":
            None

    }

}


# =====================================================
# PREDICTOR EXCLUSION MAP
# =====================================================
#
# Prevents obvious outcome/predictor leakage.
#
# Currently:
#
#     No configured exclusions for the available
#     dependent variables.
#
# This structure can be extended later.
#
# =====================================================

EXCLUDED_PREDICTOR_MAP = {

    "culture_result": [],

    "organism_identification": [],

    "antibiogram_susceptibility": []

}


# =====================================================
# MAXIMUM NUMBER OF INDEPENDENT VARIABLES
# =====================================================

MAX_INDEPENDENT_VARIABLES = len(
    INDEPENDENT_VARIABLES
)


# =====================================================
# NORMALIZE CATEGORY
# =====================================================

def normalize_category(
    value
):
    """
    Converts an outcome category into a normalized
    string representation.
    """

    if value is None:

        return None

    return str(
        value
    ).strip().lower()


# =====================================================
# NORMALIZE CATEGORY LIST
# =====================================================

def normalize_categories(
    categories
):
    """
    Normalizes and removes duplicate outcome categories.
    """

    if categories is None:

        return []

    if not isinstance(
        categories,
        (list, tuple, set)
    ):

        categories = [
            categories
        ]

    normalized = []

    for category in categories:

        value = normalize_category(
            category
        )

        if value is not None and value != "":

            if value not in normalized:

                normalized.append(
                    value
                )

    return normalized


# =====================================================
# GET OUTCOME METADATA
# =====================================================

def get_outcome_metadata(
    dependent_variable
):
    """
    Returns metadata for a dependent variable.

    Returns
    -------
    dict or None
    """

    if dependent_variable not in OUTCOME_METADATA:

        return None

    metadata = OUTCOME_METADATA[
        dependent_variable
    ]

    result = {}

    for key, value in metadata.items():

        if isinstance(
            value,
            list
        ):

            result[key] = value.copy()

        elif isinstance(
            value,
            dict
        ):

            result[key] = value.copy()

        else:

            result[key] = value

    return result


# =====================================================
# GET VARIABLE TYPE
# =====================================================

def get_variable_type(
    variable
):
    """
    Returns the configured type of a predictor.
    """

    return VARIABLE_TYPES.get(
        variable
    )


# =====================================================
# GET MODEL METADATA
# =====================================================

def get_model_metadata(
    model
):
    """
    Returns metadata for a regression model.
    """

    metadata = MODEL_METADATA.get(
        model
    )

    if metadata is None:

        return None

    return metadata.copy()


# =====================================================
# AUTOMATIC MODEL SELECTION
# =====================================================
#
# THIS IS THE IMPORTANT PART.
#
# The backend should call this function AFTER the
# observed outcome categories have been obtained.
#
# Examples:
#
#     culture_result
#     categories = ["negative", "positive"]
#         → binary_logistic
#
#     organism_identification
#     categories = ["ecoli", "klebsiella"]
#         → binary_logistic
#
#     organism_identification
#     categories = ["ecoli", "klebsiella", "pseudomonas"]
#         → multinomial_logistic
#
#     antibiogram_susceptibility
#     categories = ["resistant", "susceptible"]
#         → binary_logistic
#
#     antibiogram_susceptibility
#     categories = [
#         "resistant",
#         "intermediate",
#         "susceptible"
#     ]
#         → ordinal_logistic
#
# =====================================================

def get_automatic_model(
    dependent_variable,
    observed_categories=None
):
    """
    Automatically determines the appropriate regression
    model.

    Parameters
    ----------
    dependent_variable : str
        Name of the dependent variable.

    observed_categories : list, optional
        Actual observed outcome categories after filtering.

    Returns
    -------
    dict
    """

    if dependent_variable not in OUTCOME_METADATA:

        return {

            "success":
                False,

            "error":
                (
                    f"Invalid dependent variable "
                    f"'{dependent_variable}'."
                )

        }


    metadata = OUTCOME_METADATA[
        dependent_variable
    ]


    # -------------------------------------------------
    # Categories are required for automatic selection
    # -------------------------------------------------

    categories = normalize_categories(
        observed_categories
    )


    if len(categories) < 2:

        return {

            "success":
                False,

            "error":
                (
                    "At least two observed outcome "
                    "categories are required for regression."
                ),

            "dependent_variable":
                dependent_variable,

            "observed_categories":
                categories

        }


    outcome_type = metadata[
        "outcome_type"
    ]


    # =================================================
    # BINARY OUTCOME
    # =================================================

    if outcome_type == "binary":

        if len(categories) != 2:

            return {

                "success":
                    False,

                "error":
                    (
                        "A binary outcome must contain "
                        "exactly two observed categories."
                    ),

                "dependent_variable":
                    dependent_variable,

                "observed_categories":
                    categories

            }


        model = "binary_logistic"


    # =================================================
    # NOMINAL OUTCOME
    # =================================================

    elif outcome_type == "nominal":

        if len(categories) == 2:

            model = "binary_logistic"

        elif len(categories) > 2:

            model = "multinomial_logistic"

        else:

            return {

                "success":
                    False,

                "error":
                    (
                        "A nominal outcome requires "
                        "at least two categories."
                    )

            }


    # =================================================
    # ORDINAL OUTCOME
    # =================================================

    elif outcome_type == "ordinal":

        if len(categories) == 2:

            # Two-category ordered outcome is treated
            # as a binary outcome.

            model = "binary_logistic"

        elif len(categories) >= 3:

            model = "ordinal_logistic"

        else:

            return {

                "success":
                    False,

                "error":
                    (
                        "An ordinal outcome requires "
                        "at least two categories."
                    )

            }


    else:

        return {

            "success":
                False,

            "error":
                (
                    f"Unsupported outcome type "
                    f"'{outcome_type}'."
                )

        }


    model_metadata = MODEL_METADATA[
        model
    ]


    return {

        "success":
            True,

        "dependent_variable":
            dependent_variable,

        "outcome_type":
            outcome_type,

        "observed_categories":
            categories,

        "number_categories":
            len(categories),

        "model":
            model,

        "label":
            model_metadata["label"],

        "requires_positive_culture":
            metadata.get(
                "requires_positive_culture",
                False
            ),

        "requires_antibiotic":
            metadata.get(
                "requires_antibiotic",
                False
            )

    }


# =====================================================
# STATIC MODEL INFORMATION
# =====================================================

def get_default_model(
    dependent_variable
):
    """
    Returns the default model configured in metadata.

    This should NOT be used as the final model-selection
    mechanism when observed categories are available.

    It is mainly useful for frontend metadata/display.
    """

    if dependent_variable not in OUTCOME_METADATA:

        return None

    return OUTCOME_METADATA[
        dependent_variable
    ].get(
        "default_model"
    )


# =====================================================
# VALIDATE INDEPENDENT VARIABLES
# =====================================================

def validate_independent_variables(
    variables
):
    """
    Validates the requested independent variables.
    """

    if variables is None:

        return {

            "success":
                False,

            "error":
                "No independent variables were provided."

        }


    if not isinstance(
        variables,
        (list, tuple)
    ):

        return {

            "success":
                False,

            "error":
                "Independent variables must be a list."

        }


    variables = [

        str(variable).strip()

        for variable
        in variables

        if variable is not None

    ]


    variables = list(
        dict.fromkeys(
            variables
        )
    )


    if not variables:

        return {

            "success":
                False,

            "error":
                "At least one independent variable is required."

        }


    invalid_variables = [

        variable

        for variable
        in variables

        if variable not in INDEPENDENT_VARIABLES

    ]


    if invalid_variables:

        return {

            "success":
                False,

            "error":
                "One or more invalid independent variables.",

            "invalid_variables":
                invalid_variables

        }


    if len(variables) > MAX_INDEPENDENT_VARIABLES:

        return {

            "success":
                False,

            "error":
                (
                    "The number of independent variables "
                    "exceeds the configured maximum."
                ),

            "maximum":
                MAX_INDEPENDENT_VARIABLES

        }


    return {

        "success":
            True,

        "variables":
            variables

    }


# =====================================================
# GET EXCLUDED PREDICTORS
# =====================================================

def get_excluded_predictors(
    dependent_variable
):
    """
    Returns predictors excluded for a particular
    dependent variable.
    """

    return EXCLUDED_PREDICTOR_MAP.get(

        dependent_variable,

        []

    ).copy()


# =====================================================
# GET AVAILABLE PREDICTORS
# =====================================================

def get_available_predictors(
    dependent_variable
):
    """
    Returns predictors allowed for a given dependent
    variable.
    """

    if dependent_variable not in DEPENDENT_VARIABLES:

        return []


    excluded = set(

        get_excluded_predictors(
            dependent_variable
        )

    )


    return [

        variable

        for variable
        in INDEPENDENT_VARIABLES

        if variable not in excluded

    ]


# =====================================================
# GET REGRESSION OPTIONS
# =====================================================
#
# This function provides metadata/options to the
# frontend.
#
# IMPORTANT:
# The frontend does NOT select the regression model.
#
# The frontend only selects:
#
#     - filters
#     - dependent variable
#     - independent variables
#     - antibiotic when required
#
# The backend determines the actual model.
#
# =====================================================

def get_regression_options(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    from_month=None,      # <-- NEW
    to_month=None         # <-- NEW
):
    """
    Returns regression-related frontend options.
    """

    # =================================================
    # ALWAYS start with a clean options dictionary
    # that contains the required keys
    # =================================================

    options = {

        "independent_variables":
            INDEPENDENT_VARIABLES.copy(),

        "dependent_variables":
            DEPENDENT_VARIABLES.copy(),

        "max_independent_variables":
            MAX_INDEPENDENT_VARIABLES,

        "variable_types":
            VARIABLE_TYPES.copy(),

        "automatic_model_selection":
            True,

        "outcome_metadata": {},

        "excluded_predictor_map": {},

        "available_predictors": {},

        "models": {},

        "default_model_map": {}

    }

    # =================================================
    # POPULATE DEPENDENT VARIABLE METADATA
    # =================================================

    for variable in DEPENDENT_VARIABLES:

        options["outcome_metadata"][variable] = (
            get_outcome_metadata(variable)
        )

        options["excluded_predictor_map"][variable] = (
            get_excluded_predictors(variable)
        )

        options["available_predictors"][variable] = (
            get_available_predictors(variable)
        )

        options["default_model_map"][variable] = (
            get_default_model(variable)
        )

    # =================================================
    # POPULATE MODEL METADATA
    # =================================================

    for model, metadata in MODEL_METADATA.items():

        options["models"][model] = metadata.copy()

    # =================================================
    # TRY TO GET FILTER OPTIONS
    # =================================================
    #
    # The filter options are supplementary and should
    # NOT block the core regression metadata.
    #
    # If get_antibiogram_options() fails, we still
    # return the core metadata.
    #
    # =================================================

    try:

        from services.filters import (
            get_antibiogram_options
        )

        filter_options = get_antibiogram_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            from_month=from_month,      # <-- NEW

            to_month=to_month           # <-- NEW

        )

        if filter_options is not None:

            # Only update with keys that don't conflict
            # with our core metadata

            for key in [
                "date_range",           # <-- NEW (month picker bounds)
                "districts",
                "blocks",
                "sample_types",
                "organisms",
                "antibiotics"
            ]:

                if key in filter_options:

                    options[key] = filter_options[key]

    except Exception:
        # If filter options fail, we still have the
        # core regression metadata.
        pass

    # =================================================
    # RETURN
    # =================================================

    return options