# =====================================================
# REGRESSION METADATA
# =====================================================

import pandas as pd
# In regression_metadata.py, replace the local def with:
from services.association_metadata import apply_custom_age_groups

# =====================================================
# INDEPENDENT VARIABLES
# =====================================================

INDEPENDENT_VARIABLES = [

    "gender",

    "age_group",

    "district",

    "block",

    "sample_type",



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
# CUSTOMIZABLE VARIABLES
# =====================================================
#
# Variables that support user-defined customization.
#
# Today only age_group: the user may supply 2–5
# contiguous, non-overlapping age ranges which replace
# the default <30 / 30-60 / >60 bins before fitting.
#
# The frontend reads this list to decide which variables
# show a "Customize" button. No hardcoding in JS.
#
# =====================================================

CUSTOMIZABLE_VARIABLES = [

    "age_group"

]


# =====================================================
# OUTCOME METADATA
# =====================================================

OUTCOME_METADATA = {

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
    return VARIABLE_TYPES.get(
        variable
    )


# =====================================================
# GET MODEL METADATA
# =====================================================

def get_model_metadata(
    model
):
    metadata = MODEL_METADATA.get(
        model
    )

    if metadata is None:

        return None

    return metadata.copy()


# =====================================================
# AUTOMATIC MODEL SELECTION
# =====================================================

def get_automatic_model(
    dependent_variable,
    observed_categories=None
):
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


    elif outcome_type == "ordinal":

        if len(categories) == 2:

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
# CUSTOM AGE GROUPS
# (shared contract with association_metadata)
# =====================================================

def apply_custom_age_groups(df, age_groups):
    """
    Replaces the default age_group column with user-defined bins.

    age_groups: list of {"min": int, "max": int} dicts, or None.

    Validation rules:
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
# GET REGRESSION OPTIONS
# =====================================================

def get_regression_options(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,
    from_month=None,
    to_month=None
):
    options = {

        "independent_variables":
            INDEPENDENT_VARIABLES.copy(),

        "dependent_variables":
            DEPENDENT_VARIABLES.copy(),

        "max_independent_variables":
            MAX_INDEPENDENT_VARIABLES,

        "variable_types":
            VARIABLE_TYPES.copy(),

        "customizable_variables":
            CUSTOMIZABLE_VARIABLES.copy(),

        "automatic_model_selection":
            True,

        "outcome_metadata": {},

        "excluded_predictor_map": {},

        "available_predictors": {},

        "models": {},

        "default_model_map": {}

    }


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


    for model, metadata in MODEL_METADATA.items():

        options["models"][model] = metadata.copy()


    try:

        from services.filters import (
            get_antibiogram_options
        )

        filter_options = get_antibiogram_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            from_month=from_month,

            to_month=to_month

        )

        if filter_options is not None:

            for key in [

                "date_range",

                "districts",

                "blocks",

                "sample_types",

                "organisms",

                "antibiotics"

            ]:

                if key in filter_options:

                    options[key] = filter_options[key]

    except Exception:

        pass


    return options