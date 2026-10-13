# =====================================================
# BINARY LOGISTIC REGRESSION
# =====================================================
#
# This module fits Binary Logistic Regression.
#
# MODEL SELECTION
# ---------------
# Model selection is NOT performed in this module.
#
# regression_data.py determines that:
#
#     culture_result
#           ↓
#     binary_logistic
#
# This module is responsible only for:
#
#     1. Receiving regression-ready culture data
#     2. Encoding the binary outcome
#     3. Building the design matrix
#     4. Checking model requirements
#     5. Fitting Binary Logistic Regression
#     6. Calculating coefficients and odds ratios
#     7. Calculating model statistics
#     8. Reporting convergence
#     9. Reporting VIF
#
# =====================================================

import numpy as np
import pandas as pd

from scipy.stats import chi2
from statsmodels.api import Logit

from services.regression_data import (
    prepare_culture_result_data
)

from services.regression_helpers import (
    build_design_matrix,
    calculate_vif
)


# =====================================================
# CONSTANTS
# =====================================================

MODEL_TYPE = "binary_logistic"

MODEL_NAME = "Binary Logistic Regression"

OUTCOME_COLUMN = "culture_result"


# =====================================================
# SAFE FLOAT
# =====================================================

def _safe_float(value):
    """
    Converts a numeric value into a JSON-safe float.

    Non-finite values are returned as None.
    """

    try:

        value = float(value)

    except (TypeError, ValueError):

        return None

    if not np.isfinite(value):

        return None

    return round(
        value,
        6
    )


# =====================================================
# NORMALIZE CATEGORY
# =====================================================

def _normalize_category(value):
    """
    Normalizes a single categorical value.

    Examples
    --------
    " Positive " -> "positive"
    "Male"       -> "male"
    """

    if value is None:

        return None


    try:

        if pd.isna(value):

            return None

    except (TypeError, ValueError):

        return None


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
# VALIDATE BINARY OUTCOME
# =====================================================

def _validate_binary_outcome(df):
    """
    Validates that culture_result contains exactly
    two observed categories.

    The categories are sorted alphabetically.

    The first category is treated as the reference
    category and the second as the event category.
    """

    if df is None or df.empty:

        return {

            "valid": False,

            "error":
                "No observations are available."

        }


    if OUTCOME_COLUMN not in df.columns:

        return {

            "valid": False,

            "error":
                (
                    f"Outcome column "
                    f"'{OUTCOME_COLUMN}' is missing."
                )

        }


    values = (

        df[OUTCOME_COLUMN]

        .map(_normalize_category)

        .dropna()

        .unique()

        .tolist()

    )


    values = sorted(
        values
    )


    if len(values) != 2:

        return {

            "valid": False,

            "error":
                (
                    "Binary logistic regression "
                    "requires exactly two observed "
                    "outcome categories."
                ),

            "categories":
                values

        }


    return {

        "valid": True,

        "categories":
            values,

        "reference_category":
            values[0],

        "event_category":
            values[1]

    }


# =====================================================
# ENCODE BINARY OUTCOME
# =====================================================

def _encode_binary_outcome(
    df,
    categories
):
    """
    Encodes the binary outcome as:

        reference category -> 0
        event category     -> 1

    The original dataframe is not modified.
    """

    reference_category = categories[0]

    event_category = categories[1]


    encoded_df = df.copy()


    normalized_values = (

        encoded_df[
            OUTCOME_COLUMN
        ]

        .map(_normalize_category)

    )


    encoded_values = np.where(

        normalized_values == event_category,

        1,

        np.where(

            normalized_values == reference_category,

            0,

            np.nan

        )

    )


    encoded_df[
        OUTCOME_COLUMN
    ] = pd.to_numeric(

        encoded_values,

        errors="coerce"

    )


    return encoded_df


# =====================================================
# OUTCOME DISTRIBUTION
# =====================================================

def _get_outcome_distribution(
    df,
    categories
):
    """
    Returns outcome counts and percentages.
    """

    normalized_outcome = (

        df[OUTCOME_COLUMN]

        .map(_normalize_category)

    )


    counts = (

        normalized_outcome

        .value_counts()

        .reindex(
            categories,
            fill_value=0
        )

    )


    total = counts.sum()


    results = []


    for category in categories:

        count = int(
            counts.loc[category]
        )


        percentage = (

            (
                count
                /
                total
            )
            * 100

            if total > 0

            else 0.0

        )


        results.append({

            "category":
                category,

            "count":
                count,

            "percentage":
                round(
                    float(percentage),
                    4
                )

        })


    return results


# =====================================================
# CHECK CONVERGENCE
# =====================================================

def _check_convergence(result):
    """
    Checks whether statsmodels reports successful
    maximum-likelihood convergence.
    """

    try:

        return bool(

            result.mle_retvals.get(
                "converged",
                False
            )

        )

    except Exception:

        return False


# =====================================================
# CALCULATE ODDS RATIO RESULTS
# =====================================================

def _calculate_odds_ratio_results(
    result
):
    """
    Extracts coefficient-level results.

    For each coefficient:

        coefficient
        standard error
        z statistic
        p-value
        odds ratio
        95% CI for odds ratio
    """

    params = result.params

    standard_errors = result.bse

    p_values = result.pvalues

    confidence_intervals = (
        result.conf_int()
    )


    rows = []


    for variable in params.index:

        coefficient = (
            params[variable]
        )

        standard_error = (
            standard_errors[variable]
        )

        p_value = (
            p_values[variable]
        )

        z_value = (
            result.tvalues[variable]
        )


        ci_lower = (

            confidence_intervals.loc[
                variable,
                0
            ]

        )


        ci_upper = (

            confidence_intervals.loc[
                variable,
                1
            ]

        )


        # ---------------------------------------------
        # Odds Ratio
        # ---------------------------------------------

        try:

            odds_ratio = np.exp(
                coefficient
            )

        except Exception:

            odds_ratio = np.nan


        # ---------------------------------------------
        # Odds Ratio CI
        # ---------------------------------------------

        try:

            or_ci_lower = np.exp(
                ci_lower
            )

        except Exception:

            or_ci_lower = np.nan


        try:

            or_ci_upper = np.exp(
                ci_upper
            )

        except Exception:

            or_ci_upper = np.nan


        display_variable = (

            "Intercept"

            if variable == "const"

            else str(variable)

        )


        rows.append({

            "variable":
                display_variable,

            "coefficient":
                _safe_float(
                    coefficient
                ),

            "standard_error":
                _safe_float(
                    standard_error
                ),

            "z_value":
                _safe_float(
                    z_value
                ),

            "p_value":
                _safe_float(
                    p_value
                ),

            "odds_ratio":
                _safe_float(
                    odds_ratio
                ),

            "ci_lower":
                _safe_float(
                    or_ci_lower
                ),

            "ci_upper":
                _safe_float(
                    or_ci_upper
                )

        })


    return rows


# =====================================================
# CALCULATE MODEL STATISTICS
# =====================================================

def _calculate_model_statistics(
    result,
    null_log_likelihood,
    n_observations
):
    """
    Calculates model-level statistics:

        Log-likelihood
        Null log-likelihood
        AIC
        BIC
        McFadden pseudo R²
        Likelihood-ratio statistic
        LR degrees of freedom
        LR p-value
    """

    log_likelihood = result.llf


    number_parameters = len(
        result.params
    )


    aic = result.aic


    try:

        bic = result.bic

    except Exception:

        bic = np.nan


    # =================================================
    # MCFADDEN PSEUDO R-SQUARED
    # =================================================

    if (

        null_log_likelihood is not None

        and

        null_log_likelihood != 0

    ):

        pseudo_r_squared = (

            1

            -

            (
                log_likelihood
                /
                null_log_likelihood
            )

        )

    else:

        pseudo_r_squared = np.nan


    # =================================================
    # LIKELIHOOD-RATIO STATISTIC
    # =================================================

    if null_log_likelihood is not None:

        lr_statistic = (

            2

            *

            (
                log_likelihood
                -
                null_log_likelihood
            )

        )

    else:

        lr_statistic = np.nan


    # Number of slope parameters.
    #
    # One parameter is the intercept.

    lr_df = max(

        number_parameters - 1,

        0

    )


    # =================================================
    # LR P-VALUE
    # =================================================

    if (

        np.isfinite(lr_statistic)

        and

        lr_df > 0

    ):

        lr_p_value = chi2.sf(

            lr_statistic,

            lr_df

        )

    else:

        lr_p_value = np.nan


    return {

        "n":
            int(n_observations),

        "log_likelihood":
            _safe_float(
                log_likelihood
            ),

        "null_log_likelihood":
            _safe_float(
                null_log_likelihood
            ),

        "aic":
            _safe_float(
                aic
            ),

        "bic":
            _safe_float(
                bic
            ),

        "mcfadden_pseudo_r_squared":
            _safe_float(
                pseudo_r_squared
            ),

        "likelihood_ratio":
            _safe_float(
                lr_statistic
            ),

        "likelihood_ratio_df":
            int(lr_df),

        "likelihood_ratio_p_value":
            _safe_float(
                lr_p_value
            )

    }


# =====================================================
# CHECK SAMPLE SIZE
# =====================================================

def _check_sample_size(
    y,
    X
):
    """
    Performs a basic sample-size check.

    Requirement:

        n > number of estimated parameters
    """

    n_observations = len(y)

    number_parameters = X.shape[1]


    if n_observations <= number_parameters:

        return {

            "valid": False,

            "error":
                (
                    "There are too few observations "
                    "relative to the number of model "
                    "parameters."
                ),

            "n":
                int(n_observations),

            "number_parameters":
                int(number_parameters)

        }


    return {

        "valid": True,

        "n":
            int(n_observations),

        "number_parameters":
            int(number_parameters)

    }


# =====================================================
# CHECK DESIGN MATRIX RANK
# =====================================================

def _check_design_matrix_rank(
    X
):
    """
    Checks whether the design matrix has full
    column rank.
    """

    try:

        matrix_rank = np.linalg.matrix_rank(
            X.values
        )

        number_columns = X.shape[1]

    except Exception as exc:

        return {

            "valid": False,

            "error":
                "Unable to determine design matrix rank.",

            "details":
                str(exc)

        }


    if matrix_rank < number_columns:

        return {

            "valid": False,

            "error":
                (
                    "The regression design matrix "
                    "is singular. This usually "
                    "indicates perfect "
                    "multicollinearity among the "
                    "selected predictors."
                ),

            "matrix_rank":
                int(matrix_rank),

            "matrix_columns":
                int(number_columns)

        }


    return {

        "valid": True,

        "matrix_rank":
            int(matrix_rank),

        "matrix_columns":
            int(number_columns)

    }


# =====================================================
# FIT NULL MODEL
# =====================================================

def _fit_null_model(y):
    """
    Fits the intercept-only logistic regression model.

    Returns
    -------
    float or None
        Null-model log-likelihood.
    """

    try:

        X_null = pd.DataFrame({

            "const":
                np.ones(
                    len(y)
                )

        })


        null_model = Logit(

            y,

            X_null

        )


        null_result = null_model.fit(

            disp=False

        )


        return null_result.llf


    except Exception:

        return None


# =====================================================
# MAIN BINARY LOGISTIC REGRESSION
# =====================================================

def run_binary_logistic_regression(
    df,
    independent_variables
):
    """
    Fits Binary Logistic Regression for:

        culture_result

    IMPORTANT
    ---------
    Model selection is NOT performed here.

    The regression dispatcher must already have
    determined that:

        culture_result
                ↓
        binary_logistic
    """

    # =================================================
    # BASIC INPUT VALIDATION
    # =================================================

    if df is None or df.empty:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "No data available for "
                    "binary logistic regression."
                )

        }


    if (

        independent_variables is None

        or

        len(independent_variables) == 0

    ):

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "At least one independent "
                    "variable is required."
                )

        }


    # =================================================
    # PREPARE REGRESSION DATA
    # =================================================
    #
    # regression_data.py performs:
    #
    #     validation
    #     cleaning
    #     complete-case analysis
    #     outcome validation
    #
    # =================================================

    prepared = (
        prepare_culture_result_data(

            df,

            independent_variables

        )
    )


    if not prepared.get(
        "success",
        False
    ):

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                prepared.get(

                    "error",

                    "Unable to prepare "
                    "regression data."

                ),

            "details":
                prepared

        }


    regression_df = prepared[
        "data"
    ]


    # =================================================
    # VALIDATE BINARY OUTCOME
    # =================================================

    outcome_validation = (
        _validate_binary_outcome(

            regression_df

        )
    )


    if not outcome_validation[
        "valid"
    ]:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                outcome_validation[
                    "error"
                ],

            "categories":
                outcome_validation.get(
                    "categories",
                    []
                )

        }


    categories = (
        outcome_validation[
            "categories"
        ]
    )


    reference_category = (
        outcome_validation[
            "reference_category"
        ]
    )


    event_category = (
        outcome_validation[
            "event_category"
        ]
    )


    # =================================================
    # OUTCOME DISTRIBUTION
    # =================================================

    outcome_distribution = (
        _get_outcome_distribution(

            regression_df,

            categories

        )
    )


    # =================================================
    # ENCODE OUTCOME
    # =================================================

    encoded_df = (
        _encode_binary_outcome(

            regression_df,

            categories

        )
    )


    # =================================================
    # BUILD DESIGN MATRIX
    # =================================================

    try:

        X, reference_categories = (
            build_design_matrix(

                encoded_df,

                independent_variables

            )
        )

    except Exception as exc:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Unable to construct the "
                    "regression design matrix."
                ),

            "details":
                str(exc)

        }


    # =================================================
    # CREATE OUTCOME VECTOR
    # =================================================

    y = (
        encoded_df[
            OUTCOME_COLUMN
        ]
        .copy()
    )


    # =================================================
    # ALIGN X AND Y
    # =================================================

    valid_rows = (

        y.notna()

        &

        X.notna().all(
            axis=1
        )

    )


    X = X.loc[
        valid_rows
    ].copy()


    y = y.loc[
        valid_rows
    ].copy()


    if len(y) == 0:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "No valid observations remain "
                    "after design-matrix construction."
                )

        }


    # =================================================
    # CHECK BOTH OUTCOME CLASSES
    # =================================================

    unique_y = sorted(
        y.unique().tolist()
    )


    if unique_y != [0.0, 1.0]:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Both outcome classes must be "
                    "present after data preparation."
                ),

            "observed_outcome_values":
                unique_y

        }


    # =================================================
    # SAMPLE-SIZE CHECK
    # =================================================

    sample_size_check = (
        _check_sample_size(

            y,

            X

        )
    )


    if not sample_size_check[
        "valid"
    ]:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                sample_size_check[
                    "error"
                ],

            "n":
                sample_size_check[
                    "n"
                ],

            "number_parameters":
                sample_size_check[
                    "number_parameters"
                ]

        }


    # =================================================
    # DESIGN-MATRIX RANK CHECK
    # =================================================

    rank_check = (
        _check_design_matrix_rank(
            X
        )
    )


    if not rank_check[
        "valid"
    ]:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                rank_check[
                    "error"
                ],

            "details":
                rank_check

        }


    # =================================================
    # VIF
    # =================================================

    try:

        vif = calculate_vif(
            X
        )

    except Exception:

        vif = []


    # =================================================
    # NULL MODEL
    # =================================================

    null_log_likelihood = (
        _fit_null_model(
            y
        )
    )


    # =================================================
    # FIT FULL LOGISTIC MODEL
    # =================================================

    try:

        model = Logit(

            y,

            X

        )


        result = model.fit(

            disp=False

        )


    except np.linalg.LinAlgError as exc:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "The logistic regression "
                    "could not be estimated because "
                    "the design matrix is singular "
                    "or numerically unstable."
                ),

            "details":
                str(exc),

            "possible_causes": [

                "Perfect multicollinearity",

                "Rare predictor categories",

                "Too many predictors for the available sample",

                "Complete or quasi-complete separation"

            ]

        }


    except Exception as exc:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Binary logistic regression "
                    "failed to fit."
                ),

            "details":
                str(exc),

            "possible_causes": [

                "Complete separation",

                "Quasi-complete separation",

                "Rare predictor categories",

                "Insufficient sample size",

                "Multicollinearity"

            ]

        }


    # =================================================
    # CONVERGENCE
    # =================================================

    converged = (
        _check_convergence(
            result
        )
    )


    # =================================================
    # DO NOT REPORT A NON-CONVERGED MODEL AS SUCCESS
    # =================================================

    if not converged:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Binary logistic regression "
                    "did not converge."
                ),

            "possible_causes": [

                "Complete separation",

                "Quasi-complete separation",

                "Rare predictor categories",

                "Insufficient sample size",

                "Multicollinearity",

                "Numerical instability"

            ],

            "converged":
                False,

            "n":
                int(len(y)),

            "number_parameters":
                int(X.shape[1])

        }


    # =================================================
    # EXTRACT COEFFICIENT RESULTS
    # =================================================

    try:

        coefficients = (
            _calculate_odds_ratio_results(

                result

            )
        )

    except Exception as exc:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Unable to extract "
                    "regression coefficients."
                ),

            "details":
                str(exc)

        }


    # =================================================
    # MODEL STATISTICS
    # =================================================

    model_statistics = (
        _calculate_model_statistics(

            result,

            null_log_likelihood,

            len(y)

        )
    )


    # =================================================
    # RETURN FINAL RESULTS
    # =================================================

    return {

        "success":
            True,

        "model":
            MODEL_TYPE,

        "model_name":
            MODEL_NAME,

        # ---------------------------------------------
        # Outcome information
        # ---------------------------------------------

        "dependent_variable":
            OUTCOME_COLUMN,

        "reference_outcome":
            reference_category,

        "event_outcome":
            event_category,

        "outcome_categories":
            categories,

        "outcome_distribution":
            outcome_distribution,

        # ---------------------------------------------
        # Predictor information
        # ---------------------------------------------

        "independent_variables":
            list(independent_variables),

        "reference_categories":
            reference_categories,

        # ---------------------------------------------
        # Sample information
        # ---------------------------------------------

        "initial_n":
            prepared.get(
                "initial_n"
            ),

        "excluded_n":
            prepared.get(
                "excluded_n"
            ),

        "final_n":
            prepared.get(
                "final_n"
            ),

        "n":
            int(len(y)),

        "number_parameters":
            int(X.shape[1]),

        "number_predictors":
            int(
                X.shape[1] - 1
            ),

        # ---------------------------------------------
        # Model status
        # ---------------------------------------------

        "converged":
            True,

        # ---------------------------------------------
        # Regression coefficients
        # ---------------------------------------------

        "coefficients":
            coefficients,

        # ---------------------------------------------
        # Model statistics
        # ---------------------------------------------

        "statistics":
            model_statistics,

        # ---------------------------------------------
        # Multicollinearity diagnostic
        # ---------------------------------------------

        "vif":
            vif

    }