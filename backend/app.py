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
app.json.sort_keys = False      # Flask 2.2+
# older Flask:  app.config["JSON_SORT_KEYS"] = False
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
# GET QUERY MONTH (YYYY-MM)
# =====================================================

def get_query_month(name):
    """
    Reads a single "YYYY-MM" query parameter.

    Example:  ?from_month=2025-01

    Returns the string, or None if missing/empty.
    Raises ValueError if the format is wrong.
    """

    value = request.args.get(name, "").strip()

    if not value:
        return None

    # validates the format; raises ValueError if invalid
    pd.to_datetime(value, format="%Y-%m")

    return value

# =====================================================
# GET BODY MONTH (YYYY-MM) FROM JSON
# =====================================================

def get_body_month(data, name):
    """
    Reads a single "YYYY-MM" value from a JSON body (dict).

    Example body:  {"from_month": "2025-01"}

    Returns the string, or None if missing/empty.
    Raises ValueError if the format is wrong.
    """

    value = data.get(name)

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # validates the format; raises ValueError if invalid
    pd.to_datetime(value, format="%Y-%m")

    return value


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

        from_month=get_query_month("from_month")

        to_month = get_query_month("to_month")


        result = get_antibiogram_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            from_month=from_month,

            to_month=to_month

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

        from_month = get_query_month(
            "from_month"
        )

        to_month = get_query_month(
            "to_month"
        )


        result = get_antibiogram(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            antibiotics=antibiotics,

            from_month=from_month,

            to_month=to_month

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
        # READ SELECTED ORGANISMS   (NEW)
        #
        # Empty list = "All organisms".
        # "all" entries are ignored by the service.
        # =================================================

        selected_organisms = request.args.getlist("organisms")

        # =================================================
        # READ MONTH-YEAR RANGE
        # =================================================

        from_month = get_query_month("from_month")
        to_month = get_query_month("to_month")

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

            sample_type=sample_types,

            organisms=selected_organisms,

            from_month=from_month,

            to_month=to_month

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

        from_month = get_query_month(
            "from_month"
        )

        to_month = get_query_month(
            "to_month"
        )

        result = get_association_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            from_month=from_month,

            to_month=to_month

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

        raw_age_groups = data.get("age_groups")
        age_groups = (
            raw_age_groups
            if isinstance(raw_age_groups, list) and len(raw_age_groups) > 0
            else None
        )

        from_month = get_body_month(
            data,
            "from_month"
        )

        to_month = get_body_month(
            data,
            "to_month"
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

            antibiotics=antibiotics,

            age_groups=age_groups,

            from_month=from_month,

            to_month=to_month

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
# REGRESSION ROUTES  -  DROP-IN REPLACEMENT
# =====================================================
#
# HOW TO USE
# ----------
# In app.py, delete everything from the
# "REGRESSION OPTIONS" banner down to the end of the
# /regression-preview route, and paste this whole file
# in its place.
#
# This block expects these names to already exist in
# app.py (they do in your current code):
#
#   app, request, jsonify, json
#   get_query_month, get_body_month
#   load_analysis_dataframe, apply_filters
#   get_regression_options
#   determine_regression_model, prepare_regression_data
#   run_binary_logistic_regression
#   run_multinomial_logistic_regression
#   run_ordinal_logistic_regression
#   finalize_regression_response, build_frontend_payload
#   calculate_vif_diagnostics, calculate_condition_number
#   binary_classification_diagnostics, hosmer_lemeshow_test
#   binary_logistic_residuals, summarize_residuals
#   check_linearity_in_logit
#   multinomial_classification_diagnostics
#   proportional_odds_diagnostic
#
# WHAT CHANGED vs. YOUR ORIGINAL ROUTES
# -------------------------------------
# 1. Antibiotic parsing accepts "antibiotics" (list) and
#    the legacy "antibiotic" (string); "all" is dropped.
# 2. antibiogram_susceptibility:
#      0 antibiotics -> 400
#      1 antibiotic  -> single result (same shape as before,
#                       plus antibiogram_mode = "single")
#      2+            -> one ordinal model per antibiotic
# 3. ONE shared helper (_fit_single_regression) does
#    prepare -> fit -> diagnostics -> finalize, and is used
#    by BOTH the single path and the per-antibiotic loop.
# 4. The model for an antibiotic comes from its own
#    prepared data. Antibiotics with only two observed
#    susceptibility categories cannot be fitted (binary
#    logistic is hard-wired to culture_result), so they get
#    a clear error instead of a confusing one.
# 5. Each antibiotic is isolated: a failure becomes an
#    error entry and the loop continues.
# 6. Failure details never contain DataFrames (which would
#    break jsonify).
# 7. numpy / pandas are imported inside the diagnostics
#    function, so it no longer depends on module imports.
# 8. /regression-preview also accepts "antibiotics"
#    (uses the first one).
#
# Everything else is unchanged.
# =====================================================


ANTIBIOGRAM_OUTCOME = "antibiogram_susceptibility"


# =====================================================
# SMALL HELPERS
# =====================================================

def _parse_antibiotics(data):
    """
    Returns a de-duplicated list of non-empty antibiotic
    names from the request body.

    Accepts:
        "antibiotics": ["amikacin", "meropenem"]   (new)
        "antibiotic":  "amikacin"                  (legacy)

    "all" is dropped. First occurrence order is kept.
    """

    payload = data.get("antibiotics")

    if payload is None:

        legacy = data.get("antibiotic")

        payload = [] if legacy is None else [legacy]

    if isinstance(payload, str):

        payload = [payload]

    elif not isinstance(payload, (list, tuple)):

        payload = []

    cleaned = []

    seen = set()

    for item in payload:

        if item is None:

            continue

        name = str(item).strip()

        if not name or name.lower() == "all":

            continue

        key = name.lower()

        if key in seen:

            continue

        seen.add(key)

        cleaned.append(name)

    return cleaned


def _strip_dataframes(result):
    """
    Returns a shallow copy of a result dict without the
    regression DataFrame (and any other pandas object) so
    it can be safely passed to jsonify().
    """

    import pandas as pd

    if not isinstance(result, dict):

        return result

    return {

        key: value

        for key, value in result.items()

        if key != "data"
        and not isinstance(value, (pd.DataFrame, pd.Series))

    }


def _model_statistics_summary(model_result):
    """
    Model-level fit statistics used by every diagnostics
    branch.
    """

    statistics = model_result.get("statistics", {}) or {}

    return {

        "aic":
            statistics.get("aic"),

        "bic":
            statistics.get("bic"),

        "log_likelihood":
            statistics.get("log_likelihood"),

        "mcfadden_pseudo_r_squared":
            statistics.get("mcfadden_pseudo_r_squared")

    }


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

        from_month = get_query_month(
            "from_month"
        )

        to_month = get_query_month(
            "to_month"
        )

        options = get_regression_options(

            district=district,

            block=block,

            sample_type=sample_type,

            organisms=organisms,

            from_month=from_month,

            to_month=to_month

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

                "error":
                    "Request body must be a JSON object."

            }), 400

        dependent_variable = data.get(
            "dependent_variable"
        )

        # Observed categories, if provided
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

        from_month = get_body_month(
            data,
            "from_month"
        )

        to_month = get_body_month(
            data,
            "to_month"
        )

        print(
            f"Filters: district={district}, block={block}, "
            f"sample_type={sample_type}, organisms={organisms}, "
            f"from_month={from_month}, to_month={to_month}"
        )

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

        print(
            f"Variables: dependent={dependent_variable}, "
            f"independent={independent_variables}"
        )

        # =================================================
        # ANTIBIOTICS
        #
        # Accepts "antibiotics" (list) and the legacy
        # "antibiotic" (string). "all" is dropped.
        # =================================================

        antibiotics = _parse_antibiotics(
            data
        )

        print(f"Antibiotics: {antibiotics}")

        # =================================================
        # CUSTOM AGE GROUPS
        # =================================================

        age_groups = data.get(
            "age_groups"
        )

        if not isinstance(age_groups, list):

            age_groups = None

        print(f"Age groups: {age_groups}")

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

        is_antibiogram = (
            dependent_variable == ANTIBIOGRAM_OUTCOME
        )

        if is_antibiogram and len(antibiotics) == 0:

            print("ERROR: Antibiogram outcome requires antibiotics")

            return jsonify({

                "success": False,

                "error":
                    "At least one antibiotic must be selected "
                    "for antibiogram regression."

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

            organisms=organisms,

            from_month=from_month,

            to_month=to_month

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

        filters_metadata = {

            "district":
                district,

            "block":
                block,

            "sample_type":
                sample_type,

            "organisms":
                organisms,

            "from_month":
                from_month,

            "to_month":
                to_month

        }

        # =================================================
        # MULTI-ANTIBIOTIC BRANCH
        #
        # antibiogram_susceptibility AND two or more
        # antibiotics -> one separate model per antibiotic.
        # No pooled model is produced.
        # =================================================

        if is_antibiogram and len(antibiotics) > 1:

            return _run_per_antibiotic_regressions(

                filtered_df=filtered_df,

                dependent_variable=dependent_variable,

                independent_variables=independent_variables,

                antibiotics=antibiotics,

                ordered_categories=ordered_categories,

                age_groups=age_groups,

                filters_metadata=filters_metadata

            )

        # =================================================
        # SINGLE-MODEL PATH
        #
        # Includes:
        #   - single-antibiotic antibiogram regression
        #   - culture_result
        #   - organism_identification
        # =================================================

        single_antibiotic = (
            antibiotics[0] if is_antibiogram else None
        )

        payload, status = _fit_single_regression(

            filtered_df=filtered_df,

            dependent_variable=dependent_variable,

            independent_variables=independent_variables,

            antibiotic=single_antibiotic,

            ordered_categories=ordered_categories,

            age_groups=age_groups,

            filters_metadata=filters_metadata

        )

        if status == 200 and is_antibiogram:

            payload["antibiogram_mode"] = "single"

            payload["selected_antibiotics"] = [
                single_antibiotic
            ]

        if status == 200:

            print("=" * 60)
            print("REGRESSION COMPLETED SUCCESSFULLY")
            print("=" * 60 + "\n")

        return jsonify(
            payload
        ), status

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
# FIT ONE REGRESSION  (shared by single + multi paths)
# =====================================================

def _fit_single_regression(
    filtered_df,
    dependent_variable,
    independent_variables,
    antibiotic,
    ordered_categories,
    age_groups,
    filters_metadata
):
    """
    Runs the complete pipeline for ONE regression:

        determine model -> prepare data -> fit
        -> diagnostics -> finalize -> frontend payload

    Returns
    -------
    (payload_dict, http_status)

    On success the payload is the normal frontend payload
    and the status is 200. On failure the payload contains
    "success": False and an "error" message.

    This function never returns DataFrames in the payload.
    """

    is_antibiogram = (
        dependent_variable == ANTIBIOGRAM_OUTCOME
    )

    # -------------------------------------------------
    # Default model for this outcome
    # -------------------------------------------------

    model_information = determine_regression_model(
        dependent_variable
    )

    if not model_information.get("success", False):

        print(f"ERROR: Model selection failed: {model_information}")

        return _strip_dataframes(
            model_information
        ), 400

    model_type = model_information["model"]

    print(f"Default model for outcome: {model_type}")

    # -------------------------------------------------
    # Prepare data
    #
    # age_groups is forwarded so custom age bins are
    # applied before complete-case analysis and
    # category detection.
    # -------------------------------------------------

    print("Preparing regression data...")

    prepared = prepare_regression_data(

        filtered_df,

        dependent_variable=
            dependent_variable,

        independent_variables=
            independent_variables,

        antibiotic=
            antibiotic,

        age_groups=
            age_groups

    )

    if not prepared.get("success", False):

        print(f"ERROR: Data preparation failed: {prepared.get('error')}")

        return {

            "success": False,

            "model":
                model_type,

            "error":
                prepared.get(
                    "error",
                    "Unable to prepare regression data."
                ),

            "details":
                _strip_dataframes(prepared)

        }, 400

    regression_df = prepared.get("data")

    if regression_df is None:

        print("ERROR: Regression dataframe is None")

        return {

            "success": False,

            "model":
                model_type,

            "error":
                "Regression-ready dataframe is missing."

        }, 400

    print(f"Regression data prepared: {len(regression_df)} rows")

    # -------------------------------------------------
    # ANTIBIOGRAM: model comes from THIS antibiotic's
    # observed categories.
    #
    #   3 categories -> ordinal logistic  (supported)
    #   2 categories -> binary logistic   (NOT supported
    #                   for antibiogram: the binary module
    #                   is hard-wired to culture_result)
    #
    # A clear error is returned in the second case.
    # -------------------------------------------------

    if is_antibiogram:

        selection = prepared.get("model_selection") or {}

        prepared_model = (
            prepared.get("model")
            or selection.get("model")
        )

        if prepared_model:

            model_type = prepared_model

        print(f"Model for antibiotic '{antibiotic}': {model_type}")

        if model_type != "ordinal_logistic":

            categories = (
                selection.get("observed_categories")
                or prepared.get("outcome_categories")
                or []
            )

            observed_text = (
                ", ".join(str(c) for c in categories)
                if categories else "unknown"
            )

            message = (
                f"Only {len(categories)} susceptibility "
                f"categor{'y' if len(categories) == 1 else 'ies'} "
                f"observed for '{antibiotic}' ({observed_text}) "
                "after filtering and complete-case analysis. "
                "Ordinal logistic regression needs all three: "
                "resistant, intermediate and susceptible."
            )

            print(f"ERROR: {message}")

            return {

                "success": False,

                "model":
                    model_type,

                "antibiotic":
                    antibiotic,

                "error":
                    message,

                "details": {

                    "observed_categories":
                        list(categories),

                    "final_n":
                        prepared.get("final_n")

                }

            }, 400

    # -------------------------------------------------
    # Fit model
    #
    # All model modules receive the PREPARED dataframe so
    # custom age bins survive into model fitting.
    # -------------------------------------------------

    print("Fitting model...")

    if model_type == "binary_logistic":

        model_result = run_binary_logistic_regression(

            regression_df,

            independent_variables,

            prepared_data=prepared

        )

    elif model_type == "multinomial_logistic":

        model_result = run_multinomial_logistic_regression(

            regression_df,

            independent_variables,

            prepared_data=prepared

        )

    elif model_type == "ordinal_logistic":

        model_result = run_ordinal_logistic_regression(

            regression_df,

            independent_variables,

            ordered_categories=ordered_categories,

            ordinal_outcome_column=dependent_variable,

            prepared_data=prepared

        )

    else:

        print(f"ERROR: Unsupported model type: {model_type}")

        return {

            "success": False,

            "error":
                f"Unsupported regression model '{model_type}'."

        }, 400

    if not model_result.get("success", False):

        print(f"ERROR: Model fitting failed: {model_result.get('error')}")

        failure = _strip_dataframes(model_result)

        failure["success"] = False

        failure.setdefault(
            "error",
            "Model fitting failed."
        )

        return failure, 400

    print("Model fitted successfully")

    # -------------------------------------------------
    # Diagnostics
    # -------------------------------------------------

    print("Running diagnostics...")

    diagnostics = _run_regression_diagnostics_for_app(

        model_type=model_type,

        model_result=model_result,

        regression_df=regression_df,

        independent_variables=independent_variables,

        prepared=prepared

    )

    # -------------------------------------------------
    # Metadata
    # -------------------------------------------------

    metadata = {

        "filters":
            filters_metadata,

        "dependent_variable":
            dependent_variable,

        "independent_variables":
            independent_variables,

        "antibiotic":
            antibiotic,

        "age_groups":
            age_groups,

        "automatically_selected_model":
            model_type

    }

    # -------------------------------------------------
    # Finalize + frontend payload
    # -------------------------------------------------

    print("Finalizing response...")

    final_result = finalize_regression_response(

        model_type=model_type,

        model_result=model_result,

        diagnostics=diagnostics,

        metadata=metadata,

        alpha=0.05

    )

    frontend_payload = build_frontend_payload(
        final_result
    )

    return frontend_payload, 200


# =====================================================
# PER-ANTIBIOTIC REGRESSIONS
# =====================================================

def _run_per_antibiotic_regressions(
    filtered_df,
    dependent_variable,
    independent_variables,
    antibiotics,
    ordered_categories,
    age_groups,
    filters_metadata
):
    """
    Runs one ordinal logistic regression per selected
    antibiotic and returns a Flask response shaped like:

        {
          "success": True,
          "antibiogram_mode": "multi",
          "dependent_variable": "antibiogram_susceptibility",
          "selected_antibiotics": [...],
          "independent_variables": [...],
          "model": "ordinal_logistic",
          "antibiotics": {
             "amikacin":  { ...frontend payload... },
             "meropenem": { "success": False, "error": "..." },
             ...
          },
          "total_models_attempted": N,
          "total_models_succeeded": M
        }

    Each antibiotic is prepared independently, so its
    analysis subset contains only rows with a susceptibility
    result for that antibiotic (N differs between
    antibiotics).

    A failure for one antibiotic is recorded and the loop
    continues with the next one.
    """

    per_antibiotic = {}

    succeeded = 0

    total = len(antibiotics)

    for index, antibiotic in enumerate(antibiotics, 1):

        print(f"--- Antibiotic {index}/{total}: {antibiotic} ---")

        try:

            payload, status = _fit_single_regression(

                filtered_df=filtered_df,

                dependent_variable=dependent_variable,

                independent_variables=independent_variables,

                antibiotic=antibiotic,

                ordered_categories=ordered_categories,

                age_groups=age_groups,

                filters_metadata=filters_metadata

            )

        except Exception as exc:

            import traceback
            traceback.print_exc()

            payload = {

                "success": False,

                "error":
                    f"Unexpected error while fitting "
                    f"'{antibiotic}': {str(exc)}"

            }

            status = 500

        if status == 200 and payload.get("success", True) is not False:

            # Tell the frontend which antibiotic this is
            payload["antibiotic"] = antibiotic

            per_antibiotic[antibiotic] = payload

            succeeded += 1

        else:

            print(
                f"Antibiotic {index}/{total} failed: "
                f"{payload.get('error')}"
            )

            entry = dict(payload)

            entry["success"] = False

            entry["antibiotic"] = antibiotic

            entry.setdefault(
                "error",
                f"Unable to fit a model for '{antibiotic}'."
            )

            per_antibiotic[antibiotic] = entry

    # =================================================
    # NOTHING COULD BE FITTED
    # =================================================

    if succeeded == 0:

        reasons = "; ".join(

            f"{name}: {entry.get('error', 'failed')}"

            for name, entry in per_antibiotic.items()

        )

        return jsonify({

            "success": False,

            "antibiogram_mode": "multi",

            "dependent_variable":
                dependent_variable,

            "selected_antibiotics":
                antibiotics,

            "independent_variables":
                independent_variables,

            "error":
                "None of the selected antibiotics could be "
                "modelled with the current data and "
                "predictors. " + reasons,

            "antibiotics":
                per_antibiotic

        }), 400

    # =================================================
    # AT LEAST ONE MODEL FITTED
    # =================================================

    return jsonify({

        "success": True,

        "antibiogram_mode": "multi",

        "dependent_variable":
            dependent_variable,

        "selected_antibiotics":
            antibiotics,

        "independent_variables":
            independent_variables,

        "model":
            "ordinal_logistic",

        "antibiotics":
            per_antibiotic,

        "total_models_attempted":
            total,

        "total_models_succeeded":
            succeeded

    }), 200


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

    import numpy as np
    import pandas as pd

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

    except Exception:

        X = None

    # =================================================
    # BASIC DIAGNOSTICS
    # =================================================

    if X is not None:

        try:

            vif_result = calculate_vif_diagnostics(
                X
            )

            if vif_result.get("success", False):

                diagnostics["vif"] = vif_result.get("vif", [])

            else:

                diagnostics["vif"] = []

        except Exception:

            diagnostics["vif"] = []

        try:

            diagnostics[
                "condition_number"
            ] = calculate_condition_number(
                X
            )

        except Exception:

            diagnostics[
                "condition_number"
            ] = None

    # =================================================
    # CONVERGENCE
    # =================================================

    diagnostics["convergence"] = {

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

        "n":
            model_result.get("n"),

        "number_predictors":
            model_result.get("number_predictors"),

        "number_parameters":
            model_result.get("number_parameters")

    }

    # =================================================
    # BINARY LOGISTIC
    # =================================================

    if model_type == "binary_logistic":

        y_true = None
        predicted_probability = None

        # ---------------------------------------------
        # Observed outcome (culture_result:
        # negative -> 0, positive -> 1)
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

                y_true = (
                    outcome == "positive"
                ).astype(int).values

            except Exception:

                y_true = None

        # ---------------------------------------------
        # Predicted probabilities from the coefficients
        # ---------------------------------------------

        try:

            if X is not None and "coefficients" in model_result:

                coef_dict = {}

                for coef in model_result.get("coefficients", []):

                    coef_dict[
                        coef.get("variable")
                    ] = coef.get("coefficient")

                intercept = coef_dict.get("Intercept", 0.0)

                X_coefs = []

                for col in X.columns:

                    if col == "const":

                        continue

                    X_coefs.append(
                        coef_dict.get(col, 0.0)
                    )

                X_matrix = X.drop(
                    columns=["const"],
                    errors="ignore"
                ).values

                linear_predictor = (
                    intercept + np.dot(X_matrix, X_coefs)
                )

                predicted_probability = (
                    1 / (1 + np.exp(-linear_predictor))
                )

                predicted_probability = np.clip(
                    predicted_probability,
                    0,
                    1
                )

        except Exception:

            predicted_probability = None

        # ---------------------------------------------
        # Classification-type diagnostics
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
                ] = binary_classification_diagnostics(

                    y_true,

                    predicted_probability,

                    threshold=0.50

                )

            except Exception as exc:

                diagnostics["classification"] = {

                    "success": False,

                    "error":
                        str(exc)

                }

            try:

                diagnostics[
                    "hosmer_lemeshow"
                ] = hosmer_lemeshow_test(

                    y_true,

                    predicted_probability

                )

            except Exception as exc:

                diagnostics["hosmer_lemeshow"] = {

                    "success": False,

                    "error":
                        str(exc)

                }

            try:

                residual_result = binary_logistic_residuals(

                    y_true,

                    predicted_probability

                )

                diagnostics["residuals"] = residual_result

                if residual_result.get("success", False):

                    diagnostics[
                        "residual_summary"
                    ] = summarize_residuals(

                        residual_result.get(
                            "deviance_residuals",
                            []
                        )

                    )

            except Exception as exc:

                diagnostics["residuals"] = {

                    "success": False,

                    "error":
                        str(exc)

                }

            # -----------------------------------------
            # Linearity in the logit
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

                    diagnostics["linearity_in_logit"] = {

                        "success": False,

                        "error":
                            str(exc)

                    }

        diagnostics[
            "model_diagnostics"
        ] = _model_statistics_summary(
            model_result
        )

    # =================================================
    # MULTINOMIAL LOGISTIC
    # =================================================

    elif model_type == "multinomial_logistic":

        probabilities = None
        y_true = None

        # ---------------------------------------------
        # Observed outcome
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

                    category: index

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
        # Probabilities from the coefficients (softmax)
        # ---------------------------------------------

        try:

            if X is not None and "coefficients" in model_result:

                outcome_categories = model_result.get(
                    "outcome_categories",
                    []
                )

                n_categories = len(outcome_categories)

                if n_categories > 1:

                    coef_matrix = {}

                    for coef in model_result.get("coefficients", []):

                        outcome = coef.get("outcome_category")
                        variable = coef.get("variable")
                        value = coef.get("coefficient")

                        if outcome and variable:

                            if outcome not in coef_matrix:

                                coef_matrix[outcome] = {}

                            coef_matrix[outcome][variable] = value

                    X_matrix = X.drop(
                        columns=["const"],
                        errors="ignore"
                    ).values

                    n_obs = len(X_matrix)

                    linear_pred = np.zeros(
                        (n_obs, n_categories)
                    )

                    # Reference category (index 0) stays 0
                    for i, outcome in enumerate(
                        outcome_categories[1:],
                        1
                    ):

                        if outcome in coef_matrix:

                            coefs = coef_matrix[outcome]

                            intercept = coefs.get("Intercept", 0.0)

                            pred_coefs = []

                            for col in X.columns:

                                if col == "const":

                                    continue

                                pred_coefs.append(
                                    coefs.get(col, 0.0)
                                )

                            if len(pred_coefs) > 0 and len(X_matrix) > 0:

                                linear_pred[:, i] = (
                                    intercept
                                    + np.dot(X_matrix, pred_coefs)
                                )

                    exp_vals = np.exp(linear_pred)

                    row_sums = np.sum(
                        exp_vals,
                        axis=1,
                        keepdims=True
                    )

                    probabilities = exp_vals / row_sums

        except Exception:

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
                ] = multinomial_classification_diagnostics(

                    y_true,

                    probabilities,

                    class_labels=model_result.get(
                        "outcome_categories"
                    )

                )

            except Exception as exc:

                diagnostics["classification"] = {

                    "success": False,

                    "error":
                        str(exc)

                }

        diagnostics[
            "model_diagnostics"
        ] = _model_statistics_summary(
            model_result
        )

    # =================================================
    # ORDINAL LOGISTIC
    # =================================================

    elif model_type == "ordinal_logistic":

        diagnostics[
            "model_diagnostics"
        ] = _model_statistics_summary(
            model_result
        )

        # ---------------------------------------------
        # Proportional odds
        # ---------------------------------------------

        try:

            outcome_column = (
                model_result.get("dependent_variable")
                or ANTIBIOGRAM_OUTCOME
            )

            ordered_categories = model_result.get(
                "category_order"
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

            diagnostics["proportional_odds"] = {

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

        if isinstance(organisms, str):

            organisms = [organisms] if organisms != "all" else []

        # =================================================
        # READ MONTH-YEAR RANGE
        # =================================================

        from_month = get_body_month(
            data,
            "from_month"
        )

        to_month = get_body_month(
            data,
            "to_month"
        )

        dependent_variable = data.get(
            "dependent_variable"
        )

        independent_variables = data.get(
            "independent_variables",
            []
        )

        if isinstance(independent_variables, str):

            independent_variables = [independent_variables]

        # The preview shows ONE dataset, so the first
        # selected antibiotic is used (if any).
        antibiotics = _parse_antibiotics(
            data
        )

        antibiotic = antibiotics[0] if antibiotics else None

        # =================================================
        # CUSTOM AGE GROUPS
        # =================================================

        age_groups = data.get(
            "age_groups"
        )

        if not isinstance(age_groups, list):

            age_groups = None

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

            organisms=organisms,

            from_month=from_month,

            to_month=to_month

        )

        if filtered_df is None or filtered_df.empty:

            return jsonify({

                "success": False,

                "error":
                    "No records remain after applying filters."

            }), 404

        # =================================================
        # DETERMINE MODEL
        # =================================================

        model_information = determine_regression_model(
            dependent_variable
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

            dependent_variable=
                dependent_variable,

            independent_variables=
                independent_variables,

            antibiotic=
                antibiotic,

            age_groups=
                age_groups

        )

        if not prepared.get(
            "success",
            False
        ):

            return jsonify(
                _strip_dataframes(prepared)
            ), 400

        # =================================================
        # REMOVE DATAFRAME FROM JSON
        # =================================================

        response = _strip_dataframes(
            prepared
        )

        # For antibiogram, report the model chosen from the
        # antibiotic's own observed categories.
        response["model"] = (

            prepared.get("model")

            if dependent_variable == ANTIBIOGRAM_OUTCOME
            and prepared.get("model")

            else model_information["model"]

        )

        response["dependent_variable"] = dependent_variable

        response["independent_variables"] = independent_variables

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