/* ==========================================================
   AMSP — REGRESSION ANALYSIS
   ========================================================== */

"use strict";


/* ==========================================================
   REGRESSION OBJECT
   ========================================================== */

const Regression = {

    endpoint: "/regression",

    optionsEndpoint: "/regression-options",

    independentVariables: [],

    dependentVariables: [],

    antibiotics: [],

    excludedPredictorMap: {},

    maxIndependentVariables: 8,

    modelType: null,  // binary_logistic, multinomial_logistic, ordinal_logistic

    selected: {

        independent: [],

        dependent: null,

        antibiotics: []

    },

    controls: {

        independent: null,

        dependent: null,

        antibiotic: null

    },

    lastResult: null,

    /* ---------------------------------------------
       Custom age groups (only used when
       "age_group" is among the selected
       independent variables).
    --------------------------------------------- */

    customAgeGroups: null,

    ageGroupRows: [],

    AGE_GROUPS_MIN: 2,

    AGE_GROUPS_MAX: 5

};


/* ==========================================================
   INITIALIZE
   ========================================================== */

Regression.initialize = function () {

    this.cacheElements();

    this.cacheVariableControls();

    this.registerEvents();

    // Initially hide antibiotic group
    const antibioticGroup = document.getElementById("antibioticGroup");
    if (antibioticGroup) {
        antibioticGroup.style.display = "none";
    }

    // Ensure custom age-group UI starts in the correct state
    this.updateAgeGroupUI();

};


/* ==========================================================
   CACHE STATIC RESULT ELEMENTS
   ========================================================== */

Regression.cacheElements = function () {

    this.tableHead =
        document.getElementById("regressionTableHead");

    this.tableBody =
        document.getElementById("regressionTableBody");

    // Model fit strip
    this.pseudoRSquaredCell =
        document.getElementById("pseudoRSquaredCell");

    this.aicSummaryCell =
        document.getElementById("aicSummaryCell");

    this.bicSummaryCell =
        document.getElementById("bicSummaryCell");

    this.logLikelihoodCell =
        document.getElementById("logLikelihoodCell");

    this.nObservationsCell =
        document.getElementById("nObservationsCell");

    this.convergedCell =
        document.getElementById("convergedCell");

    // Diagnostics
    this.logLikelihoodDetailCell =
        document.getElementById("logLikelihoodDetailCell");

    this.nullLogLikelihoodCell =
        document.getElementById("nullLogLikelihoodCell");

    this.likelihoodRatioCell =
        document.getElementById("likelihoodRatioCell");

    this.aicCell =
        document.getElementById("aicCell");

    this.bicCell =
        document.getElementById("bicCell");

    this.pseudoRSquaredDetailCell =
        document.getElementById("pseudoRSquaredDetailCell");

    this.convergenceStatusCell =
        document.getElementById("convergenceStatusCell");

    this.conditionNumberCell =
        document.getElementById("conditionNumberCell");

    // Outcome distribution
    this.outcomeDistributionBody =
        document.getElementById("outcomeDistributionBody");

    // Binary classification
    this.classificationSection =
        document.getElementById("classificationSection");

    this.accuracyCell =
        document.getElementById("accuracyCell");

    this.sensitivityCell =
        document.getElementById("sensitivityCell");

    this.specificityCell =
        document.getElementById("specificityCell");

    this.precisionCell =
        document.getElementById("precisionCell");

    this.f1ScoreCell =
        document.getElementById("f1ScoreCell");

    this.tnCell = document.getElementById("tnCell");
    this.fpCell = document.getElementById("fpCell");
    this.fnCell = document.getElementById("fnCell");
    this.tpCell = document.getElementById("tpCell");

    // Multinomial classification
    this.multinomialClassificationSection =
        document.getElementById("multinomialClassificationSection");

    this.multinomialAccuracyCell =
        document.getElementById("multinomialAccuracyCell");

    this.confusionMatrixHead =
        document.getElementById("confusionMatrixHead");

    this.confusionMatrixBody =
        document.getElementById("confusionMatrixBody");

    // Hosmer-Lemeshow
    this.hosmerLemeshowSection =
        document.getElementById("hosmerLemeshowSection");

    this.hlChiSquareCell =
        document.getElementById("hlChiSquareCell");

    this.hlDFCell =
        document.getElementById("hlDFCell");

    this.hlPValueCell =
        document.getElementById("hlPValueCell");

    this.hlInterpretationCell =
        document.getElementById("hlInterpretationCell");

    // Proportional odds
    this.proportionalOddsSection =
        document.getElementById("proportionalOddsSection");

    this.proportionalOddsContent =
        document.getElementById("proportionalOddsContent");

    // VIF
    this.vifSection =
        document.getElementById("vifSection");

    this.vifTableBody =
        document.getElementById("vifTableBody");

    // Interpretation
    this.interpretationBox =
        document.getElementById("interpretationBox");

    // Info strip
    this.filtersAppliedText =
        document.getElementById("filtersAppliedText");

    this.modelTypeDisplay =
        document.getElementById("modelTypeDisplay");

    this.totalRecords =
        document.getElementById("totalRecords");

    this.reportGeneratedValue =
        document.getElementById("reportGeneratedValue");

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

    /* ---------------------------------------------
       Per-antibiotic results container
    --------------------------------------------- */

    this.perAntibioticResults =
        document.getElementById("perAntibioticRegressionResults");

};


/* ==========================================================
   CACHE VARIABLE CONTROLS
   ========================================================== */

Regression.cacheVariableControls = function () {

    this.controls.independent =
        this.buildVariableControl("independentVariablesFilter");

    this.controls.dependent =
        this.buildVariableControl("dependentVariableFilter");

    this.controls.antibiotic =
        this.buildVariableControl("antibioticFilter");

};


Regression.buildVariableControl = function (id) {

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

Regression.registerEvents = function () {

    this.attachToggle(this.controls.independent);

    this.attachToggle(this.controls.dependent);

    this.attachToggle(this.controls.antibiotic);

    if (this.controls.independent) {

        this.controls.independent.panel.addEventListener(

            "change",

            (event) => {

                if (event.target.type !== "checkbox")
                    return;

                this.handleIndependentSelection(
                    event.target
                );

            }

        );

    }

    if (this.controls.dependent) {

        this.controls.dependent.panel.addEventListener(

            "change",

            (event) => {

                if (event.target.type !== "radio")
                    return;

                this.handleDependentSelection(
                    event.target
                );

                this.controls.dependent.panel.classList.remove("show");

            }

        );

    }

    if (this.controls.antibiotic) {

        this.controls.antibiotic.panel.addEventListener(

            "change",

            (event) => {

                if (event.target.type !== "checkbox")
                    return;

                this.handleAntibioticSelection(
                    event.target
                );

            }

        );

    }

    /* ----------------------------------------------
       Custom age-group UI
    ---------------------------------------------- */

    this.attachAgeGroupEvents();

    /* ----------------------------------------------
       Populate variable dropdowns whenever
       FilterManager loads /regression-options
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
       Run Regression
    ---------------------------------------------- */

    const generateButton =
        document.getElementById("generateReport");

    if (generateButton) {

        generateButton.addEventListener(

            "click",

            () => {

                this.runRegression();

            }

        );

    }

    /* ----------------------------------------------
       Reset
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
       Export
    ---------------------------------------------- */

    const exportButton =
        document.getElementById("exportRegression");

    if (exportButton) {

        exportButton.addEventListener(

            "click",

            () => {

                this.exportTable();

            }

        );

    }

};


/* ==========================================================
   DROPDOWN TOGGLE
   ========================================================== */

Regression.attachToggle = function (control) {

    if (!control)
        return;

    control.button.addEventListener(

        "click",

        (event) => {

            event.stopPropagation();

            const isOpen =
                control.panel.classList.contains("show");

            if (typeof FilterManager !== "undefined" &&
                typeof FilterManager.closeAllPanels === "function") {

                FilterManager.closeAllPanels();

            }

            if (!isOpen) {
                control.panel.classList.add("show");
            }

        }

    );

    control.panel.addEventListener(

        "click",

        (event) => {

            event.stopPropagation();

            /* Single-choice dropdowns (dependent variable) close
               on any option click. Multi-select dropdowns
               (independent variables, antibiotics) stay open. */

            if (
                control !== this.controls.independent &&
                control !== this.controls.antibiotic &&
                event.target.closest("label")
            ) {

                setTimeout(() => {

                    control.panel.classList.remove("show");

                }, 0);

            }

        }

    );

};


/* ==========================================================
   POPULATE VARIABLE DROPDOWNS
   ========================================================== */

Regression.populateVariableOptions = function (data) {

    this.independentVariables =
        data.independent_variables || [];

    this.dependentVariables =
        data.dependent_variables || [];

    this.excludedPredictorMap =
        data.excluded_predictor_map || {};

    this.maxIndependentVariables =
        data.max_independent_variables || 8;

    this.antibiotics = data.antibiotics || [];

    this.populateIndependentControl();

    this.populateDependentControl();

    this.populateAntibioticControl();

};


Regression.populateIndependentControl = function () {

    const control =
        this.controls.independent;

    if (!control)
        return;

    control.panel.innerHTML = "";

    this.independentVariables.forEach(value => {

        const label =
            document.createElement("label");

        const checkbox =
            document.createElement("input");

        checkbox.type = "checkbox";

        checkbox.value = value;

        checkbox.checked =
            this.selected.independent.includes(value);

        label.appendChild(checkbox);

        label.appendChild(

            document.createTextNode(

                this.formatLabel(value)

            )

        );

        control.panel.appendChild(label);

    });

    this.applyPredictorExclusions();

    this.updateIndependentButtonLabel();

    this.updateAgeGroupUI();

};


Regression.populateDependentControl = function () {

    const control =
        this.controls.dependent;

    if (!control)
        return;

    control.panel.innerHTML = "";

    this.dependentVariables.forEach(value => {

        const label =
            document.createElement("label");

        const radio =
            document.createElement("input");

        radio.type = "radio";

        radio.name = "dependentVariableChoice";

        radio.value = value;

        radio.checked =
            (this.selected.dependent === value);

        label.appendChild(radio);

        label.appendChild(

            document.createTextNode(

                this.formatLabel(value)

            )

        );

        control.panel.appendChild(label);

    });

    this.updateDependentButtonLabel();

};


Regression.populateAntibioticControl = function () {

    const control =
        this.controls.antibiotic;

    if (!control)
        return;

    control.panel.innerHTML = "";

    if (!this.antibiotics || this.antibiotics.length === 0) {
        const label = document.createElement("label");
        label.textContent = "No antibiotics available";
        label.style.color = "#94a3b8";
        control.panel.appendChild(label);
        return;
    }

    // Filter antibiotics - exclude "all" if present
    const antibioticList = this.antibiotics.filter(a => a !== "all");

    if (antibioticList.length === 0) {
        const label = document.createElement("label");
        label.textContent = "No antibiotics available";
        label.style.color = "#94a3b8";
        control.panel.appendChild(label);
        return;
    }

    antibioticList.forEach(value => {

        const label =
            document.createElement("label");

        const checkbox =
            document.createElement("input");

        checkbox.type = "checkbox";

        checkbox.value = value;

        checkbox.checked =
            this.selected.antibiotics.includes(value);

        label.appendChild(checkbox);

        label.appendChild(

            document.createTextNode(

                this.formatLabel(value)

            )

        );

        control.panel.appendChild(label);

    });

    this.updateAntibioticButtonLabel();

};


/* ==========================================================
   INDEPENDENT VARIABLE SELECTION
   ========================================================== */

Regression.handleIndependentSelection = function (checkbox) {

    const value =
        checkbox.value;

    if (checkbox.checked) {

        if (this.selected.independent.length >=
            this.maxIndependentVariables) {

            checkbox.checked = false;

            if (typeof showMessage === "function") {

                showMessage(

                    "You can select up to " +
                    this.maxIndependentVariables +
                    " independent variables.",

                    "error"

                );

            }

            return;

        }

        this.selected.independent.push(value);

    }

    else {

        this.selected.independent =
            this.selected.independent.filter(

                variable => variable !== value

            );

    }

    this.updateIndependentButtonLabel();

    this.updateAgeGroupUI();

};


Regression.updateIndependentButtonLabel = function () {

    const control =
        this.controls.independent;

    if (!control)
        return;

    const count =
        this.selected.independent.length;

    if (count === 0) {

        control.button.textContent =
            control.placeholder;

    }

    else if (count <= 2) {

        control.button.textContent =

            this.selected.independent

                .map(value => this.formatLabel(value))

                .join(", ");

    }

    else {

        control.button.textContent =
            count + " selected";

    }

};


/* ==========================================================
   DEPENDENT VARIABLE SELECTION
   ========================================================== */

Regression.handleDependentSelection = function (radio) {

    if (!radio.checked) return;

    this.selected.dependent = radio.value;

    this.updateDependentButtonLabel();

    this.applyPredictorExclusions();

    this.handleAntibioticVisibility();

};


Regression.updateDependentButtonLabel = function () {

    const control =
        this.controls.dependent;

    if (!control)
        return;

    control.button.textContent =

        this.selected.dependent
            ? this.formatLabel(this.selected.dependent)
            : control.placeholder;

};


/* ==========================================================
   ANTIBIOTIC SELECTION (MULTI-SELECT)
   ========================================================== */

Regression.handleAntibioticSelection = function (checkbox) {

    const value =
        checkbox.value;

    if (checkbox.checked) {

        if (!this.selected.antibiotics.includes(value)) {

            this.selected.antibiotics.push(value);

        }

    }

    else {

        this.selected.antibiotics =
            this.selected.antibiotics.filter(

                a => a !== value

            );

    }

    this.updateAntibioticButtonLabel();

};


Regression.updateAntibioticButtonLabel = function () {

    const control =
        this.controls.antibiotic;

    if (!control)
        return;

    const count =
        this.selected.antibiotics.length;

    if (count === 0) {

        control.button.textContent =
            "Select Antibiotics";

    }

    else if (count === 1) {

        control.button.textContent =
            this.formatLabel(this.selected.antibiotics[0]);

    }

    else {

        control.button.textContent =
            count + " selected";

    }

};


Regression.handleAntibioticVisibility = function () {

    const group = document.getElementById("antibioticGroup");

    if (!group) return;

    // Show antibiotic selector only for antibiogram_susceptibility
    if (this.selected.dependent === "antibiogram_susceptibility") {

        group.style.display = "block";

        // Reset antibiotic selection when showing
        if (this.controls.antibiotic) {

            this.selected.antibiotics = [];

            this.updateAntibioticButtonLabel();

            const checkboxes = this.controls.antibiotic.panel.querySelectorAll("input[type='checkbox']");

            checkboxes.forEach(c => c.checked = false);

        }

    } else {

        group.style.display = "none";

        this.selected.antibiotics = [];

    }

};


/* ==========================================================
   PREDICTOR EXCLUSIONS
   ========================================================== */

Regression.applyPredictorExclusions = function () {

    const control =
        this.controls.independent;

    if (!control)
        return;

    const excluded =
        this.excludedPredictorMap[this.selected.dependent] || [];

    const removed = [];

    const checkboxes =
        Array.from(
            control.panel.querySelectorAll("input[type='checkbox']")
        );

    checkboxes.forEach(checkbox => {

        const label =
            checkbox.closest("label");

        const isExcluded =
            excluded.includes(checkbox.value);

        if (isExcluded) {

            if (checkbox.checked) {

                checkbox.checked = false;

                this.selected.independent =
                    this.selected.independent.filter(

                        variable => variable !== checkbox.value

                    );

                removed.push(checkbox.value);

            }

            checkbox.disabled = true;

            if (label) {

                label.classList.add("disabled-option");

                label.title =

                    "Not available as a predictor for '" +
                    this.formatLabel(this.selected.dependent) +
                    "'.";

            }

        }

        else {

            checkbox.disabled = false;

            if (label) {

                label.classList.remove("disabled-option");

                label.removeAttribute("title");

            }

        }

    });

    if (removed.length > 0) {

        this.updateIndependentButtonLabel();

        this.updateAgeGroupUI();

        if (typeof showMessage === "function") {

            showMessage(

                "Removed " +
                removed.map(value => this.formatLabel(value)).join(", ") +
                " from the selected predictors.",

                "info"

            );

        }

    }

};


/* ==========================================================
   RESET
   ========================================================== */

Regression.resetVariables = function () {

    this.selected = {

        independent: [],

        dependent: null,

        antibiotics: []

    };

    this.modelType = null;

    this.customAgeGroups = null;

    this.ageGroupRows = [];

    if (this.controls.independent) {

        this.controls.independent.button.textContent =
            this.controls.independent.placeholder;

        this.controls.independent.panel

            .querySelectorAll("input[type='checkbox']")

            .forEach(box => {

                box.checked = false;

                box.disabled = false;

                const label = box.closest("label");

                if (label) {

                    label.classList.remove("disabled-option");
                    label.removeAttribute("title");

                }

            });

    }

    if (this.controls.dependent) {

        this.controls.dependent.button.textContent =
            this.controls.dependent.placeholder;

        this.controls.dependent.panel

            .querySelectorAll("input[type='radio']")

            .forEach(box => { box.checked = false; });

    }

    if (this.controls.antibiotic) {

        this.controls.antibiotic.button.textContent =
            "Select Antibiotics";

        this.controls.antibiotic.panel

            .querySelectorAll("input[type='checkbox']")

            .forEach(box => { box.checked = false; });

    }

    // Hide antibiotic group
    const group = document.getElementById("antibioticGroup");
    if (group) {
        group.style.display = "none";
    }

    // Reset custom age-group UI
    this.closeAgeGroupPanel();

    this.clearAgeGroupError();

    this.updateAgeGroupUI();

    this.resetResults();

};


/* ==========================================================
   RUN REGRESSION
   ========================================================== */

Regression.runRegression = async function () {

    if (this.selected.independent.length === 0 ||
        !this.selected.dependent) {

        if (typeof showMessage === "function") {

            showMessage(
                "Please select at least one independent variable and a dependent variable.",
                "error"
            );

        }

        return;
    }

    // Check if antibiotic is required
    if (this.selected.dependent === "antibiogram_susceptibility" &&
        this.selected.antibiotics.length === 0) {

        if (typeof showMessage === "function") {

            showMessage(
                "Please select at least one antibiotic for antibiogram regression.",
                "error"
            );

        }

        return;
    }

    const filters =
        typeof FilterManager !== "undefined" && FilterManager.getFilters
            ? FilterManager.getFilters()
            : {
                from_month: "",
                to_month: "",
                district: "all",
                block: "all",
                sample_type: "all",
                organisms: []
            };

    const payload = {

        from_month: filters.from_month || "",

        to_month: filters.to_month || "",

        district: filters.district || "all",

        block: filters.block || "all",

        sample_type: filters.sample_type || "all",

        organisms: filters.organisms || [],

        independent_variables: this.selected.independent,

        dependent_variable: this.selected.dependent,

        antibiotics: this.selected.antibiotics

    };

    /* ---------------------------------------------
       CUSTOM AGE GROUPS
       Send age_groups only when age_group is among
       the selected predictors AND the user has
       applied custom bins.
    --------------------------------------------- */

    if (
        this.selected.independent.includes("age_group")
        &&
        this.customAgeGroups
        &&
        this.customAgeGroups.length > 0
    ) {

        payload.age_groups = this.customAgeGroups;

    }

    if (typeof showLoading === "function") {
        showLoading(true);
    }

    try {

        const result =
            await apiPost(this.endpoint, payload);

        if (!result) {

            this.resetResults();
            return;

        }

        this.render(result);

    } catch (error) {

        console.error(error);

        if (typeof showMessage === "function") {

            showMessage(
                "Regression analysis failed: " + (error.message || "Unknown error"),
                "error"
            );

        }

    } finally {

        if (typeof showLoading === "function") {
            showLoading(false);
        }

    }

};


/* ==========================================================
   RENDER RESULTS
   ========================================================== */

/* ==========================================================
   UPDATE SINGLE-RESULT TABLE HEADING
   ========================================================== */

Regression.updateSingleResultTableHeading = function (result) {

    const coeffCard = this.tableHead
        ? this.tableHead.closest(".report-card")
        : null;

    if (!coeffCard) return;

    const heading = coeffCard.querySelector(".card-header h2");
    const subtitle = coeffCard.querySelector(".card-header p");

    if (!heading) return;

    const isAntibiogram =
        this.selected.dependent === "antibiogram_susceptibility";

    const antibiotic =
        isAntibiogram && this.selected.antibiotics.length === 1
            ? this.formatLabel(this.selected.antibiotics[0])
            : null;

    if (antibiotic) {

        heading.textContent =
            "Table 1. Regression Coefficients — " + antibiotic;

        if (subtitle) {
            subtitle.textContent =
                "Outcome: susceptibility to " +
                antibiotic +
                " (resistant → intermediate → susceptible).";
        }

    } else {

        heading.textContent =
            "Table 1. Regression Coefficients";

        if (subtitle) {
            subtitle.textContent = "";
        }

    }

};


Regression.render = function (result) {

    this.lastResult = result;

    this.modelType = result.model || null;

    this.renderModelType();

    /* ---------------------------------------------
       MULTI-ANTIBIOTIC MODE
       When the backend returns antibiogram_mode
       === "multi", the single-result sections are
       hidden and only the per-antibiotic cards are
       displayed.
    --------------------------------------------- */

    if (result.antibiogram_mode === "multi") {

        this.hideSingleResultSections();

        this.renderPerAntibioticResults(result);

        this.updateInfoStrip(result);

        return;

    }

    /* ---------------------------------------------
       SINGLE RESULT MODE (Layout A)
    --------------------------------------------- */

    this.showSingleResultSections();

    this.clearPerAntibioticResults();

    // Update the table heading for a single selected
    // antibiotic before rendering the coefficients.
    this.updateSingleResultTableHeading(result);

    this.renderOutcomeDistribution(result);

    this.renderCoefficientsTable(result);

    this.renderModelFitStrip(result);

    this.renderModelFitDiagnostics(result);

    this.renderVif(result);

    this.renderClassification(result);

    this.renderMultinomialClassification(result);

    this.renderHosmerLemeshow(result);

    this.renderProportionalOdds(result);

    this.renderInterpretation(result);

    this.updateInfoStrip(result);

};

Regression.hideSingleResultSections = function () {

    const sectionIds = [
        "classificationSection",
        "multinomialClassificationSection",
        "diagnosticsSection",
        "hosmerLemeshowSection",
        "proportionalOddsSection",
        "vifSection",
        "outcomeDistributionSection"
    ];

    sectionIds.forEach(id => {

        const el = document.getElementById(id);

        if (el) el.style.display = "none";

    });

    // Hide the primary coefficients card and interpretation card
    const coeffCard = this.tableHead
        ? this.tableHead.closest(".report-card")
        : null;

    if (coeffCard) coeffCard.style.display = "none";

    if (this.interpretationBox) {

        const interpCard =
            this.interpretationBox.closest(".report-card");

        if (interpCard) interpCard.style.display = "none";

    }

};


Regression.showSingleResultSections = function () {

    const coeffCard = this.tableHead
        ? this.tableHead.closest(".report-card")
        : null;

    if (coeffCard) coeffCard.style.display = "";

    if (this.interpretationBox) {

        const interpCard =
            this.interpretationBox.closest(".report-card");

        if (interpCard) interpCard.style.display = "";

    }

    // Individual diagnostic sections are controlled by their
    // respective render methods — do not force-show here.

};


/* ==========================================================
   MODEL TYPE DISPLAY
   ========================================================== */

Regression.renderModelType = function () {

    if (!this.modelTypeDisplay) return;

    const labels = {
        "binary_logistic": "Binary Logistic",
        "multinomial_logistic": "Multinomial Logistic",
        "ordinal_logistic": "Ordinal Logistic"
    };

    this.modelTypeDisplay.textContent =
        labels[this.modelType] || this.modelType || "—";

};


/* ==========================================================
   OUTCOME DISTRIBUTION
   ========================================================== */

Regression.renderOutcomeDistribution = function (result) {

    if (!this.outcomeDistributionBody) return;

    const distribution =
        result.outcome_information?.outcome_distribution ||
        result.outcome_distribution ||
        [];

    this.outcomeDistributionBody.innerHTML = "";

    if (distribution.length === 0) {

        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 3;
        cell.style.textAlign = "center";
        cell.style.color = "#94a3b8";
        cell.textContent = "No outcome distribution available.";
        row.appendChild(cell);
        this.outcomeDistributionBody.appendChild(row);
        return;

    }

    distribution.forEach(item => {

        const row = document.createElement("tr");

        const categoryCell = document.createElement("td");
        categoryCell.textContent = this.formatLabel(item.category);

        const countCell = document.createElement("td");
        countCell.style.textAlign = "right";
        countCell.textContent = formatNumber(item.count || item.n || 0);

        const pctCell = document.createElement("td");
        pctCell.style.textAlign = "right";
        pctCell.textContent = (item.percentage || 0).toFixed(1) + "%";

        row.appendChild(categoryCell);
        row.appendChild(countCell);
        row.appendChild(pctCell);

        this.outcomeDistributionBody.appendChild(row);

    });

};


/* ==========================================================
   COEFFICIENTS TABLE
   ========================================================== */

Regression.renderCoefficientsTable = function (result) {

    if (!this.tableHead || !this.tableBody)
        return;

    this.tableHead.innerHTML = "";

    const isMultinomial = result.model === "multinomial_logistic";

    const headers = isMultinomial
        ? ["Outcome Category", "Variable", "Coefficient", "Std. Error", "z", "p-value", "RRR", "95% CI"]
        : ["Variable", "Coefficient", "Std. Error", "z", "p-value", "Odds Ratio", "95% CI"];

    const headerRow = document.createElement("tr");
    headers.forEach(label => {
        headerRow.appendChild(this.createHeaderCell(label));
    });
    this.tableHead.appendChild(headerRow);

    this.tableBody.innerHTML = "";

    const coefficients = result.coefficients || [];

    if (coefficients.length === 0) {
        const emptyRow = document.createElement("tr");
        const emptyCell = document.createElement("td");
        emptyCell.colSpan = headers.length;
        emptyCell.className = "table-empty";
        emptyCell.textContent = "No coefficients available.";
        emptyRow.appendChild(emptyCell);
        this.tableBody.appendChild(emptyRow);
        return;
    }

    coefficients.forEach(coefficient => {

        const row = document.createElement("tr");

        const isSignificant =
            coefficient.p_value !== null &&
            coefficient.p_value !== undefined &&
            coefficient.p_value < 0.05;

        if (isSignificant) {
            row.className = "significant-row";
        }

        const cells = [];

        if (isMultinomial) {
            const catCell = document.createElement("td");
            catCell.textContent = this.formatLabel(coefficient.outcome_category || "—");
            cells.push(catCell);
        }

        const varCell = document.createElement("td");
        varCell.textContent = coefficient.variable || "—";
        cells.push(varCell);

        const coefCell = document.createElement("td");
        coefCell.textContent = this.formatNumberOrDash(coefficient.coefficient);
        cells.push(coefCell);

        const seCell = document.createElement("td");
        seCell.textContent = this.formatNumberOrDash(coefficient.standard_error);
        cells.push(seCell);

        const zCell = document.createElement("td");
        zCell.textContent = this.formatNumberOrDash(coefficient.z_value || coefficient.t_value);
        cells.push(zCell);

        const pCell = document.createElement("td");
        pCell.textContent = this.formatPValue(coefficient.p_value) +
            this.significanceMarker(coefficient.p_value);
        cells.push(pCell);

        const ratioKey = isMultinomial ? "relative_risk_ratio" : "odds_ratio";
        const ratioCell = document.createElement("td");
        ratioCell.textContent = this.formatNumberOrDash(coefficient[ratioKey]);
        cells.push(ratioCell);

        const ciCell = document.createElement("td");
        ciCell.textContent =
            "[" +
            this.formatNumberOrDash(coefficient.ci_lower) +
            ", " +
            this.formatNumberOrDash(coefficient.ci_upper) +
            "]";
        cells.push(ciCell);

        cells.forEach(cell => row.appendChild(cell));
        this.tableBody.appendChild(row);

    });

};


/* ==========================================================
   MODEL FIT STRIP
   ========================================================== */

Regression.renderModelFitStrip = function (result) {

    const stats = result.statistics || {};

    if (this.pseudoRSquaredCell) {
        this.pseudoRSquaredCell.textContent =
            this.formatNumberOrDash(stats.mcfadden_pseudo_r_squared);
    }

    if (this.aicSummaryCell) {
        this.aicSummaryCell.textContent =
            this.formatNumberOrDash(stats.aic);
    }

    if (this.bicSummaryCell) {
        this.bicSummaryCell.textContent =
            this.formatNumberOrDash(stats.bic);
    }

    if (this.logLikelihoodCell) {
        this.logLikelihoodCell.textContent =
            this.formatNumberOrDash(stats.log_likelihood);
    }

    if (this.nObservationsCell) {
        this.nObservationsCell.textContent =
            formatNumber(stats.n || result.n || 0);
    }

    if (this.convergedCell) {
        const converged = result.converged !== undefined ? result.converged :
                         stats.converged !== undefined ? stats.converged :
                         result.model_status?.converged;
        this.convergedCell.textContent = converged ? "✅ Yes" : "❌ No";
        this.convergedCell.style.color = converged ? "#16a34a" : "#dc2626";
    }

};


/* ==========================================================
   MODEL FIT DIAGNOSTICS TABLE
   ========================================================== */

Regression.renderModelFitDiagnostics = function (result) {

    const stats = result.statistics || {};
    const diagnostics = result.diagnostics || {};

    if (this.logLikelihoodDetailCell) {
        this.logLikelihoodDetailCell.textContent =
            this.formatNumberOrDash(stats.log_likelihood);
    }

    if (this.nullLogLikelihoodCell) {
        this.nullLogLikelihoodCell.textContent =
            this.formatNumberOrDash(stats.null_log_likelihood);
    }

    if (this.likelihoodRatioCell) {
        const lr = stats.likelihood_ratio;
        const p = stats.likelihood_ratio_p_value;
        this.likelihoodRatioCell.textContent =
            this.formatNumberOrDash(lr) +
            (p !== undefined && p !== null ? " (p = " + this.formatPValue(p) + ")" : "");
    }

    if (this.aicCell) {
        this.aicCell.textContent = this.formatNumberOrDash(stats.aic);
    }

    if (this.bicCell) {
        this.bicCell.textContent = this.formatNumberOrDash(stats.bic);
    }

    if (this.pseudoRSquaredDetailCell) {
        this.pseudoRSquaredDetailCell.textContent =
            this.formatNumberOrDash(stats.mcfadden_pseudo_r_squared);
    }

    if (this.convergenceStatusCell) {
        const converged = result.converged !== undefined ? result.converged :
                         stats.converged !== undefined ? stats.converged :
                         result.model_status?.converged;
        this.convergenceStatusCell.textContent = converged ? "Converged ✅" : "Did not converge ❌";
        this.convergenceStatusCell.style.color = converged ? "#16a34a" : "#dc2626";
    }

    if (this.conditionNumberCell) {
        this.conditionNumberCell.textContent =
            this.formatNumberOrDash(diagnostics.condition_number);
    }

};


/* ==========================================================
   CLASSIFICATION (Binary)
   ========================================================== */

Regression.renderClassification = function (result) {

    if (!this.classificationSection) return;

    const classification =
        result.diagnostics?.classification ||
        result.binary_diagnostics ||
        {};

    if (result.model !== "binary_logistic" ||
        !classification.success ||
        classification.accuracy === undefined) {

        this.classificationSection.style.display = "none";
        return;

    }

    this.classificationSection.style.display = "";

    if (this.accuracyCell) {
        this.accuracyCell.textContent = this.formatPercent(classification.accuracy);
    }

    if (this.sensitivityCell) {
        this.sensitivityCell.textContent = this.formatPercent(classification.sensitivity);
    }

    if (this.specificityCell) {
        this.specificityCell.textContent = this.formatPercent(classification.specificity);
    }

    if (this.precisionCell) {
        this.precisionCell.textContent = this.formatPercent(classification.precision);
    }

    if (this.f1ScoreCell) {
        this.f1ScoreCell.textContent = this.formatNumberOrDash(classification.f1_score);
    }

    const cm = classification.confusion_matrix || {};
    if (this.tnCell) this.tnCell.textContent = cm.true_negative ?? "—";
    if (this.fpCell) this.fpCell.textContent = cm.false_positive ?? "—";
    if (this.fnCell) this.fnCell.textContent = cm.false_negative ?? "—";
    if (this.tpCell) this.tpCell.textContent = cm.true_positive ?? "—";

};


/* ==========================================================
   MULTINOMIAL CLASSIFICATION
   ========================================================== */

Regression.renderMultinomialClassification = function (result) {

    if (!this.multinomialClassificationSection ||
        !this.confusionMatrixHead ||
        !this.confusionMatrixBody) return;

    const classification =
        result.diagnostics?.classification ||
        result.multinomial_diagnostics ||
        {};

    if (result.model !== "multinomial_logistic" ||
        !classification.success ||
        !classification.classes) {

        this.multinomialClassificationSection.style.display = "none";
        return;

    }

    this.multinomialClassificationSection.style.display = "";

    if (this.multinomialAccuracyCell) {
        this.multinomialAccuracyCell.textContent =
            this.formatPercent(classification.accuracy);
    }

    const classes = classification.classes || [];
    const matrix = classification.confusion_matrix || [];

    this.confusionMatrixHead.innerHTML = "";
    const headRow = document.createElement("tr");
    const emptyHead = document.createElement("th");
    emptyHead.textContent = "Actual \\ Predicted";
    headRow.appendChild(emptyHead);

    classes.forEach(cls => {
        const th = document.createElement("th");
        th.textContent = this.formatLabel(cls);
        headRow.appendChild(th);
    });
    this.confusionMatrixHead.appendChild(headRow);

    this.confusionMatrixBody.innerHTML = "";
    matrix.forEach((row, i) => {
        const tr = document.createElement("tr");
        const labelCell = document.createElement("td");
        labelCell.textContent = this.formatLabel(classes[i] || i);
        tr.appendChild(labelCell);

        row.forEach(val => {
            const td = document.createElement("td");
            td.style.textAlign = "center";
            td.textContent = val;
            tr.appendChild(td);
        });

        this.confusionMatrixBody.appendChild(tr);
    });

};


/* ==========================================================
   HOSMER-LEMESHOW TEST (Binary)
   ========================================================== */

Regression.renderHosmerLemeshow = function (result) {

    if (!this.hosmerLemeshowSection) return;

    const hl = result.diagnostics?.hosmer_lemeshow || {};

    if (result.model !== "binary_logistic" || !hl.success) {
        this.hosmerLemeshowSection.style.display = "none";
        return;
    }

    this.hosmerLemeshowSection.style.display = "";

    if (this.hlChiSquareCell) {
        this.hlChiSquareCell.textContent = this.formatNumberOrDash(hl.chi_square);
    }

    if (this.hlDFCell) {
        this.hlDFCell.textContent = hl.degrees_of_freedom ?? "—";
    }

    if (this.hlPValueCell) {
        this.hlPValueCell.textContent = this.formatPValue(hl.p_value);
    }

    if (this.hlInterpretationCell) {
        const p = hl.p_value;
        if (p !== null && p !== undefined) {
            this.hlInterpretationCell.textContent =
                p > 0.05
                    ? "No evidence of lack of fit (p > 0.05) ✅"
                    : "Evidence of lack of fit (p ≤ 0.05) ⚠️";
            this.hlInterpretationCell.style.color = p > 0.05 ? "#16a34a" : "#dc2626";
        } else {
            this.hlInterpretationCell.textContent = "Unable to determine";
        }
    }

};


/* ==========================================================
   PROPORTIONAL ODDS (Ordinal)
   ========================================================== */

Regression.renderProportionalOdds = function (result) {

    if (!this.proportionalOddsSection || !this.proportionalOddsContent) return;

    const po = result.diagnostics?.proportional_odds || {};

    if (result.model !== "ordinal_logistic" || !po.success) {
        this.proportionalOddsSection.style.display = "none";
        return;
    }

    this.proportionalOddsSection.style.display = "";

    this.proportionalOddsContent.innerHTML =
        this.buildProportionalOddsHTML(po);

};


Regression.buildProportionalOddsHTML = function (po) {

    let html = "<div style='margin-bottom:8px;'><strong>Test:</strong> " +
        (po.test || "Brant-style proportional-odds diagnostic") + "</div>";

    html += "<div style='margin-bottom:8px;'><strong>Categories:</strong> " +
        (po.categories || []).join(" → ") + "</div>";

    html += "<div style='margin-bottom:12px;'><strong>Interpretation:</strong> " +
        (po.interpretation || "Run regression to see diagnostic.") + "</div>";

    const comparison = po.coefficient_comparison || [];
    if (comparison.length > 0) {
        html += "<div style='margin-top:12px; font-weight:500;'>Coefficient Comparison Across Cumulative Logits</div>";
        html += "<div class='table-container' style='margin-top:4px;'>";
        html += "<table class='summary-table'>";
        html += "<thead><tr><th>Variable</th>";

        const splitNames = new Set();
        comparison.forEach(item => {
            (item.estimates || []).forEach(e => {
                splitNames.add("Split " + e.split);
            });
        });
        const sortedSplits = Array.from(splitNames).sort();

        sortedSplits.forEach(s => {
            html += "<th style='text-align:center;'>" + s + "</th>";
        });
        html += "<th style='text-align:center;'>Range</th>";
        html += "</tr></thead><tbody>";

        comparison.forEach(item => {
            const estimates = item.estimates || [];
            const estMap = {};
            estimates.forEach(e => {
                estMap["Split " + e.split] = e.coefficient;
            });

            html += "<tr>";
            html += "<td>" + this.formatLabel(item.variable) + "</td>";
            sortedSplits.forEach(s => {
                const val = estMap[s];
                html += "<td style='text-align:center;'>" +
                    (val !== undefined ? this.formatNumberOrDash(val) : "—") + "</td>";
            });
            html += "<td style='text-align:center;'>" +
                this.formatNumberOrDash(item.coefficient_range) + "</td>";
            html += "</tr>";
        });

        html += "</tbody></table></div>";
    }

    if (po.note) {
        html += "<div style='margin-top:12px; color:#64748b; font-size:13px;'>" + po.note + "</div>";
    }

    return html;

};


/* ==========================================================
   VARIANCE INFLATION FACTORS
   ========================================================== */

Regression.renderVif = function (result) {

    if (!this.vifSection || !this.vifTableBody)
        return;

    const vif = result.vif || [];

    if (vif.length === 0) {
        this.vifSection.style.display = "none";
        return;
    }

    this.vifSection.style.display = "";

    const sortedVif = [...vif].sort((a, b) => (b.vif || 0) - (a.vif || 0));

    this.vifTableBody.innerHTML = "";

    sortedVif.forEach(entry => {

        const row = document.createElement("tr");

        const labelCell = document.createElement("td");
        labelCell.className = "row-label";
        labelCell.textContent = this.formatLabel(entry.variable);

        const vifCell = document.createElement("td");
        vifCell.style.textAlign = "center";
        vifCell.textContent = this.formatNumberOrDash(entry.vif);

        if (entry.vif > 10) {
            row.className = "significant-row";
            vifCell.style.fontWeight = "bold";
        }

        row.appendChild(labelCell);
        row.appendChild(vifCell);
        this.vifTableBody.appendChild(row);

    });

};


/* ==========================================================
   INTERPRETATION
   ========================================================== */

Regression.renderInterpretation = function (result) {

    if (!this.interpretationBox)
        return;

    this.interpretationBox.innerHTML =
        this.buildInterpretationHTML(result);

    this.interpretationBox.className = "message info";

};


Regression.buildInterpretationHTML = function (result) {

    const stats = result.statistics || {};
    const coefficients = result.coefficients || [];

    const modelLabels = {
        "binary_logistic": "Binary Logistic Regression",
        "multinomial_logistic": "Multinomial Logistic Regression",
        "ordinal_logistic": "Ordinal Logistic Regression"
    };

    const modelName = modelLabels[result.model] || result.model || "Regression";

    const dependentLabel =
        this.formatLabel(result.dependent_variable);

    const predictorLabels =
        (result.independent_variables || [])
            .map(value => this.formatLabel(value));

    const n = stats.n || result.n || 0;

    let parts = [];

    parts.push(
        "A " + modelName + " was performed with " + dependentLabel +
        " as the dependent variable and " + (predictorLabels.length > 0 ? predictorLabels.join(", ") : "no predictors") +
        " as independent variables (N = " + formatNumber(n) + ")."
    );

    const pseudoR2 = stats.mcfadden_pseudo_r_squared;
    if (pseudoR2 !== null && pseudoR2 !== undefined) {
        parts.push(
            "The model explains approximately " + this.formatPercent(pseudoR2) +
            " of the variance (McFadden R² = " + this.formatNumberOrDash(pseudoR2) + ")."
        );
    }

    const lr = stats.likelihood_ratio;
    const lrP = stats.likelihood_ratio_p_value;
    if (lr !== null && lr !== undefined && lrP !== null && lrP !== undefined) {
        const significant = lrP < 0.05;
        parts.push(
            "The overall model is " +
            (significant ? "statistically significant" : "not statistically significant") +
            " (LR χ² = " + this.formatNumberOrDash(lr) +
            ", p = " + this.formatPValue(lrP) + ")."
        );
    }

    const significantCoefs = coefficients.filter(c =>
        c.variable !== "Intercept" &&
        c.p_value !== null &&
        c.p_value !== undefined &&
        c.p_value < 0.05
    );

    if (significantCoefs.length > 0) {
        const sigList = significantCoefs.map(c => {
            const ratioKey = result.model === "multinomial_logistic" ? "relative_risk_ratio" : "odds_ratio";
            const ratio = c[ratioKey];
            const outcome = result.model === "multinomial_logistic" && c.outcome_category
                ? " (" + this.formatLabel(c.outcome_category) + ")"
                : "";
            return this.formatLabel(c.variable) + outcome +
                " (p = " + this.formatPValue(c.p_value) + ", " +
                (ratioKey === "relative_risk_ratio" ? "RRR" : "OR") +
                " = " + this.formatNumberOrDash(ratio) + ")";
        });
        parts.push(
            "The following predictors were statistically significant: " +
            sigList.join("; ") + "."
        );
    } else {
        parts.push(
            "None of the individual predictors reached statistical significance at α = 0.05."
        );
    }

    const highVif = (result.vif || []).filter(e => e.vif > 10);
    if (highVif.length > 0) {
        parts.push(
            "Note: " +
            highVif.map(e => this.formatLabel(e.variable)).join(", ") +
            " showed high Variance Inflation Factor (VIF > 10), indicating possible multicollinearity."
        );
    }

    const converged = result.converged !== undefined ? result.converged :
                     stats.converged !== undefined ? stats.converged :
                     result.model_status?.converged;
    if (converged === false) {
        parts.push(
            "⚠️ The model did not converge. Results should be interpreted with caution."
        );
    }

    return parts.join(" ");

};


/* ==========================================================
   UPDATE INFO STRIP
   ========================================================== */

Regression.updateInfoStrip = function (result) {

    if (this.filtersAppliedText) {

        const filters =
            typeof FilterManager !== "undefined" && FilterManager.getFilters
                ? FilterManager.getFilters()
                : {
                    from_month: "",
                    to_month: "",
                    district: "all",
                    block: "all",
                    sample_type: "all",
                    organisms: []
                };

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

    if (this.totalRecords) {

        // In multi mode, sum the N across per-antibiotic models
        if (result.antibiogram_mode === "multi" && result.antibiotics) {

            const entries = Object.values(result.antibiotics);

            const total = entries.reduce(
                (sum, entry) =>
                    sum + (
                        entry && entry.statistics && entry.statistics.n
                            ? Number(entry.statistics.n)
                            : 0
                    ),
                0
            );

            this.totalRecords.textContent = formatNumber(total);

        } else {

            const n = result.statistics?.n || result.n || 0;
            this.totalRecords.textContent = formatNumber(n);

        }

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

Regression.resetResults = function () {

    this.lastResult = null;

    if (this.tableHead) {
        this.tableHead.innerHTML = "";
    }

    if (this.tableBody) {
        this.tableBody.innerHTML = "";
    }

    const stripCells = [
        "pseudoRSquaredCell", "aicSummaryCell", "bicSummaryCell",
        "logLikelihoodCell", "nObservationsCell", "convergedCell"
    ];
    stripCells.forEach(key => {
        if (this[key]) {
            this[key].textContent = "—";
            if (key === "convergedCell") {
                this[key].style.color = "";
            }
        }
    });

    const diagCells = [
        "logLikelihoodDetailCell", "nullLogLikelihoodCell", "likelihoodRatioCell",
        "aicCell", "bicCell", "pseudoRSquaredDetailCell",
        "convergenceStatusCell", "conditionNumberCell"
    ];
    diagCells.forEach(key => {
        if (this[key]) {
            this[key].textContent = "—";
            if (key === "convergenceStatusCell") {
                this[key].style.color = "";
            }
        }
    });

    if (this.classificationSection) {
        this.classificationSection.style.display = "none";
    }
    const classCells = ["accuracyCell", "sensitivityCell", "specificityCell", "precisionCell", "f1ScoreCell"];
    classCells.forEach(key => {
        if (this[key]) this[key].textContent = "—";
    });
    ["tnCell", "fpCell", "fnCell", "tpCell"].forEach(key => {
        if (this[key]) this[key].textContent = "—";
    });

    if (this.multinomialClassificationSection) {
        this.multinomialClassificationSection.style.display = "none";
    }
    if (this.multinomialAccuracyCell) {
        this.multinomialAccuracyCell.textContent = "—";
    }
    if (this.confusionMatrixHead) {
        this.confusionMatrixHead.innerHTML = "";
    }
    if (this.confusionMatrixBody) {
        this.confusionMatrixBody.innerHTML = "";
    }

    if (this.hosmerLemeshowSection) {
        this.hosmerLemeshowSection.style.display = "none";
    }
    ["hlChiSquareCell", "hlDFCell", "hlPValueCell", "hlInterpretationCell"].forEach(key => {
        if (this[key]) {
            this[key].textContent = "—";
            if (key === "hlInterpretationCell") {
                this[key].style.color = "";
            }
        }
    });

    if (this.proportionalOddsSection) {
        this.proportionalOddsSection.style.display = "none";
    }
    if (this.proportionalOddsContent) {
        this.proportionalOddsContent.innerHTML = "<p style='color:#64748b;'>Run regression to see proportional odds diagnostic.</p>";
    }

    if (this.vifSection) {
        this.vifSection.style.display = "none";
    }
    if (this.vifTableBody) {
        this.vifTableBody.innerHTML = "";
    }

    if (this.interpretationBox) {

        this.interpretationBox.innerHTML =
            "Run a regression analysis to generate the statistical interpretation.";

        this.interpretationBox.className = "message info";

    }

    if (this.outcomeDistributionBody) {
        this.outcomeDistributionBody.innerHTML =
            "<tr><td colspan='3' style='text-align:center; color:#94a3b8;'>Run regression to see outcome distribution.</td></tr>";
    }

    if (this.modelTypeDisplay) {
        this.modelTypeDisplay.textContent = "—";
    }
    if (this.totalRecords) {
        this.totalRecords.textContent = "—";
    }
    if (this.reportGeneratedValue) {
        this.reportGeneratedValue.textContent = "—";
    }

    // Restore single-result sections & clear multi cards
    this.showSingleResultSections();
    this.clearPerAntibioticResults();

};


/* ==========================================================
   PER-ANTIBIOTIC RESULTS
   ========================================================== */

Regression.clearPerAntibioticResults = function () {

    if (this.perAntibioticResults) {

        this.perAntibioticResults.innerHTML = "";

    }

};


Regression.renderPerAntibioticResults = function (result) {

    const container =
        this.perAntibioticResults;

    if (!container) return;

    container.innerHTML = "";

    const antibioticEntries =
        Object.entries(result.antibiotics || {});

    if (antibioticEntries.length === 0) {

        const msg = document.createElement("div");
        msg.className = "message info";
        msg.textContent = "No per-antibiotic results were produced.";
        container.appendChild(msg);
        return;

    }

    

    // One card per antibiotic
    antibioticEntries.forEach(([antibiotic, entry], index) => {

        const card = document.createElement("section");
        card.className = "report-card";

        const cardHeader = document.createElement("div");
        cardHeader.className = "card-header";

        const headerText = document.createElement("div");

        const cardTitle = document.createElement("h2");
        cardTitle.textContent =
            "Table " + (index + 1) + ". Regression Coefficients — " +
            this.formatLabel(antibiotic);

        const cardSubtitle = document.createElement("p");
        cardSubtitle.textContent =
            "Outcome: susceptibility to " +
            this.formatLabel(antibiotic) +
            " (resistant → intermediate → susceptible).";

        headerText.appendChild(cardTitle);
        headerText.appendChild(cardSubtitle);
        cardHeader.appendChild(headerText);
        card.appendChild(cardHeader);

        if (entry && entry.error) {

            const err = document.createElement("div");
            err.className = "message error";
            err.textContent =
                "Model could not be fitted for " +
                this.formatLabel(antibiotic) +
                ": " + entry.error;
            card.appendChild(err);
            container.appendChild(card);
            return;

        }

        const mergedEntry = {
            ...entry,
            dependent_variable: "antibiogram_susceptibility",
            independent_variables: result.independent_variables || []
        };

        // 1. Coefficients + Model fit strip
        card.appendChild(
            this.buildCoefficientsTableDOM(mergedEntry)
        );

        // 2. Diagnostics
        card.appendChild(
            this.buildDiagnosticsTableDOM(mergedEntry)
        );

        // 3. Proportional odds (ordinal)
        if (
            mergedEntry.model === "ordinal_logistic" &&
            mergedEntry.diagnostics &&
            mergedEntry.diagnostics.proportional_odds &&
            mergedEntry.diagnostics.proportional_odds.success
        ) {

            card.appendChild(
                this.buildProportionalOddsDOM(mergedEntry)
            );

        }

        // 4. VIF
        if (Array.isArray(mergedEntry.vif) && mergedEntry.vif.length > 0) {

            card.appendChild(
                this.buildVifTableDOM(mergedEntry)
            );

        }

        // 5. Interpretation
        card.appendChild(
            this.buildInterpretationDOM(mergedEntry, antibiotic)
        );

        container.appendChild(card);

    });

};


/* ==========================================================
   STANDALONE DOM BUILDERS (for per-antibiotic cards)
   ========================================================== */

Regression.getConvergenceStatus = function (entry) {

    const stats = entry.statistics || {};

    return entry.converged !== undefined
        ? entry.converged
        : stats.converged !== undefined
            ? stats.converged
            : entry.model_status?.converged;

};



Regression.buildCoefficientsTableDOM = function (entry) {

    const wrapper = document.createElement("div");

    const stats = entry.statistics || {};

    const strip = document.createElement("div");
    strip.className = "test-summary-strip";

    const items = [
        { label: "McFadden R²", value: this.formatNumberOrDash(stats.mcfadden_pseudo_r_squared) },
        { label: "AIC", value: this.formatNumberOrDash(stats.aic) },
        { label: "BIC", value: this.formatNumberOrDash(stats.bic) },
        { label: "Log-Likelihood", value: this.formatNumberOrDash(stats.log_likelihood) },
        { label: "N", value: formatNumber(stats.n || entry.n || 0) },
        {
            label: "Converged",
            value: this.getConvergenceStatus(entry) ? "✅ Yes" : "❌ No"
        }
    ];

    items.forEach(item => {
        const stat = document.createElement("div");
        stat.className = "test-summary-item";

        const lbl = document.createElement("span");
        lbl.className = "test-summary-label";
        lbl.textContent = item.label;

        const val = document.createElement("span");
        val.className = "test-summary-value";
        val.textContent = item.value;

        stat.appendChild(lbl);
        stat.appendChild(document.createTextNode(" "));
        stat.appendChild(val);
        strip.appendChild(stat);
    });

    wrapper.appendChild(strip);

    // Coefficients table
    const tableContainer = document.createElement("div");
    tableContainer.className = "table-container";

    const table = document.createElement("table");
    table.className = "summary-table regression-table";

    const thead = document.createElement("thead");
    const tbody = document.createElement("tbody");

    const isMultinomial = entry.model === "multinomial_logistic";

    const headers = isMultinomial
        ? ["Outcome Category", "Variable", "Coefficient", "Std. Error", "z", "p-value", "RRR", "95% CI"]
        : ["Variable", "Coefficient", "Std. Error", "z", "p-value", "Odds Ratio", "95% CI"];

    const headerRow = document.createElement("tr");
    headers.forEach(label => {
        headerRow.appendChild(this.createHeaderCell(label));
    });
    thead.appendChild(headerRow);

    const coefficients = entry.coefficients || [];

    if (coefficients.length === 0) {
        const emptyRow = document.createElement("tr");
        const emptyCell = document.createElement("td");
        emptyCell.colSpan = headers.length;
        emptyCell.className = "table-empty";
        emptyCell.textContent = "No coefficients available.";
        emptyRow.appendChild(emptyCell);
        tbody.appendChild(emptyRow);
    }
    else {

        coefficients.forEach(coefficient => {

            const row = document.createElement("tr");

            const isSignificant =
                coefficient.p_value !== null &&
                coefficient.p_value !== undefined &&
                coefficient.p_value < 0.05;

            if (isSignificant) row.className = "significant-row";

            const cells = [];

            if (isMultinomial) {
                const catCell = document.createElement("td");
                catCell.textContent = this.formatLabel(coefficient.outcome_category || "—");
                cells.push(catCell);
            }

            const varCell = document.createElement("td");
            varCell.textContent = coefficient.variable || "—";
            cells.push(varCell);

            const coefCell = document.createElement("td");
            coefCell.textContent = this.formatNumberOrDash(coefficient.coefficient);
            cells.push(coefCell);

            const seCell = document.createElement("td");
            seCell.textContent = this.formatNumberOrDash(coefficient.standard_error);
            cells.push(seCell);

            const zCell = document.createElement("td");
            zCell.textContent = this.formatNumberOrDash(coefficient.z_value || coefficient.t_value);
            cells.push(zCell);

            const pCell = document.createElement("td");
            pCell.textContent = this.formatPValue(coefficient.p_value) +
                this.significanceMarker(coefficient.p_value);
            cells.push(pCell);

            const ratioKey = isMultinomial ? "relative_risk_ratio" : "odds_ratio";
            const ratioCell = document.createElement("td");
            ratioCell.textContent = this.formatNumberOrDash(coefficient[ratioKey]);
            cells.push(ratioCell);

            const ciCell = document.createElement("td");
            ciCell.textContent =
                "[" +
                this.formatNumberOrDash(coefficient.ci_lower) +
                ", " +
                this.formatNumberOrDash(coefficient.ci_upper) +
                "]";
            cells.push(ciCell);

            cells.forEach(cell => row.appendChild(cell));
            tbody.appendChild(row);

        });

    }

    table.appendChild(thead);
    table.appendChild(tbody);
    tableContainer.appendChild(table);
    wrapper.appendChild(tableContainer);

    return wrapper;

};


Regression.buildDiagnosticsTableDOM = function (entry) {

    const wrapper = document.createElement("div");

    const heading = document.createElement("h3");
    heading.style.marginTop = "16px";
    heading.style.marginBottom = "8px";
    heading.textContent = "Model Diagnostics";
    wrapper.appendChild(heading);

    const stats = entry.statistics || {};
    const diagnostics = entry.diagnostics || {};

    const rows = [
        ["Log-Likelihood", this.formatNumberOrDash(stats.log_likelihood)],
        ["Null Log-Likelihood", this.formatNumberOrDash(stats.null_log_likelihood)],
        [
            "Likelihood-Ratio Test",
            this.formatNumberOrDash(stats.likelihood_ratio) +
            (stats.likelihood_ratio_p_value !== undefined && stats.likelihood_ratio_p_value !== null
                ? " (p = " + this.formatPValue(stats.likelihood_ratio_p_value) + ")"
                : "")
        ],
        ["AIC", this.formatNumberOrDash(stats.aic)],
        ["BIC", this.formatNumberOrDash(stats.bic)],
        ["McFadden Pseudo R²", this.formatNumberOrDash(stats.mcfadden_pseudo_r_squared)],
        [
         "Convergence Status",
          this.getConvergenceStatus(entry)
             ? "Converged ✅"
             : "Did not converge ❌"
        ],
        ["Condition Number", this.formatNumberOrDash(diagnostics.condition_number)]
    ];

    const container = document.createElement("div");
    container.className = "table-container";

    const table = document.createElement("table");
    table.className = "summary-table";

    const tbody = document.createElement("tbody");

    rows.forEach(([label, value]) => {
        const tr = document.createElement("tr");

        const labelCell = document.createElement("td");
        labelCell.style.width = "55%";
        labelCell.textContent = label;

        const valueCell = document.createElement("td");
        valueCell.textContent = value;

        if (label === "Convergence Status") {
            const converged = this.getConvergenceStatus(entry);
            valueCell.style.color = converged ? "#16a34a" : "#dc2626";
        }

        tr.appendChild(labelCell);
        tr.appendChild(valueCell);
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
    wrapper.appendChild(container);

    return wrapper;

};


Regression.buildProportionalOddsDOM = function (entry) {

    const wrapper = document.createElement("div");

    const heading = document.createElement("h3");
    heading.style.marginTop = "16px";
    heading.style.marginBottom = "8px";
    heading.textContent = "Proportional Odds Assumption";
    wrapper.appendChild(heading);

    const content = document.createElement("div");
    content.innerHTML =
        this.buildProportionalOddsHTML(entry.diagnostics.proportional_odds);

    wrapper.appendChild(content);

    return wrapper;

};


Regression.buildVifTableDOM = function (entry) {

    const wrapper = document.createElement("div");

    const heading = document.createElement("h3");
    heading.style.marginTop = "16px";
    heading.style.marginBottom = "8px";
    heading.textContent = "Variance Inflation Factors (VIF)";
    wrapper.appendChild(heading);

    const sortedVif =
        [...entry.vif].sort((a, b) => (b.vif || 0) - (a.vif || 0));

    const container = document.createElement("div");
    container.className = "table-container";

    const table = document.createElement("table");
    table.className = "summary-table";

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");

    const th1 = document.createElement("th");
    th1.style.width = "70%";
    th1.textContent = "Predictor";
    headRow.appendChild(th1);

    const th2 = document.createElement("th");
    th2.style.width = "30%";
    th2.textContent = "VIF";
    headRow.appendChild(th2);

    thead.appendChild(headRow);

    const tbody = document.createElement("tbody");

    sortedVif.forEach(entryItem => {

        const tr = document.createElement("tr");

        const labelCell = document.createElement("td");
        labelCell.className = "row-label";
        labelCell.textContent = this.formatLabel(entryItem.variable);

        const vifCell = document.createElement("td");
        vifCell.style.textAlign = "center";
        vifCell.textContent = this.formatNumberOrDash(entryItem.vif);

        if (entryItem.vif > 10) {
            tr.className = "significant-row";
            vifCell.style.fontWeight = "bold";
        }

        tr.appendChild(labelCell);
        tr.appendChild(vifCell);
        tbody.appendChild(tr);

    });

    table.appendChild(thead);
    table.appendChild(tbody);
    container.appendChild(table);
    wrapper.appendChild(container);

    return wrapper;

};


Regression.buildInterpretationDOM = function (entry, antibiotic) {

    const wrapper = document.createElement("div");

    const heading = document.createElement("h3");
    heading.style.marginTop = "16px";
    heading.style.marginBottom = "8px";
    heading.textContent = "Statistical Interpretation";
    wrapper.appendChild(heading);

    const box = document.createElement("div");
    box.className = "message info";
    box.innerHTML =
        this.buildInterpretationHTML(entry);

    wrapper.appendChild(box);

    return wrapper;

};


/* ==========================================================
   EXPORT TABLE
   ========================================================== */

Regression.exportTable = function () {

    if (!this.lastResult) {
        if (typeof showMessage === "function") {
            showMessage("No regression results to export. Please run a regression first.", "error");
        }
        return;
    }

    // Multi mode → export all per-antibiotic coefficient tables
    if (this.lastResult.antibiogram_mode === "multi" && this.lastResult.antibiotics) {

        let csv = "Antibiotic,Variable,Coefficient,Std_Error,z,p_value,Odds_Ratio,CI_Lower,CI_Upper\n";

        Object.entries(this.lastResult.antibiotics).forEach(([antibiotic, entry]) => {

            if (!entry || entry.error) return;

            (entry.coefficients || []).forEach(coef => {
                const row = [
                    antibiotic,
                    coef.variable || "—",
                    coef.coefficient !== undefined ? coef.coefficient : "—",
                    coef.standard_error !== undefined ? coef.standard_error : "—",
                    coef.z_value || coef.t_value || "—",
                    coef.p_value !== undefined ? coef.p_value : "—",
                    coef.odds_ratio || coef.relative_risk_ratio || "—",
                    coef.ci_lower || "—",
                    coef.ci_upper || "—"
                ];
                csv += row.join(",") + "\n";
            });

        });

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "regression_per_antibiotic_" + new Date().toISOString().slice(0, 10) + ".csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        if (typeof showMessage === "function") {
            showMessage("Per-antibiotic regression tables exported successfully.", "success");
        }
        return;

    }

    // Single mode
    const coefficients = this.lastResult.coefficients || [];
    if (coefficients.length === 0) {
        if (typeof showMessage === "function") {
            showMessage("No coefficients available to export.", "error");
        }
        return;
    }

    let csv = "Variable,Coefficient,Std_Error,z,p_value,Odds_Ratio,CI_Lower,CI_Upper\n";

    coefficients.forEach(coef => {
        const row = [
            coef.variable || "—",
            coef.coefficient !== undefined ? coef.coefficient : "—",
            coef.standard_error !== undefined ? coef.standard_error : "—",
            coef.z_value || coef.t_value || "—",
            coef.p_value !== undefined ? coef.p_value : "—",
            coef.odds_ratio || coef.relative_risk_ratio || "—",
            coef.ci_lower || "—",
            coef.ci_upper || "—"
        ];
        csv += row.join(",") + "\n";
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "regression_results_" + new Date().toISOString().slice(0, 10) + ".csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    if (typeof showMessage === "function") {
        showMessage("Table exported successfully.", "success");
    }

};


/* ==========================================================
   FORMAT HELPERS
   ========================================================== */

Regression.formatLabel = function (value) {

    if (value === null || value === undefined || value === "")
        return "—";

    return String(value)

        .replace(/_/g, " ")

        .replace(/\b\w/g, character => character.toUpperCase());

};


Regression.formatPValue = function (value) {

    if (value === null || value === undefined)
        return "—";

    const number = Number(value);

    if (Number.isNaN(number))
        return "—";

    return number < 0.001 ? "<0.001" : number.toFixed(4);

};


Regression.formatNumberOrDash = function (value) {

    if (value === null || value === undefined)
        return "—";

    const number = Number(value);

    if (Number.isNaN(number))
        return "—";

    return number.toLocaleString(

        undefined,

        {

            minimumFractionDigits: 2,

            maximumFractionDigits: 4

        }

    );

};


Regression.formatPercent = function (value) {

    if (value === null || value === undefined)
        return "—";

    const number = Number(value);

    if (Number.isNaN(number))
        return "—";

    return (number * 100).toFixed(1) + "%";

};


Regression.formatMonth = function (value) {

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


Regression.formatPeriod = function (filters) {

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


Regression.significanceMarker = function (pValue) {

    if (pValue === null || pValue === undefined)
        return "";

    const p = Number(pValue);
    if (Number.isNaN(p)) return "";

    if (p < 0.001) return " ***";
    if (p < 0.01) return " **";
    if (p < 0.05) return " *";

    return "";

};


Regression.createHeaderCell = function (text) {

    const th =
        document.createElement("th");

    th.textContent = text;

    return th;

};


Regression.createDataCell = function (text) {

    const td =
        document.createElement("td");

    td.className = "text-center";

    td.textContent = text;

    return td;

};


/* ==========================================================
   CUSTOM AGE GROUPS — EVENT WIRING
   ========================================================== */

Regression.attachAgeGroupEvents = function () {

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


Regression.defaultAgeGroupRows = function () {

    return [
        { min: 0,  max: 29  },
        { min: 30, max: 60  },
        { min: 61, max: 90 }
    ];

};


Regression.updateAgeGroupUI = function () {

    const needsCustomization =
        this.selected.independent.includes("age_group");

    if (this.customizeBtn) {

        this.customizeBtn.style.display =
            needsCustomization ? "" : "none";

    }

    if (!needsCustomization && this.agePanel) {

        this.agePanel.style.display = "none";

    }

    this.updateCustomizeButtonLabel();

};


Regression.updateCustomizeButtonLabel = function () {

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


Regression.openAgeGroupPanel = function () {

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


Regression.closeAgeGroupPanel = function () {

    if (this.agePanel) this.agePanel.style.display = "none";

};


Regression.renderAgeGroupRows = function () {

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


Regression.showAgeGroupError = function (message) {

    if (!this.ageError)
        return;

    this.ageError.textContent = message;

    this.ageError.style.display = "";

};


Regression.clearAgeGroupError = function () {

    if (!this.ageError)
        return;

    this.ageError.textContent = "";

    this.ageError.style.display = "none";

};


Regression.validateAgeGroupRows = function () {

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


Regression.handleApplyAgeGroups = function () {

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


Regression.handleResetAgeGroups = function () {

    this.customAgeGroups = null;

    this.ageGroupRows = [];

    this.updateCustomizeButtonLabel();

    this.clearAgeGroupError();

    this.closeAgeGroupPanel();

};


/* ==========================================================
   EXPORT + BOOTSTRAP
   ========================================================== */

window.Regression = Regression;

document.addEventListener(

    "DOMContentLoaded",

    async function () {

        try {

            Regression.initialize();

            if (typeof FilterManager !== "undefined") {

                FilterManager.endpoint = "/regression-options";

                await FilterManager.initialise();

            }

        }

        catch (error) {

            console.error(error);

            if (typeof showMessage === "function") {

                showMessage(
                    "Failed to initialize Regression Analysis.",
                    "error"
                );

            }

        }

    }

);