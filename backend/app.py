from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np

from services.filters import get_antibiogram_options
from services.organism_summary import get_organism_summary
from services.antibiogram_percentages import get_antibiogram
from services.association_metadata import get_association_options
from services.association_test import run_association_test
from services.regression_metadata import get_regression_options
from services.regression_data import (
    prepare_regression_data,
    determine_regression_model
)

from services.binary_logistic import (
    run_binary_logistic_regression
)

from services.multinomial_logistic import (
    run_multinomial_logistic_regression
)

from services.ordinal_logistic import (
    run_ordinal_logistic_regression
)

from services.regression_diagnostics import (
    calculate_vif_diagnostics,
    calculate_condition_number,
    binary_classification_diagnostics,
    hosmer_lemeshow_test,
    binary_logistic_residuals,
    check_linearity_in_logit,
    multinomial_classification_diagnostics,
    multinomial_model_diagnostics,
    ordinal_model_diagnostics,
    proportional_odds_diagnostic,
    check_model_convergence,
    summarize_residuals,
    run_basic_regression_diagnostics
)

from services.regression_results import (
    finalize_regression_response,
    build_frontend_payload,
    format_regression_error
)

from services.data_loader import (
    load_analysis_dataframe,
    apply_filters
)




app = Flask(__name__)
CORS(app)


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return jsonify({
        "status": "running",
        "message": "AMSP Backend API"
    })


# =====================================================
# SHARED FILTER NORMALIZATION
# =====================================================

def normalize_filter_list(value):
    """
    Normalize a filter value into a list.

    Accepted inputs:

        None
        ""
        "all"
        "Udupi"
        ["Udupi"]
        ["Udupi", "Dakshina Kannada"]
        ["all"]

    Returns:

        []       -> means ALL
        [values] -> selected values

    The internal representation is ALWAYS a list.
    """

    if value is None:
        return []


    # ---------------------------------------------
    # Single string
    # ---------------------------------------------

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return []

        if value.lower() == "all":
            return []

        return [value]


    # ---------------------------------------------
    # List / tuple
    # ---------------------------------------------

    if isinstance(value, (list, tuple)):

        cleaned = []

        for item in value:

            if item is None:
                continue

            item = str(item).strip()

            if not item:
                continue

            if item.lower() == "all":
                continue

            cleaned.append(item)

        return cleaned


    # ---------------------------------------------
    # Invalid type
    # ---------------------------------------------

    raise ValueError(
        "Filter value must be a string or list."
    )


# =====================================================
# GET QUERY FILTER
# =====================================================

def get_query_filter(name):
    """
    Reads repeated query parameters.

    Example:

        ?district=Udupi&district=Dakshina%20Kannada

    becomes:

        ["Udupi", "Dakshina Kannada"]

    'all' becomes [].
    """

    values = request.args.getlist(name)

    return normalize_filter_list(values)


# =====================================================
# ANTIBIOGRAM OPTIONS
# =====================================================

@app.route("/antibiogram-options", methods=["GET"])
def antibiogram_options():

    try:

        district = get_query_filter(
            "district"
        )

        block = get_query_filter(
            "block"
        )

        sample_type = get_query_filter(
            "sample_type"
        )

        organisms = get_query_filter(
            "organisms"
        )


        result = get_antibiogram_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms

        )


        return jsonify(result)


    except Exception as e:

        return jsonify({

            "error":
                f"Could not load antibiogram options: {str(e)}"

        }), 500


# =====================================================
# ANTIBIOGRAM REPORT
# =====================================================

@app.route("/antibiogram", methods=["GET"])
def antibiogram():

    try:

        district = get_query_filter(
            "district"
        )

        block = get_query_filter(
            "block"
        )

        sample_type = get_query_filter(
            "sample_type"
        )

        organisms = get_query_filter(
            "organisms"
        )

        antibiotics = get_query_filter(
            "antibiotics"
        )


        result = get_antibiogram(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            antibiotics=antibiotics

        )


        return jsonify(result)


    except Exception as e:

        return jsonify({

            "error":
                f"Could not generate antibiogram: {str(e)}"

        }), 500


# =====================================================
# ORGANISM SUMMARY
# =====================================================

@app.route("/organisms", methods=["GET"])
def organisms():

    try:

        # =================================================
        # READ MULTIPLE FILTER VALUES
        # =================================================

        districts = request.args.getlist("district")
        blocks = request.args.getlist("block")
        sample_types = request.args.getlist("sample_type")

        # =================================================
        # DEFAULT TO ALL
        # =================================================

        if not districts:
            districts = ["all"]

        if not blocks:
            blocks = ["all"]

        if not sample_types:
            sample_types = ["all"]

        # =================================================
        # RUN ORGANISM SUMMARY
        # =================================================

        data = get_organism_summary(

            district=districts,

            block=blocks,

            sample_type=sample_types

        )

        return jsonify(data)

    except Exception as e:

        return jsonify({

            "error":
                f"Could not generate organism summary: {str(e)}"

        }), 500

# =====================================================
# ASSOCIATION OPTIONS
# =====================================================

@app.route("/association-options", methods=["GET"])
def association_options():

    try:

        district = get_query_filter(
            "district"
        )

        block = get_query_filter(
            "block"
        )

        sample_type = get_query_filter(
            "sample_type"
        )

        organisms = get_query_filter(
            "organisms"
        )


        result = get_association_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms

        )


        return jsonify(result)


    except Exception as e:

        return jsonify({

            "error":
                f"Could not load association options: {str(e)}"

        }), 500


# =====================================================
# ASSOCIATION TEST
# =====================================================

@app.route("/association-test", methods=["POST"])
def association_test():

    data = request.get_json(
        silent=True
    ) or {}


    try:

        district = normalize_filter_list(
            data.get("district")
        )

        block = normalize_filter_list(
            data.get("block")
        )

        sample_type = normalize_filter_list(
            data.get("sample_type")
        )

        organisms = normalize_filter_list(
            data.get("organisms")
        )

        antibiotics = normalize_filter_list(
            data.get("antibiotics")
        )


        result = run_association_test(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            independent_variable=data.get(
                "independent_variable"
            ),

            dependent_variable=data.get(
                "dependent_variable"
            ),

            antibiotics=antibiotics

        )


        status = (
            400
            if "error" in result
            else 200
        )


        return jsonify(result), status


    except Exception as e:

        return jsonify({

            "error": str(e)

        }), 500




# =====================================================
# REGRESSION IMPORTS
# =====================================================

import pandas as pd
import numpy as np
import json
from flask import request, jsonify

from services.regression_metadata import (
    get_regression_options
)

from services.regression_data import (
    prepare_regression_data,
    determine_regression_model
)

from services.binary_logistic import (
    run_binary_logistic_regression
)

from services.multinomial_logistic import (
    run_multinomial_logistic_regression
)

from services.ordinal_logistic import (
    run_ordinal_logistic_regression
)

from services.regression_diagnostics import (
    calculate_vif_diagnostics,
    calculate_condition_number,
    binary_classification_diagnostics,
    hosmer_lemeshow_test,
    binary_logistic_residuals,
    check_linearity_in_logit,
    multinomial_classification_diagnostics,
    multinomial_model_diagnostics,
    ordinal_model_diagnostics,
    proportional_odds_diagnostic,
    check_model_convergence,
    summarize_residuals,
    run_basic_regression_diagnostics
)

from services.regression_results import (
    finalize_regression_response,
    build_frontend_payload,
    format_regression_error
)

from services.data_loader import (
    load_analysis_dataframe,
    apply_filters
)


# =====================================================
# REGRESSION OPTIONS
# =====================================================

@app.route(
    "/regression-options",
    methods=["GET"]
)
def regression_options():

    try:

        district = request.args.get(
            "district",
            "all"
        )

        block = request.args.get(
            "block",
            "all"
        )

        sample_type = request.args.get(
            "sample_type",
            "all"
        )

        organisms = request.args.getlist(
            "organisms"
        )


        options = get_regression_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms

        )


        return jsonify(
            options
        ), 200


    except Exception as exc:

        return jsonify({

            "success": False,

            "error":
                "Unable to load regression options.",

            "details":
                str(exc)

        }), 500


# =====================================================
# DETERMINE REGRESSION MODEL
# =====================================================

@app.route(
    "/regression-model",
    methods=["POST"]
)
def regression_model():

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Request body must be a JSON object."
            }), 400

        dependent_variable = data.get(
            "dependent_variable"
        )

        # Get observed categories if provided
        observed_categories = data.get(
            "observed_categories"
        )

        if not dependent_variable:

            return jsonify({

                "success": False,

                "error":
                    "Dependent variable is required."

            }), 400


        result = determine_regression_model(
            dependent_variable,
            observed_categories=observed_categories
        )


        if not result.get(
            "success",
            False
        ):

            return jsonify(
                result
            ), 400


        return jsonify(
            result
        ), 200


    except Exception as exc:

        return jsonify({

            "success": False,

            "error":
                "Unable to determine regression model.",

            "details":
                str(exc)

        }), 500


# =====================================================
# MAIN REGRESSION ROUTE
# =====================================================

@app.route(
    "/regression",
    methods=["POST"]
)
def regression():

    try:

        # =================================================
        # REQUEST BODY
        # =================================================

        data = request.get_json(
            silent=True
        )

        # =================================================
        # DEBUG: Print request data
        # =================================================
        print("\n" + "=" * 60)
        print("REGRESSION REQUEST RECEIVED")
        print("=" * 60)
        print("Request data type:", type(data))
        if data:
            print("Request data keys:", list(data.keys()))
            print("Request data:")
            print(json.dumps(data, indent=2, default=str))
        else:
            print("Request data is None or empty")
        print("=" * 60 + "\n")


        if not isinstance(
            data,
            dict
        ):

            print("ERROR: Request body is not a dictionary")
            return jsonify({

                "success": False,

                "error":
                    "Request body must be a JSON object."

            }), 400


        # =================================================
        # FILTERS
        # =================================================

        district = data.get(
            "district",
            "all"
        )

        block = data.get(
            "block",
            "all"
        )

        sample_type = data.get(
            "sample_type",
            "all"
        )

        organisms = data.get(
            "organisms",
            []
        )

        # Ensure organisms is a list
        if isinstance(organisms, str):
            organisms = [organisms] if organisms != "all" else []

        print(f"Filters: district={district}, block={block}, sample_type={sample_type}, organisms={organisms}")


        # =================================================
        # REGRESSION VARIABLES
        # =================================================

        dependent_variable = data.get(
            "dependent_variable"
        )

        independent_variables = data.get(
            "independent_variables",
            []
        )

        # Ensure independent_variables is a list
        if isinstance(independent_variables, str):
            independent_variables = [independent_variables]
        elif not isinstance(independent_variables, list):
            independent_variables = []

        print(f"Variables: dependent={dependent_variable}, independent={independent_variables}")


        # =================================================
        # ANTIBIOTIC
        # =================================================

        antibiotic = data.get(
            "antibiotic"
        )

        # If antibiotic is "all", treat as None
        if antibiotic == "all":
            antibiotic = None

        print(f"Antibiotic: {antibiotic}")


        # =================================================
        # ORDINAL CATEGORIES (for ordinal logistic)
        # =================================================

        ordered_categories = data.get(
            "ordered_categories"
        )


        # =================================================
        # BASIC VALIDATION
        # =================================================

        if not dependent_variable:

            print("ERROR: Dependent variable is missing")
            return jsonify({

                "success": False,

                "error":
                    "Dependent variable is required."

            }), 400


        if not independent_variables:

            print("ERROR: Independent variables are missing")
            return jsonify({

                "success": False,

                "error":
                    "At least one independent variable "
                    "must be selected."

            }), 400


        # =================================================
        # LOAD COMPLETE ANALYSIS DATA
        # =================================================

        print("Loading analysis dataframe...")
        df = load_analysis_dataframe()


        if df is None or df.empty:

            print("ERROR: No analysis data available")
            return jsonify({

                "success": False,

                "error":
                    "No analysis data are available."

            }), 404

        print(f"Dataframe loaded: {len(df)} rows")


        # =================================================
        # APPLY COMMON FILTERS
        # =================================================

        print("Applying filters...")
        filtered_df = apply_filters(

            df,

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms

        )


        if filtered_df is None or filtered_df.empty:

            print("ERROR: No records after filtering")
            return jsonify({

                "success": False,

                "error":
                    (
                        "No records were found after "
                        "applying the selected filters."
                    )

            }), 404

        print(f"After filtering: {len(filtered_df)} rows")


        # =================================================
        # AUTOMATIC MODEL SELECTION
        # =================================================

        print("Determining model...")
        model_information = (
            determine_regression_model(
                dependent_variable
            )
        )


        if not model_information.get(
            "success",
            False
        ):

            print(f"ERROR: Model selection failed: {model_information}")
            return jsonify(
                model_information
            ), 400


        model_type = model_information[
            "model"
        ]

        print(f"Selected model: {model_type}")


        # =================================================
        # PREPARE REGRESSION DATA
        # =================================================

        print("Preparing regression data...")
        prepared = prepare_regression_data(

            filtered_df,

            dependent_variable=

                dependent_variable,

            independent_variables=

                independent_variables,

            antibiotic=

                antibiotic

        )


        if not prepared.get(
            "success",
            False
        ):

            print(f"ERROR: Data preparation failed: {prepared.get('error')}")
            return jsonify({

                "success": False,

                "model":
                    model_type,

                "error":
                    prepared.get(
                        "error",
                        "Unable to prepare regression data."
                    ),

                "details":
                    prepared

            }), 400


        regression_df = prepared.get(
            "data"
        )


        if regression_df is None:

            print("ERROR: Regression dataframe is None")
            return jsonify({

                "success": False,

                "model":
                    model_type,

                "error":
                    "Regression-ready dataframe is missing."

            }), 400

        print(f"Regression data prepared: {len(regression_df)} rows")


        # =================================================
        # FIT MODEL
        # =================================================

        print("Fitting model...")
        if model_type == "binary_logistic":

            model_result = (
                run_binary_logistic_regression(

                    filtered_df,

                    independent_variables

                )
            )


        elif model_type == "multinomial_logistic":

            model_result = (
                run_multinomial_logistic_regression(

                    filtered_df,

                    independent_variables,

                    prepared_data=prepared

                )
            )


        elif model_type == "ordinal_logistic":

            model_result = (
                run_ordinal_logistic_regression(

                    filtered_df,

                    independent_variables,

                    ordered_categories=ordered_categories,

                    ordinal_outcome_column=dependent_variable,

                    prepared_data=prepared

                )
            )


        else:

            print(f"ERROR: Unsupported model type: {model_type}")
            return jsonify({

                "success": False,

                "error":
                    (
                        f"Unsupported regression model "
                        f"'{model_type}'."
                    )

            }), 400


        if not model_result.get(
            "success",
            False
        ):

            print(f"ERROR: Model fitting failed: {model_result.get('error')}")
            return jsonify(
                model_result
            ), 400

        print("Model fitted successfully")


        # =================================================
        # DIAGNOSTICS
        # =================================================

        print("Running diagnostics...")
        diagnostics = (
            _run_regression_diagnostics_for_app(
                model_type=model_type,
                model_result=model_result,
                regression_df=regression_df,
                independent_variables=independent_variables,
                prepared=prepared
            )
        )


        # =================================================
        # REQUEST METADATA
        # =================================================

        metadata = {

            "filters": {

                "district":
                    district,

                "block":
                    block,

                "sample_type":
                    sample_type,

                "organisms":
                    organisms

            },

            "dependent_variable":
                dependent_variable,

            "independent_variables":
                independent_variables,

            "antibiotic":
                antibiotic,

            "automatically_selected_model":
                model_type

        }


        # =================================================
        # FINALIZE RESPONSE
        # =================================================

        print("Finalizing response...")
        final_result = (
            finalize_regression_response(

                model_type=model_type,

                model_result=model_result,

                diagnostics=diagnostics,

                metadata=metadata,

                alpha=0.05

            )
        )


        # =================================================
        # FRONTEND PAYLOAD
        # =================================================

        frontend_payload = (
            build_frontend_payload(
                final_result
            )
        )

        print("=" * 60)
        print("REGRESSION COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")

        return jsonify(
            frontend_payload
        ), 200


    except Exception as exc:

        import traceback
        traceback.print_exc()

        print(f"EXCEPTION: {exc}")

        return jsonify({

            "success": False,

            "error":
                "Regression analysis failed.",

            "details":
                str(exc)

        }), 500


# =====================================================
# REGRESSION DIAGNOSTICS DISPATCHER
# =====================================================

def _run_regression_diagnostics_for_app(
    model_type,
    model_result,
    regression_df,
    independent_variables,
    prepared=None
):

    diagnostics = {}


    # =================================================
    # DESIGN MATRIX / VIF
    # =================================================

    X = None
    reference_categories = None


    try:

        from services.regression_helpers import (
            build_design_matrix
        )


        # build_design_matrix returns (X, reference_categories)
        X, reference_categories = build_design_matrix(

            regression_df,

            independent_variables

        )


    except Exception as exc:

        X = None


    # =================================================
    # BASIC DIAGNOSTICS
    # =================================================

    if X is not None:

        try:

            vif_result = calculate_vif_diagnostics(
                X
            )

            # Extract the actual VIF list if success
            if vif_result.get("success", False):
                diagnostics["vif"] = vif_result.get("vif", [])
            else:
                diagnostics["vif"] = []

        except Exception as exc:

            diagnostics["vif"] = []


        try:

            diagnostics[
                "condition_number"
            ] = calculate_condition_number(
                X
            )

        except Exception as exc:

            diagnostics[
                "condition_number"
            ] = None


    # =================================================
    # CONVERGENCE
    # =================================================

    # The model modules return the convergence status,
    # so use that when available.

    diagnostics[
        "convergence"
    ] = {

        "success": True,

        "converged":
            bool(
                model_result.get(
                    "converged",
                    False
                )
            )

    }


    # =================================================
    # SAMPLE INFORMATION
    # =================================================

    diagnostics["sample_information"] = {

        "n": model_result.get("n"),
        "number_predictors": model_result.get("number_predictors"),
        "number_parameters": model_result.get("number_parameters")

    }


    # =================================================
    # BINARY LOGISTIC
    # =================================================

    if model_type == "binary_logistic":

        y_true = None
        predicted_probability = None


        # ---------------------------------------------
        # Get observed outcome
        # ---------------------------------------------

        if (
            regression_df is not None
            and
            "culture_result" in regression_df.columns
        ):

            try:

                outcome = (

                    regression_df[
                        "culture_result"
                    ]

                    .astype(str)

                    .str.strip()

                    .str.lower()

                )


                # Expected binary coding:
                #
                # negative -> 0
                # positive -> 1

                y_true = (
                    outcome == "positive"
                ).astype(int).values

            except Exception:

                y_true = None


        # ---------------------------------------------
        # Try to obtain predictions from model_result
        # ---------------------------------------------

        try:

            # The binary logistic module doesn't return predictions yet
            # We can compute them if we have the design matrix and coefficients
            if X is not None and "coefficients" in model_result:

                import numpy as np

                # Build coefficient vector
                coef_dict = {}
                for coef in model_result.get("coefficients", []):
                    coef_dict[coef.get("variable")] = coef.get("coefficient")

                # Get intercept
                intercept = coef_dict.get("Intercept", 0.0)

                # Get predictor coefficients
                X_coefs = []
                for col in X.columns:
                    if col == "const":
                        continue
                    X_coefs.append(coef_dict.get(col, 0.0))

                # Compute linear predictor
                X_matrix = X.drop(columns=["const"], errors="ignore").values
                linear_predictor = intercept + np.dot(X_matrix, X_coefs)

                # Compute predicted probabilities
                predicted_probability = 1 / (1 + np.exp(-linear_predictor))
                predicted_probability = np.clip(predicted_probability, 0, 1)

        except Exception as exc:

            predicted_probability = None


        # ---------------------------------------------
        # Classification diagnostics
        # ---------------------------------------------

        if (
            y_true is not None
            and
            predicted_probability is not None
            and
            len(y_true) > 0
            and
            len(predicted_probability) > 0
        ):

            try:

                diagnostics[
                    "classification"
                ] = (
                    binary_classification_diagnostics(

                        y_true,

                        predicted_probability,

                        threshold=0.50

                    )
                )

            except Exception as exc:

                diagnostics[
                    "classification"
                ] = {

                    "success": False,

                    "error":
                        str(exc)

                }


            # -----------------------------------------
            # Hosmer-Lemeshow
            # -----------------------------------------

            try:

                diagnostics[
                    "hosmer_lemeshow"
                ] = (
                    hosmer_lemeshow_test(

                        y_true,

                        predicted_probability

                    )
                )

            except Exception as exc:

                diagnostics[
                    "hosmer_lemeshow"
                ] = {

                    "success": False,

                    "error":
                        str(exc)

                }


            # -----------------------------------------
            # Residuals
            # -----------------------------------------

            try:

                residual_result = (
                    binary_logistic_residuals(

                        y_true,

                        predicted_probability

                    )
                )


                diagnostics[
                    "residuals"
                ] = residual_result


                if residual_result.get(
                    "success",
                    False
                ):

                    diagnostics[
                        "residual_summary"
                    ] = summarize_residuals(

                        residual_result.get(
                            "deviance_residuals",
                            []
                        )

                    )

            except Exception as exc:

                diagnostics[
                    "residuals"
                ] = {

                    "success": False,

                    "error":
                        str(exc)

                }


            # -----------------------------------------
            # Linearity in logit
            # -----------------------------------------

            continuous_variables = []


            for variable in independent_variables:

                if variable not in regression_df.columns:

                    continue


                if pd.api.types.is_numeric_dtype(
                    regression_df[variable]
                ):

                    continuous_variables.append(
                        variable
                    )


            if continuous_variables:

                try:

                    diagnostics[
                        "linearity_in_logit"
                    ] = check_linearity_in_logit(

                        regression_df,

                        continuous_variables,

                        "culture_result",

                        predicted_probability

                    )

                except Exception as exc:

                    diagnostics[
                        "linearity_in_logit"
                    ] = {

                        "success": False,

                        "error":
                            str(exc)

                    }


        # ---------------------------------------------
        # Model-level diagnostics
        # ---------------------------------------------

        diagnostics[
            "model_diagnostics"
        ] = {

            "aic":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "aic"
                ),

            "bic":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "bic"
                ),

            "log_likelihood":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "log_likelihood"
                ),

            "mcfadden_pseudo_r_squared":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "mcfadden_pseudo_r_squared"
                )

        }


    # =================================================
    # MULTINOMIAL LOGISTIC
    # =================================================

    elif model_type == "multinomial_logistic":

        probabilities = None
        y_true = None


        # ---------------------------------------------
        # Get observed outcome
        # ---------------------------------------------

        if (
            regression_df is not None
            and
            "organism_identification" in regression_df.columns
        ):

            try:

                categories = sorted(

                    regression_df[
                        "organism_identification"
                    ]

                    .dropna()

                    .astype(str)

                    .str.strip()

                    .str.lower()

                    .unique()

                    .tolist()

                )


                mapping = {

                    category:
                        index

                    for index, category
                    in enumerate(categories)

                }


                y_true = (

                    regression_df[
                        "organism_identification"
                    ]

                    .astype(str)

                    .str.strip()

                    .str.lower()

                    .map(mapping)

                    .values

                )

            except Exception:

                y_true = None


        # ---------------------------------------------
        # Try to compute probabilities from coefficients
        # ---------------------------------------------

        try:

            if X is not None and "coefficients" in model_result:

                # Get outcome categories
                outcome_categories = model_result.get("outcome_categories", [])
                n_categories = len(outcome_categories)

                if n_categories > 1:

                    # Build coefficient matrix
                    coef_matrix = {}
                    for coef in model_result.get("coefficients", []):
                        outcome = coef.get("outcome_category")
                        variable = coef.get("variable")
                        value = coef.get("coefficient")
                        if outcome and variable:
                            if outcome not in coef_matrix:
                                coef_matrix[outcome] = {}
                            coef_matrix[outcome][variable] = value

                    # Prepare design matrix without intercept
                    X_matrix = X.drop(columns=["const"], errors="ignore").values

                    # Compute linear predictors for each category
                    # Reference category is 0
                    n_obs = len(X_matrix)
                    linear_pred = np.zeros((n_obs, n_categories))

                    # Reference category (index 0) has linear predictor = 0
                    for i, outcome in enumerate(outcome_categories[1:], 1):
                        if outcome in coef_matrix:
                            coefs = coef_matrix[outcome]
                            intercept = coefs.get("Intercept", 0.0)
                            # Get coefficients for each predictor
                            pred_coefs = []
                            for col in X.columns:
                                if col == "const":
                                    continue
                                pred_coefs.append(coefs.get(col, 0.0))
                            # Compute linear predictor
                            if len(pred_coefs) > 0 and len(X_matrix) > 0:
                                linear_pred[:, i] = intercept + np.dot(X_matrix, pred_coefs)

                    # Compute probabilities using softmax
                    exp_vals = np.exp(linear_pred)
                    row_sums = np.sum(exp_vals, axis=1, keepdims=True)
                    probabilities = exp_vals / row_sums

        except Exception as exc:

            probabilities = None


        if (
            y_true is not None
            and
            probabilities is not None
            and
            len(y_true) > 0
        ):

            try:

                diagnostics[
                    "classification"
                ] = (
                    multinomial_classification_diagnostics(

                        y_true,

                        probabilities,

                        class_labels=model_result.get(
                            "outcome_categories"
                        )

                    )
                )

            except Exception as exc:

                diagnostics[
                    "classification"
                ] = {

                    "success": False,

                    "error":
                        str(exc)

                }


        # ---------------------------------------------
        # Model diagnostics
        # ---------------------------------------------

        diagnostics[
            "model_diagnostics"
        ] = {

            "aic":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "aic"
                ),

            "bic":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "bic"
                ),

            "log_likelihood":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "log_likelihood"
                ),

            "mcfadden_pseudo_r_squared":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "mcfadden_pseudo_r_squared"
                )

        }


    # =================================================
    # ORDINAL LOGISTIC
    # =================================================

    elif model_type == "ordinal_logistic":

        # ---------------------------------------------
        # Model diagnostics
        # ---------------------------------------------

        diagnostics[
            "model_diagnostics"
        ] = {

            "aic":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "aic"
                ),

            "bic":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "bic"
                ),

            "log_likelihood":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "log_likelihood"
                ),

            "mcfadden_pseudo_r_squared":
                model_result.get(
                    "statistics",
                    {}
                ).get(
                    "mcfadden_pseudo_r_squared"
                )

        }


        # ---------------------------------------------
        # Proportional odds
        # ---------------------------------------------

        try:

            # Get outcome column
            outcome_column = "antibiogram_susceptibility"
            if "dependent_variable" in model_result:
                if model_result["dependent_variable"] == "age_group":
                    outcome_column = "age_group"

            ordered_categories = (

                model_result.get(
                    "category_order"
                )

            )


            if not ordered_categories:

                ordered_categories = [

                    "resistant",

                    "intermediate",

                    "susceptible"

                ]


            diagnostics[
                "proportional_odds"
            ] = proportional_odds_diagnostic(

                regression_df,

                outcome_column,

                independent_variables,

                ordered_categories

            )

        except Exception as exc:

            diagnostics[
                "proportional_odds"
            ] = {

                "success": False,

                "error":
                    str(exc)

            }


    return diagnostics


# =====================================================
# REGRESSION DATA PREVIEW
# =====================================================

@app.route(
    "/regression-preview",
    methods=["POST"]
)
def regression_preview():

    try:

        data = request.get_json(
            silent=True
        )


        if not isinstance(
            data,
            dict
        ):

            return jsonify({

                "success": False,

                "error":
                    "Request body must be a JSON object."

            }), 400


        district = data.get(
            "district",
            "all"
        )

        block = data.get(
            "block",
            "all"
        )

        sample_type = data.get(
            "sample_type",
            "all"
        )

        organisms = data.get(
            "organisms",
            []
        )


        dependent_variable = data.get(
            "dependent_variable"
        )

        independent_variables = data.get(
            "independent_variables",
            []
        )

        antibiotic = data.get(
            "antibiotic"
        )


        if not dependent_variable:

            return jsonify({

                "success": False,

                "error":
                    "Dependent variable is required."

            }), 400


        if not independent_variables:

            return jsonify({

                "success": False,

                "error":
                    "At least one independent variable "
                    "is required."

            }), 400


        # =================================================
        # LOAD DATA
        # =================================================

        df = load_analysis_dataframe()


        if df is None or df.empty:

            return jsonify({

                "success": False,

                "error":
                    "No analysis data are available."

            }), 404


        # =================================================
        # APPLY FILTERS
        # =================================================

        filtered_df = apply_filters(

            df,

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms

        )


        if filtered_df.empty:

            return jsonify({

                "success": False,

                "error":
                    "No records remain after applying filters."

            }), 404


        # =================================================
        # DETERMINE MODEL
        # =================================================

        model_information = (
            determine_regression_model(
                dependent_variable
            )
        )


        if not model_information.get(
            "success",
            False
        ):

            return jsonify(
                model_information
            ), 400


        # =================================================
        # PREPARE
        # =================================================

        prepared = prepare_regression_data(

            filtered_df,

            dependent_variable,

            independent_variables,

            antibiotic

        )


        if not prepared.get(
            "success",
            False
        ):

            return jsonify(
                prepared
            ), 400


        # =================================================
        # REMOVE DATAFRAME FROM JSON
        # =================================================

        response = dict(
            prepared
        )


        response.pop(
            "data",
            None
        )


        response[
            "model"
        ] = model_information[
            "model"
        ]


        response[
            "dependent_variable"
        ] = dependent_variable


        response[
            "independent_variables"
        ] = independent_variables


        return jsonify(
            response
        ), 200


    except Exception as exc:

        return jsonify({

            "success": False,

            "error":
                "Unable to prepare regression preview.",

            "details":
                str(exc)

        }), 500


# =====================================================
# RUN APP
# =====================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )