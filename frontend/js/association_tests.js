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

    lastResult: null,

    perAntibioticContainer: null,

    /* ---------------------------------------------
       Custom age groups (only used when the
       independent variable is "age_group").
    --------------------------------------------- */

    customAgeGroups: null,

    ageGroupRows: [],

    AGE_GROUPS_MIN: 2,

    AGE_GROUPS_MAX: 5

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

    /* ---------------------------------------------
       Custom age-group UI elements
    --------------------------------------------- */

    this.customizeBtn =
        document.getElementById("customizeAgeGroupsBtn");

    this.agePanel =
        document.getElementById("customAgeGroupsPanel");

    this.ageRowsContainer =
        document.getElementById("ageGroupsRows");

    this.ageError =
        document.getElementById("customAgeGroupsError");

    this.addAgeGroupBtn =
        document.getElementById("addAgeGroupBtn");

    this.resetAgeGroupsBtn =
        document.getElementById("resetAgeGroupsBtn");

    this.applyAgeGroupsBtn =
        document.getElementById("applyAgeGroupsBtn");

};


/* ==========================================================
   CACHE INDEPENDENT / DEPENDENT VARIABLE CONTROLS
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
       Custom age-group UI
    ---------------------------------------------- */

    this.attachAgeGroupEvents();

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
   DROPDOWN OPEN / CLOSE
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
   SINGLE-CHOICE BEHAVIOUR
   ========================================================== */

AssociationTests.handleVariableSelection = function (key, control, radio) {

    this.selected[key] =
        radio.checked ? radio.value : this.selected[key];

    this.updateVariableButtonLabel(control, key);

    if (key === "dependent") {
        this.updateAntibioticVisibility();
    }

    if (key === "independent") {
        this.updateAgeGroupUI();
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

    this.customAgeGroups = null;

    this.ageGroupRows = [];

    this.updateAntibioticVisibility();

    this.updateAgeGroupUI();

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
                    "Please select at least one antibiotic.",
                    "error"
                );

            }

            return;

        }

        payload.antibiotics = chosenAntibiotics;

    }

    if (
        this.selected.independent === "age_group"
        &&
        this.customAgeGroups
        &&
        this.customAgeGroups.length > 0
    ) {

        payload.age_groups = this.customAgeGroups;

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

    if (
        result.antibiogram_mode === "multi"
        &&
        result.antibiotics
    ) {

        this.renderPerAntibioticResults(result);

    }

    else {

        this.clearPerAntibioticResults();

    }

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
   POPULATE TABLE ROWS (SHARED)
   ========================================================== */

AssociationTests.populateTableRows = function (result, thead, tbody) {

    const rowKeys =
        Object.keys(result.row_totals || {});

    const columnKeys =
        Object.keys(result.column_totals || {});

    thead.innerHTML = "";

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

    thead.appendChild(headerRow);

    tbody.innerHTML = "";

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

        tbody.appendChild(emptyRow);

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

        tbody.appendChild(row);

    });

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

    tbody.appendChild(totalRow);

};


/* ==========================================================
   RENDER CONTINGENCY TABLE (CUMULATIVE)
   ========================================================== */

AssociationTests.renderTable = function (result) {

    if (!this.tableHead || !this.tableBody)
        return;

    this.populateTableRows(
        result,
        this.tableHead,
        this.tableBody
    );

};


/* ==========================================================
   BUILD A STANDALONE CONTINGENCY TABLE ELEMENT
   ========================================================== */

AssociationTests.buildTableDOM = function (result) {

    const table =
        document.createElement("table");

    table.className = "summary-table";

    const thead =
        document.createElement("thead");

    const tbody =
        document.createElement("tbody");

    table.appendChild(thead);

    table.appendChild(tbody);

    this.populateTableRows(result, thead, tbody);

    return table;

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
   ASSUMPTION CHECKS (CUMULATIVE)
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
   BUILD A STANDALONE ASSUMPTIONS STRIP ELEMENT
   ========================================================== */

AssociationTests.buildAssumptionsDOM = function (result) {

    const assumptions =
        result.assumptions || {};

    const section =
        document.createElement("section");

    section.className = "info-strip";

    const items = [

        {
            label: "Minimum Expected Frequency",
            value:
                (assumptions.minimum_expected_frequency === null ||
                 assumptions.minimum_expected_frequency === undefined)
                    ? "—"
                    : assumptions.minimum_expected_frequency
        },

        {
            label: "Cells with Expected < 5",
            value:
                (assumptions.cells_with_expected_below_5 === null ||
                 assumptions.cells_with_expected_below_5 === undefined)
                    ? "—"
                    : assumptions.cells_with_expected_below_5
        },

        {
            label: "% Cells with Expected < 5",
            value:
                (assumptions.percent_cells_with_expected_below_5 === null ||
                 assumptions.percent_cells_with_expected_below_5 === undefined)
                    ? "—"
                    : assumptions.percent_cells_with_expected_below_5 + "%"
        },

        {
            label: "Recommended Test",
            value:
                result.test || "—"
        }

    ];

    items.forEach(item => {

        const stat =
            document.createElement("div");

        stat.className = "info-strip-stat";

        const label =
            document.createElement("div");

        label.className = "info-strip-label";

        label.textContent = item.label;

        const value =
            document.createElement("div");

        value.className = "info-strip-value";

        value.textContent = item.value;

        stat.appendChild(label);

        stat.appendChild(value);

        section.appendChild(stat);

    });

    return section;

};


/* ==========================================================
   BUILD INTERPRETATION TEXT (SHARED)
   ========================================================== */

AssociationTests.buildInterpretationText = function (
    result,
    selectedAntibiotic
) {

    const independentLabel =
        this.formatLabel(result.independent_variable);

    let dependentLabel =
        this.formatLabel(result.dependent_variable);

    const antibiotic =
        selectedAntibiotic || result.selected_antibiotic;

    if (antibiotic) {

        dependentLabel +=

            " (" +
            this.formatLabel(antibiotic) +
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

    return {

        text: parts.join(" "),

        className: "message info"

    };

};


/* ==========================================================
   STATISTICAL INTERPRETATION (CUMULATIVE)
   ========================================================== */

AssociationTests.renderInterpretation = function (result) {

    if (!this.interpretationBox)
        return;

    const built =
        this.buildInterpretationText(result);

    this.interpretationBox.textContent =
        built.text;

    this.interpretationBox.className =
        built.className;

};


/* ==========================================================
   PER-ANTIBIOTIC RESULTS CONTAINER
   ========================================================== */

AssociationTests.ensurePerAntibioticContainer = function () {

    if (this.perAntibioticContainer)
        return this.perAntibioticContainer;

    let container =
        document.getElementById("perAntibioticResults");

    if (!container) {

        container =
            document.createElement("div");

        container.id = "perAntibioticResults";

        let anchor = null;

        if (this.interpretationBox) {

            anchor =
                this.interpretationBox.closest(".report-card")
                || this.interpretationBox.parentElement;

        }

        if (anchor && anchor.parentElement) {

            anchor.parentElement.insertBefore(
                container,
                anchor.nextSibling
            );

        }

        else {

            const contentArea =
                document.querySelector(".content-area")
                || document.body;

            contentArea.appendChild(container);

        }

    }

    this.perAntibioticContainer = container;

    return container;

};


AssociationTests.clearPerAntibioticResults = function () {

    const container =
        this.ensurePerAntibioticContainer();

    if (container) {

        container.innerHTML = "";

    }

};


/* ==========================================================
   RENDER PER-ANTIBIOTIC RESULTS
   ========================================================== */

AssociationTests.renderPerAntibioticResults = function (result) {

    const container =
        this.ensurePerAntibioticContainer();

    if (!container)
        return;

    container.innerHTML = "";

    if (result.pooled_warning) {

        const warning =
            document.createElement("div");

        warning.className = "message info";

        warning.style.marginBottom = "16px";

        warning.textContent = result.pooled_warning;

        container.appendChild(warning);

    }

    const antibioticEntries =
        Object.entries(result.antibiotics || {});

    if (antibioticEntries.length === 0) {

        return;

    }

    const header =
        document.createElement("header");

    header.className = "topbar";

    header.style.marginBottom = "12px";

    const heading =
        document.createElement("h2");

    heading.textContent =
        "Per-Antibiotic Results";

    const subtitle =
        document.createElement("p");

    subtitle.textContent =
        "Individual association tests for each selected antibiotic";

    header.appendChild(heading);

    header.appendChild(subtitle);

    container.appendChild(header);

    antibioticEntries.forEach(([antibiotic, entry]) => {

        const card =
            document.createElement("section");

        card.className = "report-card";

        const cardHeader =
            document.createElement("div");

        cardHeader.className = "card-header";

        const cardTitle =
            document.createElement("h3");

        cardTitle.textContent =
            this.formatLabel(antibiotic);

        cardHeader.appendChild(cardTitle);

        card.appendChild(cardHeader);

        if (entry.error) {

            const errorBox =
                document.createElement("div");

            errorBox.className = "message error";

            errorBox.textContent = entry.error;

            card.appendChild(errorBox);

            container.appendChild(card);

            return;

        }

        const mergedEntry = {

            ...entry,

            independent_variable: result.independent_variable,

            dependent_variable: result.dependent_variable

        };

        const tableWrapper =
            document.createElement("div");

        tableWrapper.className = "table-container";

        tableWrapper.appendChild(
            this.buildTableDOM(mergedEntry)
        );

        card.appendChild(tableWrapper);

        card.appendChild(
            this.buildAssumptionsDOM(mergedEntry)
        );

        const interpretation =
            this.buildInterpretationText(
                mergedEntry,
                antibiotic
            );

        const interpretationDiv =
            document.createElement("div");

        interpretationDiv.className =
            interpretation.className;

        interpretationDiv.textContent =
            interpretation.text;

        card.appendChild(interpretationDiv);

        container.appendChild(card);

    });

};


/* ==========================================================
   FORMAT "YYYY-MM" AS "Jan 2025"
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
   BUILD PERIOD TEXT
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

    this.clearPerAntibioticResults();

};


/* ==========================================================
   FORMAT VARIABLE / CATEGORY LABEL
   ========================================================== */

AssociationTests.formatLabel = function (value) {

    if (value === null || value === undefined || value === "")
        return "—";

    return String(value)

        .replace(/_/g, " ")

        .replace(/\b\w/g, character => character.toUpperCase());

};


/* ==========================================================
   CUSTOM AGE GROUPS — EVENT WIRING
   ========================================================== */

AssociationTests.attachAgeGroupEvents = function () {

    if (this.customizeBtn) {

        this.customizeBtn.addEventListener("click", () => {

            if (!this.agePanel)
                return;

            if (this.agePanel.style.display === "none") {
                this.openAgeGroupPanel();
            }

            else {
                this.closeAgeGroupPanel();
            }

        });

    }

    if (this.addAgeGroupBtn) {

        this.addAgeGroupBtn.addEventListener("click", () => {

            if (this.ageGroupRows.length >= this.AGE_GROUPS_MAX)
                return;

            const last =
                this.ageGroupRows[this.ageGroupRows.length - 1];

            const nextMin =
                (last ? last.max : 0) + 1;

            this.ageGroupRows.push({
                min: nextMin,
                max: nextMin + 30
            });

            this.renderAgeGroupRows();

        });

    }

    if (this.resetAgeGroupsBtn) {

        this.resetAgeGroupsBtn.addEventListener(
            "click",
            () => this.handleResetAgeGroups()
        );

    }

    if (this.applyAgeGroupsBtn) {

        this.applyAgeGroupsBtn.addEventListener(
            "click",
            () => this.handleApplyAgeGroups()
        );

    }

};


/* ==========================================================
   CUSTOM AGE GROUPS — DEFAULT ROWS
   Matches the backend's default bins (<30 / 30-60 / >60).
   ========================================================== */

AssociationTests.defaultAgeGroupRows = function () {

    return [
        { min: 0,  max: 29  },
        { min: 30, max: 60  },
        { min: 61, max: 150 }
    ];

};


/* ==========================================================
   CUSTOM AGE GROUPS — BUTTON VISIBILITY
   ========================================================== */

AssociationTests.updateAgeGroupUI = function () {

    const needsCustomization =
        this.selected.independent === "age_group";

    if (this.customizeBtn) {

        this.customizeBtn.style.display =
            needsCustomization ? "" : "none";

    }

    if (!needsCustomization && this.agePanel) {

        this.agePanel.style.display = "none";

    }

    this.updateCustomizeButtonLabel();

};


AssociationTests.updateCustomizeButtonLabel = function () {

    if (!this.customizeBtn)
        return;

    if (
        this.customAgeGroups
        &&
        this.customAgeGroups.length > 0
    ) {

        this.customizeBtn.textContent =
            `Age Groups: Custom (${this.customAgeGroups.length}) — Edit`;

    }

    else {

        this.customizeBtn.textContent =
            "Customize Age Groups";

    }

};


/* ==========================================================
   CUSTOM AGE GROUPS — PANEL OPEN / CLOSE
   ========================================================== */

AssociationTests.openAgeGroupPanel = function () {

    if (!this.agePanel)
        return;

    this.ageGroupRows =
        this.customAgeGroups
            ? this.customAgeGroups.map(
                group => ({ min: group.min, max: group.max })
              )
            : this.defaultAgeGroupRows();

    this.renderAgeGroupRows();

    this.clearAgeGroupError();

    this.agePanel.style.display = "";

};


AssociationTests.closeAgeGroupPanel = function () {

    if (this.agePanel)
        this.agePanel.style.display = "none";

};


/* ==========================================================
   CUSTOM AGE GROUPS — RENDER ROWS
   ========================================================== */

AssociationTests.renderAgeGroupRows = function () {

    if (!this.ageRowsContainer)
        return;

    this.ageRowsContainer.innerHTML = "";

    this.ageGroupRows.forEach((row, index) => {

        const rowEl =
            document.createElement("div");

        rowEl.style.display = "flex";
        rowEl.style.alignItems = "center";
        rowEl.style.gap = "8px";
        rowEl.style.marginBottom = "8px";

        const label =
            document.createElement("span");

        label.textContent = `Group ${index + 1}`;
        label.style.minWidth = "70px";
        label.style.fontWeight = "500";

        rowEl.appendChild(label);

        const minInput =
            document.createElement("input");

        minInput.type = "number";
        minInput.min = "0";
        minInput.step = "1";
        minInput.value = row.min;
        minInput.placeholder = "Min";
        minInput.className = "month-input";
        minInput.style.maxWidth = "100px";

        minInput.addEventListener("input", () => {

            const parsed = parseInt(minInput.value, 10);

            this.ageGroupRows[index].min =
                Number.isFinite(parsed) ? parsed : 0;

        });

        rowEl.appendChild(minInput);

        const sep =
            document.createElement("span");

        sep.textContent = "to";

        rowEl.appendChild(sep);

        const maxInput =
            document.createElement("input");

        maxInput.type = "number";
        maxInput.min = "1";
        maxInput.step = "1";
        maxInput.value = row.max;
        maxInput.placeholder = "Max";
        maxInput.className = "month-input";
        maxInput.style.maxWidth = "100px";

        maxInput.addEventListener("input", () => {

            const parsed = parseInt(maxInput.value, 10);

            this.ageGroupRows[index].max =
                Number.isFinite(parsed) ? parsed : 0;

        });

        rowEl.appendChild(maxInput);

        const removeBtn =
            document.createElement("button");

        removeBtn.type = "button";
        removeBtn.className = "secondary-button";
        removeBtn.textContent = "×";
        removeBtn.style.padding = "4px 10px";
        removeBtn.disabled =
            this.ageGroupRows.length <= this.AGE_GROUPS_MIN;

        removeBtn.addEventListener("click", () => {

            this.ageGroupRows.splice(index, 1);

            this.renderAgeGroupRows();

        });

        rowEl.appendChild(removeBtn);

        this.ageRowsContainer.appendChild(rowEl);

    });

    if (this.addAgeGroupBtn) {

        this.addAgeGroupBtn.disabled =
            this.ageGroupRows.length >= this.AGE_GROUPS_MAX;

    }

};


/* ==========================================================
   CUSTOM AGE GROUPS — ERROR DISPLAY
   ========================================================== */

AssociationTests.showAgeGroupError = function (message) {

    if (!this.ageError)
        return;

    this.ageError.textContent = message;

    this.ageError.style.display = "";

};


AssociationTests.clearAgeGroupError = function () {

    if (!this.ageError)
        return;

    this.ageError.textContent = "";

    this.ageError.style.display = "none";

};


/* ==========================================================
   CUSTOM AGE GROUPS — VALIDATION
   ========================================================== */

AssociationTests.validateAgeGroupRows = function () {

    if (this.ageGroupRows.length < this.AGE_GROUPS_MIN) {

        return (
            `At least ${this.AGE_GROUPS_MIN} age groups are required.`
        );

    }

    if (this.ageGroupRows.length > this.AGE_GROUPS_MAX) {

        return (
            `At most ${this.AGE_GROUPS_MAX} age groups are allowed.`
        );

    }

    for (let i = 0; i < this.ageGroupRows.length; i++) {

        const { min, max } = this.ageGroupRows[i];

        if (min < 0) {

            return (
                `Group ${i + 1}: minimum cannot be negative.`
            );

        }

        if (min >= max) {

            return (
                `Group ${i + 1}: minimum must be less than maximum.`
            );

        }

    }

    for (let i = 0; i < this.ageGroupRows.length - 1; i++) {

        if (this.ageGroupRows[i].max + 1 !== this.ageGroupRows[i + 1].min) {

            return (
                `Group ${i + 1} ends at ${this.ageGroupRows[i].max}, ` +
                `but Group ${i + 2} starts at ${this.ageGroupRows[i + 1].min}. ` +
                `Groups must be contiguous (no gaps, no overlaps).`
            );

        }

    }

    return null;

};


/* ==========================================================
   CUSTOM AGE GROUPS — APPLY / RESET
   ========================================================== */

AssociationTests.handleApplyAgeGroups = function () {

    this.clearAgeGroupError();

    const error =
        this.validateAgeGroupRows();

    if (error) {

        this.showAgeGroupError(error);

        return;

    }

    this.customAgeGroups =
        this.ageGroupRows.map(
            group => ({ min: group.min, max: group.max })
        );

    this.updateCustomizeButtonLabel();

    this.closeAgeGroupPanel();

};


AssociationTests.handleResetAgeGroups = function () {

    this.customAgeGroups = null;

    this.ageGroupRows = [];

    this.updateCustomizeButtonLabel();

    this.clearAgeGroupError();

    this.closeAgeGroupPanel();

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