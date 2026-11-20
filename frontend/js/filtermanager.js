/* ==========================================================
   FILTER MANAGER
   Shared Cascading Filter Manager
   ========================================================== */

"use strict";


/* ==========================================================
   FILTER MANAGER OBJECT
   ========================================================== */

const FilterManager = {};


/* ==========================================================
   API ENDPOINT
   ========================================================== */

FilterManager.endpoint =
    "/antibiogram-options";


/* ==========================================================
   FILTER STATE
   ========================================================== */

FilterManager.state = {

    from_month: "",

    to_month: "",

    district: ["all"],

    block: ["all"],

    sample_type: ["all"],

    organisms: ["all"],

    antibiotics: ["all"]

};


/* ==========================================================
   DOM REFERENCES
   ========================================================== */

FilterManager.controls = {

    fromMonth: null,

    toMonth: null,

    district: null,

    block: null,

    sampleType: null,

    organisms: null,

    antibiotics: null

};


/* ==========================================================
   REQUEST SEQUENCE COUNTER
   Guards loadOptions() against stale async responses.
   ========================================================== */

FilterManager._optionsRequestSeq = 0;


/* ==========================================================
   MONTH DEFAULTS
   ========================================================== */

FilterManager.defaults = {

    from_month: "",

    to_month: ""

};


FilterManager.monthsTouched = false;


FilterManager.currentMonth = function () {

    const now =
        new Date();

    return (

        now.getFullYear() +
        "-" +
        String(now.getMonth() + 1).padStart(2, "0")

    );

};


FilterManager.effectiveMonth = function (value, defaultValue) {

    if (!value)
        return "";

    return value === defaultValue
        ? ""
        : value;

};


/* ==========================================================
   INITIALISE
   ========================================================== */

FilterManager.initialise = async function () {

    this.cacheControls();

    this.attachEvents();

    await this.loadOptions();

};


/* ==========================================================
   CACHE DOM ELEMENTS
   ========================================================== */

FilterManager.cacheControls = function () {

    this.controls.fromMonth =
        document.getElementById("fromMonth");


    this.controls.toMonth =
        document.getElementById("toMonth");


    this.controls.district =
        this.buildControl("districtFilter", "multi");


    this.controls.block =
        this.buildControl("blockFilter", "multi");


    this.controls.sampleType =
        this.buildControl("sampleTypeFilter", "multi");


    this.controls.organisms =
        this.buildControl("organismsFilter", "multi");


    this.controls.antibiotics =
        this.buildControl("antibioticsFilter", "multi");

};


FilterManager.buildControl = function (id, mode) {

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

        mode

    };

};


/* ==========================================================
   GET CURRENT FILTERS
   ========================================================== */

FilterManager.getFilters = function () {

    return {

        from_month:
            this.state.from_month,

        to_month:
            this.state.to_month,

        district:
            [...this.state.district],

        block:
            [...this.state.block],

        sample_type:
            [...this.state.sample_type],

        organisms:
            [...this.state.organisms],

        antibiotics:
            [...this.state.antibiotics]

    };

};


/* ==========================================================
   HAS ANTIBIOTIC FILTER?
   ========================================================== */

FilterManager.hasAntibioticFilter = function () {

    return this.controls.antibiotics !== null;

};


/* ==========================================================
   LOAD FILTER OPTIONS FROM BACKEND
   ==========================================================
   Guards against stale async responses using a sequence
   counter. If a newer loadOptions() has started before an
   older response arrives, the older response is discarded.

   Without this guard, two overlapping option fetches (e.g.
   when the user ticks two organisms in quick succession)
   can overwrite `state.organisms` with an out-of-date
   response that does not contain the user's latest pick.
   ========================================================== */

FilterManager.loadOptions = async function () {

    const seq =
        ++this._optionsRequestSeq;


    const query =
        this.buildQueryString();


    const data =
        await apiGet(
            this.endpoint + query
        );


    /* ----------------------------------------------
       Discard stale response
    ---------------------------------------------- */

    if (seq !== this._optionsRequestSeq)
        return;


    if (!data)
        return;


    this.synchroniseStateWithOptions(data);


    this.populateFilters(data);


    document.dispatchEvent(

        new CustomEvent(
            "filterOptionsLoaded",
            {
                detail: data
            }
        )

    );

};


/* ==========================================================
   BUILD QUERY STRING
   ========================================================== */

FilterManager.buildQueryString = function () {

    const params =
        new URLSearchParams();


    if (this.state.from_month) {

        params.append(
            "from_month",
            this.state.from_month
        );

    }


    if (this.state.to_month) {

        params.append(
            "to_month",
            this.state.to_month
        );

    }


    this.state.district.forEach(
        value => {

            params.append(
                "district",
                value
            );

        }
    );


    this.state.block.forEach(
        value => {

            params.append(
                "block",
                value
            );

        }
    );


    this.state.sample_type.forEach(
        value => {

            params.append(
                "sample_type",
                value
            );

        }
    );


    this.state.organisms.forEach(
        value => {

            params.append(
                "organisms",
                value
            );

        }
    );


    return "?" + params.toString();

};


/* ==========================================================
   APPLY MONTH PICKER BOUNDS
   ========================================================== */

FilterManager.applyMonthBounds = function (data) {

    const range =
        data.date_range || {};

    const today =
        this.currentMonth();

    const upper =
        (range.max && range.max > today)
            ? range.max
            : today;

    this.defaults.from_month =
        range.min || "";

    this.defaults.to_month =
        today;


    [
        this.controls.fromMonth,
        this.controls.toMonth
    ].forEach(input => {

        if (!input)
            return;

        if (range.min)
            input.min = range.min;

        input.max = upper;

    });


    if (!this.monthsTouched) {

        if (
            this.controls.fromMonth &&
            !this.controls.fromMonth.value &&
            this.defaults.from_month
        ) {

            this.controls.fromMonth.value =
                this.defaults.from_month;

        }

        if (
            this.controls.toMonth &&
            !this.controls.toMonth.value
        ) {

            this.controls.toMonth.value =
                this.defaults.to_month;

        }

    }

};


/* ==========================================================
   POPULATE ALL FILTERS
   ========================================================== */

FilterManager.populateFilters = function (data) {

    this.applyMonthBounds(data);


    this.populateControl(

        this.controls.district,

        data.districts || ["all"],

        this.state.district

    );


    this.populateControl(

        this.controls.block,

        data.blocks || ["all"],

        this.state.block

    );


    this.populateControl(

        this.controls.sampleType,

        data.sample_types || ["all"],

        this.state.sample_type

    );


    this.populateControl(

        this.controls.organisms,

        data.organisms || ["all"],

        this.state.organisms

    );


    if (
        this.hasAntibioticFilter()
        &&
        data.antibiotics
    ) {

        this.populateControl(

            this.controls.antibiotics,

            data.antibiotics,

            this.state.antibiotics

        );

    }

};


/* ==========================================================
   POPULATE ONE CHECKBOX DROPDOWN
   ========================================================== */

FilterManager.populateControl = function (
    control,
    values,
    selected
) {

    if (!control)
        return;


    control.panel.innerHTML = "";


    const selectedValues =
        Array.isArray(selected)
            ? selected
            : [selected];


    values.forEach(value => {

        const label =
            document.createElement("label");


        const checkbox =
            document.createElement("input");


        checkbox.type =
            "checkbox";


        checkbox.value =
            value;


        checkbox.checked =
            selectedValues.includes(value);


        label.appendChild(
            checkbox
        );


        label.appendChild(

            document.createTextNode(

                value.toLowerCase() === "all"
                    ? "All"
                    : value

            )

        );


        control.panel.appendChild(
            label
        );

    });


    const checked =
        control.panel.querySelectorAll(
            "input[type='checkbox']:checked"
        );


    if (checked.length === 0) {

        const allBox =
            Array.from(
                control.panel.querySelectorAll(
                    "input[type='checkbox']"
                )
            ).find(
                box =>
                    box.value.toLowerCase() === "all"
            );


        if (allBox) {

            allBox.checked = true;

        }

    }


    this.updateButtonLabel(control);

};


/* ==========================================================
   UPDATE DROPDOWN BUTTON LABEL
   ========================================================== */

FilterManager.updateButtonLabel = function (
    control
) {

    if (!control)
        return;


    const checkboxes =
        Array.from(

            control.panel.querySelectorAll(
                "input[type='checkbox']"
            )

        );


    const checked =
        checkboxes.filter(

            checkbox =>
                checkbox.checked
                &&
                checkbox.value.toLowerCase() !== "all"

        );


    if (checked.length === 0) {

        control.button.textContent =
            "All";

    }

    else if (checked.length === 1) {

        control.button.textContent =
            checked[0].value;

    }

    else {

        control.button.textContent =
            checked.length + " selected";

    }

};


/* ==========================================================
   ATTACH EVENT LISTENERS
   ========================================================== */

FilterManager.attachEvents = function () {

    this.attachMonthEvents();


    this.attachToggle(
        this.controls.district
    );


    this.attachToggle(
        this.controls.block
    );


    this.attachToggle(
        this.controls.sampleType
    );


    this.attachToggle(
        this.controls.organisms
    );


    this.attachToggle(
        this.controls.antibiotics
    );


    this.attachPanelEvents(
        this.controls.district
    );


    this.attachPanelEvents(
        this.controls.block
    );


    this.attachPanelEvents(
        this.controls.sampleType
    );


    this.attachPanelEvents(
        this.controls.organisms
    );


    this.attachPanelEvents(
        this.controls.antibiotics
    );


    document.addEventListener(
        "click",
        () => {

            this.closeAllPanels();

        }
    );


    const generateButton =
        document.getElementById(
            "generateReport"
        );


    if (generateButton) {

        generateButton.addEventListener(

            "click",

            () => {

                this.updateState();

                this.notifyChange();

            }

        );

    }


    const resetButton =
        document.getElementById(
            "resetFilters"
        );


    if (resetButton) {

        resetButton.addEventListener(

            "click",

            async () => {

                await this.resetAll();

                this.notifyChange();

            }

        );

    }

};


/* ==========================================================
   MONTH PICKER EVENTS
   ========================================================== */

FilterManager.attachMonthEvents = function () {

    const handler = async event => {

        this.monthsTouched = true;

        this.enforceMonthOrder(
            event.target
        );

        this.updateState();

        this.resetDependentFilters(
            "month"
        );

        await this.loadOptions();

    };


    [
        this.controls.fromMonth,
        this.controls.toMonth
    ].forEach(input => {

        if (!input)
            return;

        input.addEventListener(
            "change",
            handler
        );

    });

};


/* ==========================================================
   KEEP FROM <= TO
   ========================================================== */

FilterManager.enforceMonthOrder = function (
    changedInput
) {

    const from =
        this.controls.fromMonth;

    const to =
        this.controls.toMonth;


    if (!from || !to)
        return;

    if (!from.value || !to.value)
        return;


    if (from.value > to.value) {

        if (changedInput === from) {

            to.value = from.value;

        }

        else {

            from.value = to.value;

        }

    }

};


/* ==========================================================
   TOGGLE DROPDOWN
   ========================================================== */

FilterManager.attachToggle = function (
    control
) {

    if (!control)
        return;


    control.button.addEventListener(

        "click",

        event => {

            event.stopPropagation();


            const isOpen =
                control.panel.classList.contains(
                    "show"
                );


            this.closeAllPanels();


            if (!isOpen) {

                control.panel.classList.add(
                    "show"
                );

            }

        }

    );


    control.panel.addEventListener(

        "click",

        event => {

            event.stopPropagation();

        }

    );

};


/* ==========================================================
   CLOSE ALL DROPDOWNS
   ========================================================== */

FilterManager.closeAllPanels = function () {

    document

        .querySelectorAll(
            ".dropdown-panel.show"
        )

        .forEach(
            panel => {

                panel.classList.remove(
                    "show"
                );

            }
        );

};


/* ==========================================================
   HANDLE CHECKBOX CHANGES
   ========================================================== */

FilterManager.attachPanelEvents = function (
    control
) {

    if (!control)
        return;


    control.panel.addEventListener(

        "change",

        async event => {

            if (
                event.target.type !==
                "checkbox"
            )
                return;


            this.handleMultiSelection(
                control,
                event.target
            );


            this.updateButtonLabel(
                control
            );


            this.updateState();


            this.resetDependentFilters(
                control
            );


            await this.loadOptions();

        }

    );

};


/* ==========================================================
   MULTI-SELECT "ALL" LOGIC
   ========================================================== */

FilterManager.handleMultiSelection = function (
    control,
    checkbox
) {

    const checkboxes =
        Array.from(

            control.panel.querySelectorAll(
                "input[type='checkbox']"
            )

        );


    const allBox =
        checkboxes.find(

            box =>
                box.value.toLowerCase() ===
                "all"

        );


    if (!allBox)
        return;


    if (
        checkbox === allBox
        &&
        checkbox.checked
    ) {

        checkboxes.forEach(
            box => {

                if (box !== allBox) {

                    box.checked =
                        false;

                }

            }
        );

    }

    else if (
        checkbox !== allBox
        &&
        checkbox.checked
    ) {

        allBox.checked =
            false;

    }


    const specificSelections =
        checkboxes.filter(

            box =>
                box !== allBox
                &&
                box.checked

        );


    if (
        specificSelections.length === 0
    ) {

        allBox.checked =
            true;

    }

};


/* ==========================================================
   UPDATE INTERNAL STATE FROM DOM
   ========================================================== */

FilterManager.updateState = function () {

    this.state.from_month =
        this.controls.fromMonth
            ? this.effectiveMonth(
                this.controls.fromMonth.value,
                this.defaults.from_month
            )
            : "";


    this.state.to_month =
        this.controls.toMonth
            ? this.effectiveMonth(
                this.controls.toMonth.value,
                this.defaults.to_month
            )
            : "";


    this.state.district =
        this.getMultiValues(
            this.controls.district
        );


    this.state.block =
        this.getMultiValues(
            this.controls.block
        );


    this.state.sample_type =
        this.getMultiValues(
            this.controls.sampleType
        );


    this.state.organisms =
        this.getMultiValues(
            this.controls.organisms
        );


    this.state.antibiotics =
        this.getMultiValues(
            this.controls.antibiotics
        );

};


/* ==========================================================
   GET MULTI-SELECT VALUES
   ========================================================== */

FilterManager.getMultiValues = function (
    control
) {

    if (!control)
        return ["all"];


    const checked =
        Array.from(

            control.panel.querySelectorAll(
                "input[type='checkbox']:checked"
            )

        ).map(
            box => box.value
        );


    return checked.length
        ? checked
        : ["all"];

};


/* ==========================================================
   RESET DEPENDENT FILTERS
   ========================================================== */

FilterManager.resetDependentFilters = function (
    changedControl
) {

    if (changedControl === "month") {

        this.state.district =
            ["all"];

        this.state.block =
            ["all"];

        this.state.sample_type =
            ["all"];

        this.state.organisms =
            ["all"];

        this.state.antibiotics =
            ["all"];

        return;

    }


    if (
        changedControl ===
        this.controls.district
    ) {

        this.state.block =
            ["all"];

        this.state.sample_type =
            ["all"];

        this.state.organisms =
            ["all"];

        this.state.antibiotics =
            ["all"];

        return;

    }


    if (
        changedControl ===
        this.controls.block
    ) {

        this.state.sample_type =
            ["all"];

        this.state.organisms =
            ["all"];

        this.state.antibiotics =
            ["all"];

        return;

    }


    if (
        changedControl ===
        this.controls.sampleType
    ) {

        this.state.organisms =
            ["all"];

        this.state.antibiotics =
            ["all"];

        return;

    }


    if (
        changedControl ===
        this.controls.organisms
    ) {

        this.state.antibiotics =
            ["all"];

    }

};


/* ==========================================================
   SYNCHRONISE STATE WITH AVAILABLE OPTIONS
   ========================================================== */

FilterManager.synchroniseStateWithOptions =
    function (data) {

        this.state.district =
            this.keepValidSelections(
                this.state.district,
                data.districts || ["all"]
            );


        this.state.block =
            this.keepValidSelections(
                this.state.block,
                data.blocks || ["all"]
            );


        this.state.sample_type =
            this.keepValidSelections(
                this.state.sample_type,
                data.sample_types || ["all"]
            );


        this.state.organisms =
            this.keepValidSelections(
                this.state.organisms,
                data.organisms || ["all"]
            );


        this.state.antibiotics =
            this.keepValidSelections(
                this.state.antibiotics,
                data.antibiotics || ["all"]
            );

};


/* ==========================================================
   KEEP ONLY VALID SELECTIONS
   ========================================================== */

FilterManager.keepValidSelections =
    function (
        selected,
        available
    ) {

        const selectedValues =
            Array.isArray(selected)
                ? selected
                : [selected];


        const availableValues =
            new Set(
                available.map(
                    value =>
                        String(value)
                )
            );


        if (
            selectedValues.some(
                value =>
                    String(value).toLowerCase() ===
                    "all"
            )
        ) {

            return ["all"];

        }


        const valid =
            selectedValues.filter(
                value =>
                    availableValues.has(
                        String(value)
                    )
            );


        if (valid.length === 0) {

            return ["all"];

        }


        return valid;

    };


/* ==========================================================
   NOTIFY OTHER MODULES
   ========================================================== */

FilterManager.notifyChange = function () {

    const filters =
        this.getFilters();


    console.log(
        "[FilterManager] notifyChange:",
        filters
    );


    document.dispatchEvent(

        new CustomEvent(
            "filtersChanged",
            {
                detail: filters
            }
        )

    );

};


/* ==========================================================
   PUBLIC REFRESH
   ========================================================== */

FilterManager.refresh = async function () {

    this.updateState();

    await this.loadOptions();

};


/* ==========================================================
   RESET EVERYTHING
   ========================================================== */

FilterManager.resetAll = async function () {

    this.state = {

        from_month: "",

        to_month: "",

        district: ["all"],

        block: ["all"],

        sample_type: ["all"],

        organisms: ["all"],

        antibiotics: ["all"]

    };


    this.monthsTouched = false;

    if (this.controls.fromMonth)
        this.controls.fromMonth.value = this.defaults.from_month || "";

    if (this.controls.toMonth)
        this.controls.toMonth.value = this.defaults.to_month || "";


    await this.loadOptions();

};


/* ==========================================================
   BACKWARD-COMPATIBLE ALIAS
   ========================================================== */

FilterManager.reset =
    FilterManager.resetAll;


/* ==========================================================
   EXPORT
   ========================================================== */

window.FilterManager =
    FilterManager;