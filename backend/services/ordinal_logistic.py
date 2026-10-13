# ============================================================
# ORDINAL LOGISTIC REGRESSION
# ============================================================
#
# Proportional-odds ordinal logistic regression using
# statsmodels OrderedModel.
#
# This module supports dynamic outcome columns:
#   - age_group (for age group ordinal regression)
#   - antibiogram_susceptibility (for antibiogram ordinal regression)
#
# IMPORTANT:
#     Ordinal categories must have a meaningful order.
#
# ============================================================

import numpy as np
import pandas as pd

from scipy.stats import chi2

from statsmodels.miscmodels.ordinal_model import OrderedModel

from services.regression_data import (
    prepare_ordinal_outcome_data
)

from services.regression_helpers import (
    calculate_vif
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_ORDERED_CATEGORIES = {
    "age_group": [
        "<30",
        "30-60",
        ">60"
    ],
    "antibiogram_susceptibility": [
        "resistant",
        "intermediate",
        "susceptible"
    ]
}


# ============================================================
# SAFE FLOAT
# ============================================================

def _safe_float(value, digits=6):

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
        digits
    )


# ============================================================
# SAFE INT
# ============================================================

def _safe_int(value):

    try:

        return int(value)

    except (
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# NORMALIZE CATEGORY
# ============================================================

def _normalize_category(value):

    if value is None:

        return None

    try:

        if pd.isna(value):

            return None

    except Exception:

        pass

    value = str(value).strip().lower()

    if value in {
        "",
        "nan",
        "none",
        "null",
        "<na>"
    }:

        return None

    return value


# ============================================================
# VALIDATE ORDINAL OUTCOME
# ============================================================

def _validate_ordinal_outcome(
    df,
    ordinal_outcome_column,
    ordered_categories=None
):

    if df is None or df.empty:

        return {
            "valid": False,
            "error":
                "No observations are available."
        }


    if ordinal_outcome_column not in df.columns:

        return {
            "valid": False,
            "error":
                (
                    f"Ordinal outcome column "
                    f"'{ordinal_outcome_column}' "
                    "is missing."
                )
        }


    values = (

        df[ordinal_outcome_column]

        .map(
            _normalize_category
        )

        .dropna()

    )


    if values.empty:

        return {
            "valid": False,
            "error":
                "The ordinal outcome contains no valid observations."
        }


    observed_categories = (
        values.unique().tolist()
    )


    # --------------------------------------------------------
    # Determine category ordering
    # --------------------------------------------------------

    if ordered_categories is not None:

        categories = [

            _normalize_category(category)

            for category
            in ordered_categories

        ]

        categories = [

            category

            for category
            in categories

            if category is not None

        ]

        categories = list(
            dict.fromkeys(categories)
        )

    else:

        # Use default ordering based on outcome column
        categories = DEFAULT_ORDERED_CATEGORIES.get(
            ordinal_outcome_column,
            None
        )

        if categories is None:
            return {
                "valid": False,
                "error":
                    (
                        "An explicit ordinal category order "
                        "must be supplied for this outcome."
                    )
            }


    if len(categories) < 3:

        return {
            "valid": False,
            "error":
                (
                    "Ordinal logistic regression requires "
                    "at least three ordered categories."
                ),
            "categories":
                categories
        }


    # --------------------------------------------------------
    # Unexpected categories
    # --------------------------------------------------------

    unexpected_categories = [

        category

        for category
        in observed_categories

        if category not in categories

    ]


    if unexpected_categories:

        return {
            "valid": False,
            "error":
                (
                    "The dataframe contains outcome "
                    "categories that are not included "
                    "in the specified ordinal order."
                ),
            "unexpected_categories":
                unexpected_categories,
            "ordered_categories":
                categories
        }


    # --------------------------------------------------------
    # Missing ordered categories
    # --------------------------------------------------------

    missing_categories = [

        category

        for category
        in categories

        if category not in observed_categories

    ]


    if missing_categories:

        return {
            "valid": False,
            "error":
                (
                    "One or more ordered outcome categories "
                    "have no observations."
                ),
            "missing_categories":
                missing_categories,
            "categories":
                categories
        }


    return {

        "valid":
            True,

        "categories":
            categories,

        "lowest_category":
            categories[0],

        "highest_category":
            categories[-1]

    }


# ============================================================
# ENCODE ORDINAL OUTCOME
# ============================================================

def _encode_ordinal_outcome(
    df,
    ordinal_outcome_column,
    categories
):

    encoded_df = df.copy()


    category_mapping = {

        category: index

        for index, category
        in enumerate(categories)

    }


    normalized_values = (

        encoded_df[
            ordinal_outcome_column
        ]

        .map(
            _normalize_category
        )

    )


    encoded_df[
        ordinal_outcome_column
    ] = normalized_values.map(
        category_mapping
    )


    encoded_df[
        ordinal_outcome_column
    ] = pd.to_numeric(

        encoded_df[
            ordinal_outcome_column
        ],

        errors="coerce"

    )


    return (
        encoded_df,
        category_mapping
    )


# ============================================================
# OUTCOME DISTRIBUTION
# ============================================================

def _get_outcome_distribution(
    df,
    ordinal_outcome_column,
    categories
):

    normalized = (

        df[
            ordinal_outcome_column
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


    for order, category in enumerate(
        categories
    ):

        count = int(
            counts.loc[category]
        )


        percentage = (

            count / total * 100

            if total > 0

            else 0

        )


        rows.append({

            "order":
                int(order),

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


    return rows


# ============================================================
# NULL LOG-LIKELIHOOD
# ============================================================

def _calculate_null_log_likelihood(
    y,
    number_categories
):

    try:

        y = np.asarray(
            y,
            dtype=int
        )


        y = y[
            np.isfinite(y)
        ]


        if len(y) == 0:

            return np.nan


        counts = np.bincount(

            y,

            minlength=number_categories

        )


        total = counts.sum()


        if total <= 0:

            return np.nan


        probabilities = (
            counts / total
        )


        probabilities = np.clip(

            probabilities,

            1e-12,

            1.0

        )


        return float(

            np.sum(

                counts
                *
                np.log(probabilities)

            )

        )

    except Exception:

        return np.nan


# ============================================================
# MODEL STATISTICS
# ============================================================

def _calculate_model_statistics(
    result,
    null_log_likelihood,
    n_observations,
    number_categories
):

    try:

        log_likelihood = float(
            result.llf
        )

    except Exception:

        log_likelihood = np.nan


    try:

        aic = float(
            result.aic
        )

    except Exception:

        aic = np.nan


    try:

        bic = float(
            result.bic
        )

    except Exception:

        bic = np.nan


    # --------------------------------------------------------
    # McFadden pseudo R²
    # --------------------------------------------------------

    if (

        np.isfinite(log_likelihood)

        and

        np.isfinite(null_log_likelihood)

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


    # --------------------------------------------------------
    # Likelihood-ratio statistic
    # --------------------------------------------------------

    if (

        np.isfinite(log_likelihood)

        and

        np.isfinite(null_log_likelihood)

    ):

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


    # --------------------------------------------------------
    # Number of predictor coefficients
    #
    # OrderedModel has:
    #
    #     predictor coefficients
    #     +
    #     K - 1 threshold parameters
    #
    # Therefore LR df is the number of predictors.
    # --------------------------------------------------------

    try:

        number_parameters = len(
            result.params
        )

    except Exception:

        number_parameters = 0


    number_thresholds = (
        number_categories - 1
    )


    lr_df = max(

        number_parameters
        -
        number_thresholds,

        0

    )


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
            _safe_int(
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
            _safe_int(
                lr_df
            ),

        "likelihood_ratio_p_value":
            _safe_float(
                lr_p_value
            )

    }


# ============================================================
# EXTRACT PREDICTOR RESULTS
# ============================================================

def _extract_ordinal_results(
    result
):

    params = result.params
    standard_errors = result.bse
    z_values = result.tvalues
    p_values = result.pvalues

    confidence_intervals = (
        result.conf_int()
    )


    rows = []


    for variable in params.index:

        variable_name = str(
            variable
        )


        # OrderedModel threshold parameters
        # contain "/".
        if "/" in variable_name:

            continue


        coefficient = params[
            variable
        ]

        standard_error = standard_errors[
            variable
        ]

        z_value = z_values[
            variable
        ]

        p_value = p_values[
            variable
        ]


        try:

            ci_lower = confidence_intervals.loc[
                variable,
                0
            ]

            ci_upper = confidence_intervals.loc[
                variable,
                1
            ]

        except Exception:

            ci_lower = np.nan
            ci_upper = np.nan


        try:

            odds_ratio = np.exp(
                coefficient
            )

        except Exception:

            odds_ratio = np.nan


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


        rows.append({

            "variable":
                variable_name,

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


# ============================================================
# EXTRACT ORDINAL THRESHOLDS
# ============================================================

def _extract_thresholds(
    result,
    categories
):

    try:

        threshold_indices = [

            index

            for index
            in result.params.index

            if "/" in str(index)

        ]


        if not threshold_indices:

            return []


        transformed_parameters = np.asarray(

            [

                result.params[index]

                for index
                in threshold_indices

            ],

            dtype=float

        )


        actual_thresholds = (

            result.model.transform_threshold_params(
                transformed_parameters
            )

        )


        # transform_threshold_params returns
        # [-inf, threshold_1, ..., threshold_K-1, inf]
        actual_thresholds = actual_thresholds[1:-1]


        threshold_results = []


        for index, threshold in enumerate(
            actual_thresholds
        ):

            if index >= len(
                threshold_indices
            ):

                break


            parameter_name = str(
                threshold_indices[index]
            )


            # ------------------------------------------------
            # Approximate SE using numerical derivative.
            #
            # This is primarily descriptive. Predictor ORs
            # remain the main inferential quantities.
            # ------------------------------------------------

            try:

                covariance = result.cov_params()

                parameter_position = (
                    result.params.index.get_loc(
                        threshold_indices[index]
                    )
                )

                transformed_variance = (

                    covariance.iloc[
                        parameter_position,
                        parameter_position
                    ]

                )

                if index == 0:

                    derivative = 1.0

                else:

                    derivative = np.exp(
                        transformed_parameters[index]
                    )


                threshold_se = (

                    abs(derivative)
                    *
                    np.sqrt(
                        max(
                            transformed_variance,
                            0
                        )
                    )

                )

            except Exception:

                threshold_se = np.nan


            if (

                np.isfinite(threshold_se)

            ):

                ci_lower = (

                    threshold
                    -
                    1.96 * threshold_se

                )

                ci_upper = (

                    threshold
                    +
                    1.96 * threshold_se

                )

            else:

                ci_lower = np.nan
                ci_upper = np.nan


            if index < len(categories) - 1:

                lower_category = categories[
                    index
                ]

                upper_category = categories[
                    index + 1
                ]

                threshold_label = (

                    f"{lower_category} / "
                    f"{upper_category}"

                )

            else:

                threshold_label = parameter_name


            threshold_results.append({

                "threshold":
                    threshold_label,

                "parameter":
                    parameter_name,

                "value":
                    _safe_float(
                        threshold
                    ),

                "standard_error":
                    _safe_float(
                        threshold_se
                    ),

                "ci_lower":
                    _safe_float(
                        ci_lower
                    ),

                "ci_upper":
                    _safe_float(
                        ci_upper
                    )

            })


        return threshold_results


    except Exception:

        return []


# ============================================================
# CHECK CONVERGENCE
# ============================================================

def _check_convergence(
    result
):

    try:

        return bool(

            result.mle_retvals.get(
                "converged",
                False
            )

        )

    except Exception:

        return False


# ============================================================
# BUILD DESIGN MATRIX
# ============================================================

def _build_design_matrix(
    df,
    independent_variables
):

    predictor_frames = []

    reference_categories = {}

    missing_predictor_rows = pd.Series(
        False,
        index=df.index
    )


    for column in independent_variables:

        series = df[column]


        # ----------------------------------------------------
        # Numeric predictor
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            series
        ):

            numeric_series = pd.to_numeric(

                series,

                errors="coerce"

            )


            missing_predictor_rows |= (
                numeric_series.isna()
            )


            predictor_frame = pd.DataFrame({

                column:
                    numeric_series

            }, index=df.index)


        # ----------------------------------------------------
        # Categorical predictor
        # ----------------------------------------------------

        else:

            values = (

                series

                .map(
                    _normalize_category
                )

            )


            missing_predictor_rows |= (
                values.isna()
            )


            levels = (

                values

                .dropna()

                .unique()

                .tolist()

            )


            if len(levels) < 2:

                return {

                    "success": False,

                    "error":
                        (
                            f"Predictor '{column}' "
                            "has fewer than two usable "
                            "categories."
                        )

                }


            # Deterministic ordering.
            levels = sorted(
                levels
            )


            reference_category = (
                levels[0]
            )


            reference_categories[
                column
            ] = reference_category


            categorical = pd.Categorical(

                values,

                categories=levels

            )


            predictor_frame = pd.get_dummies(

                categorical,

                prefix=column,

                drop_first=True,

                dtype=float

            )


            predictor_frame.index = (
                df.index
            )


            # ------------------------------------------------
            # IMPORTANT:
            #
            # Missing categorical observations must NOT be
            # interpreted as the reference category.
            #
            # Set all dummy variables to NaN for missing
            # observations so they are removed during
            # alignment.
            # ------------------------------------------------

            missing_rows = values.isna()

            if missing_rows.any():

                predictor_frame.loc[
                    missing_rows,
                    :
                ] = np.nan


        predictor_frames.append(
            predictor_frame
        )


    if not predictor_frames:

        return {

            "success": False,

            "error":
                "No predictor variables were available."

        }


    X = pd.concat(

        predictor_frames,

        axis=1

    )


    X = X.astype(float)


    return {

        "success":
            True,

        "X":
            X,

        "reference_categories":
            reference_categories,

        "missing_predictor_rows":
            missing_predictor_rows

    }


# ============================================================
# MAIN ORDINAL LOGISTIC REGRESSION
# ============================================================

def run_ordinal_logistic_regression(
    df,
    independent_variables,
    ordered_categories=None,
    ordinal_outcome_column=None,
    prepared_data=None
):
    """
    Fits Ordinal Logistic Regression.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
    independent_variables : list
        List of predictor names
    ordered_categories : list, optional
        Explicit ordered categories for the outcome
    ordinal_outcome_column : str, optional
        The outcome column to use. If None, uses from prepared_data.
    prepared_data : dict, optional
        Pre-prepared data from prepare_regression_data()
        If provided, skips data preparation step.
    """

    # ========================================================
    # Determine outcome column from prepared_data if available
    # ========================================================

    if prepared_data is not None and prepared_data.get("success", False):
        # Use the dependent_variable from prepared_data
        ordinal_outcome_column = prepared_data.get("dependent_variable", ordinal_outcome_column)

    # ========================================================
    # If still None, check which ordinal outcome column is available
    # ========================================================

    if ordinal_outcome_column is None:
        # Check which ordinal outcome column is available in the dataframe
        if "antibiogram_susceptibility" in df.columns:
            ordinal_outcome_column = "antibiogram_susceptibility"
        elif "age_group" in df.columns:
            ordinal_outcome_column = "age_group"
        else:
            ordinal_outcome_column = "age_group"

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if df is None or df.empty:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                "No data available for ordinal logistic regression."

        }


    if (

        independent_variables is None

        or

        len(independent_variables) == 0

    ):

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "At least one independent variable "
                    "is required."
                )

        }


    # Remove duplicate predictor names while
    # preserving order.
    independent_variables = list(
        dict.fromkeys(
            independent_variables
        )
    )


    missing_predictors = [

        variable

        for variable
        in independent_variables

        if variable not in df.columns

    ]


    if missing_predictors:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "One or more independent variables "
                    "were not found in the dataframe."
                ),

            "missing_variables":
                missing_predictors

        }


    # ========================================================
    # DEFAULT ORDINAL ORDER
    # ========================================================

    if ordered_categories is None:

        ordered_categories = DEFAULT_ORDERED_CATEGORIES.get(
            ordinal_outcome_column,
            None
        )


    # ========================================================
    # GET REGRESSION READY DATA
    # ========================================================

    # If prepared_data is provided, use it directly
    if prepared_data is not None and prepared_data.get("success", False):

        regression_df = prepared_data["data"].copy()
        prepared = prepared_data

        # Update outcome column from prepared data if needed
        if prepared.get("dependent_variable"):
            ordinal_outcome_column = prepared.get("dependent_variable")

    else:
        # Prepare data from scratch using the ordinal data preparation
        try:

            prepared = prepare_ordinal_outcome_data(

                df,

                independent_variables,

                ordered_categories=
                    ordered_categories

            )

        except Exception as exc:

            return {

                "success": False,

                "model":
                    "ordinal_logistic",

                "error":
                    "Unable to prepare ordinal regression data.",

                "details":
                    str(exc)

            }


        if not prepared.get(
            "success",
            False
        ):

            return {

                "success": False,

                "model":
                    "ordinal_logistic",

                "error":
                    prepared.get(
                        "error",
                        "Unable to prepare ordinal regression data."
                    ),

                "details":
                    prepared

            }


        regression_df = prepared[
            "data"
        ].copy()

        # Update outcome column from prepared data
        ordinal_outcome_column = prepared.get("dependent_variable", ordinal_outcome_column)


    # ========================================================
    # VALIDATE OUTCOME
    # ========================================================

    validation = (
        _validate_ordinal_outcome(

            regression_df,

            ordinal_outcome_column,

            ordered_categories=
                ordered_categories

        )
    )


    if not validation["valid"]:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                validation["error"],

            "details":
                validation

        }


    categories = validation[
        "categories"
    ]


    # ========================================================
    # ENCODE OUTCOME
    # ========================================================

    encoded_df, category_mapping = (
        _encode_ordinal_outcome(

            regression_df,

            ordinal_outcome_column,

            categories

        )
    )


    # ========================================================
    # BUILD DESIGN MATRIX
    # ========================================================

    design = _build_design_matrix(

        encoded_df,

        independent_variables

    )


    if not design["success"]:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                design["error"]

        }


    X = design["X"]

    reference_categories = (
        design["reference_categories"]
    )


    # ========================================================
    # ALIGN OUTCOME AND PREDICTORS
    # ========================================================

    y = encoded_df[
        ordinal_outcome_column
    ].astype(float)


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
                "ordinal_logistic",

            "error":
                (
                    "No valid observations remain after "
                    "removing missing outcome or predictor values."
                )

        }


    # ========================================================
    # CHECK OUTCOME CATEGORIES
    # ========================================================

    observed_codes = sorted(
        y.unique().tolist()
    )


    expected_codes = list(
        range(
            len(categories)
        )
    )


    if observed_codes != expected_codes:

        observed_categories = [

            categories[int(code)]

            for code
            in observed_codes

            if int(code) < len(categories)

        ]


        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "Not all ordinal outcome categories "
                    "are represented in the final analysis sample."
                ),

            "observed_categories":
                observed_categories,

            "expected_categories":
                categories

        }


    # ========================================================
    # OUTCOME DISTRIBUTION
    # ========================================================

    analysis_df = encoded_df.loc[
        valid_rows
    ].copy()


    outcome_distribution = (
        _get_outcome_distribution(

            analysis_df,

            ordinal_outcome_column,

            categories

        )
    )


    # ========================================================
    # SAMPLE SIZE
    # ========================================================

    n_observations = len(y)

    number_predictors = X.shape[1]

    number_categories = len(categories)

    number_thresholds = (
        number_categories - 1
    )

    number_parameters = (

        number_predictors
        +
        number_thresholds

    )


    if n_observations <= number_parameters:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "There are too few observations "
                    "relative to the number of ordinal "
                    "regression parameters."
                ),

            "n":
                int(n_observations),

            "number_parameters":
                int(number_parameters)

        }


    # ========================================================
    # CHECK DESIGN MATRIX RANK
    # ========================================================

    try:

        matrix_rank = np.linalg.matrix_rank(
            X.values
        )

        number_columns = X.shape[1]

    except Exception:

        matrix_rank = None
        number_columns = X.shape[1]


    if (

        matrix_rank is not None

        and

        matrix_rank < number_columns

    ):

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "The ordinal regression design "
                    "matrix is singular."
                ),

            "matrix_rank":
                int(matrix_rank),

            "matrix_columns":
                int(number_columns),

            "possible_causes": [

                "Perfect multicollinearity",

                "Rare predictor categories",

                "Too many predictors",

                "Empty combinations of predictors"

            ]

        }


    # ========================================================
    # VIF
    # ========================================================

    try:

        vif = calculate_vif(X)

    except Exception:

        vif = []


    # ========================================================
    # NULL MODEL
    # ========================================================

    null_log_likelihood = (
        _calculate_null_log_likelihood(

            y,

            number_categories

        )
    )


    # ========================================================
    # FIT ORDINAL MODEL
    # ========================================================

    try:

        model = OrderedModel(

            y,

            X,

            distr="logit"

        )


        result = model.fit(

            method="bfgs",

            disp=False,

            maxiter=1000

        )


    except np.linalg.LinAlgError as exc:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "The ordinal logistic regression "
                    "could not be estimated because the "
                    "design matrix is singular or "
                    "numerically unstable."
                ),

            "details":
                str(exc),

            "possible_causes": [

                "Perfect multicollinearity",

                "Rare predictor categories",

                "Sparse data",

                "Too many predictors",

                "Numerical instability"

            ]

        }


    except Exception as exc:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "Ordinal logistic regression "
                    "failed during model fitting."
                ),

            "details":
                str(exc),

            "possible_causes": [

                "Incorrect outcome ordering",

                "Sparse outcome categories",

                "Rare predictor levels",

                "Multicollinearity",

                "Insufficient sample size",

                "Numerical convergence problems"

            ]

        }


    # ========================================================
    # CONVERGENCE
    # ========================================================

    converged = _check_convergence(
        result
    )


    # ========================================================
    # EXTRACT PREDICTOR RESULTS
    # ========================================================

    try:

        coefficients = (
            _extract_ordinal_results(
                result
            )
        )

    except Exception as exc:

        return {

            "success": False,

            "model":
                "ordinal_logistic",

            "error":
                (
                    "Unable to extract ordinal "
                    "regression coefficients."
                ),

            "details":
                str(exc)

        }


    # ========================================================
    # EXTRACT THRESHOLDS
    # ========================================================

    thresholds = _extract_thresholds(

        result,

        categories

    )


    # ========================================================
    # MODEL STATISTICS
    # ========================================================

    model_statistics = (
        _calculate_model_statistics(

            result,

            null_log_likelihood,

            n_observations,

            number_categories

        )
    )


    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return {

        "success":
            True,

        "model":
            "ordinal_logistic",

        "model_name":
            "Ordinal Logistic Regression",

        # ----------------------------------------------------
        # Outcome
        # ----------------------------------------------------

        "dependent_variable":
            ordinal_outcome_column,

        "outcome_categories":
            categories,

        "category_order":
            categories,

        "category_mapping":
            category_mapping,

        "lowest_category":
            categories[0],

        "highest_category":
            categories[-1],

        "outcome_distribution":
            outcome_distribution,

        # ----------------------------------------------------
        # Predictors
        # ----------------------------------------------------

        "independent_variables":
            list(independent_variables),

        "design_matrix_columns":
            list(X.columns),

        "reference_categories":
            reference_categories,

        # ----------------------------------------------------
        # Sample
        # ----------------------------------------------------

        "n":
            int(n_observations),

        "number_predictors":
            int(number_predictors),

        "number_thresholds":
            int(number_thresholds),

        "number_parameters":
            int(number_parameters),

        # ----------------------------------------------------
        # Model status
        # ----------------------------------------------------

        "converged":
            converged,

        # ----------------------------------------------------
        # Effects
        # ----------------------------------------------------

        "coefficients":
            coefficients,

        # ----------------------------------------------------
        # Thresholds
        # ----------------------------------------------------

        "thresholds":
            thresholds,

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        "statistics":
            model_statistics,

        # ----------------------------------------------------
        # Diagnostics
        # ----------------------------------------------------

        "vif":
            vif

    }