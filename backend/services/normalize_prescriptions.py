"""
normalize_prescriptions.py

Converts the wide-format prescriptions table into a
long-format analysis dataframe.

One prescription row
        ↓
Multiple culture report rows
"""

import re
import pandas as pd


# =====================================================
# REPORT META COLUMNS
# =====================================================

REPORT_COLUMNS = {

    "sample_id",
    "lab_no",
    "collection_date",
    "sample_type",
    "collection_time",
    "test_date",
    "referred_by",
    "reporting_date",
    "culture_result",
    "organism_identification",
    "report_original_name",
    "report_stored_name",
    "report_size",
    "report_mime",
    "uploaded_by_id",
    "uploaded_by_username",
    "created_at"

}


# =====================================================
# DETECT REPORT NUMBERS
# =====================================================

def get_report_numbers(columns):
    """
    Detect available report numbers automatically.

    Example:
        sample_id_1
        sample_id_2
        ...
        sample_id_10

    Returns:
        [1, 2, ..., 10]
    """

    reports = set()

    pattern = re.compile(r"sample_id_(\d+)$")

    for column in columns:

        match = pattern.match(column)

        if match:

            reports.add(int(match.group(1)))

    return sorted(reports)


# =====================================================
# DETECT ANTIBIOTIC COLUMNS
# =====================================================

def get_antibiotic_columns(columns):
    """
    Detect antibiotic names automatically.

    Example

        ciprofloxacin_1
        amikacin_1

    becomes

        ciprofloxacin
        amikacin
    """

    antibiotics = []

    for column in columns:

        if not column.endswith("_1"):
            continue

        base = column[:-2]

        if base not in REPORT_COLUMNS:

            antibiotics.append(base)

    return sorted(antibiotics)


# =====================================================
# CHECK WHETHER A REPORT BLOCK HAS DATA
# =====================================================

def has_report_data(row, report_number, antibiotics):
    """
    Returns True if the report block contains
    any meaningful information.
    """

    report_fields = [

        "sample_id",
        "lab_no",
        "collection_date",
        "sample_type",
        "collection_time",
        "test_date",
        "referred_by",
        "reporting_date",
        "culture_result",
        "organism_identification"

    ]

    for field in report_fields:

        column = f"{field}_{report_number}"

        if column in row.index:

            value = row[column]

            if pd.notna(value) and str(value).strip() != "":

                return True

    # Check antibiogram values

    for antibiotic in antibiotics:

        column = f"{antibiotic}_{report_number}"

        if column in row.index:

            value = row[column]

            if pd.notna(value) and str(value).strip() != "":

                return True

    return False


# =====================================================
# NORMALIZE PRESCRIPTIONS
# =====================================================

def normalize_prescriptions(df):

    if df.empty:
        return df

    report_numbers = get_report_numbers(df.columns)

    antibiotics = get_antibiotic_columns(df.columns)

    print("\nREPORT NUMBERS:", report_numbers)
    print("NUMBER OF ANTIBIOTICS:", len(antibiotics))
    print("FIRST 5 ANTIBIOTICS:", antibiotics[:5])

    # -------------------------------------------------
    # PATIENT-LEVEL COLUMNS
    # -------------------------------------------------

    patient_columns = [

        column

        for column in df.columns

        if not re.search(r"_\d+$", column)

    ]

    records = []

    # -------------------------------------------------
    # LOOP THROUGH PRESCRIPTIONS
    # -------------------------------------------------

    for _, prescription in df.iterrows():

        patient_data = {

            column: prescription[column]

            for column in patient_columns

        }

        # ---------------------------------------------
        # LOOP THROUGH REPORT SETS
        # ---------------------------------------------

        for report_number in report_numbers:

            if not has_report_data(
                prescription,
                report_number,
                antibiotics
            ):
                continue

            report = patient_data.copy()

            report["report_number"] = report_number

            # -----------------------------------------
            # REPORT INFORMATION
            # -----------------------------------------

            for field in REPORT_COLUMNS:

                column = f"{field}_{report_number}"

                report[field] = (

                    prescription[column]

                    if column in df.columns

                    else None

                )

            # -----------------------------------------
            # ANTIBIOGRAM
            # -----------------------------------------

            for antibiotic in antibiotics:

                column = f"{antibiotic}_{report_number}"

                report[antibiotic] = (

                    prescription[column]

                    if column in df.columns

                    else None

                )

            records.append(report)

    print("\nNUMBER OF RECORDS CREATED:", len(records))

    analysis_df = pd.DataFrame(records)

    print("DataFrame shape:", analysis_df.shape)
    print("Has culture_result?", "culture_result" in analysis_df.columns)
    print("First 20 columns:")
    print(analysis_df.columns.tolist()[:20])

    analysis_df.attrs["antibiotic_columns"] = antibiotics
    analysis_df.attrs["report_numbers"] = report_numbers


    print("\n===== BEFORE RETURN FROM NORMALIZE =====")
    print("Shape:", analysis_df.shape)
    print("Columns:", analysis_df.columns.tolist())
    print("culture_result exists:", "culture_result" in analysis_df.columns)

    if "culture_result" in analysis_df.columns:
        print(
         analysis_df["culture_result"].value_counts(dropna=False)
        )

    print("========================================\n")

    return analysis_df.reset_index(drop=True)