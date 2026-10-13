import math
from scipy.stats import chi2_contingency, fisher_exact


# =====================================================
# SAFE NUMBER CONVERTER
# =====================================================

def safe_number(value, decimals=6):

    try:

        if value is None:
            return None

        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return round(value, decimals)

    except (TypeError, ValueError):
        return None


# =====================================================
# CHI-SQUARE TEST
# =====================================================

def run_chi_square_test(contingency_table):

    if contingency_table is None or contingency_table.empty:
        return {
            "test": "Chi-square",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": "Empty contingency table"
        }

    try:

        is_2x2 = contingency_table.shape == (2, 2)

        chi2, p_value, dof, expected = chi2_contingency(
            contingency_table.values,
            correction=is_2x2
        )

        return {
            "test": "Chi-square",
            "test_statistic": safe_number(chi2, 4),
            "degrees_of_freedom": int(dof),
            "p_value": safe_number(p_value, 6),
            "yates_correction_applied": is_2x2,
            "warning": ""
        }

    except ValueError as e:

        return {
            "test": "Chi-square",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": f"Chi-square could not be computed: {str(e)}"
        }

    except Exception as e:

        return {
            "test": "Chi-square",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": f"Unexpected Chi-square error: {str(e)}"
        }


# =====================================================
# FISHER EXACT TEST (2x2 ONLY)
# =====================================================

def run_fisher_exact_test(contingency_table):

    if contingency_table is None or contingency_table.empty:
        return {
            "test": "Fisher Exact",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": "Empty contingency table"
        }

    if contingency_table.shape != (2, 2):
        return {
            "test": "Fisher Exact",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": "Fisher Exact Test requires a 2x2 contingency table"
        }

    try:

        odds_ratio, p_value = fisher_exact(
            contingency_table.values
        )

        odds_ratio_clean = safe_number(
            odds_ratio,
            4
        )

        return {
            "test": "Fisher Exact",
            "test_statistic": odds_ratio_clean,
            "degrees_of_freedom": None,
            "p_value": safe_number(p_value, 6),
            "odds_ratio": odds_ratio_clean,
            "warning": (
                "Odds ratio undefined due to zero cells"
                if odds_ratio_clean is None
                else ""
            )
        }

    except Exception as e:

        return {
            "test": "Fisher Exact",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": f"Fisher Exact Test could not be computed: {str(e)}"
        }


# =====================================================
# FISHER-FREEMAN-HALTON TEST
# =====================================================
#
# IMPORTANT:
# scipy fisher_exact is guaranteed for 2x2 tables.
# For r x c tables, support depends on SciPy version.
#
# This function tries r x c Fisher exact safely.
# If unavailable, it returns a warning instead of crashing.
# =====================================================

_FFH_MAX_TOTAL_N = 5000
_FFH_MAX_CELLS = 60


def run_fisher_freeman_halton_test(contingency_table):

    if contingency_table is None or contingency_table.empty:
        return {
            "test": "Fisher-Freeman-Halton",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": "Empty contingency table"
        }

    rows, cols = contingency_table.shape

    if rows < 2 or cols < 2:
        return {
            "test": "Fisher-Freeman-Halton",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": "Fisher-Freeman-Halton requires at least a 2x2 table"
        }

    total_n = int(contingency_table.values.sum())
    total_cells = rows * cols

    if total_n <= 0:
        return {
            "test": "Fisher-Freeman-Halton",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": "Contingency table contains no observations"
        }

    if total_n > _FFH_MAX_TOTAL_N or total_cells > _FFH_MAX_CELLS:
        return {
            "test": "Fisher-Freeman-Halton",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": (
                f"Table too large for Fisher-Freeman-Halton test "
                f"({rows}x{cols}, n={total_n}). "
                f"Combine sparse categories or use Chi-square."
            )
        }

    try:

        result = fisher_exact(
            contingency_table.values
        )

        # Newer SciPy versions
        if hasattr(result, "statistic") and hasattr(result, "pvalue"):

            statistic = result.statistic
            p_value = result.pvalue

        # Some SciPy versions return tuple
        elif isinstance(result, tuple) and len(result) >= 2:

            statistic = result[0]
            p_value = result[1]

        else:

            return {
                "test": "Fisher-Freeman-Halton",
                "test_statistic": None,
                "degrees_of_freedom": None,
                "p_value": None,
                "warning": (
                    "Your installed SciPy version does not support "
                    "r x c Fisher-Freeman-Halton testing."
                )
            }

        return {
            "test": "Fisher-Freeman-Halton",
            "test_statistic": safe_number(statistic, 6),
            "degrees_of_freedom": None,
            "p_value": safe_number(p_value, 6),
            "warning": ""
        }

    except Exception as e:

        return {
            "test": "Fisher-Freeman-Halton",
            "test_statistic": None,
            "degrees_of_freedom": None,
            "p_value": None,
            "warning": (
                "Fisher-Freeman-Halton could not be computed. "
                "Your SciPy version may only support Fisher Exact "
                f"for 2x2 tables. Details: {str(e)}"
            )
        }