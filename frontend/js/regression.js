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

        antibiotic: null

    },

    controls: {

        independent: null,

        dependent: null,

        antibiotic: null

    },

    lastResult: null

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

                /* NEW: close the dropdown as soon as a choice is made */

                this.controls.dependent.panel.classList.remove("show");

            }

        );

    }

    if (this.controls.antibiotic) {

        this.controls.antibiotic.panel.addEventListener(

            "change",

            (event) => {

                if (event.target.type !== "radio")
                    return;

                this.handleAntibioticSelection(
                    event.target
                );

                /* NEW: close the dropdown as soon as a choice is made */

                this.controls.antibiotic.panel.classList.remove("show");

            }

        );

    }

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

            /* NEW: single-choice dropdowns (dependent variable,
               antibiotic) close on any option click, even when the
               option is already selected. The multi-select
               predictors dropdown stays open. */

            if (
                control !== this.controls.independent &&
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

        const radio =
            document.createElement("input");

        radio.type = "radio";

        radio.name = "antibioticChoice";

        radio.value = value;

        radio.checked =
            (this.selected.antibiotic === value);

        label.appendChild(radio);

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

    // Show/hide antibiotic selector based on dependent variable
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
   ANTIBIOTIC SELECTION
   ========================================================== */

Regression.handleAntibioticSelection = function (radio) {

    if (!radio.checked) return;

    this.selected.antibiotic = radio.value;

    this.updateAntibioticButtonLabel();

};


Regression.updateAntibioticButtonLabel = function () {

    const control =
        this.controls.antibiotic;

    if (!control)
        return;

    control.button.textContent =

        this.selected.antibiotic
            ? this.formatLabel(this.selected.antibiotic)
            : "Select Antibiotic";

};


Regression.handleAntibioticVisibility = function () {

    const group = document.getElementById("antibioticGroup");

    if (!group) return;

    // Show antibiotic selector only for antibiogram_susceptibility
    if (this.selected.dependent === "antibiogram_susceptibility") {

        group.style.display = "block";

        // Reset antibiotic selection when showing
        if (this.controls.antibiotic) {
            this.selected.antibiotic = null;
            this.updateAntibioticButtonLabel();
            const radios = this.controls.antibiotic.panel.querySelectorAll("input[type='radio']");
            radios.forEach(r => r.checked = false);
        }

    } else {

        group.style.display = "none";
        this.selected.antibiotic = null;

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

        antibiotic: null

    };

    this.modelType = null;

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
            "Select Antibiotic";

        this.controls.antibiotic.panel

            .querySelectorAll("input[type='radio']")

            .forEach(box => { box.checked = false; });

    }

    // Hide antibiotic group
    const group = document.getElementById("antibioticGroup");
    if (group) {
        group.style.display = "none";
    }

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
        !this.selected.antibiotic) {

        if (typeof showMessage === "function") {

            showMessage(
                "Please select an antibiotic for antibiogram regression.",
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

        /* NEW: time duration (month-year, "YYYY-MM" or "") */

        from_month: filters.from_month || "",

        to_month: filters.to_month || "",

        district: filters.district || "all",

        block: filters.block || "all",

        sample_type: filters.sample_type || "all",

        organisms: filters.organisms || [],

        independent_variables: this.selected.independent,

        dependent_variable: this.selected.dependent,

        antibiotic: this.selected.antibiotic

    };

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

Regression.render = function (result) {

    this.lastResult = result;

    this.modelType = result.model;

    this.renderModelType();

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
            // Outcome category
            const catCell = document.createElement("td");
            catCell.textContent = this.formatLabel(coefficient.outcome_category || "—");
            cells.push(catCell);
        }

        // Variable name
        const varCell = document.createElement("td");
        varCell.textContent = coefficient.variable || "—";
        cells.push(varCell);

        // Coefficient
        const coefCell = document.createElement("td");
        coefCell.textContent = this.formatNumberOrDash(coefficient.coefficient);
        cells.push(coefCell);

        // Std Error
        const seCell = document.createElement("td");
        seCell.textContent = this.formatNumberOrDash(coefficient.standard_error);
        cells.push(seCell);

        // z-value
        const zCell = document.createElement("td");
        zCell.textContent = this.formatNumberOrDash(coefficient.z_value || coefficient.t_value);
        cells.push(zCell);

        // p-value
        const pCell = document.createElement("td");
        pCell.textContent = this.formatPValue(coefficient.p_value) +
            this.significanceMarker(coefficient.p_value);
        cells.push(pCell);

        // Ratio (OR or RRR)
        const ratioKey = isMultinomial ? "relative_risk_ratio" : "odds_ratio";
        const ratioCell = document.createElement("td");
        ratioCell.textContent = this.formatNumberOrDash(coefficient[ratioKey]);
        cells.push(ratioCell);

        // CI
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

    // Confusion matrix
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

    // Build confusion matrix
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

    let html = "<div style='margin-bottom:8px;'><strong>Test:</strong> " +
        (po.test || "Brant-style proportional-odds diagnostic") + "</div>";

    html += "<div style='margin-bottom:8px;'><strong>Categories:</strong> " +
        (po.categories || []).join(" → ") + "</div>";

    html += "<div style='margin-bottom:12px;'><strong>Interpretation:</strong> " +
        (po.interpretation || "Run regression to see diagnostic.") + "</div>";

    // Show coefficient comparison if available
    const comparison = po.coefficient_comparison || [];
    if (comparison.length > 0) {
        html += "<div style='margin-top:12px; font-weight:500;'>Coefficient Comparison Across Cumulative Logits</div>";
        html += "<div class='table-container' style='margin-top:4px;'>";
        html += "<table class='summary-table'>";
        html += "<thead><tr><th>Variable</th>";

        // Get unique split names
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

    this.proportionalOddsContent.innerHTML = html;

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

    // Sort by VIF descending
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

    const stats = result.statistics || {};
    const diagnostics = result.diagnostics || {};
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

    // Model fit
    const pseudoR2 = stats.mcfadden_pseudo_r_squared;
    if (pseudoR2 !== null && pseudoR2 !== undefined) {
        parts.push(
            "The model explains approximately " + this.formatPercent(pseudoR2) +
            " of the variance (McFadden R² = " + this.formatNumberOrDash(pseudoR2) + ")."
        );
    }

    // Likelihood ratio test
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

    // Significant predictors
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
            const direction = c.coefficient > 0 ? "increased" : "decreased";
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

    // VIF warnings
    const highVif = (result.vif || []).filter(e => e.vif > 10);
    if (highVif.length > 0) {
        parts.push(
            "Note: " +
            highVif.map(e => this.formatLabel(e.variable)).join(", ") +
            " showed high Variance Inflation Factor (VIF > 10), indicating possible multicollinearity."
        );
    }

    // Convergence
    const converged = result.converged !== undefined ? result.converged :
                     stats.converged !== undefined ? stats.converged :
                     result.model_status?.converged;
    if (converged === false) {
        parts.push(
            "⚠️ The model did not converge. Results should be interpreted with caution."
        );
    }

    this.interpretationBox.innerHTML =
        parts.join(" ");

    this.interpretationBox.className = "message info";

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

    if (this.modelTypeDisplay) {
        // Already updated in renderModelType
    }

    if (this.totalRecords) {

        const n = result.statistics?.n || result.n || 0;
        this.totalRecords.textContent = formatNumber(n);

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

    // Reset model fit strip
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

    // Reset diagnostics
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

    // Reset classification
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

    // Reset multinomial classification
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

    // Reset Hosmer-Lemeshow
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

    // Reset proportional odds
    if (this.proportionalOddsSection) {
        this.proportionalOddsSection.style.display = "none";
    }
    if (this.proportionalOddsContent) {
        this.proportionalOddsContent.innerHTML = "<p style='color:#64748b;'>Run regression to see proportional odds diagnostic.</p>";
    }

    // Reset VIF
    if (this.vifSection) {
        this.vifSection.style.display = "none";
    }
    if (this.vifTableBody) {
        this.vifTableBody.innerHTML = "";
    }

    // Reset interpretation
    if (this.interpretationBox) {

        this.interpretationBox.innerHTML =
            "Run a regression analysis to generate the statistical interpretation.";

        this.interpretationBox.className = "message info";

    }

    // Reset outcome distribution
    if (this.outcomeDistributionBody) {
        this.outcomeDistributionBody.innerHTML =
            "<tr><td colspan='3' style='text-align:center; color:#94a3b8;'>Run regression to see outcome distribution.</td></tr>";
    }

    // Reset info strip
    if (this.modelTypeDisplay) {
        this.modelTypeDisplay.textContent = "—";
    }
    if (this.totalRecords) {
        this.totalRecords.textContent = "—";
    }
    if (this.reportGeneratedValue) {
        this.reportGeneratedValue.textContent = "—";
    }

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

    const coefficients = this.lastResult.coefficients || [];
    if (coefficients.length === 0) {
        if (typeof showMessage === "function") {
            showMessage("No coefficients available to export.", "error");
        }
        return;
    }

    // Build CSV
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

    // Download
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


/* ==========================================================
   FORMAT "YYYY-MM" AS "Jan 2025"   (NEW)
   ========================================================== */

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


/* ==========================================================
   BUILD PERIOD TEXT   (NEW)
   ========================================================== */

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


/* ==========================================================
   SIGNIFICANCE MARKER
   ========================================================== */

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


/* ==========================================================
   TABLE CELL HELPERS
   ========================================================== */

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