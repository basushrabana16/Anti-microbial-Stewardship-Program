from services.data_loader import (
    load_analysis_dataframe,
    apply_filters,
    validate_variables
)

from services.association_helpers import (
    build_contingency_table,
    calculate_expected_frequencies,
    calculate_row_percentages,
    evaluate_assumptions,
    calculate_totals
)

from services.association_statistics import (
    run_chi_square_test,
    run_fisher_exact_test,
    run_fisher_freeman_halton_test
)


# =====================================================
# ALLOWED VARIABLES
# =====================================================

INDEPENDENT_VARIABLES = [

    "gender",
    "age_group",
    "district",
    "block",
    "sample_type",
    "referred_by",
    "collection_month",
    "collection_season"

]


DEPENDENT_VARIABLES = [

    "culture_result",
    "organism_identification",
    "antibiogram_susceptibility"

]


# =====================================================
# MAIN ASSOCIATION TEST
# =====================================================

def run_association_test(

    district="all",
    block="all",
    sample_type="all",
    organisms=None,

    independent_variable=None,
    dependent_variable=None,

    antibiotics=None

):


    # =================================================
    # LOAD DATA
    # =================================================

    df = load_analysis_dataframe()


    if df is None or df.empty:

        return {
            "error": "No data available."
        }



    # =================================================
    # APPLY FILTERS
    # =================================================

    df = apply_filters(

        df,

        district=district,
        block=block,
        sample_type=sample_type,
        organisms=organisms or []

    )


    if df.empty:

        return {

            "error":
                "No records found after applying filters."

        }



    # =================================================
    # VARIABLE VALIDATION
    # =================================================

    validation = validate_variables(

        independent_variable,

        dependent_variable,

        INDEPENDENT_VARIABLES,

        DEPENDENT_VARIABLES

    )


    if validation:

        return validation



    # =================================================
    # ANTIBIOGRAM HANDLING
    # =================================================

    is_antibiogram = (

        dependent_variable ==
        "antibiogram_susceptibility"

    )


    selected_antibiotic = None


    if is_antibiogram:


        antibiotics = antibiotics or []


        selected = [

            str(a)
            .strip()
            .lower()

            for a in antibiotics

            if str(a).strip().lower()
            != "all"

        ]


        if not selected:

            return {

                "error":
                "Please select an antibiotic."

            }


        selected_antibiotic = selected[0]


        if selected_antibiotic not in df.columns:

            return {

                "error":
                f"Antibiotic '{selected_antibiotic}' not found."

            }


        dependent_column = selected_antibiotic


    else:

        dependent_column = dependent_variable




    # =================================================
    # CONTINGENCY TABLE
    # =================================================

    contingency_table = build_contingency_table(

        df=df,

        independent_variable=
            independent_variable,

        dependent_variable=
            dependent_column,

        is_antibiogram_susceptibility=
            is_antibiogram

    )


    if contingency_table is None:


        return {

            "error":
            "Unable to construct contingency table."

        }




    if (

        contingency_table.shape[0] < 2

        or

        contingency_table.shape[1] < 2

    ):


        return {


            "error":
            "At least two categories are required "
            "for both variables.",


            "contingency_table":
            contingency_table.to_dict()

        }




    # =================================================
    # TABLE SUMMARY
    # =================================================

    expected_df = calculate_expected_frequencies(

        contingency_table

    )


    row_percentages = calculate_row_percentages(

        contingency_table

    )


    totals = calculate_totals(

        contingency_table

    )


    assumptions = evaluate_assumptions(

        expected_df

    )



    # =================================================
    # AUTOMATIC TEST SELECTION
    # =================================================

    is_2x2 = (

        contingency_table.shape ==
        (2,2)

    )


    min_expected = assumptions[

        "minimum_expected_frequency"

    ]


    percent_below_5 = assumptions[

        "percent_cells_with_expected_below_5"

    ]



    if is_2x2:


        if min_expected >= 5:


            statistics = run_chi_square_test(

                contingency_table

            )


            decision = (

                "2x2 table with adequate expected "
                "frequencies. Chi-square test used."

            )


        else:


            statistics = run_fisher_exact_test(

                contingency_table

            )


            decision = (

                "2x2 table with low expected "
                "frequency. Fisher Exact test used."

            )



    else:


        if percent_below_5 < 20:


            statistics = run_chi_square_test(

                contingency_table

            )


            decision = (

                "Expected frequency assumption satisfied. "
                "Chi-square test used."

            )


        else:


            statistics = run_fisher_freeman_halton_test(

                contingency_table

            )


            decision = (

                "Many expected frequencies below 5. "
                "Fisher-Freeman-Halton test used."

            )




    # =================================================
    # FINAL RESPONSE
    # =================================================

    return {


        "independent_variable":
            independent_variable,


        "dependent_variable":
            dependent_variable,


        "selected_antibiotic":
            selected_antibiotic,


        "total_records":
            int(
                contingency_table.values.sum()
            ),


        "table_shape":

            f"{contingency_table.shape[0]}x"
            f"{contingency_table.shape[1]}",



        "test":

            statistics.get(
                "test"
            ),



        "decision":

            decision,



        "test_statistic":

            statistics.get(
                "test_statistic"
            ),



        "degrees_of_freedom":

            statistics.get(
                "degrees_of_freedom"
            ),



        "p_value":

            statistics.get(
                "p_value"
            ),



        "warning":

            statistics.get(
                "warning",
                ""
            ),



        "contingency_table":

            contingency_table.to_dict(),



        "row_percentages":

            row_percentages.to_dict(),



        "expected_frequencies":

            expected_df.round(2).to_dict(),



        "row_totals":

            totals["row_totals"],



        "column_totals":

            totals["column_totals"],



        "grand_total":

            totals["grand_total"],



        "assumptions":

            assumptions

    }




# =====================================================
# ASSOCIATION SUMMARY
# =====================================================

def get_association_summary():

    return {


        "independent_variables":
            INDEPENDENT_VARIABLES,


        "dependent_variables":
            DEPENDENT_VARIABLES,


        "automatic_test_selection":

        {

            "2x2 with expected frequency <5":
                "Fisher Exact Test",


            "rxc with >=20% expected frequencies <5":
                "Fisher-Freeman-Halton Test",


            "otherwise":
                "Chi-square Test"

        }

    }