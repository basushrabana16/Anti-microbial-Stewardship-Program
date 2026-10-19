/* ==========================================================
   FILTER MANAGER
   Shared Cascading Filter Manager

   Cascading hierarchy:

       Time Duration (From Month / To Month)   <-- NEW
           ↓
       District
           ↓
       Block
           ↓
       Sample Type
           ↓
       Organism
           ↓
       Antibiotic

   ALL filters support:

       All
       OR
       Multiple selected values

   The time duration filter uses two month pickers
   (<input type="month">) and is applied to the
   prescription_date column on the backend.
   Values are "YYYY-MM" strings; "" means no limit.

   Used by:
       - Organism Summary
       - Antibiogram
       - Association Tests
       - Regression
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

    from_month: "",        /* NEW */

    to_month: "",          /* NEW */

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

    fromMonth: null,       /* NEW */

    toMonth: null,         /* NEW */

    district: null,

    block: null,

    sampleType: null,

    organisms: null,

    antibiotics: null

};


/* ==========================================================
   MONTH DEFAULTS   (NEW)

   From  -> earliest prescription month in the database
   To    -> the current month (today)

   The pickers SHOW these defaults, but a value equal to
   its default is NOT sent to the backend. That way the
   default view behaves like "All" (no restriction) and
   rows with a missing prescription_date are not dropped
   until the user actually narrows the period.
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

    /*
       NEW: month-year pickers.

       These are plain <input type="month"> elements:

           <input type="month" id="fromMonth">
           <input type="month" id="toMonth">

       If a page does not have them, the controls stay
       null and everything else works as before.
    */

    this.controls.fromMonth =
        document.getElementById("fromMonth");


    this.controls.toMonth =
        document.getElementById("toMonth");


    /*
       ALL other filters are multi-select.

       District:
           All OR multiple districts

       Block:
           All OR multiple blocks

       Sample Type:
           All OR multiple sample types

       Organisms:
           All OR multiple organisms

       Antibiotics:
           All OR multiple antibiotics
    */

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
            this.state.from_month,          /* NEW */

        to_month:
            this.state.to_month,            /* NEW */

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
   ========================================================== */

FilterManager.loadOptions = async function () {

    const query =
        this.buildQueryString();


    const data =
        await apiGet(
            this.endpoint + query
        );


    if (!data)
        return;


    /*
       Before populating dependent controls,
       make sure the current state is still valid.

       This prevents stale selections such as:

           District = Dakshina Kannada
           Block = block belonging only to Udupi
    */

    this.synchroniseStateWithOptions(data);


    this.populateFilters(data);


    /*
       Let page-specific modules read fields
       FilterManager does not itself model.
    */

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


    /*
       NEW: Time duration (month-year).

       Only sent when a month is actually chosen.
       Backend parameter names: from_month, to_month
    */

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


    /*
       District
    */

    this.state.district.forEach(
        value => {

            params.append(
                "district",
                value
            );

        }
    );


    /*
       Block
    */

    this.state.block.forEach(
        value => {

            params.append(
                "block",
                value
            );

        }
    );


    /*
       Sample Type
    */

    this.state.sample_type.forEach(
        value => {

            params.append(
                "sample_type",
                value
            );

        }
    );


    /*
       Organisms
    */

    this.state.organisms.forEach(
        value => {

            params.append(
                "organisms",
                value
            );

        }
    );


    /*
       Antibiotics are intentionally NOT sent
       to /antibiogram-options.

       Antibiotics are the final-level options
       generated by the selected organism(s).

       They will be sent when the actual analysis
       request is made.
    */


    return "?" + params.toString();

};


/* ==========================================================
   APPLY MONTH PICKER BOUNDS   (NEW)
   ========================================================== */

FilterManager.applyMonthBounds = function (data) {

    /*
       The backend returns the earliest and latest
       prescription month in the FULL dataset:

           data.date_range = { min: "YYYY-MM", max: "YYYY-MM" }

       min  -> default and lower limit for both pickers
       today's month -> default and upper limit
    */

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


    /*
       Fill the defaults only until the user has touched
       the pickers (or pressed Reset, which restores them).
    */

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

    this.applyMonthBounds(data);          /* NEW */


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


    /*
       Make sure selected is always an array.
    */

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


        /*
           "all" is selected when state contains "all".
        */

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


    /*
       If there is no valid selection,
       automatically select All.
    */

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


    /*
       Nothing selected / All selected
    */

    if (checked.length === 0) {

        control.button.textContent =
            "All";

    }


    /*
       One value selected
    */

    else if (checked.length === 1) {

        control.button.textContent =
            checked[0].value;

    }


    /*
       Multiple values selected
    */

    else {

        control.button.textContent =
            checked.length + " selected";

    }

};


/* ==========================================================
   ATTACH EVENT LISTENERS
   ========================================================== */

FilterManager.attachEvents = function () {

    this.attachMonthEvents();             /* NEW */


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


    /* --------------------------------------------------
       Close dropdowns when clicking outside
    -------------------------------------------------- */

    document.addEventListener(
        "click",
        () => {

            this.closeAllPanels();

        }
    );


    /* --------------------------------------------------
       Generate Report
    -------------------------------------------------- */

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


    /* --------------------------------------------------
       Reset Filters
    -------------------------------------------------- */

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
   MONTH PICKER EVENTS   (NEW)
   ========================================================== */

FilterManager.attachMonthEvents = function () {

    const handler = async event => {

        this.monthsTouched = true;

        /*
           Keep From <= To.
        */

        this.enforceMonthOrder(
            event.target
        );


        /*
           Save the new months.
        */

        this.updateState();


        /*
           Time is the top-level filter, so changing it
           resets every dependent filter.
        */

        this.resetDependentFilters(
            "month"
        );


        /*
           Refresh cascading options.

           Report data itself is NOT regenerated.
        */

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
   KEEP FROM <= TO   (NEW)
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


    /*
       "YYYY-MM" strings compare correctly as text.
       If the range is reversed, move the OTHER picker
       to match the one the user just changed.
    */

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


    /*
       Prevent clicking inside the panel
       from closing the dropdown.
    */

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


            /*
               ALL filters now use multi-select
               behaviour.
            */

            this.handleMultiSelection(
                control,
                event.target
            );


            this.updateButtonLabel(
                control
            );


            /*
               Save the changed filter.
            */

            this.updateState();


            /*
               Reset dependent filters.

               Example:

                   District changes
                       ↓
                   Block reset
                       ↓
                   Sample Type reset
                       ↓
                   Organism reset
                       ↓
                   Antibiotic reset
            */

            this.resetDependentFilters(
                control
            );


            /*
               Refresh cascading options.

               Report data itself is NOT regenerated.
            */

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


    /*
       User selected ALL.
    */

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


    /*
       User selected a specific value.
       Remove ALL.
    */

    else if (
        checkbox !== allBox
        &&
        checkbox.checked
    ) {

        allBox.checked =
            false;

    }


    /*
       User deselected a value.
       If nothing remains selected,
       restore ALL.
    */

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

    /*
       NEW: month pickers ("" when empty / not on page)
    */

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

    /*
       NEW: Month changed
       → reset District, Block, Sample Type,
         Organisms and Antibiotics
    */

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


    /*
       District changed
       → reset Block, Sample Type,
         Organisms and Antibiotics
    */

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


    /*
       Block changed
       → reset Sample Type,
         Organisms and Antibiotics
    */

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


    /*
       Sample Type changed
       → reset Organisms and Antibiotics
    */

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


    /*
       Organism changed
       → reset Antibiotics
    */

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

        /*
           District
        */

        this.state.district =
            this.keepValidSelections(
                this.state.district,
                data.districts || ["all"]
            );


        /*
           Block
        */

        this.state.block =
            this.keepValidSelections(
                this.state.block,
                data.blocks || ["all"]
            );


        /*
           Sample Type
        */

        this.state.sample_type =
            this.keepValidSelections(
                this.state.sample_type,
                data.sample_types || ["all"]
            );


        /*
           Organisms
        */

        this.state.organisms =
            this.keepValidSelections(
                this.state.organisms,
                data.organisms || ["all"]
            );


        /*
           Antibiotics
        */

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


        /*
           If ALL is available and the current
           selection is ALL, keep ALL.
        */

        if (
            selectedValues.some(
                value =>
                    String(value).toLowerCase() ===
                    "all"
            )
        ) {

            return ["all"];

        }


        /*
           Keep only values that still exist
           in the new cascading options.
        */

        const valid =
            selectedValues.filter(
                value =>
                    availableValues.has(
                        String(value)
                    )
            );


        /*
           Nothing valid remains.
           Return ALL.
        */

        if (valid.length === 0) {

            return ["all"];

        }


        return valid;

    };


/* ==========================================================
   NOTIFY OTHER MODULES
   ========================================================== */

FilterManager.notifyChange = function () {

    document.dispatchEvent(

        new CustomEvent(
            "filtersChanged",
            {
                detail:
                    this.getFilters()
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

        from_month: "",          /* NEW */

        to_month: "",            /* NEW */

        district: ["all"],

        block: ["all"],

        sample_type: ["all"],

        organisms: ["all"],

        antibiotics: ["all"]

    };


    /*
       NEW: put the month pickers back to their defaults
       (earliest month in the data, current month).
    */

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