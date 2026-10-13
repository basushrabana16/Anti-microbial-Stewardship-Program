from database.connection import get_connection
from services.query_builder import get_analysis_dataframe


conn = get_connection()


df = get_analysis_dataframe(conn)

print(df.shape)

print(df.head())

print(
    df.filter(
        regex="culture_result"
    ).notna().sum()
)


"""

df = get_analysis_dataframe(conn)

print("\n===== QUERY BUILDER TEST =====")

print("Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print(
    "\nculture_result exists:",
    "culture_result" in df.columns
)

print("\nFirst rows:")
print(df.head())
"""

print("==============================")

conn.close()