import pandas as pd

from services.normalize_prescriptions import normalize_prescriptions


# =====================================================
# LOAD COMPLETE ANALYSIS DATAFRAME
# =====================================================

def get_analysis_dataframe(conn):
    """
    Loads the complete prescriptions table from the
    database and converts it into the canonical
    long-format analysis dataframe.

    Returns
    -------
    pandas.DataFrame

        One row = One culture report
    """

    # -------------------------------------------------
    # LOAD PRESCRIPTIONS TABLE
    # -------------------------------------------------

    query = """
        SELECT *
        FROM prescriptions
        WHERE cs_sample_send = 'yes'
          AND status = 'expert_done_final'
    """

    prescriptions_df = pd.read_sql(
        query,
        conn
    )

    print("\nDATABASE COLUMNS")
    print(prescriptions_df.columns.tolist())
    print()

    if prescriptions_df.empty:
        return prescriptions_df

    # -------------------------------------------------
    # NORMALIZE WIDE TABLE
    # -------------------------------------------------

    analysis_df = normalize_prescriptions(
        prescriptions_df
    )

    print("\nANALYSIS COLUMNS")
    print(list(analysis_df.columns))
    print("\nNUMBER OF ROWS:", len(analysis_df))

    return analysis_df