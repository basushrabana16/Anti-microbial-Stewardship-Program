# =====================================================
# REGRESSION BACKEND TEST
# =====================================================

import sys
import os
import traceback


print("====================================")
print("REGRESSION TEST FILE IS RUNNING")
print("====================================")


# =====================================================
# BACKEND PATH
# =====================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BACKEND_DIR = os.path.dirname(
    CURRENT_DIR
)

if BACKEND_DIR not in sys.path:
    sys.path.insert(
        0,
        BACKEND_DIR
    )


print("\nBackend path:")
print(BACKEND_DIR)


# =====================================================
# IMPORT DATA LOADER
# =====================================================

print("\n[1] Importing data_loader...")

try:

    from services.data_loader import (
        load_analysis_dataframe
    )

    print(
        "[OK] data_loader imported successfully"
    )

except Exception as exc:

    print(
        "[ERROR] Unable to import data_loader"
    )

    print(type(exc).__name__)
    print(str(exc))

    traceback.print_exc()

    sys.exit(1)


# =====================================================
# IMPORT REGRESSION DATA
# =====================================================

print("\n[2] Importing regression_data...")

try:

    from services.regression_data import (
        prepare_regression_data,
        determine_regression_model
    )

    print(
        "[OK] regression_data imported successfully"
    )

except Exception as exc:

    print(
        "[ERROR] Unable to import regression_data"
    )

    print(type(exc).__name__)
    print(str(exc))

    traceback.print_exc()

    sys.exit(1)


# =====================================================
# IMPORT MODEL FILES
# =====================================================

print("\n[3] Importing regression models...")

try:

    from services.binary_logistic import (
        run_binary_logistic_regression
    )

    print(
        "[OK] binary_logistic imported successfully"
    )

except Exception as exc:

    print(
        "[ERROR] Unable to import binary_logistic"
    )

    print(type(exc).__name__)
    print(str(exc))

    traceback.print_exc()

    sys.exit(1)


try:

    from services.multinomial_logistic import (
        run_multinomial_logistic_regression
    )

    print(
        "[OK] multinomial_logistic imported successfully"
    )

except Exception as exc:

    print(
        "[ERROR] Unable to import multinomial_logistic"
    )

    print(type(exc).__name__)
    print(str(exc))

    traceback.print_exc()

    sys.exit(1)


# =====================================================
# LOAD ACTUAL BACKEND DATA
# =====================================================

print("\n")
print("====================================")
print("LOADING ACTUAL DATABASE DATA")
print("====================================")

try:

    df = load_analysis_dataframe()

except Exception as exc:

    print("\n!!! DATA LOADING ERROR !!!")

    print(type(exc).__name__)
    print(str(exc))

    traceback.print_exc()

    sys.exit(1)


# =====================================================
# BASIC DATA CHECK
# =====================================================

print("\n")
print("====================================")
print("DATA LOADED SUCCESSFULLY")
print("====================================")

print(
    "Rows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)

print(
    "Shape:",
    df.shape
)

print("\nColumns:")

print(
    df.columns.tolist()
)


# =====================================================
# CHECK REQUIRED COLUMNS
# =====================================================

print("\n")
print("====================================")
print("CHECKING REQUIRED REGRESSION COLUMNS")
print("====================================")


required_columns = [

    "culture_result",

    "organism_identification",

    "district",

    "block",

    "sample_type",

    "referred_by"

]


missing_columns = [

    column

    for column in required_columns

    if column not in df.columns

]


if missing_columns:

    print(
        "\n[ERROR] Missing required columns:"
    )

    print(
        missing_columns
    )

    sys.exit(1)


print(
    "[OK] Required columns are present."
)


# =====================================================
# CHECK ANTIBIOTIC METADATA
# =====================================================

print("\n")
print("====================================")
print("CHECKING ANTIBIOTIC METADATA")
print("====================================")


antibiotics = df.attrs.get(
    "antibiotic_columns",
    []
)


print(
    "Number of antibiotics:",
    len(antibiotics)
)


print(
    "First 10 antibiotics:"
)

print(
    list(antibiotics)[:10]
)


# =====================================================
# CHECK CULTURE RESULT
# =====================================================

print("\n")
print("====================================")
print("CULTURE RESULT DISTRIBUTION")
print("====================================")

print(
    df[
        "culture_result"
    ]
    .value_counts(
        dropna=False
    )
)


# =====================================================
# CHECK ORGANISM DISTRIBUTION
# =====================================================

print("\n")
print("====================================")
print("ORGANISM DISTRIBUTION")
print("====================================")


if "organism_identification" in df.columns:

    print(

        df[
            "organism_identification"
        ]
        .value_counts(
            dropna=False
        )
        .head(20)

    )


# =====================================================
# SELECT PREDICTORS
# =====================================================

# These should match the variables in
# regression_metadata.py

INDEPENDENT_VARIABLES = [

    "gender",

    "age_group",

    "district",

    "block",

    "sample_type",

    "referred_by"

]


print("\n")
print("====================================")
print("CHECKING PREDICTORS")
print("====================================")

print(
    "Predictors:"
)

print(
    INDEPENDENT_VARIABLES
)


missing_predictors = [

    variable

    for variable in INDEPENDENT_VARIABLES

    if variable not in df.columns

]


if missing_predictors:

    print(
        "\n[ERROR] Missing predictor columns:"
    )

    print(
        missing_predictors
    )

    sys.exit(1)


print(
    "[OK] All predictors are present."
)


# =====================================================
# TEST MODEL SELECTION
# =====================================================

print("\n")
print("====================================")
print("TESTING AUTOMATIC MODEL SELECTION")
print("====================================")


outcomes = [

    "culture_result",

    "organism_identification",

    "antibiogram_susceptibility"

]


for outcome in outcomes:

    print(
        f"\nOutcome: {outcome}"
    )

    try:

        model_result = (
            determine_regression_model(
                outcome
            )
        )

        print(
            model_result
        )

    except Exception as exc:

        print(
            "[ERROR]"
        )

        print(
            type(exc).__name__,
            str(exc)
        )


# =====================================================
# TEST CULTURE RESULT PREPARATION
# =====================================================

print("\n")
print("====================================")
print("TEST 1: BINARY LOGISTIC DATA")
print("====================================")


try:

    binary_data = prepare_regression_data(

        df,

        dependent_variable="culture_result",

        independent_variables=(
            INDEPENDENT_VARIABLES
        )

    )


    print(
        "Success:",
        binary_data.get("success")
    )

    print(
        "Model:",
        binary_data.get("model")
    )

    print(
        "Dependent variable:",
        binary_data.get(
            "dependent_variable"
        )
    )

    print(
        "Initial N:",
        binary_data.get("initial_n")
    )

    print(
        "Excluded N:",
        binary_data.get("excluded_n")
    )

    print(
        "Final N:",
        binary_data.get("final_n")
    )

    if not binary_data.get("success"):

        print(
            "\n[ERROR]"
        )

        print(
            binary_data.get("error")
        )

    else:

        print(
            "\n[OK] Binary regression data prepared."
        )


except Exception as exc:

    print(
        "\n[ERROR] Binary preparation failed."
    )

    print(
        type(exc).__name__
    )

    print(
        str(exc)
    )

    traceback.print_exc()


# =====================================================
# TEST ORGANISM DATA PREPARATION
# =====================================================

print("\n")
print("====================================")
print("TEST 2: MULTINOMIAL LOGISTIC DATA")
print("====================================")


try:

    multinomial_data = prepare_regression_data(

        df,

        dependent_variable=(
            "organism_identification"
        ),

        independent_variables=(
            INDEPENDENT_VARIABLES
        )

    )


    print(
        "Success:",
        multinomial_data.get("success")
    )

    print(
        "Model:",
        multinomial_data.get("model")
    )

    print(
        "Dependent variable:",
        multinomial_data.get(
            "dependent_variable"
        )
    )

    print(
        "Initial N:",
        multinomial_data.get("initial_n")
    )

    print(
        "Excluded N:",
        multinomial_data.get("excluded_n")
    )

    print(
        "Final N:",
        multinomial_data.get("final_n")
    )

    print(
        "Outcome categories:"
    )

    print(
        multinomial_data.get(
            "outcome_categories"
        )
    )

    if not multinomial_data.get("success"):

        print(
            "\n[ERROR]"
        )

        print(
            multinomial_data.get("error")
        )

    else:

        print(
            "\n[OK] Multinomial regression data prepared."
        )


except Exception as exc:

    print(
        "\n[ERROR] Multinomial preparation failed."
    )

    print(
        type(exc).__name__
    )

    print(
        str(exc)
    )

    traceback.print_exc()


# =====================================================
# TEST ANTIBIOGRAM DATA PREPARATION
# =====================================================

print("\n")
print("====================================")
print("TEST 3: ORDINAL LOGISTIC DATA")
print("====================================")


if len(antibiotics) == 0:

    print(
        "[SKIPPED] No antibiotic columns were found."
    )

else:

    selected_antibiotic = (
        antibiotics[0]
    )

    print(
        "Testing antibiotic:",
        selected_antibiotic
    )


    try:

        ordinal_data = prepare_regression_data(

            df,

            dependent_variable=(
                "antibiogram_susceptibility"
            ),

            independent_variables=(
                INDEPENDENT_VARIABLES
            ),

            antibiotic=(
                selected_antibiotic
            )

        )


        print(
            "Success:",
            ordinal_data.get("success")
        )

        print(
            "Model:",
            ordinal_data.get("model")
        )

        print(
            "Dependent variable:",
            ordinal_data.get(
                "dependent_variable"
            )
        )

        print(
            "Antibiotic:",
            ordinal_data.get(
                "antibiotic"
            )
        )

        print(
            "Antibiotic column:",
            ordinal_data.get(
                "antibiotic_column"
            )
        )

        print(
            "Outcome categories:",
            ordinal_data.get(
                "outcome_categories"
            )
        )

        print(
            "Category order:",
            ordinal_data.get(
                "category_order"
            )
        )

        if not ordinal_data.get("success"):

            print(
                "\n[ERROR]"
            )

            print(
                ordinal_data.get("error")
            )

        else:

            print(
                "\n[OK] Ordinal regression data prepared."
            )


    except Exception as exc:

        print(
            "\n[ERROR] Ordinal preparation failed."
        )

        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

        traceback.print_exc()


# =====================================================
# RUN BINARY MODEL
# =====================================================

print("\n")
print("====================================")
print("TEST 4: RUN BINARY LOGISTIC MODEL")
print("====================================")


try:

    if binary_data.get("success"):

        binary_result = (
            run_binary_logistic_regression(

                binary_data["data"],

                INDEPENDENT_VARIABLES

            )
        )


        print(
            "Success:",
            binary_result.get("success")
        )

        print(
            "Model:",
            binary_result.get("model")
        )

        print(
            "Model name:",
            binary_result.get("model_name")
        )

        print(
            "N:",
            binary_result.get("n")
        )

        print(
            "Converged:",
            binary_result.get("converged")
        )

        if not binary_result.get("success"):

            print(
                "Error:",
                binary_result.get("error")
            )

        else:

            print(
                "[OK] Binary model fitted."
            )

    else:

        print(
            "[SKIPPED] Binary preparation failed."
        )


except Exception as exc:

    print(
        "[ERROR] Binary model failed."
    )

    print(
        type(exc).__name__,
        str(exc)
    )

    traceback.print_exc()


# =====================================================
# RUN MULTINOMIAL MODEL
# =====================================================

print("\n")
print("====================================")
print("TEST 5: RUN MULTINOMIAL LOGISTIC MODEL")
print("====================================")


try:

    if multinomial_data.get("success"):

        multinomial_result = (
            run_multinomial_logistic_regression(

                multinomial_data["data"],

                INDEPENDENT_VARIABLES

            )
        )


        print(
            "Success:",
            multinomial_result.get("success")
        )

        print(
            "Model:",
            multinomial_result.get("model")
        )

        print(
            "Model name:",
            multinomial_result.get("model_name")
        )

        print(
            "N:",
            multinomial_result.get("n")
        )

        print(
            "Number of outcome categories:",
            multinomial_result.get(
                "number_outcome_categories"
            )
        )

        print(
            "Converged:",
            multinomial_result.get(
                "converged"
            )
        )

        if not multinomial_result.get("success"):

            print(
                "Error:",
                multinomial_result.get("error")
            )

        else:

            print(
                "[OK] Multinomial model fitted."
            )

    else:

        print(
            "[SKIPPED] Multinomial preparation failed."
        )


except Exception as exc:

    print(
        "[ERROR] Multinomial model failed."
    )

    print(
        type(exc).__name__,
        str(exc)
    )

    traceback.print_exc()


# =====================================================
# FINAL MESSAGE
# =====================================================

print("\n")
print("====================================")
print("REGRESSION BACKEND TEST COMPLETED")
print("====================================")