# ============================================================
# REGRESSION DIAGNOSTICS
# ============================================================
#
# Diagnostic utilities for:
#
#     1. Binary Logistic Regression
#     2. Multinomial Logistic Regression
#     3. Ordinal Logistic Regression
#
# This module does NOT fit the primary regression models.
#
# It provides:
#
#     - VIF
#     - Condition number
#     - Binary classification diagnostics
#     - Hosmer-Lemeshow test
#     - Binary logistic residuals
#     - Linearity in the logit screening
#     - Multinomial diagnostics
#     - Ordinal diagnostics
#     - Brant-style proportional-odds diagnostic
#     - Convergence checks
#     - Residual summaries
#
# ============================================================

import numpy as np
import pandas as pd

from scipy.stats import (
    chi2,
    pearsonr
)

import statsmodels.api as sm

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
)


# ============================================================
# SAFE FLOAT
# ============================================================

def _safe_float(
    value,
    digits=6
):

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
# SAFE INTEGER
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


# ============================================================
# VIF
# ============================================================

def calculate_vif_diagnostics(X):

    if X is None:

        return {

            "success": False,

            "error":
                "Design matrix is None."

        }


    if not isinstance(
        X,
        pd.DataFrame
    ):

        X = pd.DataFrame(X)


    if X.empty:

        return {

            "success": False,

            "error":
                "Design matrix is empty."

        }


    predictor_columns = [

        column

        for column
        in X.columns

        if str(column).lower()
        not in {
            "const",
            "intercept"
        }

    ]


    if not predictor_columns:

        return {

            "success": True,

            "vif": [],

            "interpretation":
                "No predictor columns available."

        }


    predictors = X[
        predictor_columns
    ].copy()


    predictors = (

        predictors

        .apply(
            pd.to_numeric,
            errors="coerce"
        )

        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )

        .dropna(
            axis=0,
            how="any"
        )

    )


    # --------------------------------------------------------
    # Remove constant predictors
    # --------------------------------------------------------

    usable_columns = [

        column

        for column
        in predictors.columns

        if predictors[column].nunique(
            dropna=True
        ) > 1

    ]


    predictors = predictors[
        usable_columns
    ]


    if predictors.empty:

        return {

            "success": True,

            "vif": [],

            "interpretation":
                (
                    "No variable with sufficient "
                    "variation is available for VIF."
                )

        }


    # --------------------------------------------------------
    # Need enough observations
    # --------------------------------------------------------

    if len(predictors) <= len(
        predictors.columns
    ):

        return {

            "success": False,

            "vif": [],

            "error":
                (
                    "There are too few observations "
                    "to calculate reliable VIF values."
                )

        }


    vif_results = []


    for index, column in enumerate(
        predictors.columns
    ):

        try:

            vif_value = (
                variance_inflation_factor(

                    predictors.values,

                    index

                )
            )

        except Exception:

            vif_value = np.nan


        vif = _safe_float(
            vif_value
        )


        if vif is None:

            interpretation = (
                "Unable to calculate VIF."
            )

        elif vif < 5:

            interpretation = (
                "No substantial multicollinearity."
            )

        elif vif < 10:

            interpretation = (
                "Potential multicollinearity."
            )

        else:

            interpretation = (
                "High multicollinearity."
            )


        vif_results.append({

            "variable":
                str(column),

            "vif":
                vif,

            "interpretation":
                interpretation

        })


    return {

        "success":
            True,

        "vif":
            vif_results

    }


# ============================================================
# CONDITION NUMBER
# ============================================================

def calculate_condition_number(X):

    if X is None:

        return None


    try:

        X_numeric = (

            pd.DataFrame(X)

            .apply(
                pd.to_numeric,
                errors="coerce"
            )

            .replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )

            .dropna(
                axis=0,
                how="any"
            )

        )


        if X_numeric.empty:

            return None


        # Remove constant columns.
        usable_columns = [

            column

            for column
            in X_numeric.columns

            if X_numeric[column].nunique() > 1

        ]


        X_numeric = X_numeric[
            usable_columns
        ]


        if X_numeric.empty:

            return None


        # ----------------------------------------------------
        # Standardize predictors.
        # ----------------------------------------------------

        means = X_numeric.mean()

        standard_deviations = (
            X_numeric.std(
                ddof=0
            )
        )


        standard_deviations = (
            standard_deviations
            .replace(
                0,
                np.nan
            )
        )


        X_standardized = (

            X_numeric
            -
            means

        ) / standard_deviations


        X_standardized = (

            X_standardized

            .replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )

            .dropna(
                axis=0,
                how="any"
            )

        )


        if X_standardized.empty:

            return None


        condition_number = np.linalg.cond(
            X_standardized.values
        )


        return _safe_float(
            condition_number
        )


    except Exception:

        return None


# ============================================================
# BINARY CLASSIFICATION DIAGNOSTICS
# ============================================================

def binary_classification_diagnostics(
    y_true,
    predicted_probability,
    threshold=0.50
):

    try:

        y_true = np.asarray(
            y_true,
            dtype=float
        )

        predicted_probability = np.asarray(
            predicted_probability,
            dtype=float
        )

    except Exception:

        return {

            "success": False,

            "error":
                "Unable to convert classification inputs."

        }


    if len(y_true) != len(
        predicted_probability
    ):

        return {

            "success": False,

            "error":
                (
                    "Observed outcomes and predicted "
                    "probabilities have different lengths."
                )

        }


    valid = (

        np.isfinite(y_true)

        &

        np.isfinite(
            predicted_probability
        )

    )


    y_true = y_true[
        valid
    ]

    predicted_probability = (
        predicted_probability[
            valid
        ]
    )


    if len(y_true) == 0:

        return {

            "success": False,

            "error":
                "No valid observations available."

        }


    # Validate binary outcome.
    unique_outcomes = np.unique(
        y_true
    )


    if not np.all(
        np.isin(
            unique_outcomes,
            [0, 1]
        )
    ):

        return {

            "success": False,

            "error":
                "y_true must contain only 0 and 1."

        }


    predicted_probability = np.clip(

        predicted_probability,

        0,

        1

    )


    predicted_class = (

        predicted_probability
        >= threshold

    ).astype(int)


    tp = int(
        np.sum(
            (y_true == 1)
            &
            (predicted_class == 1)
        )
    )


    tn = int(
        np.sum(
            (y_true == 0)
            &
            (predicted_class == 0)
        )
    )


    fp = int(
        np.sum(
            (y_true == 0)
            &
            (predicted_class == 1)
        )
    )


    fn = int(
        np.sum(
            (y_true == 1)
            &
            (predicted_class == 0)
        )
    )


    total = (
        tp
        +
        tn
        +
        fp
        +
        fn
    )


    accuracy = (

        (tp + tn)
        /
        total

        if total > 0

        else np.nan

    )


    sensitivity = (

        tp
        /
        (tp + fn)

        if (tp + fn) > 0

        else np.nan

    )


    specificity = (

        tn
        /
        (tn + fp)

        if (tn + fp) > 0

        else np.nan

    )


    precision = (

        tp
        /
        (tp + fp)

        if (tp + fp) > 0

        else np.nan

    )


    recall = sensitivity


    f1 = (

        2
        *
        precision
        *
        recall
        /
        (
            precision
            +
            recall
        )

        if (

            np.isfinite(precision)

            and

            np.isfinite(recall)

            and

            precision + recall > 0

        )

        else np.nan

    )


    return {

        "success":
            True,

        "threshold":
            _safe_float(
                threshold
            ),

        "confusion_matrix": {

            "true_negative":
                tn,

            "false_positive":
                fp,

            "false_negative":
                fn,

            "true_positive":
                tp

        },

        "accuracy":
            _safe_float(
                accuracy
            ),

        "sensitivity":
            _safe_float(
                sensitivity
            ),

        "specificity":
            _safe_float(
                specificity
            ),

        "precision":
            _safe_float(
                precision
            ),

        "recall":
            _safe_float(
                recall
            ),

        "f1_score":
            _safe_float(
                f1
            )

    }


# ============================================================
# HOSMER-LEMESHOW TEST
# ============================================================

def hosmer_lemeshow_test(
    y_true,
    predicted_probability,
    groups=10
):

    try:

        data = pd.DataFrame({

            "observed":
                np.asarray(
                    y_true,
                    dtype=float
                ),

            "probability":
                np.asarray(
                    predicted_probability,
                    dtype=float
                )

        })

    except Exception:

        return {

            "success": False,

            "error":
                "Unable to construct Hosmer-Lemeshow data."

        }


    data = (

        data

        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )

        .dropna()

    )


    if len(data) < 20:

        return {

            "success": False,

            "error":
                (
                    "Hosmer-Lemeshow test requires "
                    "at least 20 observations."
                )

        }


    unique_outcomes = np.unique(
        data["observed"]
    )


    if not np.all(
        np.isin(
            unique_outcomes,
            [0, 1]
        )
    ):

        return {

            "success": False,

            "error":
                "Observed outcome must contain only 0 and 1."

        }


    groups = max(
        2,
        min(
            int(groups),
            len(data)
        )
    )


    try:

        data["group"] = pd.qcut(

            data["probability"],

            q=groups,

            duplicates="drop"

        )

    except Exception:

        return {

            "success": False,

            "error":
                (
                    "Unable to create probability "
                    "groups for Hosmer-Lemeshow test."
                )

        }


    grouped = (
        data
        .groupby(
            "group",
            observed=True
        )
    )


    observed_events = (
        grouped["observed"]
        .sum()
        .to_numpy()
    )


    total = (
        grouped["observed"]
        .count()
        .to_numpy()
    )


    expected_events = (
        grouped["probability"]
        .sum()
        .to_numpy()
    )


    observed_non_events = (

        total
        -
        observed_events

    )


    expected_non_events = (

        total
        -
        expected_events

    )


    event_denominator = np.where(

        expected_events > 0,

        expected_events,

        np.nan

    )


    non_event_denominator = np.where(

        expected_non_events > 0,

        expected_non_events,

        np.nan

    )


    chi_square = np.nansum(

        (
            observed_events
            -
            expected_events
        ) ** 2

        /

        event_denominator

    )


    chi_square += np.nansum(

        (
            observed_non_events
            -
            expected_non_events
        ) ** 2

        /

        non_event_denominator

    )


    number_groups = len(
        total
    )


    degrees_of_freedom = (
        number_groups - 2
    )


    if degrees_of_freedom > 0:

        p_value = chi2.sf(

            chi_square,

            degrees_of_freedom

        )

    else:

        p_value = np.nan


    group_results = []


    for index in range(
        number_groups
    ):

        group_results.append({

            "group":
                int(index + 1),

            "observed_events":
                int(
                    observed_events[index]
                ),

            "expected_events":
                _safe_float(
                    expected_events[index]
                ),

            "observed_non_events":
                int(
                    observed_non_events[index]
                ),

            "expected_non_events":
                _safe_float(
                    expected_non_events[index]
                ),

            "n":
                int(
                    total[index]
                )

        })


    if (

        np.isfinite(p_value)

        and

        p_value > 0.05

    ):

        interpretation = (
            "No evidence of lack of fit."
        )

    elif np.isfinite(p_value):

        interpretation = (
            "Evidence of lack of fit."
        )

    else:

        interpretation = (
            "Unable to determine model fit."
        )


    return {

        "success":
            True,

        "test":
            "Hosmer-Lemeshow",

        "chi_square":
            _safe_float(
                chi_square
            ),

        "degrees_of_freedom":
            _safe_int(
                degrees_of_freedom
            ),

        "p_value":
            _safe_float(
                p_value
            ),

        "groups":
            number_groups,

        "interpretation":
            interpretation,

        "group_results":
            group_results

    }


# ============================================================
# BINARY LOGISTIC RESIDUALS
# ============================================================
# ============================================================
# BINARY LOGISTIC RESIDUALS
# ============================================================

def binary_logistic_residuals(
    y_true,
    predicted_probability
):

    try:

        y = np.asarray(
            y_true,
            dtype=float
        )

        p = np.asarray(
            predicted_probability,
            dtype=float
        )

    except Exception:

        return {

            "success": False,

            "error":
                "Unable to convert residual inputs."

        }


    if len(y) != len(p):

        return {

            "success": False,

            "error":
                (
                    "Observed outcomes and predicted "
                    "probabilities have different lengths."
                )

        }


    valid = (

        np.isfinite(y)
        &
        np.isfinite(p)

    )


    y = y[
        valid
    ]

    p = p[
        valid
    ]


    if len(y) == 0:

        return {

            "success": False,

            "error":
                "No valid observations available."

        }


    # Clip probabilities to avoid log(0) and division by zero
    epsilon = 1e-10

    p_safe = np.clip(

        p,

        epsilon,

        1 - epsilon

    )


    # Response residual
    response_residual = (
        y - p_safe
    )


    # Pearson residual
    pearson_residual = (

        (y - p_safe)

        /

        np.sqrt(
            p_safe
            *
            (1 - p_safe)
        )

    )

    # Replace any infinite Pearson residuals with NaN
    pearson_residual = np.where(
        np.isfinite(pearson_residual),
        pearson_residual,
        np.nan
    )


    # Deviance residual - with safe computation
    # Handle edge cases where y=0 or y=1 and p_safe is clipped

    # Term for y=1: y * log(y / p)
    y_term = np.zeros_like(y)
    mask_y_positive = y > 0
    if np.any(mask_y_positive):
        # Only compute where y > 0
        y_vals = y[mask_y_positive]
        p_vals = p_safe[mask_y_positive]
        # Clip ratio to avoid numerical issues
        ratio = np.clip(y_vals / p_vals, 1e-10, 1e10)
        y_term[mask_y_positive] = y_vals * np.log(ratio)

    # Term for y=0: (1-y) * log((1-y) / (1-p))
    non_y_term = np.zeros_like(y)
    mask_non_y_positive = (1 - y) > 0
    if np.any(mask_non_y_positive):
        # Only compute where y < 1
        one_minus_y = 1 - y[mask_non_y_positive]
        one_minus_p = 1 - p_safe[mask_non_y_positive]
        # Clip ratio to avoid numerical issues
        ratio = np.clip(one_minus_y / one_minus_p, 1e-10, 1e10)
        non_y_term[mask_non_y_positive] = one_minus_y * np.log(ratio)

    deviance_component = (
        2
        *
        (
            y_term
            +
            non_y_term
        )

    )

    # Clip to avoid negative values due to numerical issues
    deviance_component = np.maximum(
        deviance_component,
        0
    )

    # Replace any NaNs in deviance_component with 0
    deviance_component = np.nan_to_num(
        deviance_component,
        nan=0.0
    )

    deviance_residual = (

        np.sign(
            y - p_safe
        )

        *

        np.sqrt(
            deviance_component
        )

    )

    # Replace NaNs in deviance_residual with 0
    deviance_residual = np.nan_to_num(
        deviance_residual,
        nan=0.0
    )


    return {

        "success":
            True,

        "n":
            int(len(y)),

        "response_residuals":
            response_residual.tolist(),

        "pearson_residuals":
            pearson_residual.tolist(),

        "deviance_residuals":
            deviance_residual.tolist(),

        "summary": {

            "pearson_mean":
                _safe_float(
                    np.nanmean(
                        pearson_residual
                    )
                ),

            "pearson_sd":
                _safe_float(
                    np.nanstd(
                        pearson_residual,
                        ddof=1
                    )
                ),

            "deviance_mean":
                _safe_float(
                    np.nanmean(
                        deviance_residual
                    )
                ),

            "deviance_sd":
                _safe_float(
                    np.nanstd(
                        deviance_residual,
                        ddof=1
                    )
                )

        }

    }

# ============================================================
# LINEARITY IN LOGIT
# ============================================================

def check_linearity_in_logit(
    df,
    continuous_variables,
    outcome_column,
    predicted_probability
):

    if df is None or df.empty:

        return {

            "success": False,

            "error":
                "Input dataframe is empty."

        }


    if outcome_column not in df.columns:

        return {

            "success": False,

            "error":
                (
                    f"Outcome column '{outcome_column}' "
                    "was not found."
                )

        }


    if not continuous_variables:

        return {

            "success": True,

            "results": []

        }


    try:

        p = np.asarray(
            predicted_probability,
            dtype=float
        )

    except Exception:

        return {

            "success": False,

            "error":
                "Unable to convert predicted probabilities."

        }


    if len(df) != len(p):

        return {

            "success": False,

            "error":
                (
                    "Dataframe and predicted probabilities "
                    "have different lengths."
                )

        }


    epsilon = 1e-10

    p = np.clip(

        p,

        epsilon,

        1 - epsilon

    )


    logit = np.log(

        p
        /
        (1 - p)

    )


    results = []


    for variable in continuous_variables:

        if variable not in df.columns:

            results.append({

                "variable":
                    variable,

                "correlation":
                    None,

                "p_value":
                    None,

                "error":
                    "Variable not found."

            })

            continue


        x = pd.to_numeric(

            df[variable],

            errors="coerce"

        ).to_numpy(
            dtype=float
        )


        valid = (

            np.isfinite(x)

            &

            np.isfinite(logit)

        )


        if np.sum(valid) < 3:

            results.append({

                "variable":
                    variable,

                "correlation":
                    None,

                "p_value":
                    None,

                "error":
                    "Too few valid observations."

            })

            continue


        # Pearson correlation between X and fitted logit
        # is only a screening diagnostic.
        try:

            correlation, p_value = pearsonr(

                x[valid],

                logit[valid]

            )

        except Exception:

            correlation = np.nan
            p_value = np.nan


        results.append({

            "variable":
                variable,

            "correlation":
                _safe_float(
                    correlation
                ),

            "p_value":
                _safe_float(
                    p_value
                )

        })


    return {

        "success":
            True,

        "results":
            results,

        "note":
            (
                "This Pearson-correlation approach is only "
                "a preliminary screening diagnostic. "
                "It should not be used as the sole assessment "
                "of linearity in the logit."
            )

    }


# ============================================================
# MULTINOMIAL CLASSIFICATION DIAGNOSTICS
# ============================================================

def multinomial_classification_diagnostics(
    y_true,
    predicted_probabilities,
    class_labels=None
):

    try:

        y = np.asarray(
            y_true
        )

        probabilities = np.asarray(
            predicted_probabilities,
            dtype=float
        )

    except Exception:

        return {

            "success": False,

            "error":
                "Unable to convert multinomial inputs."

        }


    if probabilities.ndim != 2:

        return {

            "success": False,

            "error":
                "Predicted probabilities must be a matrix."

        }


    if len(y) != probabilities.shape[0]:

        return {

            "success": False,

            "error":
                (
                    "Observed outcomes and predicted "
                    "probabilities have different lengths."
                )

        }


    if probabilities.shape[1] < 2:

        return {

            "success": False,

            "error":
                "At least two outcome classes are required."

        }


    valid = np.isfinite(
        probabilities
    ).all(
        axis=1
    )


    y = y[
        valid
    ]

    probabilities = probabilities[
        valid
    ]


    if len(y) == 0:

        return {

            "success": False,

            "error":
                "No valid observations available."

        }


    predicted_class = np.argmax(

        probabilities,

        axis=1

    )


    try:

        y_numeric = y.astype(int)

    except Exception:

        return {

            "success": False,

            "error":
                (
                    "Multinomial diagnostic requires "
                    "numeric class codes."
                )

        }


    accuracy = np.mean(

        predicted_class
        ==
        y_numeric

    )


    classes = np.unique(

        np.concatenate(
            [
                y_numeric,
                predicted_class
            ]
        )

    )


    confusion_matrix = []


    for actual in classes:

        row = []


        for predicted in classes:

            count = np.sum(

                (y_numeric == actual)
                &
                (predicted_class == predicted)

            )


            row.append(
                int(count)
            )


        confusion_matrix.append(
            row
        )


    if class_labels is None:

        labels = [

            str(class_value)

            for class_value
            in classes

        ]

    else:

        labels = [

            str(label)

            for label
            in class_labels

        ]


    return {

        "success":
            True,

        "accuracy":
            _safe_float(
                accuracy
            ),

        "classes":
            labels,

        "confusion_matrix":
            confusion_matrix

    }


# ============================================================
# MULTINOMIAL MODEL DIAGNOSTICS
# ============================================================

def multinomial_model_diagnostics(
    result
):

    if result is None:

        return {

            "success": False,

            "error":
                "Model result is None."

        }


    try:

        llf = float(
            result.llf
        )

    except Exception:

        llf = np.nan


    try:

        llnull = float(
            result.llnull
        )

    except Exception:

        llnull = np.nan


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


    if (

        np.isfinite(llf)

        and

        np.isfinite(llnull)

        and

        llnull != 0

    ):

        pseudo_r_squared = (

            1
            -
            (
                llf
                /
                llnull
            )

        )

    else:

        pseudo_r_squared = np.nan


    if (

        np.isfinite(llf)

        and

        np.isfinite(llnull)

    ):

        lr_statistic = (

            2
            *
            (
                llf
                -
                llnull
            )

        )

    else:

        lr_statistic = np.nan


    try:

        df_model = int(
            result.df_model
        )

    except Exception:

        df_model = None


    if (

        np.isfinite(lr_statistic)

        and

        df_model is not None

        and

        df_model > 0

    ):

        lr_p_value = chi2.sf(

            lr_statistic,

            df_model

        )

    else:

        lr_p_value = np.nan


    return {

        "success":
            True,

        "log_likelihood":
            _safe_float(
                llf
            ),

        "null_log_likelihood":
            _safe_float(
                llnull
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
            df_model,

        "likelihood_ratio_p_value":
            _safe_float(
                lr_p_value
            )

    }


# ============================================================
# ORDINAL MODEL DIAGNOSTICS
# ============================================================

def ordinal_model_diagnostics(
    result
):

    if result is None:

        return {

            "success": False,

            "error":
                "Model result is None."

        }


    try:

        llf = float(
            result.llf
        )

    except Exception:

        llf = np.nan


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


    try:

        converged = bool(

            result.mle_retvals.get(
                "converged",
                False
            )

        )

    except Exception:

        converged = False


    try:

        iterations = (
            result.mle_retvals.get(
                "iterations"
            )
        )

    except Exception:

        iterations = None


    return {

        "success":
            True,

        "log_likelihood":
            _safe_float(
                llf
            ),

        "aic":
            _safe_float(
                aic
            ),

        "bic":
            _safe_float(
                bic
            ),

        "converged":
            converged,

        "iterations":
            _safe_int(
                iterations
            )

    }


# ============================================================
# PROPORTIONAL ODDS / BRANT-STYLE DIAGNOSTIC
# ============================================================
#
# For K ordered categories, fit K-1 cumulative binary
# logistic regressions:
#
#     Y <= category 1  vs  Y > category 1
#
#     Y <= category 2  vs  Y > category 2
#
# etc.
#
# The proportional-odds assumption requires the predictor
# coefficients to be approximately constant across these
# cumulative logits.
#
# This function is a Brant-style coefficient comparison,
# not a formal implementation of the original Brant test.
#
# ============================================================

def proportional_odds_diagnostic(
    df,
    outcome_column,
    predictor_columns,
    ordered_categories=None
):

    if df is None or df.empty:

        return {

            "success": False,

            "error":
                "Input dataframe is empty."

        }


    if outcome_column not in df.columns:

        return {

            "success": False,

            "error":
                (
                    f"Outcome column '{outcome_column}' "
                    "was not found."
                )

        }


    if not predictor_columns:

        return {

            "success": False,

            "error":
                "No predictor columns were supplied."

        }


    predictor_columns = list(
        dict.fromkeys(
            predictor_columns
        )
    )


    missing_predictors = [

        variable

        for variable
        in predictor_columns

        if variable not in df.columns

    ]


    if missing_predictors:

        return {

            "success": False,

            "error":
                (
                    "One or more predictor columns "
                    "were not found."
                ),

            "missing_predictors":
                missing_predictors

        }


    # ========================================================
    # NORMALIZE OUTCOME
    # ========================================================

    outcome = (

        df[outcome_column]

        .map(
            _normalize_category
        )

    )


    # ========================================================
    # DETERMINE CATEGORY ORDER
    # ========================================================

    if ordered_categories is None:

        if outcome_column == "age_group":

            categories = [

                "<30",
                "30-60",
                ">60"

            ]

        else:

            return {

                "success": False,

                "error":
                    (
                        "Explicit ordered_categories "
                        "must be supplied for ordinal "
                        "outcomes."
                    )

            }

    else:

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
        dict.fromkeys(
            categories
        )
    )


    if len(categories) < 3:

        return {

            "success": False,

            "error":
                (
                    "At least three ordered categories "
                    "are required."
                )

        }


    # ========================================================
    # VALIDATE OUTCOME CATEGORIES
    # ========================================================

    observed_categories = set(
        outcome.dropna().unique()
    )


    unexpected = [

        category

        for category
        in observed_categories

        if category not in categories

    ]


    if unexpected:

        return {

            "success": False,

            "error":
                (
                    "Unexpected outcome categories "
                    "were found."
                ),

            "unexpected_categories":
                unexpected,

            "ordered_categories":
                categories

        }


    missing = [

        category

        for category
        in categories

        if category not in observed_categories

    ]


    if missing:

        return {

            "success": False,

            "error":
                (
                    "One or more ordered outcome "
                    "categories have no observations."
                ),

            "missing_categories":
                missing

        }


    # ========================================================
    # BUILD DESIGN MATRIX
    # ========================================================

    predictor_frames = []

    reference_categories = {}

    predictor_missing = pd.Series(
        False,
        index=df.index
    )


    for column in predictor_columns:

        series = df[column]


        # ----------------------------------------------------
        # Numeric predictor
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            series
        ):

            numeric_values = pd.to_numeric(

                series,

                errors="coerce"

            )


            predictor_missing |= (
                numeric_values.isna()
            )


            predictor_frame = pd.DataFrame({

                column:
                    numeric_values

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


            predictor_missing |= (
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


            levels = sorted(
                levels
            )


            reference_categories[
                column
            ] = levels[0]


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


            predictor_frame.index = df.index


            # Do NOT let missing categorical values become
            # the reference category.
            missing_rows = values.isna()

            if missing_rows.any():

                predictor_frame.loc[
                    missing_rows,
                    :
                ] = np.nan


        predictor_frames.append(
            predictor_frame
        )


    X = pd.concat(

        predictor_frames,

        axis=1

    )


    X = X.astype(float)


    if X.empty:

        return {

            "success": False,

            "error":
                "No predictor variables were available."

        }


    # ========================================================
    # FIT CUMULATIVE LOGISTIC MODELS
    # ========================================================

    split_results = []


    for split_index in range(
        len(categories) - 1
    ):

        lower_categories = categories[
            :split_index + 1
        ]


        higher_categories = categories[
            split_index + 1:
        ]


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # The cumulative binary outcome must contain NaN for
        # missing original outcome values. Using .isin(...)
        # directly would otherwise convert missing outcomes
        # into a valid 0.
        # ----------------------------------------------------

        binary_outcome = pd.Series(

            np.nan,

            index=df.index,

            dtype=float

        )


        outcome_valid = outcome.notna()


        binary_outcome.loc[
            outcome_valid
        ] = (

            outcome.loc[
                outcome_valid
            ]

            .isin(
                lower_categories
            )

            .astype(float)

        )


        valid = (

            binary_outcome.notna()

            &

            X.notna().all(
                axis=1
            )

        )


        y_binary = binary_outcome.loc[
            valid
        ].astype(float)


        X_binary = X.loc[
            valid
        ].copy()


        # ----------------------------------------------------
        # Both binary classes must be present.
        # ----------------------------------------------------

        if y_binary.nunique() < 2:

            split_results.append({

                "split":
                    int(split_index + 1),

                "lower_categories":
                    lower_categories,

                "higher_categories":
                    higher_categories,

                "success":
                    False,

                "error":
                    (
                        "Both outcome classes are not "
                        "represented in this cumulative split."
                    )

            })

            continue


        # ----------------------------------------------------
        # Add intercept.
        #
        # Unlike OrderedModel, ordinary Logit requires an
        # intercept unless explicitly omitted.
        # ----------------------------------------------------

        X_binary_with_intercept = sm.add_constant(

            X_binary,

            has_constant="add"

        )


        try:

            binary_model = sm.Logit(

                y_binary,

                X_binary_with_intercept

            )


            binary_result = binary_model.fit(

                method="newton",

                disp=False,

                maxiter=1000

            )


            coefficients = []


            for variable in X_binary.columns:

                coefficient = (
                    binary_result.params
                    .get(
                        variable,
                        np.nan
                    )
                )


                standard_error = (
                    binary_result.bse
                    .get(
                        variable,
                        np.nan
                    )
                )


                p_value = (
                    binary_result.pvalues
                    .get(
                        variable,
                        np.nan
                    )
                )


                try:

                    confidence_interval = (
                        binary_result.conf_int()
                        .loc[
                            variable
                        ]
                    )

                    ci_lower = (
                        confidence_interval.iloc[0]
                    )

                    ci_upper = (
                        confidence_interval.iloc[1]
                    )

                except Exception:

                    ci_lower = np.nan
                    ci_upper = np.nan


                try:

                    odds_ratio = np.exp(
                        coefficient
                    )

                    or_ci_lower = np.exp(
                        ci_lower
                    )

                    or_ci_upper = np.exp(
                        ci_upper
                    )

                except Exception:

                    odds_ratio = np.nan
                    or_ci_lower = np.nan
                    or_ci_upper = np.nan


                coefficients.append({

                    "variable":
                        str(variable),

                    "coefficient":
                        _safe_float(
                            coefficient
                        ),

                    "standard_error":
                        _safe_float(
                            standard_error
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


            try:

                converged = bool(

                    binary_result
                    .mle_retvals
                    .get(
                        "converged",
                        False
                    )

                )

            except Exception:

                converged = False


            split_results.append({

                "split":
                    int(split_index + 1),

                "lower_categories":
                    lower_categories,

                "higher_categories":
                    higher_categories,

                "success":
                    True,

                "n":
                    int(len(y_binary)),

                "coefficients":
                    coefficients,

                "converged":
                    converged

            })


        except Exception as exc:

            split_results.append({

                "split":
                    int(split_index + 1),

                "lower_categories":
                    lower_categories,

                "higher_categories":
                    higher_categories,

                "success":
                    False,

                "error":
                    str(exc)

            })


    # ========================================================
    # COMPARE COEFFICIENTS
    # ========================================================

    successful_splits = [

        split

        for split
        in split_results

        if split.get(
            "success"
        ) is True

    ]


    coefficient_comparison = []


    if successful_splits:

        variable_names = [

            str(column)

            for column
            in X.columns

        ]


        for variable in variable_names:

            values = []


            for split in successful_splits:

                for coefficient in split[
                    "coefficients"
                ]:

                    if (

                        coefficient[
                            "variable"
                        ]

                        ==

                        variable

                    ):

                        values.append({

                            "split":
                                split["split"],

                            "coefficient":
                                coefficient[
                                    "coefficient"
                                ],

                            "odds_ratio":
                                coefficient[
                                    "odds_ratio"
                                ],

                            "p_value":
                                coefficient[
                                    "p_value"
                                ]

                        })


            if values:

                numeric_coefficients = [

                    item["coefficient"]

                    for item in values

                    if item["coefficient"]
                    is not None

                ]


                if numeric_coefficients:

                    coefficient_range = (

                        max(
                            numeric_coefficients
                        )

                        -

                        min(
                            numeric_coefficients
                        )

                    )

                else:

                    coefficient_range = np.nan


                coefficient_comparison.append({

                    "variable":
                        variable,

                    "estimates":
                        values,

                    "coefficient_range":
                        _safe_float(
                            coefficient_range
                        )

                })


    # ========================================================
    # OVERALL INTERPRETATION
    # ========================================================

    expected_splits = (
        len(categories) - 1
    )


    if len(successful_splits) < expected_splits:

        interpretation = (

            "The proportional-odds diagnostic "
            "could not be completed for all cumulative "
            "splits."

        )

    elif coefficient_comparison:

        interpretation = (

            "The proportional-odds assumption requires "
            "predictor coefficients to be approximately "
            "constant across cumulative logits. Large "
            "differences in coefficient estimates across "
            "splits may indicate violation of the assumption."

        )

    else:

        interpretation = (

            "No coefficient comparisons were available."

        )


    return {

        "success":
            True,

        "test":
            "Brant-style proportional-odds diagnostic",

        "outcome":
            outcome_column,

        "categories":
            categories,

        "number_cumulative_splits":
            expected_splits,

        "reference_categories":
            reference_categories,

        "splits":
            split_results,

        "coefficient_comparison":
            coefficient_comparison,

        "interpretation":
            interpretation,

        "note":
            (
                "This is a Brant-style coefficient comparison "
                "across cumulative binary logistic models. "
                "It is not the original formal Brant test. "
                "Coefficient differences should be evaluated "
                "together with substantive knowledge and other "
                "diagnostics."
            )

    }


# ============================================================
# GENERIC MODEL CONVERGENCE
# ============================================================

def check_model_convergence(
    result
):

    if result is None:

        return {

            "success":
                False,

            "converged":
                False,

            "error":
                "Model result is None."

        }


    try:

        mle_retvals = (
            result.mle_retvals
        )


        if isinstance(
            mle_retvals,
            dict
        ):

            if "converged" in mle_retvals:

                return {

                    "success":
                        True,

                    "converged":
                        bool(
                            mle_retvals[
                                "converged"
                            ]
                        ),

                    "iterations":
                        _safe_int(
                            mle_retvals.get(
                                "iterations"
                            )
                        )

                }

    except Exception:

        pass


    try:

        fit_history = (
            result.fit_history
        )


        if isinstance(
            fit_history,
            dict
        ):

            if "converged" in fit_history:

                return {

                    "success":
                        True,

                    "converged":
                        bool(
                            fit_history[
                                "converged"
                            ]
                        )

                }

    except Exception:

        pass


    return {

        "success":
            False,

        "converged":
            False,

        "error":
            (
                "Convergence status could not "
                "be determined."
            )

    }


# ============================================================
# GENERIC RESIDUAL SUMMARY
# ============================================================

def summarize_residuals(
    residuals
):

    if residuals is None:

        return {

            "success":
                False,

            "error":
                "Residuals are None."

        }


    try:

        values = np.asarray(

            residuals,

            dtype=float

        )

    except Exception:

        return {

            "success":
                False,

            "error":
                "Unable to convert residuals."

        }


    values = values[
        np.isfinite(values)
    ]


    if len(values) == 0:

        return {

            "success":
                False,

            "error":
                "No finite residuals available."

        }


    absolute_values = np.abs(
        values
    )


    return {

        "success":
            True,

        "n":
            int(len(values)),

        "mean":
            _safe_float(
                np.mean(values)
            ),

        "sd":
            _safe_float(
                np.std(
                    values,
                    ddof=1
                )
            ),

        "minimum":
            _safe_float(
                np.min(values)
            ),

        "maximum":
            _safe_float(
                np.max(values)
            ),

        "mean_absolute":
            _safe_float(
                np.mean(
                    absolute_values
                )
            ),

        "maximum_absolute":
            _safe_float(
                np.max(
                    absolute_values
                )
            )

    }


# ============================================================
# COMBINED BASIC DIAGNOSTICS
# ============================================================

def run_basic_regression_diagnostics(
    X,
    result=None
):

    vif_result = (
        calculate_vif_diagnostics(
            X
        )
    )


    condition_number = (
        calculate_condition_number(
            X
        )
    )


    convergence = (
        check_model_convergence(
            result
        )
    )


    return {

        "vif":
            vif_result,

        "condition_number":
            condition_number,

        "convergence":
            convergence

    }