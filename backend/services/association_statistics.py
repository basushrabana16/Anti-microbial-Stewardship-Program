import math
import numpy as np
from scipy.stats import chi2, chi2_contingency, fisher_exact


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

        chi2_value, p_value, dof, expected = chi2_contingency(
            contingency_table.values,
            correction=is_2x2
        )

        return {
            "test": "Chi-square",
            "test_statistic": safe_number(chi2_value, 4),
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
# CHI-SQUARE TEST FOR TREND (COCHRAN-ARMITAGE)
# =====================================================
#
# Tests whether the proportion of the event category
# (e.g. culture "positive") rises or falls steadily
# across ORDERED groups (e.g. age groups).
#
# Requirements
# ------------
#   - rows are the ordered groups (the caller must
#     already have them in order)
#   - exactly two outcome columns (binary outcome)
#   - at least three ordered groups
#
# Method
# ------
#   x_i = score of group i      (default 1, 2, ..., k)
#   n_i = group total
#   r_i = events in the group
#   N   = sum(n_i)     R = sum(r_i)     p = R / N
#
#   T   = sum( x_i * (r_i - n_i * p) )
#   Sxx = sum(n_i * x_i^2) - (sum(n_i * x_i))^2 / N
#   Z   = T / sqrt( p * (1 - p) * Sxx )
#
#   chi-square (1 df) = Z^2
#
# This is the same statistic as R's prop.trend.test().
# A positive Z means the event proportion INCREASES
# with the score; a negative Z means it DECREASES.
# =====================================================

TREND_TEST_NAME = "Chi-square test for trend (Cochran-Armitage)"


def run_chi_square_trend_test(
    contingency_table,
    event_category="positive",
    scores=None
):
    """
    Parameters
    ----------
    contingency_table : DataFrame
        Rows = ORDERED groups, columns = outcome categories
        (exactly two).
    event_category : str
        Column treated as the event (case-insensitive).
    scores : list of numbers, optional
        One score per row. Default is 1, 2, ..., k.
    """

    result = {

        "test": TREND_TEST_NAME,

        "test_statistic": None,

        "degrees_of_freedom": 1,

        "p_value": None,

        "z_statistic": None,

        "direction": None,

        "proportion_slope": None,

        "event_category": event_category,

        "score_type": None,

        "groups": [],

        "warning": ""

    }

    # -------------------------------------------------
    # BASIC CHECKS
    # -------------------------------------------------

    if contingency_table is None or contingency_table.empty:

        result["warning"] = "Empty contingency table."

        return result

    if contingency_table.shape[1] != 2:

        result["warning"] = (
            "The trend test needs a binary outcome "
            "(exactly two categories)."
        )

        return result

    if contingency_table.shape[0] < 3:

        result["warning"] = (
            "The trend test needs at least three ordered "
            "groups. With two groups it is identical to "
            "the ordinary chi-square test."
        )

        return result

    # -------------------------------------------------
    # EVENT COLUMN
    # -------------------------------------------------

    event_column = None

    for column in contingency_table.columns:

        if str(column).strip().lower() == str(event_category).strip().lower():

            event_column = column

            break

    if event_column is None:

        result["warning"] = (
            f"Event category '{event_category}' was not found "
            f"in the outcome columns."
        )

        return result

    try:

        events = contingency_table[event_column].values.astype(float)

        group_totals = contingency_table.sum(axis=1).values.astype(float)

        group_labels = [
            str(label)
            for label in contingency_table.index
        ]

        k = len(group_totals)

        # ---------------------------------------------
        # SCORES
        # ---------------------------------------------

        if scores is not None and len(scores) == k:

            x = np.asarray(scores, dtype=float)

            result["score_type"] = "custom"

        else:

            x = np.arange(1, k + 1, dtype=float)

            result["score_type"] = "equally spaced (1, 2, ..., k)"

        # ---------------------------------------------
        # TOTALS
        # ---------------------------------------------

        total_n = group_totals.sum()

        total_events = events.sum()

        if total_n <= 0:

            result["warning"] = "Contingency table has no observations."

            return result

        if total_events == 0 or total_events == total_n:

            result["warning"] = (
                "The outcome does not vary (all observations are "
                "in one category), so a trend cannot be tested."
            )

            return result

        p_bar = total_events / total_n

        # ---------------------------------------------
        # STATISTIC
        # ---------------------------------------------

        s_x = float((group_totals * x).sum())

        s_xx = float((group_totals * x ** 2).sum()) - (s_x ** 2) / total_n

        if s_xx <= 0:

            result["warning"] = (
                "The group scores have no spread, so a trend "
                "cannot be tested."
            )

            return result

        t_stat = float((x * (events - group_totals * p_bar)).sum())

        variance = p_bar * (1.0 - p_bar) * s_xx

        z_value = t_stat / math.sqrt(variance)

        chi_square_value = z_value ** 2

        p_value = float(chi2.sf(chi_square_value, 1))

        # ---------------------------------------------
        # DIRECTION / SLOPE
        # ---------------------------------------------

        if abs(z_value) < 1e-12:

            direction = "no trend"

        elif z_value > 0:

            direction = "increasing"

        else:

            direction = "decreasing"

        slope = t_stat / s_xx

        # ---------------------------------------------
        # PER-GROUP SUMMARY
        # ---------------------------------------------

        groups = []

        for index in range(k):

            n_i = group_totals[index]

            groups.append({

                "group":
                    group_labels[index],

                "score":
                    safe_number(x[index], 4),

                "n":
                    int(n_i),

                "events":
                    int(events[index]),

                "percent":
                    safe_number(
                        100.0 * events[index] / n_i if n_i > 0 else None,
                        2
                    )

            })

        # ---------------------------------------------
        # CAUTION FOR SPARSE DATA
        # ---------------------------------------------

        expected_events = group_totals * p_bar

        expected_non_events = group_totals * (1.0 - p_bar)

        warning = ""

        if min(expected_events.min(), expected_non_events.min()) < 5:

            warning = (
                "Some expected counts are below 5, so the trend "
                "test (which relies on a large-sample "
                "approximation) should be interpreted cautiously."
            )

        result.update({

            "test_statistic": safe_number(chi_square_value, 4),

            "p_value": safe_number(p_value, 6),

            "z_statistic": safe_number(z_value, 4),

            "direction": direction,

            "proportion_slope": safe_number(slope, 6),

            "groups": groups,

            "warning": warning

        })

        return result

    except Exception as e:

        result["warning"] = (
            f"Trend test could not be computed: {str(e)}"
        )

        return result


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