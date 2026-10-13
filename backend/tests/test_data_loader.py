# =====================================================
# TEST DATA LOADER
# =====================================================

from services.data_loader import (
    load_analysis_dataframe,
    apply_filters,
    validate_variables
)


# =====================================================
# TEST COMPLETE DATA LOADING PIPELINE
# =====================================================

def test_load_analysis_dataframe():

    print("\n===== DATA LOADER TEST =====")

    df = load_analysis_dataframe()

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())


    print("\nFirst rows:")
    print(df.head())


    print("\nRequired columns check:")

    required_columns = [
        "culture_result",
        "organism_identification",
        "district",
        "block",
        "sample_type"
    ]


    for col in required_columns:

        print(
            col,
            ":",
            col in df.columns
        )


    return df



# =====================================================
# TEST FILTER FUNCTION
# =====================================================

def test_apply_filters(df):

    print("\n===== FILTER TEST =====")


    filtered = apply_filters(
        df,
        district="all",
        block="all",
        sample_type="all",
        organisms=None
    )


    print("\nNo filter shape:")
    print(filtered.shape)



    # Test organism filter only if column exists

    if "organism_identification" in df.columns:

        organisms = (
            df["organism_identification"]
            .dropna()
            .unique()
            .tolist()
        )


        if organisms:

            print(
                "\nTesting organism filter:",
                organisms[0]
            )


            filtered_org = apply_filters(
                df,
                organisms=[
                    organisms[0]
                ]
            )


            print(
                "Filtered shape:"
            )

            print(
                filtered_org.shape
            )



# =====================================================
# TEST VARIABLE VALIDATION
# =====================================================

def test_validate_variables():

    print("\n===== VARIABLE VALIDATION TEST =====")


    independent_variables = [
        "gender",
        "district",
        "block"
    ]


    dependent_variables = [
        "culture_result",
        "organism_identification"
    ]


    result = validate_variables(
        "gender",
        "culture_result",
        independent_variables,
        dependent_variables
    )


    print(
        "Valid variables result:"
    )

    print(result)



    result_invalid = validate_variables(
        "wrong_variable",
        "culture_result",
        independent_variables,
        dependent_variables
    )


    print(
        "\nInvalid variable result:"
    )

    print(result_invalid)



# =====================================================
# RUN TESTS
# =====================================================

if __name__ == "__main__":

    df = test_load_analysis_dataframe()

    if not df.empty:

        test_apply_filters(df)

    test_validate_variables()