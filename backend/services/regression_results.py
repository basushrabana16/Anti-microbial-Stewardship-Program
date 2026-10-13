# =====================================================
# REGRESSION RESULTS
# =====================================================
#
# Final result formatting and aggregation layer for:
#
#     1. Binary Logistic Regression
#     2. Multinomial Logistic Regression
#     3. Ordinal Logistic Regression
#
# This module DOES NOT:
#
#     - load data
#     - apply filters
#     - fit models
#     - calculate regression coefficients
#     - perform statistical tests
#
# Responsibility:
#
#     - standardize model output
#     - standardize diagnostic output
#     - create JSON-safe responses
#     - provide a consistent API structure
#     - generate compact model summaries
#
# =====================================================

import numpy as np


# =====================================================
# MODEL NAMES
# =====================================================

MODEL_NAMES = {

    "binary_logistic":
        "Binary Logistic Regression",

    "multinomial_logistic":
        "Multinomial Logistic Regression",

    "ordinal_logistic":
        "Ordinal Logistic Regression"

}


# =====================================================
# SAFE VALUE
# =====================================================

def _safe_value(value):
    """
    Recursively converts NumPy/Pandas/scientific values
    into JSON-safe Python values.

    Non-finite numeric values become None.
    """

    if value is None:
        return None

    # -------------------------------------------------
    # NumPy scalar
    # -------------------------------------------------

    if isinstance(value, np.generic):

        return _safe_value(
            value.item()
        )


    # -------------------------------------------------
    # NumPy array
    # -------------------------------------------------

    if isinstance(value, np.ndarray):

        return [

            _safe_value(item)

            for item in value.tolist()

        ]


    # -------------------------------------------------
    # Boolean
    # -------------------------------------------------

    if isinstance(value, bool):
        return value


    # -------------------------------------------------
    # Integer
    # -------------------------------------------------

    if isinstance(value, int):
        return int(value)


    # -------------------------------------------------
    # Float
    # -------------------------------------------------

    if isinstance(value, float):

        if not np.isfinite(value):
            return None

        return float(value)


    # -------------------------------------------------
    # Dictionary
    # -------------------------------------------------

    if isinstance(value, dict):

        return {

            str(key):
                _safe_value(val)

            for key, val in value.items()

        }


    # -------------------------------------------------
    # List / Tuple / Set
    # -------------------------------------------------

    if isinstance(
        value,
        (list, tuple, set)
    ):

        return [

            _safe_value(item)

            for item in value

        ]


    # -------------------------------------------------
    # Pandas-like scalar
    # -------------------------------------------------

    try:

        if hasattr(value, "item"):

            converted = value.item()

            if converted is not value:

                return _safe_value(
                    converted
                )

    except Exception:

        pass


    # -------------------------------------------------
    # Missing-value fallback
    # -------------------------------------------------

    try:

        if value is np.nan:
            return None

    except Exception:

        pass


    return value


# =====================================================
# MODEL TYPE VALIDATION
# =====================================================

def validate_model_type(
    model_type
):

    return model_type in MODEL_NAMES


# =====================================================
# EMPTY RESULT
# =====================================================

def empty_regression_result(
    model_type,
    error,
    details=None
):

    result = {

        "success":
            False,

        "model":
            model_type,

        "model_name":
            MODEL_NAMES.get(
                model_type,
                str(model_type)
            ),

        "error":
            str(error)

    }


    if details is not None:

        result[
            "details"
        ] = _safe_value(
            details
        )


    return _safe_value(
        result
    )


# =====================================================
# SUCCESS RESULT
# =====================================================

def create_regression_result(
    model_type,
    model_result,
    diagnostics=None,
    metadata=None
):
    """
    Creates a standardized regression response.
    """

    # =================================================
    # VALIDATE MODEL TYPE
    # =================================================

    if not validate_model_type(
        model_type
    ):

        return empty_regression_result(

            model_type,

            "Invalid regression model type."

        )


    # =================================================
    # VALIDATE MODEL RESULT
    # =================================================

    if model_result is None:

        return empty_regression_result(

            model_type,

            "No model result was provided."

        )


    if not isinstance(
        model_result,
        dict
    ):

        return empty_regression_result(

            model_type,

            "Model result must be a dictionary."

        )


    # =================================================
    # MODEL FAILED
    # =================================================

    if not model_result.get(
        "success",
        False
    ):

        response = {

            "success":
                False,

            "model":
                model_type,

            "model_name":
                MODEL_NAMES[
                    model_type
                ],

            "error":
                model_result.get(
                    "error",
                    "Regression model failed."
                )

        }


        if "details" in model_result:

            response[
                "details"
            ] = model_result.get(
                "details"
            )


        if "possible_causes" in model_result:

            response[
                "possible_causes"
            ] = model_result.get(
                "possible_causes"
            )


        return _safe_value(
            response
        )


    # =================================================
    # BASIC RESPONSE
    # =================================================

    response = {

        "success":
            True,

        "model":
            model_type,

        "model_name":
            MODEL_NAMES[
                model_type
            ]

    }


    # =================================================
    # REQUEST METADATA
    # =================================================

    if metadata is not None:

        response[
            "request"
        ] = _safe_value(
            metadata
        )


    # =================================================
    # DEPENDENT VARIABLE
    # =================================================

    if "dependent_variable" in model_result:

        response[
            "dependent_variable"
        ] = _safe_value(

            model_result[
                "dependent_variable"
            ]

        )


    # =================================================
    # INDEPENDENT VARIABLES
    # =================================================

    if "independent_variables" in model_result:

        response[
            "independent_variables"
        ] = _safe_value(

            model_result[
                "independent_variables"
            ]

        )


    # =================================================
    # SAMPLE INFORMATION
    # =================================================

    sample_information = {}


    sample_keys = [

        "n",
        "number_predictors",
        "number_parameters",
        "number_categories",
        "number_thresholds"

    ]


    for key in sample_keys:

        if key in model_result:

            sample_information[
                key
            ] = model_result[
                key
            ]


    if sample_information:

        response[
            "sample_information"
        ] = _safe_value(
            sample_information
        )


    # =================================================
    # OUTCOME INFORMATION
    # =================================================

    outcome_information = {}


    outcome_keys = [

        "outcome_categories",
        "category_order",
        "category_mapping",
        "lowest_category",
        "highest_category",
        "outcome_distribution"

    ]


    for key in outcome_keys:

        if key in model_result:

            outcome_information[
                key
            ] = model_result[
                key
            ]


    if outcome_information:

        response[
            "outcome_information"
        ] = _safe_value(
            outcome_information
        )


    # =================================================
    # REFERENCE CATEGORIES
    # =================================================

    if "reference_categories" in model_result:

        response[
            "reference_categories"
        ] = _safe_value(

            model_result[
                "reference_categories"
            ]

        )


    # =================================================
    # MODEL STATUS
    # =================================================

    model_status = {}


    if "converged" in model_result:

        model_status[
            "converged"
        ] = model_result[
            "converged"
        ]


    if model_status:

        response[
            "model_status"
        ] = _safe_value(
            model_status
        )


    # =================================================
    # COEFFICIENTS
    # =================================================

    response[
        "coefficients"
    ] = _safe_value(

        model_result.get(
            "coefficients",
            []
        )

    )


    # =================================================
    # THRESHOLDS
    # =================================================

    response[
        "thresholds"
    ] = _safe_value(

        model_result.get(
            "thresholds",
            []
        )

    )


    # =================================================
    # MODEL STATISTICS
    # =================================================

    response[
        "statistics"
    ] = _safe_value(

        model_result.get(
            "statistics",
            {}
        )

    )


    # =================================================
    # VIF
    # =================================================

    #
    # Diagnostics take priority.
    #

    if diagnostics is not None:

        vif_result = diagnostics.get(
            "vif"
        )


        if vif_result is not None:

            # -----------------------------------------
            # If diagnostics contains:
            #
            # {"success": True, "vif": [...]}
            #
            # expose the actual VIF list.
            # -----------------------------------------

            if isinstance(
                vif_result,
                dict
            ) and "vif" in vif_result:

                response[
                    "vif"
                ] = _safe_value(
                    vif_result.get(
                        "vif",
                        []
                    )
                )

            else:

                response[
                    "vif"
                ] = _safe_value(
                    vif_result
                )


        else:

            response[
                "vif"
            ] = _safe_value(

                model_result.get(
                    "vif",
                    []
                )

            )

    else:

        response[
            "vif"
        ] = _safe_value(

            model_result.get(
                "vif",
                []
            )

        )


    # =================================================
    # OTHER DIAGNOSTICS
    # =================================================

    if diagnostics is not None:

        diagnostic_copy = dict(
            diagnostics
        )


        # VIF is exposed separately.
        diagnostic_copy.pop(
            "vif",
            None
        )


        response[
            "diagnostics"
        ] = _safe_value(
            diagnostic_copy
        )

    else:

        response[
            "diagnostics"
        ] = {}


    # =================================================
    # RAW MODEL INFORMATION
    # =================================================

    if "raw_model_information" in model_result:

        response[
            "raw_model_information"
        ] = _safe_value(

            model_result[
                "raw_model_information"
            ]

        )


    # =================================================
    # FINAL JSON-SAFE RESPONSE
    # =================================================

    return _safe_value(
        response
    )


# =====================================================
# ADD DIAGNOSTICS
# =====================================================

def add_diagnostics(
    regression_result,
    diagnostics
):
    """
    Adds diagnostic results to an existing response.

    Existing diagnostics are preserved.
    """

    if regression_result is None:

        regression_result = {}


    if diagnostics is None:

        return _safe_value(
            regression_result
        )


    existing = regression_result.get(
        "diagnostics",
        {}
    )


    if not isinstance(
        existing,
        dict
    ):

        existing = {}


    if isinstance(
        diagnostics,
        dict
    ):

        existing.update(
            diagnostics
        )

    else:

        existing[
            "additional"
        ] = diagnostics


    regression_result[
        "diagnostics"
    ] = existing


    return _safe_value(
        regression_result
    )


# =====================================================
# ADD MODEL STATISTICS
# =====================================================

def add_model_statistics(
    regression_result,
    statistics
):

    if regression_result is None:

        regression_result = {}


    regression_result[
        "statistics"
    ] = _safe_value(
        statistics
    )


    return _safe_value(
        regression_result
    )


# =====================================================
# ADD COEFFICIENTS
# =====================================================

def add_coefficients(
    regression_result,
    coefficients
):

    if regression_result is None:

        regression_result = {}


    regression_result[
        "coefficients"
    ] = _safe_value(
        coefficients
    )


    return _safe_value(
        regression_result
    )


# =====================================================
# ADD VIF
# =====================================================

def add_vif(
    regression_result,
    vif
):

    if regression_result is None:

        regression_result = {}


    # If complete VIF diagnostic object is supplied,
    # extract the actual VIF list.

    if isinstance(
        vif,
        dict
    ) and "vif" in vif:

        vif = vif.get(
            "vif",
            []
        )


    regression_result[
        "vif"
    ] = _safe_value(
        vif
    )


    return _safe_value(
        regression_result
    )


# =====================================================
# REGRESSION SUMMARY
# =====================================================

def create_regression_summary(
    regression_result
):
    """
    Creates a compact summary suitable for the frontend.
    """

    if (
        regression_result is None
        or
        not regression_result.get(
            "success",
            False
        )
    ):

        return {

            "success":
                False,

            "error":
                "Regression result is unavailable."

        }


    sample_information = (
        regression_result.get(
            "sample_information",
            {}
        )
    )


    statistics = (
        regression_result.get(
            "statistics",
            {}
        )
    )


    model_status = (
        regression_result.get(
            "model_status",
            {}
        )
    )


    summary = {

        "model":
            regression_result.get(
                "model_name"
            ),

        "dependent_variable":
            regression_result.get(
                "dependent_variable"
            ),

        "n":
            sample_information.get(
                "n"
            ),

        "number_predictors":
            sample_information.get(
                "number_predictors"
            )

    }


    # =================================================
    # MODEL STATISTICS
    # =================================================

    statistic_keys = [

        "aic",
        "bic",
        "log_likelihood",
        "null_log_likelihood",
        "mcfadden_pseudo_r_squared",
        "likelihood_ratio",
        "likelihood_ratio_df",
        "likelihood_ratio_p_value"

    ]


    for key in statistic_keys:

        if key in statistics:

            summary[
                key
            ] = statistics[
                key
            ]


    # =================================================
    # CONVERGENCE
    # =================================================

    if "converged" in model_status:

        summary[
            "converged"
        ] = model_status[
            "converged"
        ]


    return _safe_value(
        summary
    )


# =====================================================
# SIGNIFICANT PREDICTORS
# =====================================================

def get_significant_predictors(
    regression_result,
    alpha=0.05
):
    """
    Extracts statistically significant predictor
    coefficients.

    Threshold parameters from ordinal logistic
    regression are NOT included.
    """

    if (
        regression_result is None
        or
        not regression_result.get(
            "success",
            False
        )
    ):

        return []


    coefficients = (
        regression_result.get(
            "coefficients",
            []
        )
    )


    if not isinstance(
        coefficients,
        list
    ):

        return []


    try:

        alpha = float(alpha)

    except (
        TypeError,
        ValueError
    ):

        alpha = 0.05


    if not np.isfinite(alpha):

        alpha = 0.05


    significant = []


    for coefficient in coefficients:

        if not isinstance(
            coefficient,
            dict
        ):

            continue


        p_value = coefficient.get(
            "p_value"
        )


        if p_value is None:

            continue


        try:

            p_value = float(
                p_value
            )

        except (
            TypeError,
            ValueError
        ):

            continue


        if not np.isfinite(
            p_value
        ):

            continue


        if p_value < alpha:

            significant.append(
                coefficient
            )


    return _safe_value(
        significant
    )


# =====================================================
# ADD SIGNIFICANCE SUMMARY
# =====================================================

def add_significance_summary(
    regression_result,
    alpha=0.05
):

    if regression_result is None:

        regression_result = {}


    try:

        alpha = float(alpha)

    except (
        TypeError,
        ValueError
    ):

        alpha = 0.05


    if not np.isfinite(alpha):

        alpha = 0.05


    significant = (
        get_significant_predictors(

            regression_result,

            alpha=alpha

        )
    )


    regression_result[
        "significance"
    ] = {

        "alpha":
            _safe_value(
                alpha
            ),

        "number_significant_predictors":
            len(
                significant
            ),

        "significant_predictors":
            significant

    }


    return _safe_value(
        regression_result
    )


# =====================================================
# FORMAT ERROR
# =====================================================

def format_regression_error(
    model_type,
    error,
    details=None,
    possible_causes=None
):

    response = {

        "success":
            False,

        "model":
            model_type,

        "model_name":
            MODEL_NAMES.get(
                model_type,
                model_type
            ),

        "error":
            str(error)

    }


    if details is not None:

        response[
            "details"
        ] = _safe_value(
            details
        )


    if possible_causes is not None:

        try:

            response[
                "possible_causes"
            ] = [

                str(cause)

                for cause
                in possible_causes

            ]

        except Exception:

            response[
                "possible_causes"
            ] = [
                str(possible_causes)
            ]


    return _safe_value(
        response
    )


# =====================================================
# FINALIZE REGRESSION RESPONSE
# =====================================================

def finalize_regression_response(
    model_type,
    model_result,
    diagnostics=None,
    metadata=None,
    alpha=0.05
):
    """
    Main function used by the Flask/API layer.

    Pipeline:

        model result
             ↓
        standardized result
             ↓
        diagnostics
             ↓
        significance summary
             ↓
        compact summary
             ↓
        JSON-safe response
    """

    # =================================================
    # STANDARDIZE MODEL RESULT
    # =================================================

    response = create_regression_result(

        model_type=model_type,

        model_result=model_result,

        diagnostics=diagnostics,

        metadata=metadata

    )


    # =================================================
    # STOP IF MODEL FAILED
    # =================================================

    if not response.get(
        "success",
        False
    ):

        return _safe_value(
            response
        )


    # =================================================
    # SIGNIFICANCE
    # =================================================

    response = add_significance_summary(

        response,

        alpha=alpha

    )


    # =================================================
    # COMPACT SUMMARY
    # =================================================

    response[
        "summary"
    ] = create_regression_summary(
        response
    )


    # =================================================
    # FINAL JSON CONVERSION
    # =================================================

    return _safe_value(
        response
    )


# =====================================================
# FRONTEND COEFFICIENT TABLE
# =====================================================

def format_coefficient_table(
    regression_result
):
    """
    Converts model coefficients into a consistent
    frontend-friendly table.

    Output:

        variable
        coefficient
        standard_error
        test_statistic
        p_value
        odds_ratio
        ci_lower
        ci_upper
        significance
    """

    if (
        regression_result is None
        or
        not regression_result.get(
            "success",
            False
        )
    ):

        return []


    coefficients = (
        regression_result.get(
            "coefficients",
            []
        )
    )


    if not isinstance(
        coefficients,
        list
    ):

        return []


    table = []


    for coefficient in coefficients:

        if not isinstance(
            coefficient,
            dict
        ):

            continue


        # ---------------------------------------------
        # Test statistic
        # ---------------------------------------------

        test_statistic = (
            coefficient.get(
                "z_value"
            )
        )


        if test_statistic is None:

            test_statistic = (
                coefficient.get(
                    "t_value"
                )
            )


        if test_statistic is None:

            test_statistic = (
                coefficient.get(
                    "test_statistic"
                )
            )


        # ---------------------------------------------
        # P-value
        # ---------------------------------------------

        p_value = coefficient.get(
            "p_value"
        )


        numeric_p = None


        try:

            if p_value is not None:

                numeric_p = float(
                    p_value
                )

        except (
            TypeError,
            ValueError
        ):

            numeric_p = None


        # ---------------------------------------------
        # Significance
        # ---------------------------------------------

        if (

            numeric_p is not None

            and

            np.isfinite(numeric_p)

            and

            numeric_p < 0.001

        ):

            significance = "***"


        elif (

            numeric_p is not None

            and

            np.isfinite(numeric_p)

            and

            numeric_p < 0.01

        ):

            significance = "**"


        elif (

            numeric_p is not None

            and

            np.isfinite(numeric_p)

            and

            numeric_p < 0.05

        ):

            significance = "*"


        else:

            significance = ""


        # ---------------------------------------------
        # Row
        # ---------------------------------------------

        table.append({

            "variable":
                coefficient.get(
                    "variable"
                ),

            "coefficient":
                coefficient.get(
                    "coefficient"
                ),

            "standard_error":
                coefficient.get(
                    "standard_error"
                ),

            "test_statistic":
                test_statistic,

            "p_value":
                p_value,

            "odds_ratio":
                coefficient.get(
                    "odds_ratio"
                ),

            "ci_lower":
                coefficient.get(
                    "ci_lower"
                ),

            "ci_upper":
                coefficient.get(
                    "ci_upper"
                ),

            "significance":
                significance

        })


    return _safe_value(
        table
    )


# =====================================================
# FRONTEND PAYLOAD
# =====================================================

def build_frontend_payload(
    regression_result
):
    """
    Creates the clean payload consumed by the frontend.

    The frontend does not need to know the internal
    statsmodels structure.
    """

    # =================================================
    # FAILED RESULT
    # =================================================

    if (
        regression_result is None
        or
        not regression_result.get(
            "success",
            False
        )
    ):

        return {

            "success":
                False,

            "error":
                (
                    regression_result.get(
                        "error",
                        "Regression failed."
                    )
                    if regression_result
                    else
                    "Regression failed."
                )

        }


    # =================================================
    # COMMON PAYLOAD
    # =================================================

    payload = {

        "success":
            True,

        "model":
            regression_result.get(
                "model"
            ),

        "model_name":
            regression_result.get(
                "model_name"
            ),

        "dependent_variable":
            regression_result.get(
                "dependent_variable"
            ),

        "independent_variables":
            regression_result.get(
                "independent_variables",
                []
            ),

        "sample_information":
            regression_result.get(
                "sample_information",
                {}
            ),

        "outcome_information":
            regression_result.get(
                "outcome_information",
                {}
            ),

        "reference_categories":
            regression_result.get(
                "reference_categories",
                {}
            ),

        "model_status":
            regression_result.get(
                "model_status",
                {}
            ),

        "summary":
            regression_result.get(
                "summary",
                {}
            ),

        "coefficients":
            format_coefficient_table(
                regression_result
            ),

        "thresholds":
            regression_result.get(
                "thresholds",
                []
            ),

        "statistics":
            regression_result.get(
                "statistics",
                {}
            ),

        "diagnostics":
            regression_result.get(
                "diagnostics",
                {}
            ),

        "vif":
            regression_result.get(
                "vif",
                []
            ),

        "significance":
            regression_result.get(
                "significance",
                {}

            )

    }


    # =================================================
    # MODEL-SPECIFIC DIAGNOSTICS
    # =================================================

    model = regression_result.get(
        "model"
    )


    if model == "binary_logistic":

        payload[
            "binary_diagnostics"
        ] = regression_result.get(
            "diagnostics",
            {}
        )


    elif model == "multinomial_logistic":

        payload[
            "multinomial_diagnostics"
        ] = regression_result.get(
            "diagnostics",
            {}
        )


    elif model == "ordinal_logistic":

        payload[
            "ordinal_diagnostics"
        ] = regression_result.get(
            "diagnostics",
            {}
        )


    # =================================================
    # FINAL JSON-SAFE PAYLOAD
    # =================================================

    return _safe_value(
        payload
    )