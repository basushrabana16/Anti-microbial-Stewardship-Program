
import random
import re
from datetime import date, datetime, time, timedelta

import mysql.connector

# =========================================================
# CONFIGURATION
# =========================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Absolutemysql#1",
    "database": "secure_app"
}

NUM_RECORDS = 200
random.seed(42)

# =========================================================
# SAMPLE DATA
# =========================================================
SAMPLE_TYPES = [
    "urine", "blood", "sputum", "pus",
    "wound swab", "stool", "CSF"
]

ORGANISMS = [
    "Escherichia coli",
    "Klebsiella pneumoniae",
    "Pseudomonas aeruginosa",
    "Staphylococcus aureus",
    "Enterococcus faecalis",
    "Acinetobacter baumannii",
    "Proteus mirabilis"
]

REFERRERS = [
    "OPD", "Emergency", "Medicine",
    "Surgery", "ICU", "Pediatrics"
]

CULTURE_VALUES = ["positive", "no growth"]
SUSCEPTIBILITY_VALUES = [
    "susceptible", "intermediate", "resistant"
]

REPORT_KEYWORDS = [
    "sample_id",
    "lab_no",
    "collection_date",
    "sample_type",
    "collection_time",
    "test_date",
    "referred_by",
    "reporting_date",
    "culture_result",
    "organism",
    "report_file",
    "report_original_name",
    "report_stored_name",
    "report_file_name",
    "report_size",
    "report_mime",
    "uploaded_by",
    "uploader",
    "uploaded_at",
    "created_at"
]

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def enum_values(column_type):
    """Extract valid values from a MySQL ENUM definition."""
    if not column_type.lower().startswith("enum("):
        return []

    return re.findall(r"'((?:[^'\\]|\\.)*)'", column_type)


def random_date(start_year=2024, end_year=2026):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(
        days=random.randint(0, (end - start).days)
    )


def random_time():
    return time(
        random.randint(7, 19),
        random.choice([0, 15, 30, 45])
    )


def matches_report_column(column_name, report_number, column_type):
    """Identify C/S report columns, excluding uploader ID fields."""
    name = column_name.lower()
    suffix = f"_{report_number}"

    if not name.endswith(suffix):
        return False

    base_name = name[:-len(suffix)]

    # Exclude uploaded_by columns completely.
    if "uploaded_by" in base_name:
        return False

    allowed = {v.lower() for v in enum_values(column_type)}

    # Include antibiotic susceptibility columns.
    if {
        "susceptible", "intermediate", "resistant"
    }.issubset(allowed):
        return True

    return any(keyword in base_name for keyword in REPORT_KEYWORDS)


def generate_value(column_name, column_type):
    """Generate a value compatible with the column's data type."""
    name = column_name.lower()
    base_name = re.sub(r"_\d+$", "", name)
    col_type = column_type.lower()
    allowed = enum_values(column_type)

    # Use valid ENUM values defined in the database.
    if allowed:
        allowed_lower = {v.lower() for v in allowed}

        if "culture_result" in base_name:
            preferred = [
                v for v in allowed
                if v.lower() in {
                    "positive", "no growth", "negative"
                }
            ]
            return random.choice(preferred or allowed)

        if {
            "susceptible", "intermediate", "resistant"
        }.issubset(allowed_lower):
            return random.choice(allowed)

        if "sample_type" in base_name:
            preferred = [
                v for v in allowed
                if v.lower() in {
                    "urine", "blood", "sputum", "pus",
                    "wound swab", "stool", "csf",
                    "throat swab", "other"
                }
            ]
            return random.choice(preferred or allowed)

        return random.choice(allowed)

    # Date/time types.
    if col_type == "date" or col_type.startswith("date "):
        return random_date()

    if col_type == "time" or col_type.startswith("time "):
        return random_time()

    if "datetime" in col_type or "timestamp" in col_type:
        return datetime.combine(random_date(), random_time())

    # Numeric types.
    if any(t in col_type for t in (
        "tinyint", "smallint", "mediumint", "int", "bigint"
    )):
        if "size" in base_name:
            return random.randint(20000, 500000)
        return random.randint(1, 1000)

    if any(t in col_type for t in ("decimal", "float", "double")):
        return round(random.uniform(1, 100), 2)

    # Text fields.
    if any(t in col_type for t in (
        "char", "text", "tinytext", "mediumtext", "longtext"
    )):
        if "organism" in base_name:
            return random.choice(ORGANISMS)
        if "sample_type" in base_name:
            return random.choice(SAMPLE_TYPES)
        if "referred_by" in base_name:
            return random.choice(REFERRERS)
        if "mime" in base_name:
            return "application/pdf"
        if "original_name" in base_name or "file_name" in base_name:
            return f"CS_Report_{random.randint(10000, 99999)}.pdf"
        if "stored_name" in base_name:
            return f"{random.randint(100000, 999999)}_report.pdf"
        if "lab_no" in base_name:
            return f"LAB-{random.randint(10000, 99999)}"
        if "sample_id" in base_name:
            return f"CS-{random.randint(100000, 999999)}"
        return f"Dummy_{random.randint(1000, 9999)}"

    # Unknown or unsupported field: leave NULL.
    return None


# =========================================================
# CONNECT TO MYSQL
# =========================================================
connection = mysql.connector.connect(**DB_CONFIG)
cursor = connection.cursor(dictionary=True)

try:
    cursor.execute("""
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE,
               COLUMN_DEFAULT, EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = 'prescriptions'
        ORDER BY ORDINAL_POSITION
    """, (DB_CONFIG["database"],))

    schema = cursor.fetchall()

    if not schema:
        raise RuntimeError(
            "The prescriptions table was not found."
        )

    columns_by_name = {
        row["COLUMN_NAME"]: row for row in schema
    }

    # Detect C/S report columns, excluding uploaded_by_*.
    report_columns = []

    for report_number in range(1, 11):
        for column in schema:
            if matches_report_column(
                column["COLUMN_NAME"],
                report_number,
                column["COLUMN_TYPE"]
            ):
                report_columns.append(column["COLUMN_NAME"])

    report_columns = list(dict.fromkeys(report_columns))

    if not report_columns:
        raise RuntimeError("No C/S report columns were detected.")

    print(f"Detected {len(report_columns)} C/S report columns.")
    print("Uploader ID columns will not be inserted.")

    # Check mandatory columns not included in this INSERT.
    required_columns = [
        row["COLUMN_NAME"]
        for row in schema
        if row["IS_NULLABLE"] == "NO"
        and row["COLUMN_DEFAULT"] is None
        and "auto_increment" not in str(row["EXTRA"]).lower()
        and row["COLUMN_NAME"] not in report_columns
    ]

    if required_columns:
        raise RuntimeError(
            "Required columns are missing from this report-only "
            "INSERT: " + ", ".join(required_columns)
            + ". Populate these fields or ensure they have "
              "valid defaults before proceeding."
        )

    quoted_columns = ", ".join(
        f"`{column}`" for column in report_columns
    )
    placeholders = ", ".join(["%s"] * len(report_columns))

    insert_sql = (
        f"INSERT INTO `prescriptions` ({quoted_columns}) "
        f"VALUES ({placeholders})"
    )

    # =====================================================
    # GENERATE PRESCRIPTION ROWS WITH 1–10 REPORT SETS
    # =====================================================
    for record_number in range(NUM_RECORDS):
        values = {column: None for column in report_columns}

        number_of_reports = random.randint(1, 10)

        for report_number in range(1, 11):
            if report_number > number_of_reports:
                continue

            culture_column = f"culture_result_{report_number}"

            # Generate a culture outcome that matches the
            # actual ENUM spelling/capitalization in MySQL.
            culture_result = None

            if culture_column in columns_by_name:
                allowed = enum_values(
                    columns_by_name[culture_column]["COLUMN_TYPE"]
                )
                choices = [
                    v for v in allowed
                    if v.lower() in {"positive", "no growth", "negative"}
                ]
                culture_result = (
                    random.choice(choices)
                    if choices
                    else random.choice(CULTURE_VALUES)
                )
            else:
                culture_result = random.choice(CULTURE_VALUES)

            for column_name in report_columns:
                suffix = f"_{report_number}"

                if not column_name.lower().endswith(suffix):
                    continue

                base_name = column_name[:-len(suffix)].lower()
                column_type = columns_by_name[column_name]["COLUMN_TYPE"]
                allowed_lower = {
                    v.lower() for v in enum_values(column_type)
                }

                if "culture_result" in base_name:
                    values[column_name] = culture_result

                elif "organism" in base_name:
                    values[column_name] = (
                        random.choice(ORGANISMS)
                        if culture_result.lower() == "positive"
                        else None
                    )

                elif {
                    "susceptible", "intermediate", "resistant"
                }.issubset(allowed_lower):
                    values[column_name] = (
                        random.choice(SUSCEPTIBILITY_VALUES)
                        if culture_result.lower() == "positive"
                        else None
                    )

                else:
                    values[column_name] = generate_value(
                        column_name, column_type
                    )

        cursor.execute(
            insert_sql,
            [values[column] for column in report_columns]
        )

    connection.commit()
    print(f"Successfully inserted {NUM_RECORDS} dummy records.")

except Exception:
    connection.rollback()
    raise

finally:
    cursor.close()
    connection.close()
