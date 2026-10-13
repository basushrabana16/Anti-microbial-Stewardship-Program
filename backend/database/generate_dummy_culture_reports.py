import random
from datetime import date, timedelta, datetime

from connection import get_connection


# =====================================================
# CONFIGURATION
# =====================================================

N_RECORDS = 200
N_SAMPLES = 10


# =====================================================
# MASTER DATA
# =====================================================

districts = [
    "Nadia",
    "Hooghly",
    "Kolkata",
    "Murshidabad"
]


blocks = [
    "Krishnagar",
    "Ranaghat",
    "Berhampore",
    "Chinsurah"
]


organisms = [
    "Escherichia coli",
    "Klebsiella pneumoniae",
    "Pseudomonas aeruginosa",
    "Acinetobacter baumannii",
    "Staphylococcus aureus",
    "Enterococcus faecalis",
    "Proteus mirabilis",
    "Citrobacter freundii",
    "Enterobacter cloacae"
]


sample_types = [
    "Urine",
    "Blood",
    "Pus",
    "Sputum",
    "Endotracheal Aspirate",
    "Wound Swab"
]


referred_by = [
    "Medicine",
    "Surgery",
    "ICU",
    "Pediatrics",
    "Gynecology",
    "Orthopedics"
]


antibiotics = [

    "amoxycillin",
    "moxifloxacin",
    "amoxyclav",
    "norfloxacin",
    "ampicillin",
    "ofloxacin",
    "oxacillin",
    "azithromycin",
    "penicillin",
    "clarithromycin",
    "piperacillin",
    "erythromycin",
    "piperacillin_tazobactam",
    "imipenem",
    "cephalexin",
    "meropenem",
    "cefuroxime",
    "doxycycline",
    "ceftriaxone",
    "tetracycline",
    "cefotaxime",
    "linezolid",
    "ceftazidime",
    "clindamycin",
    "cefixime",
    "vancomycin",
    "cefepime",
    "cotrimoxazole",
    "cefoxitin",
    "chloramphenicol",
    "amikacin",
    "nitrofurantoin",
    "gentamicin",
    "aztreonam",
    "netilmicin",
    "fosfomycin",
    "nalidixic_acid",
    "ciprofloxacin",
    "gatifloxacin",
    "levofloxacin"

]


susceptibility = [
    "susceptible",
    "intermediate",
    "resistant"
]


# =====================================================
# RANDOM DATE
# =====================================================

def random_date():

    start = date(2024, 1, 1)

    end = date(2025, 12, 31)

    return (
        start +
        timedelta(
            days=random.randint(
                0,
                (end - start).days
            )
        )
    )


# =====================================================
# CREATE ONE DATABASE ROW
# =====================================================

def generate_row(record_id):

    row = {}

    # -------------------------------------------------
    # Identification fields
    # -------------------------------------------------

    row["study_id"] = f"STUDY-{record_id:04d}"

    row["cs_sample_send"] = random.choice(["yes", "no"])

    row["regn_no"] = f"REG-{record_id:05d}"

    row["prescription_date"] = random_date()

    # -------------------------------------------------
    # Patient information - Using correct column names from schema
    # -------------------------------------------------

    row["patient_name"] = f"Patient_{record_id}"

    # Use age_years (not age) - this matches the database schema
    age = random.randint(1, 90)
    row["age_years"] = age
    row["age_months"] = random.randint(0, 11)
    row["age_days"] = random.randint(0, 30)

    # gender - matches database schema
    row["gender"] = random.choice(["male", "female"])

    # district and block - match database schema
    row["district"] = random.choice(districts)
    row["block"] = random.choice(blocks)

    # -------------------------------------------------
    # Ten culture report sets
    # -------------------------------------------------

    for sample in range(1, N_SAMPLES + 1):

        positive = random.random() < 0.65

        collection_date = random_date()

        test_date = collection_date + timedelta(days=2)

        reporting_date = test_date + timedelta(days=2)

        sample_id = f"S{record_id:04d}-{sample}"

        row[f"sample_id_{sample}"] = sample_id

        row[f"lab_no_{sample}"] = f"L{random.randint(10000, 99999)}"

        row[f"collection_date_{sample}"] = collection_date

        row[f"sample_type_{sample}"] = random.choice(sample_types)

        row[f"collection_time_{sample}"] = "09:30:00"

        row[f"test_date_{sample}"] = test_date

        row[f"referred_by_{sample}"] = random.choice(referred_by)

        row[f"reporting_date_{sample}"] = reporting_date

        row[f"culture_result_{sample}"] = "positive" if positive else "no growth"

        row[f"organism_identification_{sample}"] = (
            random.choice(organisms) if positive else None
        )

        # -------------------------------------------------
        # Antibiogram susceptibility
        # -------------------------------------------------

        for antibiotic in antibiotics:

            row[f"{antibiotic}_{sample}"] = (

                random.choice(susceptibility)

                if positive

                else None

            )

        # -------------------------------------------------
        # Report metadata
        # -------------------------------------------------

        row[f"report_original_name_{sample}"] = f"{sample_id}.pdf"

        row[f"report_stored_name_{sample}"] = f"stored_{sample_id}.pdf"

        row[f"report_size_{sample}"] = random.randint(50000, 300000)

        row[f"report_mime_{sample}"] = "application/pdf"

        row[f"uploaded_by_id_{sample}"] = 1

        row[f"uploaded_by_username_{sample}"] = "admin"

        row[f"created_at_{sample}"] = datetime.now()

    return row


# =====================================================
# INSERT DATA
# =====================================================

def insert_dummy_data():

    print("\n" + "=" * 50)
    print("GENERATING DUMMY CULTURE DATA")
    print("=" * 50)
    print(f"Number of prescriptions: {N_RECORDS}")
    print(f"Samples per prescription: {N_SAMPLES}")
    print(f"Total reports expected: {N_RECORDS * N_SAMPLES}")
    print("=" * 50 + "\n")

    conn = get_connection()
    cursor = conn.cursor()

    # Check if table has data and ask for confirmation
    cursor.execute("SELECT COUNT(*) FROM prescriptions")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"WARNING: prescriptions table already has {count} records.")
        response = input("Do you want to delete existing data and regenerate? (y/n): ")
        if response.lower() == 'y':
            cursor.execute("TRUNCATE TABLE prescriptions")
            conn.commit()
            print("Existing data truncated.\n")
        else:
            print("Exiting without changes.")
            cursor.close()
            conn.close()
            return

    print("Generating data...\n")

    for i in range(1, N_RECORDS + 1):

        row = generate_row(i)

        columns = list(row.keys())

        values = [row[col] for col in columns]

        placeholders = ",".join(["%s"] * len(columns))

        query = f"""
        INSERT INTO prescriptions
        (
            {','.join(columns)}
        )
        VALUES
        (
            {placeholders}
        )
        """

        cursor.execute(query, values)

        if i % 25 == 0:
            print(f"  {i} records inserted...")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n" + "=" * 50)
    print("DUMMY DATA GENERATION COMPLETED")
    print("=" * 50)
    print(f"Total prescriptions: {N_RECORDS}")
    print(f"Total reports (rows in analysis): {N_RECORDS * N_SAMPLES}")
    print("")
    print("Data summary - ALL PREDICTOR COLUMNS HAVE COMPLETE DATA:")
    print(f"  - age_years: 1-90 (never missing)")
    print(f"  - gender: male/female (never missing)")
    print(f"  - district: always populated")
    print(f"  - block: always populated")
    print(f"  - sample_type: always populated")
    print(f"  - referred_by: always populated")
    print(f"  - culture_result: positive/no growth (never missing)")
    print(f"  - organism_identification: populated for positive cultures")
    print(f"  - antibiogram: populated for positive cultures")
    print("")
    print("NOTE: age_group will be automatically derived from age_years")
    print("      by add_derived_columns() in association_metadata.py")
    print("=" * 50 + "\n")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    insert_dummy_data()