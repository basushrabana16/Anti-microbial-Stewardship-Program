from services.data_loader import (
    load_analysis_dataframe,
    apply_filters
)


# =====================================================
# SMALL HELPERS
# =====================================================

def _clean_text(series):
    """Trimmed string version of a column (blank for missing)."""

    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


def _percentage(count, base):
    """Percentage rounded to 2 decimals (0 when base is 0)."""

    return round(count * 100 / base, 2) if base else 0


def _normalize_organism_selection(organisms):
    """
    Converts the Organisms filter into a clean list.
    "all", None and empty values mean "no selection".
    """

    if not organisms:
        return []

    if isinstance(organisms, str):
        organisms = [organisms]

    return [

        str(organism).strip()

        for organism in organisms

        if (
            organism is not None
            and str(organism).strip()
            and str(organism).strip().lower() != "all"
        )

    ]


def _empty_response():

    return {
        "culture_positivity": [],
        "organism_distribution": [],
        "culture_positivity_groups": [],
        "organism_distribution_by_sample": []
    }


def _sample_groups(frame):
    """
    Splits a dataframe into one group per sample type.

    Returns a list of (display_name, sub_dataframe), sorted
    alphabetically (case-insensitive). Records with no sample
    type go into a final "Unspecified sample type" group so the
    groups always add up to the full table.
    """

    keys = frame["sample_clean"].str.lower()

    groups = []

    for key, sub_frame in frame.groupby(keys, sort=False):

        if key == "":
            name = "Unspecified sample type"
        else:
            name = sub_frame["sample_clean"].iloc[0]

        groups.append((name, sub_frame))

    groups.sort(
        key=lambda item: (
            item[0] == "Unspecified sample type",
            item[0].lower()
        )
    )

    return groups


# =====================================================
# TABLE 1 BUILDER: ONE TABLE (rows of Result / Count / %)
# =====================================================

def _positivity_rows(
    base,
    positive_count,
    nogrowth_count,
    positive_label="Positive",
    other_count=None
):
    """
    Rows of one culture-positivity table.

    Percentages are of `base` (all cultures of the sample type).
    "Positive (other organisms)" is added only when other_count
    is given.
    """

    rows = [{
        "Result": positive_label,
        "Count": int(positive_count),
        "Percentage": _percentage(positive_count, base)
    }]

    if other_count is not None:

        rows.append({
            "Result": "Positive (other organisms)",
            "Count": int(other_count),
            "Percentage": _percentage(other_count, base)
        })

    rows.append({
        "Result": "No Growth",
        "Count": int(nogrowth_count),
        "Percentage": _percentage(nogrowth_count, base)
    })

    return rows


# =====================================================
# TABLE 1 GRID: SAMPLE TYPE x ORGANISM TABLES
# =====================================================

def _build_culture_positivity_groups(df, selected_organisms):
    """
    For every sample type in the (already filtered) data:

        1. one table with the organisms in scope pooled together
        2. one table for each individual organism in scope
           (only when two or more organisms are in scope there)

    "In scope" = the organisms chosen in the Organisms filter,
    or every organism when the filter is "All".

    Duplicate tables are skipped:
        - one sample type + all organisms  -> the pooled table
          equals the cumulative table already shown
        - a single organism in scope       -> the individual
          table equals the pooled table

    Percentages are calculated within the sample type
    (all cultures of that sample type = 100%).
    """

    scope_is_all = len(selected_organisms) == 0

    selected_keys = {
        organism.lower()
        for organism in selected_organisms
    }

    groups = _sample_groups(df)

    only_one_sample_type = len(groups) == 1

    output = []

    for sample_name, frame in groups:

        base = len(frame)

        positive_frame = frame[
            frame["culture_result_clean"] == "positive"
        ]

        nogrowth_count = int(
            (frame["culture_result_clean"] == "no growth").sum()
        )

        positive_total = len(positive_frame)

        # organisms present among this sample type's positives
        organism_counts = (
            positive_frame[
                positive_frame["organism_clean"] != ""
            ]["organism_clean"]
            .value_counts()
        )

        # keep the original spelling, match case-insensitively
        present = [

            (organism, int(count))

            for organism, count in organism_counts.items()

            if scope_is_all or organism.lower() in selected_keys

        ]

        # most frequent first, then alphabetical
        present.sort(key=lambda item: (-item[1], item[0].lower()))

        tables = []

        # ---------------------------------------------
        # POOLED TABLE
        # ---------------------------------------------

        if scope_is_all:

            # identical to the cumulative table when there is
            # only one sample type
            if not only_one_sample_type:

                tables.append({
                    "title": f"{sample_name} \u2014 All organisms",
                    "rows": _positivity_rows(
                        base,
                        positive_total,
                        nogrowth_count
                    )
                })

        else:

            in_scope = sum(count for _, count in present)

            if len(selected_organisms) == 1:
                label = selected_organisms[0]
                positive_label = f"Positive ({label})"
            elif len(selected_organisms) <= 3:
                label = " + ".join(selected_organisms)
                positive_label = "Positive (selected organisms)"
            else:
                label = f"{len(selected_organisms)} selected organisms"
                positive_label = "Positive (selected organisms)"

            tables.append({
                "title": f"{sample_name} \u2014 {label}",
                "rows": _positivity_rows(
                    base,
                    in_scope,
                    nogrowth_count,
                    positive_label=positive_label,
                    other_count=positive_total - in_scope
                )
            })

                # ---------------------------------------------
        # INDIVIDUAL ORGANISM TABLES
        #
        # When specific organisms are selected, show one
        # table for EVERY selected organism, even those with
        # zero positives in this sample type (so the grid is
        # consistent across sample types).
        #
        # When "All" is selected, show one table for every
        # organism that has a positive count in this sample.
        # ---------------------------------------------

        if scope_is_all:

            individual_organisms = [
                (organism, int(count))
                for organism, count in organism_counts.items()
            ]

        else:

            count_lookup = {
                organism.lower(): int(count)
                for organism, count in organism_counts.items()
            }

            individual_organisms = [
                (organism, count_lookup.get(organism.lower(), 0))
                for organism in selected_organisms
            ]

        individual_organisms.sort(
            key=lambda item: (-item[1], item[0].lower())
        )

        if len(individual_organisms) >= 2:

            for organism, count in individual_organisms:

                tables.append({
                    "title": f"{sample_name} \u2014 {organism}",
                    "rows": _positivity_rows(
                        base,
                        count,
                        nogrowth_count,
                        positive_label=f"Positive ({organism})",
                        other_count=positive_total - count
                    )
                })

        if tables:

            output.append({
                "sample_type": sample_name,
                "total_cultures": int(base),
                "tables": tables
            })

    return output


# =====================================================
# TABLE 2 PER SAMPLE TYPE
# =====================================================

def _build_organism_distribution_by_sample(positive_named_df):
    """
    One organism-distribution table per sample type, using only
    positive cultures with an identified organism.

    Percentages are calculated within each sample type.

    Returns [] when there is only one sample type (it would only
    repeat the cumulative table).
    """

    if positive_named_df.empty:
        return []

    groups = _sample_groups(positive_named_df)

    if len(groups) < 2:
        return []

    output = []

    for sample_name, frame in groups:

        counts = (
            frame["organism_clean"]
            .value_counts()
            .sort_values(ascending=False)
        )

        total_positive = int(counts.sum())

        rows = [

            {
                "Organism": organism,
                "Count": int(count),
                "Percentage": _percentage(int(count), total_positive)
            }

            for organism, count in counts.items()

        ]

        if rows:

            output.append({
                "sample_type": sample_name,
                "total_positive": total_positive,
                "rows": rows
            })

    return output


# =====================================================
# ORGANISM SUMMARY
# =====================================================

def get_organism_summary(
    district="all",
    block="all",
    sample_type="all",
    organisms=None,        # <-- NEW
    from_month=None,
    to_month=None
):
    """
    Returns:

    1. culture_positivity               (cumulative Table 1, unchanged)
    2. organism_distribution            (cumulative Table 2, unchanged)
    3. culture_positivity_groups        (NEW: sample type x organism tables)
    4. organism_distribution_by_sample  (NEW: Table 2 per sample type)

    The Organisms filter does NOT change the cumulative tables
    (they keep covering every culture in the selection). It only
    decides which organisms appear in the sample-wise Table 1
    tables.

    Supports multiple values for district, block, sample_type and
    month-year range filtering (from_month / to_month, "YYYY-MM").
    """

    selected_organisms = _normalize_organism_selection(organisms)

    # -------------------------------------------------
    # LOAD ANALYSIS DATA
    # -------------------------------------------------

    df = load_analysis_dataframe()

    if df.empty:
        return _empty_response()

    # -------------------------------------------------
    # APPLY FILTERS
    #
    # NOTE: organisms are deliberately NOT passed here.
    # apply_filters() would keep only positive cultures of
    # those organisms, which would remove every "No Growth"
    # row from Table 1.
    # -------------------------------------------------

    df = apply_filters(
        df,
        district=district,
        block=block,
        sample_type=sample_type,
        from_month=from_month,
        to_month=to_month
    )

    if df.empty:
        return _empty_response()

    # =================================================
    # CLEAN COLUMNS
    # =================================================

    df = df.copy()

    df["culture_result_clean"] = (
        _clean_text(df["culture_result"]).str.lower()
    )

    if "sample_type" in df.columns:
        df["sample_clean"] = _clean_text(df["sample_type"])
    else:
        df["sample_clean"] = ""

    df["organism_clean"] = (
        _clean_text(df["organism_identification"])
    )

    # =================================================
    # TABLE A: CULTURE POSITIVITY (cumulative)
    # =================================================

    total_samples = len(df)

    positive_count = int(
        (df["culture_result_clean"] == "positive").sum()
    )

    nogrowth_count = int(
        (df["culture_result_clean"] == "no growth").sum()
    )

    table_a = [

        {
            "Result": "Positive",

            "Count": positive_count,

            "Percentage": round(
                positive_count * 100 / total_samples,
                2
            ) if total_samples else 0
        },

        {
            "Result": "No Growth",

            "Count": nogrowth_count,

            "Percentage": round(
                nogrowth_count * 100 / total_samples,
                2
            ) if total_samples else 0
        }

    ]

    # =================================================
    # TABLE B: ORGANISM DISTRIBUTION (cumulative)
    # =================================================

    # Only positive cultures with an identified organism.

    positive_named = df[
        (df["culture_result_clean"] == "positive")
        &
        (df["organism_clean"] != "")
    ]

    if positive_named.empty:

        table_b = []

    else:

        organism_counts = (

            positive_named["organism_clean"]

            .value_counts()

            .sort_values(
                ascending=False
            )

        )

        total_positive = int(
            organism_counts.sum()
        )

        table_b = []

        for organism, count in organism_counts.items():

            count = int(count)

            table_b.append({

                "Organism": organism,

                "Count": count,

                "Percentage": (

                    round(
                        count * 100 / total_positive,
                        2
                    )

                    if total_positive

                    else 0

                )

            })

    # =================================================
    # NEW: SAMPLE-WISE TABLES
    # =================================================

    culture_positivity_groups = (
        _build_culture_positivity_groups(
            df,
            selected_organisms
        )
    )

    organism_distribution_by_sample = (
        _build_organism_distribution_by_sample(
            positive_named
        )
    )

    # =================================================
    # RETURN RESULT
    # =================================================

    return {

        "culture_positivity": table_a,

        "organism_distribution": table_b,

        "culture_positivity_groups":
            culture_positivity_groups,

        "organism_distribution_by_sample":
            organism_distribution_by_sample

    }