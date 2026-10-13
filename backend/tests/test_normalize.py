import pandas as pd

from services.normalize_prescriptions import normalize_prescriptions


# ---------------------------------------
# CREATE MOCK PRESCRIPTION DATA
# ---------------------------------------

data = {

    "patient_name": ["Test Patient"],

    "sample_id_1": ["S001"],

    "culture_result_1": ["Positive"],

    "organism_identification_1": [
        "E.coli"
    ],

    "sample_type_1": [
        "Urine"
    ],

    "ciprofloxacin_1": [
        "Sensitive"
    ]

}


df = pd.DataFrame(data)


# ---------------------------------------
# RUN NORMALIZATION
# ---------------------------------------

result = normalize_prescriptions(df)


print("\n===== NORMALIZATION TEST =====")

print(result)

print("\nColumns:")
print(result.columns.tolist())

print(
    "\nCulture result exists:",
    "culture_result" in result.columns
)

print("==============================")