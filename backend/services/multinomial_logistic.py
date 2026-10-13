# =====================================================
# MULTINOMIAL LOGISTIC REGRESSION
# =====================================================

import warnings

import numpy as np
import pandas as pd

from scipy.stats import chi2
from statsmodels.discrete.discrete_model import MNLogit

from services.regression_data import (
    prepare_organism_identification_data
)

from services.regression_helpers import (
    build_design_matrix,
    calculate_vif
)


# =====================================================
# CONSTANTS
# =====================================================

OUTCOME_COLUMN = "organism_identification"

MODEL_NAME = "Multinomial Logistic Regression"

MODEL_TYPE = "multinomial_logistic"


# =====================================================
# SAFE FLOAT
# =====================================================

def _safe_float(value):
    """
    Converts a numeric value to a JSON-safe float.

    Non-finite values are returned as None.
    """

    try:

        value = float(value)

    except (
        TypeError,
        ValueError
    ):

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
    " E. coli " -> "e. coli"
    "Male"      -> "male"
    None        -> None
    """

    if value is None:

        return None


    try:

        if pd.isna(value):

            return None

    except (
        TypeError,
        ValueError
    ):

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
# VALIDATE MULTINOMIAL OUTCOME
# =====================================================

def _validate_multinomial_outcome(df):
    """
    Validates the multinomial outcome.

    Multinomial logistic regression requires at least
    three distinct outcome categories.

    The first alphabetically ordered category is used
    as the reference category.
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

        df[
            OUTCOME_COLUMN
        ]

        .map(
            _normalize_category
        )

        .dropna()

        .unique()

        .tolist()

    )


    # -------------------------------------------------
    # Alphabetical ordering
    # -------------------------------------------------

    values = sorted(
        values
    )


    # -------------------------------------------------
    # Minimum number of categories
    # -------------------------------------------------

    if len(values) < 3:

        return {

            "valid": False,

            "error":
                (
                    "Multinomial logistic regression "
                    "requires at least three outcome "
                    "categories."
                ),

            "categories":
                values

        }


    return {

        "valid": True,

        "categories":
            values,

        "reference_category":
            values[0]

    }


# =====================================================
# ENCODE MULTINOMIAL OUTCOME
# =====================================================

def _encode_multinomial_outcome(
    df,
    categories
):
    """
    Encodes the multinomial outcome.

        category[0] -> 0  reference
        category[1] -> 1
        category[2] -> 2
        ...

    The first category is the reference outcome.
    """

    encoded_df = df.copy()


    category_to_code = {

        category: index

        for index, category
        in enumerate(categories)

    }


    normalized_values = (

        encoded_df[
            OUTCOME_COLUMN
        ]

        .map(
            _normalize_category
        )

    )


    encoded_df[
        OUTCOME_COLUMN
    ] = (

        normalized_values.map(
            category_to_code
        )

    )


    encoded_df[
        OUTCOME_COLUMN
    ] = pd.to_numeric(

        encoded_df[
            OUTCOME_COLUMN
        ],

        errors="coerce"

    )


    return (

        encoded_df,

        category_to_code

    )


# =====================================================
# OUTCOME DISTRIBUTION
# =====================================================

def _get_outcome_distribution(
    df,
    categories
):
    """
    Returns counts and percentages for each outcome
    category.
    """

    normalized = (

        df[
            OUTCOME_COLUMN
        ]

        .map(
            _normalize_category
        )

    )


    counts = (

        normalized

        .value_counts()

        .reindex(

            categories,

            fill_value=0

        )

    )


    total = counts.sum()

    rows = []


    for category in categories:

        count = int(
            counts.loc[
                category
            ]
        )


        if total > 0:

            percentage = (

                count
                /
                total
                *
                100

            )

        else:

            percentage = 0


        rows.append({

            "category":
                category,

            "count":
                count,

            "percentage":
                round(
                    float(
                        percentage
                    ),
                    4
                )

        })


    return rows


# =====================================================
# CHECK CONVERGENCE
# =====================================================

def _check_convergence(result):
    """
    Checks whether statsmodels reports successful
    convergence.
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
# CALCULATE MODEL STATISTICS
# =====================================================

def _calculate_model_statistics(
    result,
    null_log_likelihood,
    n_observations,
    number_categories,
    number_predictors
):
    """
    Calculates model-level statistics.

    Includes:

        Log-likelihood
        Null log-likelihood
        AIC
        BIC
        McFadden pseudo-R²
        Likelihood-ratio statistic
        LR degrees of freedom
        LR p-value
        Number of parameters
    """

    log_likelihood = result.llf


    # -------------------------------------------------
    # Number of parameters
    # -------------------------------------------------

    number_parameters = (

        (number_predictors + 1)

        *

        (number_categories - 1)

    )


    # -------------------------------------------------
    # AIC
    # -------------------------------------------------

    try:

        aic = result.aic

    except Exception:

        aic = np.nan


    # -------------------------------------------------
    # BIC
    # -------------------------------------------------

    try:

        bic = result.bic

    except Exception:

        bic = np.nan


    # -------------------------------------------------
    # McFadden pseudo R²
    # -------------------------------------------------

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


    # -------------------------------------------------
    # Likelihood-ratio statistic
    # -------------------------------------------------

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


    # -------------------------------------------------
    # LR degrees of freedom
    #
    # Full model:
    #     (p + 1)(K - 1)
    #
    # Null model:
    #     (K - 1)
    #
    # Difference:
    #     p(K - 1)
    # -------------------------------------------------

    lr_df = (

        number_predictors

        *

        (number_categories - 1)

    )


    # -------------------------------------------------
    # LR p-value
    # -------------------------------------------------

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
            int(
                n_observations
            ),

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
            int(
                lr_df
            ),

        "likelihood_ratio_p_value":
            _safe_float(
                lr_p_value
            ),

        "number_parameters":
            int(
                number_parameters
            )

    }


# =====================================================
# EXTRACT MULTINOMIAL RESULTS
# =====================================================

def _extract_multinomial_results(
    result,
    categories,
    reference_category
):
    """
    Extracts coefficient-level results from MNLogit.

    For every non-reference outcome category:

        coefficient
        standard error
        z-value
        p-value
        Relative Risk Ratio
        95% CI for RRR
    """

    params = pd.DataFrame(
        result.params
    )

    standard_errors = pd.DataFrame(
        result.bse
    )

    z_values = pd.DataFrame(
        result.tvalues
    )

    p_values = pd.DataFrame(
        result.pvalues
    )

    confidence_intervals = (
        result.conf_int()
    )


    # -------------------------------------------------
    # Non-reference categories
    # -------------------------------------------------

    non_reference_categories = (
        categories[1:]
    )


    parameter_columns = list(
        params.columns
    )


    rows = []


    # =================================================
    # LOOP THROUGH OUTCOME EQUATIONS
    # =================================================

    for equation_index, outcome_category in enumerate(
        non_reference_categories
    ):

        if equation_index >= len(
            parameter_columns
        ):

            continue


        equation_column = parameter_columns[
            equation_index
        ]


        # -------------------------------------------------
        # Find confidence interval for equation
        # -------------------------------------------------

        equation_ci = None


        try:

            if isinstance(

                confidence_intervals.index,

                pd.MultiIndex

            ):

                level_zero = (

                    confidence_intervals
                    .index
                    .get_level_values(0)
                    .unique()
                    .tolist()

                )


                possible_labels = [

                    equation_index,

                    str(
                        equation_index
                    ),

                    equation_index + 1,

                    str(
                        equation_index + 1
                    ),

                    equation_column,

                    str(
                        equation_column
                    )

                ]


                selected_label = None


                for label in possible_labels:

                    if label in level_zero:

                        selected_label = label

                        break


                if selected_label is not None:

                    equation_ci = (

                        confidence_intervals
                        .xs(
                            selected_label,
                            level=0
                        )

                    )

            else:

                equation_ci = (
                    confidence_intervals
                )

        except Exception:

            equation_ci = None


        # =================================================
        # LOOP THROUGH MODEL PARAMETERS
        # =================================================

        for variable in params.index:

            coefficient = params.loc[
                variable,
                equation_column
            ]


            standard_error = (
                standard_errors.loc[
                    variable,
                    equation_column
                ]
            )


            z_value = (
                z_values.loc[
                    variable,
                    equation_column
                ]
            )


            p_value = (
                p_values.loc[
                    variable,
                    equation_column
                ]
            )


            # -------------------------------------------------
            # Confidence interval
            # -------------------------------------------------

            ci_lower = np.nan

            ci_upper = np.nan


            if equation_ci is not None:

                try:

                    ci_lower = (
                        equation_ci.loc[
                            variable,
                            "lower"
                        ]
                    )

                    ci_upper = (
                        equation_ci.loc[
                            variable,
                            "upper"
                        ]
                    )

                except Exception:

                    # Some statsmodels versions may
                    # return numeric column labels.

                    try:

                        ci_lower = (
                            equation_ci.loc[
                                variable,
                                0
                            ]
                        )

                        ci_upper = (
                            equation_ci.loc[
                                variable,
                                1
                            ]
                        )

                    except Exception:

                        ci_lower = np.nan

                        ci_upper = np.nan


            # -------------------------------------------------
            # Relative Risk Ratio
            # -------------------------------------------------

            try:

                rrr = np.exp(
                    coefficient
                )

            except Exception:

                rrr = np.nan


            # -------------------------------------------------
            # RRR confidence interval
            # -------------------------------------------------

            try:

                rrr_ci_lower = np.exp(
                    ci_lower
                )

            except Exception:

                rrr_ci_lower = np.nan


            try:

                rrr_ci_upper = np.exp(
                    ci_upper
                )

            except Exception:

                rrr_ci_upper = np.nan


            # -------------------------------------------------
            # Display variable
            # -------------------------------------------------

            if str(variable) == "const":

                display_variable = (
                    "Intercept"
                )

            else:

                display_variable = str(
                    variable
                )


            # -------------------------------------------------
            # Append result
            # -------------------------------------------------

            rows.append({

                "outcome_category":
                    str(
                        outcome_category
                    ),

                "reference_outcome":
                    str(
                        reference_category
                    ),

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

                "relative_risk_ratio":
                    _safe_float(
                        rrr
                    ),

                "ci_lower":
                    _safe_float(
                        rrr_ci_lower
                    ),

                "ci_upper":
                    _safe_float(
                        rrr_ci_upper
                    )

            })


    return rows


# =====================================================
# MAIN MULTINOMIAL LOGISTIC REGRESSION
# =====================================================

# =====================================================
# MAIN MULTINOMIAL LOGISTIC REGRESSION
# =====================================================

def run_multinomial_logistic_regression(
    df,
    independent_variables,
    prepared_data=None
):
    """
    Fits Multinomial Logistic Regression.

    Outcome:
        organism_identification

    Reference:
        First alphabetically ordered organism.

    The regression model is automatically selected
    upstream from the dependent variable.

    Parameters
    ----------
    df : pandas.DataFrame
        Original filtered dataframe (used if prepared_data is None)
    independent_variables : list
        List of predictor names
    prepared_data : dict, optional
        Pre-prepared data from prepare_organism_identification_data()
        If provided, skips data preparation step.
    """

    # =================================================
    # INPUT VALIDATION
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
                    "No data available for multinomial "
                    "logistic regression."
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
                    "At least one independent variable "
                    "is required."
                )

        }


    # =================================================
    # PREPARE DATA
    # =================================================
    #
    # If prepared_data is provided, use it directly.
    # Otherwise, prepare the data from the dataframe.
    #
    # ALSO: Check if df is already the prepared dataframe
    # (contains only the required columns with no missing values)
    #
    # =================================================

    # Check if df might already be prepared data
    # If it has "data" key, it's a prepared dict
    if isinstance(df, dict) and df.get("success", False):
        # The caller passed prepared_data as df
        prepared_data = df
        # Try to get original df from somewhere else
        # This is a fallback for mis-parameterization

    if prepared_data is not None and prepared_data.get("success", False):

        # Use pre-prepared data
        regression_df = prepared_data["data"].copy()
        prepared = prepared_data

        # Ensure the model type matches
        if prepared.get("model") != MODEL_TYPE:
            return {

                "success": False,

                "model":
                    MODEL_TYPE,

                "model_name":
                    MODEL_NAME,

                "error":
                    (
                        f"Prepared data model mismatch: "
                        f"expected {MODEL_TYPE}, got {prepared.get('model')}"
                    )

            }

    else:

        # =================================================
        # CHECK IF df IS ALREADY A PREPARED DATAFRAME
        # =================================================
        #
        # If the dataframe doesn't have 'culture_result' column
        # but has 'organism_identification', it's likely already prepared.
        #
        # =================================================

        if "culture_result" not in df.columns and "organism_identification" in df.columns:
            # This looks like prepared data - use it directly
            regression_df = df.copy()
            prepared = {"data": regression_df, "success": True}

        else:
            # Prepare data from scratch
            prepared = (

                prepare_organism_identification_data(

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

                            "Unable to prepare multinomial "
                            "regression data."

                        ),

                    "details":
                        prepared

                }


            regression_df = prepared[
                "data"
            ].copy()


    # =================================================
    # VALIDATE OUTCOME
    # =================================================

    validation = (

        _validate_multinomial_outcome(

            regression_df

        )

    )


    if not validation["valid"]:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                validation["error"],

            "categories":
                validation.get(
                    "categories",
                    []
                )

        }


    categories = validation[
        "categories"
    ]


    reference_category = validation[
        "reference_category"
    ]


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

    encoded_df, category_mapping = (

        _encode_multinomial_outcome(

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
                    "multinomial design matrix."
                ),

            "details":
                str(exc)

        }


    # =================================================
    # CREATE Y
    # =================================================

    y = (

        encoded_df[
            OUTCOME_COLUMN
        ]

        .copy()

    )


    # =================================================
    # ALIGN DATA
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


    # =================================================
    # CHECK OBSERVATIONS
    # =================================================

    if len(y) == 0:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "No valid observations remain after "
                    "design-matrix construction."
                )

        }


    # =================================================
    # CHECK OUTCOME CATEGORIES
    # =================================================

    observed_codes = sorted(

        y.unique().tolist()

    )


    expected_codes = list(

        range(
            len(categories)
        )

    )


    if observed_codes != expected_codes:

        observed_categories = []

        for code in observed_codes:

            try:

                code = int(code)

                if (
                    0
                    <=
                    code
                    <
                    len(categories)
                ):

                    observed_categories.append(
                        categories[code]
                    )

            except (
                TypeError,
                ValueError
            ):

                continue


        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Not all organism categories are "
                    "represented after model preparation."
                ),

            "observed_categories":
                observed_categories,

            "expected_categories":
                categories

        }


    # =================================================
    # SAMPLE SIZE
    # =================================================

    n_observations = len(
        y
    )


    number_predictors = (

        X.shape[1] - 1

    )


    number_categories = len(
        categories
    )


    # =================================================
    # NUMBER OF PARAMETERS
    # =================================================

    number_parameters = (

        (number_predictors + 1)

        *

        (number_categories - 1)

    )


    if n_observations <= number_parameters:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "There are too few observations "
                    "relative to the number of multinomial "
                    "regression parameters."
                ),

            "n":
                int(
                    n_observations
                ),

            "number_parameters":
                int(
                    number_parameters
                )

        }


    # =================================================
    # CHECK DESIGN MATRIX RANK
    # =================================================

    try:

        matrix_rank = np.linalg.matrix_rank(
            X.values
        )

        number_columns = X.shape[1]

    except Exception as exc:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "Unable to determine the rank "
                    "of the multinomial design matrix."
                ),

            "details":
                str(exc)

        }


    if matrix_rank < number_columns:

        return {

            "success": False,

            "model":
                MODEL_TYPE,

            "model_name":
                MODEL_NAME,

            "error":
                (
                    "The multinomial regression design "
                    "matrix is singular."
                ),

            "matrix_rank":
                int(
                    matrix_rank
                ),

            "matrix_columns":
                int(
                    number_columns
                ),

            "possible_causes": [

                "Perfect multicollinearity",

                "Rare predictor categories",

                "Too many predictors",

                "Empty or sparse combinations "
                "of predictor categories"

            ]

        }


    # =================================================
    # CALCULATE VIF
    # =================================================

    try:

        vif = calculate_vif(
            X
        )

    except Exception:

        vif = []


    # =================================================
    # FIT NULL MODEL
    # =================================================

    try:

        X_null = pd.DataFrame({

            "const":
                np.ones(
                    len(y)
                )

        })


        null_model = MNLogit(
            y,
            X_null
        )


        with warnings.catch_warnings():

            warnings.simplefilter(
                "ignore"
            )

            null_result = null_model.fit(

                maxiter=200,

                disp=False

            )


        null_log_likelihood = (
            null_result.llf
        )


    except Exception:

        null_log_likelihood = None


    # =================================================
    # FIT FULL MULTINOMIAL MODEL
    # =================================================

    try:

        model = MNLogit(
            y,
            X
        )


        with warnings.catch_warnings():

            warnings.simplefilter(
                "ignore"
            )

            result = model.fit(

                maxiter=200,

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
                    "The multinomial logistic regression "
                    "could not be estimated because the "
                    "design matrix is singular or "
                    "numerically unstable."
                ),

            "details":
                str(exc),

            "possible_causes": [

                "Perfect multicollinearity",

                "Rare organism categories",

                "Rare predictor categories",

                "Sparse combinations of predictors",

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
                    "Multinomial logistic regression "
                    "failed during model fitting."
                ),

            "details":
                str(exc),

            "possible_causes": [

                "Rare organism categories",

                "Sparse data",

                "Perfect or quasi-complete separation",

                "Multicollinearity",

                "Insufficient sample size",

                "Numerical convergence problems"

            ]

        }


    # =================================================
    # CONVERGENCE
    # =================================================

    converged = _check_convergence(
        result
    )


    # =================================================
    # EXTRACT RESULTS
    # =================================================

    try:

        coefficients = (

            _extract_multinomial_results(

                result,

                categories,

                reference_category

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
                    "Unable to extract multinomial "
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

            n_observations,

            number_categories,

            number_predictors

        )

    )


    # =================================================
    # RETURN RESULTS
    # =================================================

    return {

        "success":
            True,

        "model":
            MODEL_TYPE,

        "model_name":
            MODEL_NAME,

        # ---------------------------------------------
        # Outcome
        # ---------------------------------------------

        "dependent_variable":
            OUTCOME_COLUMN,

        "reference_outcome":
            reference_category,

        "outcome_categories":
            categories,

        "outcome_distribution":
            outcome_distribution,

        "category_mapping":
            category_mapping,

        # ---------------------------------------------
        # Predictors
        # ---------------------------------------------

        "independent_variables":
            list(
                independent_variables
            ),

        "reference_categories":
            reference_categories,

        # ---------------------------------------------
        # Sample information
        # ---------------------------------------------

        "n":
            int(
                n_observations
            ),

        "number_outcome_categories":
            int(
                number_categories
            ),

        "number_predictors":
            int(
                number_predictors
            ),

        "number_parameters":
            int(
                number_parameters
            ),

        # ---------------------------------------------
        # Model status
        # ---------------------------------------------

        "converged":
            converged,

        # ---------------------------------------------
        # Coefficients / RRR
        # ---------------------------------------------

        "coefficients":
            coefficients,

        # ---------------------------------------------
        # Model statistics
        # ---------------------------------------------

        "statistics":
            model_statistics,

        # ---------------------------------------------
        # Diagnostics
        # ---------------------------------------------

        "vif":
            vif

    }