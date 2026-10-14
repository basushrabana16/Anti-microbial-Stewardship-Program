"""
Create 100 fully populated synthetic rows in `prescriptions`.
TEST DATABASE ONLY. These values are fabricated and are not real clinical/lab data.
No rows are inserted until APPLY_CHANGES is changed to True.
Requires your existing connection.py with get_connection().
"""
import random, re, sys
from datetime import date, datetime, time, timedelta
from connection import get_connection

N_RECORDS = 100
APPLY_CHANGES = True
CONFIRMATION = "INSERT 100 SYNTHETIC ROWS"
random.seed(20261014)

DISTRICTS = ["Nadia", "Hooghly", "Kolkata", "Murshidabad", "Howrah", "Malda"]
BLOCKS = ["Krishnagar", "Ranaghat", "Berhampore", "Chinsurah", "Bally", "English Bazar"]
NAMES = ["Aarav Das", "Ananya Roy", "Rohan Sen", "Priya Dutta", "Arjun Ghosh",
         "Ishita Paul", "Sayan Mukherjee", "Riya Saha", "Debjit Bose", "Moumita Das"]
HOSPITALS = ["District Hospital", "Rural Hospital", "Community Health Centre",
             "Sub-Divisional Hospital", "Medical College Hospital"]
SAMPLES = ["urine", "blood", "sputum", "pus", "wound swab", "stool"]
ORGANISMS = ["Escherichia coli", "Klebsiella pneumoniae", "Staphylococcus aureus",
             "Pseudomonas aeruginosa", "Enterococcus species", "Proteus mirabilis"]
ANTIBIOTICS = ["amoxycillin", "amoxyclav", "ampicillin", "azithromycin",
               "ceftriaxone", "ciprofloxacin", "gentamicin", "amikacin", "meropenem"]
ROUTES = ["oral", "IV", "IM"]
FREQUENCIES = ["OD", "BD", "TDS", "QID", "12 hourly", "8 hourly"]
DECISIONS = ["stop", "escalate", "de-escalate", "switch to oral",
             "switch to narrow spectrum", "change to other broad spectrum"]

def enum_members(sql_type):
    if not (sql_type or "").lower().startswith("enum("):
        return []
    return re.findall(r"'((?:[^'\\]|\\.)*)'", sql_type)

def choose_enum(col, members, i):
    n = col.lower()
    if n == "status":
        return "cs-wait" if "cs-wait" in members else members[0]
    if "culture_result" in n:
        return "positive" if i % 3 != 0 and "positive" in members else (
            "no growth" if "no growth" in members else members[0])
    if any(x in n for x in ["gender"]):
        options = [x for x in members if x in ["male", "female", "other"]]
        return random.choice(options or members)
    if "susceptible" in n or any(x in n for x in [
        "amoxycillin_", "moxifloxacin_", "amoxyclav_", "norfloxacin_", "ampicillin_",
        "ofloxacin_", "oxacillin_", "azithromycin_", "penicillin_", "clarithromycin_",
        "piperacillin_", "erythromycin_", "imipenem_", "cephalexin_", "meropenem_",
        "cefuroxime_", "doxycycline_", "ceftriaxone_", "tetracycline_", "cefotaxime_",
        "linezolid_", "ceftazidime_", "clindamycin_", "cefixime_", "vancomycin_",
        "cefepime_", "cotrimoxazole_", "cefoxitin_", "chloramphenicol_", "amikacin_",
        "nitrofurantoin_", "gentamicin_", "aztreonam_", "netilmicin_", "fosfomycin_",
        "nalidixic_acid_", "ciprofloxacin_", "gatifloxacin_", "levofloxacin_", "colistin_",
        "ertapenem_", "sulfamethoxazole_trimethoprim_"]):
        return random.choice(members)
    if "outcome" in n:
        return random.choice(members)
    if "decision" in n:
        return random.choice([x for x in members if x in DECISIONS] or members)
    if "route" in n:
        return random.choice([x for x in members if x in ROUTES] or members)
    if "dose_unit" in n:
        return random.choice(members)
    if "dose_rating" in n or "frequency_rating" in n:
        return random.choice(members)
    if "aware" in n:
        return random.choice(members)
    if "duration_mentioned" in n:
        return "mentioned" if "mentioned" in members else members[0]
    if any(x in n for x in ["consented", "sample_send", "guideline", "matched",
                            "body_weight_mentioned", "eval_b_", "patient_"]):
        return "yes" if "yes" in members else members[0]
    return random.choice(members)

def text_value(col, sql_type, i, slot):
    n = col.lower()
    if n == "study_id": value = f"DEMO-{i+1:05d}"
    elif n == "regn_no": value = f"DEMO-R-{i+1:05d}"
    elif n == "patient_name": value = NAMES[i % len(NAMES)]
    elif n == "gender": value = random.choice(["male", "female", "other"])
    elif n == "district": value = random.choice(DISTRICTS)
    elif n == "block": value = random.choice(BLOCKS)
    elif "hospital" in n: value = random.choice(HOSPITALS)
    elif "diagnosis" in n: value = random.choice(["UTI", "Respiratory tract infection", "Skin infection", "Febrile illness"])
    elif "sample_type" in n: value = random.choice(SAMPLES)
    elif "organism_identification" in n: value = random.choice(ORGANISMS)
    elif "sample_id" in n: value = f"SAMP-{i+1:05d}-{slot+1}"
    elif "lab_no" in n: value = f"LAB-{i+1:05d}-{slot+1}"
    elif "original_name" in n: value = f"synthetic_report_{i+1:05d}_{slot+1}.pdf"
    elif "stored_name" in n: value = f"synthetic_{i+1:05d}_{slot+1}.pdf"
    elif "mime" in n: value = "application/pdf"
    elif "referred_by" in n: value = random.choice(["OPD", "IPD", "Medicine", "Paediatrics", "Surgery"])
    elif "username" in n or "collector_name" in n: value = "Synthetic Test User"
    elif "antibiotic" in n or re.match(r"^(d|da)_name_\d+$", n): value = random.choice(ANTIBIOTICS)
    elif "route" in n: value = random.choice(ROUTES)
    elif "frequency" in n and "rating" not in n: value = random.choice(FREQUENCIES)
    elif "dose" in n and "rating" not in n and "unit" not in n: value = str(random.choice([250, 500, 750, 1000]))
    elif "justification" in n: value = "Synthetic test value; verify against protocol."
    elif "aware" in n: value = "access"
    elif "guideline" in n or "matched" in n: value = "yes"
    elif "phase" in n: value = "baseline"
    elif "report" in n: value = f"Synthetic report {i+1}-{slot+1}"
    else: value = f"Synthetic {col} {i+1}"
    m = re.match(r"(?:var)?char\((\d+)\)", (sql_type or "").lower())
    return value[:int(m.group(1))] if m else value

def value_for(col, sql_type, i, slot):
    n, t = col.lower(), (sql_type or "").lower()
    enums = enum_members(sql_type)
    if enums:
        return choose_enum(n, enums, i)
    if "timestamp" in t or t == "datetime":
        dt = datetime(2025, 1, 1, 9, 0) + timedelta(days=i, minutes=slot*13)
        if n == "updated_at": dt += timedelta(hours=1)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if t == "date":
        return (date(2025, 1, 1) + timedelta(days=i % 365)).isoformat()
    if t == "time":
        return time(8 + i % 10, (i*7) % 60).strftime("%H:%M:%S")
    if any(x in t for x in ["tinyint", "smallint", "mediumint", "bigint", "int"]):
        if n == "age_years": return random.randint(1, 90)
        if n == "age_months": return random.randint(0, 11)
        if n == "age_days": return random.randint(0, 30)
        if "weight" in n: return random.randint(8, 85)
        if "size" in n: return random.randint(10000, 800000)
        if "duration" in n or "hospital_stay" in n: return random.randint(1, 10)
        if n.endswith("not_required"): return 0
        if "total" in n or any(x in n for x in ["injectable", "generic", "who_eml", "nelm", "formulary", "fdc"]):
            return random.randint(0, 8)
        return 1
    if any(x in t for x in ["decimal", "float", "double"]):
        return round(random.uniform(8, 85), 2) if "weight" in n else round(random.uniform(1, 10), 2)
    return text_value(col, sql_type, i, slot)

def main():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SHOW FULL COLUMNS FROM `prescriptions`")
        meta = cur.fetchall()
        if not meta:
            raise RuntimeError("No columns found for prescriptions.")
        columns = []
        for m in meta:
            name, typ, extra = m[0], m[1], (m[6] or "").lower()
            if "auto_increment" in extra or "generated" in extra:
                continue
            columns.append((name, typ))
        rows = []
        for i in range(N_RECORDS):
            row = {}
            for col, typ in columns:
                match = re.search(r"_(\d+)$", col)
                slot = int(match.group(1))-1 if match else 0
                row[col] = value_for(col, typ, i, slot)
                if row[col] is None or row[col] == "":
                    raise RuntimeError(f"Generated blank/NULL for {col}, row {i+1}")
            rows.append(row)

        print(f"Prepared {len(rows)} rows × {len(columns)} insertable columns = {len(rows)*len(columns)} values.")
        print("All insertable columns have non-empty synthetic values. Auto-increment id is generated by MySQL.")
        print("First row preview:")
        for k in list(rows[0])[:30]: print(f"  {k} = {rows[0][k]!r}")
        if len(columns) > 30: print(f"  ... and {len(columns)-30} additional columns")
        if not APPLY_CHANGES:
            print("\nDRY RUN ONLY. Nothing inserted. Review output, then set APPLY_CHANGES = True.")
            return

        if input(f"Type exactly '{CONFIRMATION}' to continue: ").strip() != CONFIRMATION:
            print("Confirmation mismatch; nothing inserted.")
            return

        names = list(rows[0])
        qcols = ", ".join("`"+x.replace("`", "``")+"`" for x in names)
        placeholders = ", ".join(["%s"] * len(names))
        sql = f"INSERT INTO `prescriptions` ({qcols}) VALUES ({placeholders})"
        try:
            cur.executemany(sql, [tuple(row[c] for c in names) for row in rows])
            conn.commit()
            print(f"Inserted {cur.rowcount} synthetic rows.")
        except Exception:
            conn.rollback()
            raise
        cur.execute("SELECT COUNT(*) FROM prescriptions")
        print("Total rows now in prescriptions:", cur.fetchone()[0])
        # Check newly inserted rows by their unique DEMO study IDs.
        cur.execute("SELECT COUNT(*) FROM prescriptions WHERE study_id LIKE 'DEMO-%'")
        print("Rows with generated DEMO study IDs:", cur.fetchone()[0])
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        print("If insertion failed, review ENUM values, foreign keys, and CHECK constraints.")
        sys.exit(1)
