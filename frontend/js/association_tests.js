/* ==========================================================
   AMSP — ASSOCIATION TESTS
   ========================================================== */

"use strict";


/* ==========================================================
   ASSOCIATION TESTS OBJECT
   ========================================================== */

const AssociationTests = {

    endpoint: "/association-test",

    independentVariables: [],

    dependentVariables: [],

    selected: {

        independent: null,

        dependent: null

    },

    controls: {

        independent: null,

        dependent: null

    },

    lastResult: null

};


/* ==========================================================
   INITIALIZE
   ========================================================== */

AssociationTests.initialize = function () {

    this.cacheElements();

    this.cacheVariableControls();

    this.registerEvents();

};


/* ==========================================================
   CACHE STATIC RESULT ELEMENTS
   ========================================================== */

AssociationTests.cacheElements = function () {

    this.tableHead =
        document.getElementById("associationTableHead");

    this.tableBody =
        document.getElementById("associationTableBody");

    this.minimumExpectedCell =
        document.getElementById("minimumExpectedCell");

    this.cellsBelowFiveCell =
        document.getElementById("cellsBelowFiveCell");

    this.percentBelowFiveCell =
        document.getElementById("percentBelowFiveCell");

    this.recommendedTestCell =
        document.getElementById("recommendedTestCell");

    this.interpretationBox =
        document.getElementById("interpretationBox");

    this.filtersAppliedText =
        document.getElementById("filtersAppliedText");

    this.selectedTest =
        document.getElementById("selectedTest");

    this.totalRecords =
        document.getElementById("totalRecords");

    this.reportGeneratedValue =
        document.getElementById("reportGeneratedValue");

    this.antibioticGroup =
        document.getElementById("antibioticGroup");

};


/* ==========================================================
   CACHE INDEPENDENT / DEPENDENT VARIABLE CONTROLS

   These are single-choice radio-button dropdowns, visually
   similar to district/block/sample type, but they are not
   part of FilterManager's fixed control set (their option
   lists come from a different part of the /association-options
   payload and have no "All" choice).
   ========================================================== */

AssociationTests.cacheVariableControls = function () {

    this.controls.independent =
        this.buildVariableControl("independentVariableFilter");

    this.controls.dependent =
        this.buildVariableControl("dependentVariableFilter");

};


AssociationTests.buildVariableControl = function (id) {

    const container =
        document.getElementById(id);

    if (!container)
        return null;

    const button =
        container.querySelector(".dropdown-button");

    const panel =
        container.querySelector(".dropdown-panel");

    if (!button || !panel)
        return null;

    return {

        container,

        button,

        panel,

        placeholder: button.textContent.trim()

    };

};


/* ==========================================================
   REGISTER EVENTS
   ========================================================== */

AssociationTests.registerEvents = function () {

    this.attachVariableEvents(
        this.controls.independent,
        "independent"
    );

    this.attachVariableEvents(
        this.controls.dependent,
        "dependent"
    );

    /* ----------------------------------------------
       Populate variable dropdowns whenever
       FilterManager loads /association-options
    ---------------------------------------------- */

    document.addEventListener(

        "filterOptionsLoaded",

        (event) => {

            this.populateVariableOptions(
                event.detail || {}
            );

        }

    );

    /* ----------------------------------------------
       Run Association Test
    ---------------------------------------------- */

    const generateButton =
        document.getElementById("generateReport");

    if (generateButton) {

        generateButton.addEventListener(

            "click",

            () => {

                this.runTest();

            }

        );

    }

    /* ----------------------------------------------
       Reset — clears variable selections and results
       (FilterManager's own listener on this same
       button independently resets the months, district,
       block, sample type, organisms and antibiotics)
    ---------------------------------------------- */

    const resetButton =
        document.getElementById("resetFilters");

    if (resetButton) {

        resetButton.addEventListener(

            "click",

            () => {

                this.resetVariables();

            }

        );

    }

    /* ----------------------------------------------
       Export placeholder
    ---------------------------------------------- */

    const exportButton =
        document.getElementById("exportAssociation");

    if (exportButton) {

        exportButton.addEventListener(

            "click",

            () => {

                if (typeof showMessage === "function") {

                    showMessage(
                        "Export is not available yet. This button is a placeholder.",
                        "info"
                    );

                }

            }

        );

    }

};


/* ==========================================================
   DROPDOWN OPEN / CLOSE (reuses FilterManager's
   closeAllPanels so outside-click and other dropdowns
   behave consistently across the page)
   ========================================================== */

AssociationTests.attachVariableEvents = function (control, key) {

    if (!control)
        return;

    control.button.addEventListener(

        "click",

        (event) => {

            event.stopPropagation();

            const isOpen =
                control.panel.classList.contains("show");

            FilterManager.closeAllPanels();

            if (!isOpen) {
                control.panel.classList.add("show");
            }

        }

    );

    control.panel.addEventListener(

        "click",

        (event) => {

            event.stopPropagation();

            /* NEW: clicking any option closes the dropdown, even
               when the option clicked is the one already selected
               (a "change" event does not fire in that case). */

            if (event.target.closest("label")) {

                setTimeout(() => {

                    control.panel.classList.remove("show");

                }, 0);

            }

        }

    );

    control.panel.addEventListener(

        "change",

        (event) => {

            if (event.target.type !== "radio")
                return;

            this.handleVariableSelection(
                key,
                control,
                event.target
            );

            /* NEW: close the dropdown as soon as a choice is made */

            control.panel.classList.remove("show");

        }

    );

};


/* ==========================================================
   POPULATE INDEPENDENT / DEPENDENT VARIABLE DROPDOWNS
   ========================================================== */

AssociationTests.populateVariableOptions = function (data) {

    this.independentVariables =
        data.independent_variables || [];

    this.dependentVariables =
        data.dependent_variables || [];

    this.populateVariableControl(
        this.controls.independent,
        this.independentVariables,
        "independent"
    );

    this.populateVariableControl(
        this.controls.dependent,
        this.dependentVariables,
        "dependent"
    );

};


AssociationTests.populateVariableControl = function (control, values, key) {

    if (!control)
        return;

    control.panel.innerHTML = "";

    values.forEach(value => {

        const label =
            document.createElement("label");

        const radio =
            document.createElement("input");

        radio.type = "radio";

        /* Grouping by name is what makes the browser itself
           enforce "only one selected" — selecting a new option
           automatically deselects the previous one. */

        radio.name = key + "VariableChoice";

        radio.value = value;

        radio.checked =
            (this.selected[key] === value);

        label.appendChild(radio);

        label.appendChild(

            document.createTextNode(

                this.formatLabel(value)

            )

        );

        control.panel.appendChild(label);

    });

    this.updateVariableButtonLabel(control, key);

};


/* ==========================================================
   SINGLE-CHOICE BEHAVIOUR FOR VARIABLE DROPDOWNS
   (radio buttons — exactly one selected, no "All" option)
   ========================================================== */

AssociationTests.handleVariableSelection = function (key, control, radio) {

    this.selected[key] =
        radio.checked ? radio.value : this.selected[key];

    this.updateVariableButtonLabel(control, key);

    if (key === "dependent") {
        this.updateAntibioticVisibility();
    }

};


AssociationTests.updateVariableButtonLabel = function (control, key) {

    if (!control)
        return;

    const value =
        this.selected[key];

    control.button.textContent =
        value ? this.formatLabel(value) : control.placeholder;

};


/* ==========================================================
   SHOW / HIDE ANTIBIOTIC FILTER

   The backend only ever tests one antibiotic at a time
   (the first non-"all" value sent), and only when the
   dependent variable is "antibiogram_susceptibility".
   ========================================================== */

AssociationTests.updateAntibioticVisibility = function () {

    if (!this.antibioticGroup)
        return;

    const needsAntibiotic =
        this.selected.dependent === "antibiogram_susceptibility";

    this.antibioticGroup.style.display =
        needsAntibiotic ? "" : "none";

};


/* ==========================================================
   RESET VARIABLE SELECTIONS + RESULTS
   ========================================================== */

AssociationTests.resetVariables = function () {

    this.selected = {

        independent: null,

        dependent: null

    };

    if (this.controls.independent) {

        this.controls.independent.button.textContent =
            this.controls.independent.placeholder;

        this.controls.independent.panel

            .querySelectorAll("input[type='radio']")

            .forEach(box => { box.checked = false; });

    }

    if (this.controls.dependent) {

        this.controls.dependent.button.textContent =
            this.controls.dependent.placeholder;

        this.controls.dependent.panel

            .querySelectorAll("input[type='radio']")

            .forEach(box => { box.checked = false; });

    }

    this.updateAntibioticVisibility();

    this.resetResults();

};


/* ==========================================================
   RUN ASSOCIATION TEST
   ========================================================== */

AssociationTests.runTest = async function () {

    if (!this.selected.independent || !this.selected.dependent) {

        if (typeof showMessage === "function") {

            showMessage(
                "Please select both an independent and a dependent variable.",
                "error"
            );

        }

        return;

    }

    const filters =
        FilterManager.getFilters();

    const payload = {

        /* NEW: time duration (month-year, "YYYY-MM" or "") */

        from_month: filters.from_month || "",

        to_month: filters.to_month || "",

        district: filters.district,

        block: filters.block,

        sample_type: filters.sample_type,

        organisms: filters.organisms,

        independent_variable: this.selected.independent,

        dependent_variable: this.selected.dependent,

        antibiotics: []

    };

    if (this.selected.dependent === "antibiogram_susceptibility") {

        const chosenAntibiotics =
            (filters.antibiotics || []).filter(

                antibiotic =>

                    String(antibiotic).trim().toLowerCase() !== "all"

            );

        if (chosenAntibiotics.length === 0) {

            if (typeof showMessage === "function") {

                showMessage(
                    "Please select an antibiotic.",
                    "error"
                );

            }

            return;

        }

        payload.antibiotics = chosenAntibiotics;

    }

    const result =
        await apiPost(this.endpoint, payload);

    if (!result) {

        this.resetResults();

        return;

    }

    this.render(result);

};


/* ==========================================================
   RENDER RESULTS
   ========================================================== */

AssociationTests.render = function (result) {

    this.lastResult = result;

    this.renderTable(result);

    this.renderAssumptions(result);

    this.renderInterpretation(result);

    this.updateInfoStrip(result);

};


/* ==========================================================
   FORMAT P-VALUE
   ========================================================== */

AssociationTests.formatPValue = function (value) {

    if (value === null || value === undefined)
        return "—";

    const number = Number(value);

    if (Number.isNaN(number))
        return "—";

    return number < 0.001 ? "<0.001" : number.toFixed(4);

};


/* ==========================================================
   RENDER CONTINGENCY TABLE
   (dynamic column header row + body + total row)
   ========================================================== */

AssociationTests.renderTable = function (result) {

    if (!this.tableHead || !this.tableBody)
        return;

    const rowKeys =
        Object.keys(result.row_totals || {});

    const columnKeys =
        Object.keys(result.column_totals || {});

    /* ---------------------------------------------
       Single header row:
       Variable | ...dependent categories... | Total |
       Test | Statistic | df | p-value
    --------------------------------------------- */

    this.tableHead.innerHTML = "";

    const headerRow =
        document.createElement("tr");

    headerRow.appendChild(
        this.createHeaderCell("Variable")
    );

    columnKeys.forEach(columnKey => {

        headerRow.appendChild(

            this.createHeaderCell(
                this.formatLabel(columnKey)
            )

        );

    });

    headerRow.appendChild(
        this.createHeaderCell("Total")
    );

    headerRow.appendChild(this.createHeaderCell("Test"));

    headerRow.appendChild(this.createHeaderCell("Statistic"));

    headerRow.appendChild(this.createHeaderCell("df"));

    headerRow.appendChild(this.createHeaderCell("p-value"));

    this.tableHead.appendChild(headerRow);

    /* ---------------------------------------------
       Body rows
    --------------------------------------------- */

    this.tableBody.innerHTML = "";

    if (rowKeys.length === 0 || columnKeys.length === 0) {

        const emptyRow =
            document.createElement("tr");

        const emptyCell =
            document.createElement("td");

        emptyCell.colSpan =
            columnKeys.length + 6;

        emptyCell.className = "table-empty";

        emptyCell.textContent =
            "No data available for the selected variables.";

        emptyRow.appendChild(emptyCell);

        this.tableBody.appendChild(emptyRow);

        return;

    }

    rowKeys.forEach((rowKey, index) => {

        const row =
            document.createElement("tr");

        const labelCell =
            document.createElement("td");

        labelCell.className = "row-label";

        labelCell.textContent =
            this.formatLabel(rowKey);

        row.appendChild(labelCell);

        columnKeys.forEach(columnKey => {

            const count =
                (result.contingency_table[columnKey] || {})[rowKey] ?? 0;

            const percentage =
                (result.row_percentages[columnKey] || {})[rowKey] ?? 0;

            row.appendChild(

                this.createDataCell(
                    this.formatCell(count, percentage)
                )

            );

        });

        row.appendChild(

            this.createDataCell(

                formatNumber(result.row_totals[rowKey])

            )

        );

        /* -----------------------------------------
           Test / Statistic / df / p-value are
           properties of the whole table, not any
           one category — write them once, on the
           first category row, spanning down over
           every category row via rowspan. They do
           NOT extend into the Total row below.
        ----------------------------------------- */

        if (index === 0) {

            const rowspanCount =
                rowKeys.length;

            row.appendChild(

                this.createStatCell(
                    result.test || "—",
                    rowspanCount
                )

            );

            row.appendChild(

                this.createStatCell(

                    (result.test_statistic === null ||
                     result.test_statistic === undefined)
                        ? "—"
                        : result.test_statistic,

                    rowspanCount

                )

            );

            row.appendChild(

                this.createStatCell(

                    (result.degrees_of_freedom === null ||
                     result.degrees_of_freedom === undefined)
                        ? "—"
                        : result.degrees_of_freedom,

                    rowspanCount

                )

            );

            row.appendChild(

                this.createStatCell(
                    this.formatPValue(result.p_value),
                    rowspanCount
                )

            );

        }

        this.tableBody.appendChild(row);

    });

    /* ---------------------------------------------
       Total row — no Test/Statistic/df/p-value
       cells; those columns stay blank here since
       the rowspan above only covers the category
       rows.
    --------------------------------------------- */

    const totalRow =
        document.createElement("tr");

    totalRow.className = "total-row";

    const totalLabelCell =
        document.createElement("td");

    totalLabelCell.textContent = "Total";

    totalRow.appendChild(totalLabelCell);

    const grandTotal =
        result.grand_total || 0;

    columnKeys.forEach(columnKey => {

        const columnTotal =
            result.column_totals[columnKey] || 0;

        const percentage =
            grandTotal > 0
                ? (columnTotal / grandTotal) * 100
                : 0;

        totalRow.appendChild(

            this.createDataCell(
                this.formatCell(columnTotal, percentage)
            )

        );

    });

    const grandTotalCell =
        document.createElement("td");

    grandTotalCell.textContent =
        formatNumber(grandTotal);

    totalRow.appendChild(grandTotalCell);

    this.tableBody.appendChild(totalRow);

};


/* ==========================================================
   TABLE CELL HELPERS
   ========================================================== */

AssociationTests.createHeaderCell = function (text) {

    const th =
        document.createElement("th");

    th.textContent = text;

    return th;

};


AssociationTests.createDataCell = function (text) {

    const td =
        document.createElement("td");

    td.className = "text-center";

    td.textContent = text;

    return td;

};


AssociationTests.createStatCell = function (text, rowspanCount) {

    const td =
        document.createElement("td");

    td.className = "text-center stat-cell";

    td.rowSpan = rowspanCount;

    td.textContent = text;

    return td;

};


AssociationTests.formatCell = function (count, percentage) {

    const safeCount =
        Number(count) || 0;

    const safePercentage =
        Number(percentage) || 0;

    return (

        formatNumber(safeCount) +
        " (" +
        safePercentage.toFixed(2) +
        "%)"

    );

};


/* ==========================================================
   ASSUMPTION CHECKS
   ========================================================== */

AssociationTests.renderAssumptions = function (result) {

    const assumptions =
        result.assumptions || {};

    if (this.minimumExpectedCell) {

        this.minimumExpectedCell.textContent =

            (assumptions.minimum_expected_frequency === null ||
             assumptions.minimum_expected_frequency === undefined)

                ? "—"
                : assumptions.minimum_expected_frequency;

    }

    if (this.cellsBelowFiveCell) {

        this.cellsBelowFiveCell.textContent =

            (assumptions.cells_with_expected_below_5 === null ||
             assumptions.cells_with_expected_below_5 === undefined)

                ? "—"
                : assumptions.cells_with_expected_below_5;

    }

    if (this.percentBelowFiveCell) {

        this.percentBelowFiveCell.textContent =

            (assumptions.percent_cells_with_expected_below_5 === null ||
             assumptions.percent_cells_with_expected_below_5 === undefined)

                ? "—"
                : assumptions.percent_cells_with_expected_below_5 + "%";

    }

    if (this.recommendedTestCell) {

        this.recommendedTestCell.textContent =
            result.test || "—";

    }

};


/* ==========================================================
   STATISTICAL INTERPRETATION
   ========================================================== */

AssociationTests.renderInterpretation = function (result) {

    if (!this.interpretationBox)
        return;

    const independentLabel =
        this.formatLabel(result.independent_variable);

    let dependentLabel =
        this.formatLabel(result.dependent_variable);

    if (result.selected_antibiotic) {

        dependentLabel +=

            " (" +
            this.formatLabel(result.selected_antibiotic) +
            ")";

    }

    const parts = [];

    parts.push(

        "A " + (result.test || "statistical") + " test was used to " +
        "assess the association between " + independentLabel +
        " and " + dependentLabel + "."

    );

    if (result.decision) {
        parts.push(result.decision);
    }

    if (result.p_value === null || result.p_value === undefined) {

        parts.push(

            "The p-value could not be computed" +
            (result.warning ? " (" + result.warning + ")." : ".")

        );

    }

    else {

        const isSignificant =
            Number(result.p_value) < 0.05;

        parts.push(

            "The result is " +
            (isSignificant ? "statistically significant" : "not statistically significant") +
            " at \u03B1 = 0.05 (p " +
            (isSignificant ? "< " : "= ") +
            this.formatPValue(result.p_value) +
            ")."

        );

        if (result.warning) {
            parts.push(result.warning);
        }

    }

    this.interpretationBox.textContent =
        parts.join(" ");

    this.interpretationBox.className =
        "message " + (result.warning ? "info" : "info");

};


/* ==========================================================
   FORMAT "YYYY-MM" AS "Jan 2025"   (NEW)
   ========================================================== */

AssociationTests.formatMonth = function (value) {

    if (!value)
        return "";

    const parts =
        String(value).split("-");

    if (parts.length !== 2)
        return String(value);

    const date =
        new Date(

            Number(parts[0]),

            Number(parts[1]) - 1,

            1

        );

    return date.toLocaleString(

        "en-GB",

        {

            month: "short",

            year: "numeric"

        }

    );

};


/* ==========================================================
   BUILD PERIOD TEXT   (NEW)
   ========================================================== */

AssociationTests.formatPeriod = function (filters) {

    if (filters.from_month && filters.to_month) {

        return (

            this.formatMonth(filters.from_month) +
            " \u2013 " +
            this.formatMonth(filters.to_month)

        );

    }

    if (filters.from_month) {

        return "From " + this.formatMonth(filters.from_month);

    }

    if (filters.to_month) {

        return "Up to " + this.formatMonth(filters.to_month);

    }

    return "All";

};


/* ==========================================================
   UPDATE INFO STRIP
   ========================================================== */

AssociationTests.updateInfoStrip = function (result) {

    if (this.filtersAppliedText) {

        const filters =
            FilterManager.getFilters();

        const organismsText =

            (!filters.organisms || filters.organisms.length === 0 ||
             (filters.organisms.length === 1 && filters.organisms[0] === "all"))

                ? "All"

                : filters.organisms.length + " selected";

        this.filtersAppliedText.textContent =

            "Period: " + this.formatPeriod(filters) +
            " | District: " + (filters.district || "All") +
            " | Block: " + (filters.block || "All") +
            " | Sample Type: " + (filters.sample_type || "All") +
            " | Organisms: " + organismsText;

    }

    if (this.selectedTest) {
        this.selectedTest.textContent = result.test || "Auto";
    }

    if (this.totalRecords) {

        this.totalRecords.textContent =
            formatNumber(result.total_records || 0);

    }

    if (this.reportGeneratedValue) {

        this.reportGeneratedValue.textContent =

            new Date().toLocaleString(

                "en-GB",

                {

                    day: "2-digit",

                    month: "short",

                    year: "numeric",

                    hour: "2-digit",

                    minute: "2-digit"

                }

            );

    }

};


/* ==========================================================
   RESET RESULTS DISPLAY
   ========================================================== */

AssociationTests.resetResults = function () {

    this.lastResult = null;

    if (this.tableHead) {
        this.tableHead.innerHTML = "";
    }

    if (this.tableBody) {
        this.tableBody.innerHTML = "";
    }

    ["minimumExpectedCell", "cellsBelowFiveCell",
     "percentBelowFiveCell", "recommendedTestCell"]

        .forEach(key => {

            if (this[key]) {
                this[key].textContent = "—";
            }

        });

    if (this.interpretationBox) {

        this.interpretationBox.textContent =
            "Run an association analysis to generate the statistical interpretation.";

        this.interpretationBox.className = "message info";

    }

    if (this.selectedTest) {
        this.selectedTest.textContent = "Auto";
    }

    if (this.totalRecords) {
        this.totalRecords.textContent = "—";
    }

    if (this.reportGeneratedValue) {
        this.reportGeneratedValue.textContent = "—";
    }

};


/* ==========================================================
   FORMAT VARIABLE / CATEGORY LABEL
   e.g. "age_group" -> "Age Group", "no growth" -> "No Growth"
   ========================================================== */

AssociationTests.formatLabel = function (value) {

    if (value === null || value === undefined || value === "")
        return "—";

    return String(value)

        .replace(/_/g, " ")

        .replace(/\b\w/g, character => character.toUpperCase());

};


/* ==========================================================
   EXPORT + BOOTSTRAP
   ========================================================== */

window.AssociationTests = AssociationTests;

document.addEventListener(

    "DOMContentLoaded",

    async function () {

        try {

            AssociationTests.initialize();

            if (typeof FilterManager !== "undefined") {

                FilterManager.endpoint = "/association-options";

                await FilterManager.initialise();

            }

        }

        catch (error) {

            console.error(error);

            if (typeof showMessage === "function") {

                showMessage(
                    "Failed to initialize Association Tests.",
                    "error"
                );

            }

        }

    }

);