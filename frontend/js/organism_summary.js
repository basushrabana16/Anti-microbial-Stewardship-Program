/* ==========================================================
   AMSP - ORGANISM SUMMARY
   ========================================================== */

"use strict";


/* ==========================================================
   ORGANISM SUMMARY OBJECT
   ========================================================== */

const OrganismSummary = {

    endpoint:
        "http://127.0.0.1:5000/organisms",

    data: null,

    filters: null

};


/* ==========================================================
   INITIALIZE PAGE
   ========================================================== */

OrganismSummary.initialize = async function () {

    this.cacheElements();

    this.registerEvents();

    await this.loadSummary();

};


/* ==========================================================
   CACHE DOM ELEMENTS
   ========================================================== */

OrganismSummary.cacheElements = function () {

    this.cultureBody =
        document.getElementById(
            "culturePositivityBody"
        );

    this.organismBody =
        document.getElementById(
            "organismDistributionBody"
        );

    this.cultureGroupsContainer =
        document.getElementById(
            "culturePositivityGroups"
        );

    this.organismBySampleContainer =
        document.getElementById(
            "organismDistributionBySample"
        );

    this.filtersAppliedText =
        document.getElementById(
            "filtersAppliedText"
        );

    this.totalSamplesValue =
        document.getElementById(
            "totalSamplesValue"
        );

    this.reportGeneratedValue =
        document.getElementById(
            "reportGeneratedValue"
        );

};


/* ==========================================================
   REGISTER EVENTS
   ========================================================== */

OrganismSummary.registerEvents = function () {

    document.addEventListener(

        "filtersChanged",

        async () => {

            await this.loadSummary();

        }

    );


    /* ----------------------------------------------
       Export Table placeholders
    ---------------------------------------------- */

    document
        .querySelectorAll("[data-export-target]")
        .forEach(button => {

            button.addEventListener(

                "click",

                () => {

                    if (
                        typeof showMessage ===
                        "function"
                    ) {

                        showMessage(

                            "Export is not available yet. This button is a placeholder.",

                            "info"

                        );

                    }

                }

            );

        });

};


/* ==========================================================
   LOAD SUMMARY
   ========================================================== */

OrganismSummary.loadSummary = async function () {

    try {

        this.showLoading();


        /* ------------------------------------------
           GET CURRENT FILTER STATE
        ------------------------------------------ */

        this.filters =
            FilterManager.getFilters();


        /* ------------------------------------------
           BUILD QUERY
        ------------------------------------------ */

        const query =
            this.buildQueryString();


        /* ------------------------------------------
           FETCH DATA
        ------------------------------------------ */

        const response =
            await fetch(

                this.endpoint + query

            );


        if (!response.ok) {

            throw new Error(

                "Unable to fetch organism summary."

            );

        }


        this.data =
            await response.json();


        /* ------------------------------------------
           RENDER
        ------------------------------------------ */

        this.render();

    }

    catch (error) {

        console.error(error);

        this.showError(
            error.message
        );

    }

    finally {

        this.hideLoading();

    }

};


/* ==========================================================
   BUILD QUERY STRING
   ==========================================================

   IMPORTANT:

   District, block, sample_type and organisms are
   multi-select filters.

   Example:

   district=Udupi
   district=Dakshina%20Kannada

   instead of:

   district=Udupi,Dakshina%20Kannada

   from_month / to_month ("YYYY-MM") are sent
   only when a month has been chosen.
   ========================================================== */

OrganismSummary.buildQueryString = function () {

    const params =
        new URLSearchParams();


    /* ==================================================
       TIME DURATION (MONTH-YEAR)
       ================================================== */

    if (this.filters.from_month) {

        params.append(

            "from_month",

            this.filters.from_month

        );

    }


    if (this.filters.to_month) {

        params.append(

            "to_month",

            this.filters.to_month

        );

    }


    /* ==================================================
       DISTRICT
       ================================================== */

    const districts =
        Array.isArray(this.filters.district)

            ? this.filters.district

            : [this.filters.district];


    districts.forEach(district => {

        if (

            district &&

            district.toLowerCase() !== "all"

        ) {

            params.append(

                "district",

                district

            );

        }

    });


    /* ==================================================
       BLOCK
       ================================================== */

    const blocks =
        Array.isArray(this.filters.block)

            ? this.filters.block

            : [this.filters.block];


    blocks.forEach(block => {

        if (

            block &&

            block.toLowerCase() !== "all"

        ) {

            params.append(

                "block",

                block

            );

        }

    });


    /* ==================================================
       SAMPLE TYPE
       ================================================== */

    const sampleTypes =
        Array.isArray(
            this.filters.sample_type
        )

            ? this.filters.sample_type

            : [this.filters.sample_type];


    sampleTypes.forEach(sampleType => {

        if (

            sampleType &&

            sampleType.toLowerCase() !== "all"

        ) {

            params.append(

                "sample_type",

                sampleType

            );

        }

    });


    /* ==================================================
       ORGANISMS
       ================================================== */

    const organisms =
        Array.isArray(this.filters.organisms)

            ? this.filters.organisms

            : [this.filters.organisms];


    organisms.forEach(organism => {

        if (

            organism &&

            organism.toLowerCase() !== "all"

        ) {

            params.append(

                "organisms",

                organism

            );

        }

    });


    return "?" + params.toString();

};


/* ==========================================================
   RENDER COMPLETE PAGE
   ========================================================== */

OrganismSummary.render = function () {

    this.renderCulturePositivity(

        this.data.culture_positivity || []

    );


    this.renderCulturePositivityGroups(

        this.data.culture_positivity_groups || []

    );


    this.renderOrganismDistribution(

        this.data.organism_distribution || []

    );


    this.renderOrganismDistributionBySample(

        this.data.organism_distribution_by_sample || []

    );


    this.updateInfoStrip(

        this.data.culture_positivity || []

    );

};


/* ==========================================================
   RENDER CULTURE POSITIVITY TABLE (CUMULATIVE)
   ========================================================== */

OrganismSummary.renderCulturePositivity = function (data) {

    if (!this.cultureBody) {

        return;

    }


    this.cultureBody.innerHTML = "";


    if (
        !data ||
        data.length === 0
    ) {

        this.cultureBody.appendChild(

            this.createEmptyRow(

                3,

                "No culture positivity data available."

            )

        );

        return;

    }


    data.forEach(item => {

        const row =
            document.createElement("tr");


        row.appendChild(

            this.createCell(
                item.Result
            )

        );


        row.appendChild(

            this.createNumberCell(
                item.Count
            )

        );


        row.appendChild(

            this.createPercentageCell(
                item.Percentage
            )

        );


        this.cultureBody.appendChild(row);

    });


    /* ----------------------------------------------
       TOTAL ROW
    ---------------------------------------------- */

    const totalCount =

        data.reduce(

            (sum, item) =>

                sum +
                (Number(item.Count) || 0),

            0

        );


    this.cultureBody.appendChild(

        this.createTotalRow([

            "Total",

            this.formatNumber(
                totalCount
            ),

            this.formatPercentage(100)

        ])

    );

};


/* ==========================================================
   RENDER TABLE 1 GROUPS (SAMPLE TYPE × ORGANISM)
   ========================================================== */

OrganismSummary.renderCulturePositivityGroups = function (groups) {

    if (!this.cultureGroupsContainer) {

        return;

    }


    this.cultureGroupsContainer.innerHTML = "";


    if (
        !groups ||
        groups.length === 0
    ) {

        return;

    }


    groups.forEach(group => {

        const section =
            document.createElement("section");

        section.className =
            "report-card";


        /* ------------------------------------------
           GROUP HEADER
        ------------------------------------------ */

        const header =
            document.createElement("div");

        header.className =
            "card-header";


        const headerInner =
            document.createElement("div");


        const heading =
            document.createElement("h3");

        heading.textContent =
            "Sample Type: " +
            (group.sample_type || "Unspecified");


        const subtitle =
            document.createElement("p");

        subtitle.textContent =
            "Total cultures: " +
            this.formatNumber(group.total_cultures);


        headerInner.appendChild(heading);

        headerInner.appendChild(subtitle);

        header.appendChild(headerInner);

        section.appendChild(header);


        /* ------------------------------------------
           ONE SUB-TABLE PER { title, rows }
        ------------------------------------------ */

        (group.tables || []).forEach(entry => {

            const wrapper =
                document.createElement("div");

            wrapper.className =
                "table-container";


            const subTitle =
                document.createElement("h4");

            subTitle.style.margin =
                "0 0 10px 0";

            subTitle.style.fontSize =
                "14px";

            subTitle.style.fontWeight =
                "600";

            subTitle.textContent =
                entry.title || "";


            wrapper.appendChild(subTitle);

            wrapper.appendChild(

                this.buildPositivitySubTable(
                    entry.rows
                )

            );


            section.appendChild(wrapper);

        });


        this.cultureGroupsContainer.appendChild(section);

    });

};


/* ==========================================================
   BUILD ONE TABLE 1 SUB-TABLE
   ========================================================== */

OrganismSummary.buildPositivitySubTable = function (rows) {

    const table =
        document.createElement("table");

    table.className =
        "summary-table";


    /* ------------------------------------------
       HEADER
    ------------------------------------------ */

    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    [
        { label: "Result",         width: "45%" },
        { label: "Count (n)",      width: "25%" },
        { label: "Percentage (%)", width: "30%" }
    ].forEach(column => {

        const th =
            document.createElement("th");

        th.style.width =
            column.width;

        th.textContent =
            column.label;

        headerRow.appendChild(th);

    });


    thead.appendChild(headerRow);

    table.appendChild(thead);


    /* ------------------------------------------
       BODY
    ------------------------------------------ */

    const tbody =
        document.createElement("tbody");


    let totalCount = 0;


    (rows || []).forEach(item => {

        const row =
            document.createElement("tr");


        row.appendChild(

            this.createCell(
                item.Result
            )

        );


        row.appendChild(

            this.createNumberCell(
                item.Count
            )

        );


        row.appendChild(

            this.createPercentageCell(
                item.Percentage
            )

        );


        tbody.appendChild(row);


        totalCount +=
            (Number(item.Count) || 0);

    });


    tbody.appendChild(

        this.createTotalRow([

            "Total",

            this.formatNumber(
                totalCount
            ),

            this.formatPercentage(100)

        ])

    );


    table.appendChild(tbody);


    return table;

};


/* ==========================================================
   RENDER ORGANISM DISTRIBUTION TABLE (CUMULATIVE)
   ========================================================== */

OrganismSummary.renderOrganismDistribution = function (data) {

    if (!this.organismBody) {

        return;

    }


    this.organismBody.innerHTML = "";


    if (
        !data ||
        data.length === 0
    ) {

        this.organismBody.appendChild(

            this.createEmptyRow(

                4,

                "No organism distribution data available."

            )

        );

        return;

    }


    data.forEach(

        (item, index) => {

            const row =
                document.createElement("tr");


            /* --------------------------------------
               Sl. No.
            -------------------------------------- */

            row.appendChild(

                this.createSlNoCell(

                    index + 1

                )

            );


            /* --------------------------------------
               Organism
            -------------------------------------- */

            row.appendChild(

                this.createCell(

                    item.Organism

                )

            );


            /* --------------------------------------
               Count
            -------------------------------------- */

            row.appendChild(

                this.createNumberCell(

                    item.Count

                )

            );


            /* --------------------------------------
               Percentage
            -------------------------------------- */

            row.appendChild(

                this.createPercentageCell(

                    item.Percentage

                )

            );


            this.organismBody.appendChild(row);

        }

    );


    /* ----------------------------------------------
       TOTAL ROW
    ---------------------------------------------- */

    const totalCount =

        data.reduce(

            (sum, item) =>

                sum +
                (Number(item.Count) || 0),

            0

        );


    this.organismBody.appendChild(

        this.createTotalRow([

            "",

            "Total",

            this.formatNumber(
                totalCount
            ),

            this.formatPercentage(100)

        ])

    );

};


/* ==========================================================
   RENDER TABLE 2 PER SAMPLE TYPE
   ========================================================== */

OrganismSummary.renderOrganismDistributionBySample = function (data) {

    if (!this.organismBySampleContainer) {

        return;

    }


    this.organismBySampleContainer.innerHTML = "";


    if (
        !data ||
        data.length === 0
    ) {

        return;

    }


    data.forEach(item => {

        const section =
            document.createElement("section");

        section.className =
            "report-card";


        /* ------------------------------------------
           HEADER
        ------------------------------------------ */

        const header =
            document.createElement("div");

        header.className =
            "card-header";


        const headerInner =
            document.createElement("div");


        const heading =
            document.createElement("h3");

        heading.textContent =
            "Sample Type: " +
            (item.sample_type || "Unspecified");


        const subtitle =
            document.createElement("p");

        subtitle.textContent =
            "Positive cultures with identified organism: " +
            this.formatNumber(item.total_positive);


        headerInner.appendChild(heading);

        headerInner.appendChild(subtitle);

        header.appendChild(headerInner);

        section.appendChild(header);


        /* ------------------------------------------
           SUB-TABLE
        ------------------------------------------ */

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "table-container";


        wrapper.appendChild(

            this.buildOrganismDistributionSubTable(
                item.rows
            )

        );


        section.appendChild(wrapper);

        this.organismBySampleContainer.appendChild(section);

    });

};


/* ==========================================================
   BUILD ONE TABLE 2 SUB-TABLE
   ========================================================== */

OrganismSummary.buildOrganismDistributionSubTable = function (rows) {

    const table =
        document.createElement("table");

    table.className =
        "summary-table";


    /* ------------------------------------------
       HEADER
    ------------------------------------------ */

    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    [
        { label: "Sl. No.",        width: "10%" },
        { label: "Organism",       width: "45%" },
        { label: "Count (n)",      width: "20%" },
        { label: "Percentage (%)", width: "25%" }
    ].forEach(column => {

        const th =
            document.createElement("th");

        th.style.width =
            column.width;

        th.textContent =
            column.label;

        headerRow.appendChild(th);

    });


    thead.appendChild(headerRow);

    table.appendChild(thead);


    /* ------------------------------------------
       BODY
    ------------------------------------------ */

    const tbody =
        document.createElement("tbody");


    let totalCount = 0;


    (rows || []).forEach((item, index) => {

        const row =
            document.createElement("tr");


        row.appendChild(

            this.createSlNoCell(
                index + 1
            )

        );


        row.appendChild(

            this.createCell(
                item.Organism
            )

        );


        row.appendChild(

            this.createNumberCell(
                item.Count
            )

        );


        row.appendChild(

            this.createPercentageCell(
                item.Percentage
            )

        );


        tbody.appendChild(row);


        totalCount +=
            (Number(item.Count) || 0);

    });


    tbody.appendChild(

        this.createTotalRow([

            "",

            "Total",

            this.formatNumber(
                totalCount
            ),

            this.formatPercentage(100)

        ])

    );


    table.appendChild(tbody);


    return table;

};


/* ==========================================================
   CREATE STANDARD TABLE CELL
   ========================================================== */

OrganismSummary.createCell = function (value) {

    const td =
        document.createElement("td");

    td.textContent =
        value ?? "";

    return td;

};


/* ==========================================================
   CREATE NUMBER CELL
   ========================================================== */

OrganismSummary.createNumberCell = function (value) {

    const td =
        document.createElement("td");

    td.className =
        "text-center";

    td.textContent =
        this.formatNumber(value);

    return td;

};


/* ==========================================================
   CREATE PERCENTAGE CELL
   ========================================================== */

OrganismSummary.createPercentageCell = function (value) {

    const td =
        document.createElement("td");

    td.className =
        "text-center";

    td.textContent =
        this.formatPercentage(value);

    return td;

};


/* ==========================================================
   FORMAT NUMBER
   ========================================================== */

OrganismSummary.formatNumber = function (value) {

    if (

        value === null ||

        value === undefined ||

        value === ""

    ) {

        return "-";

    }

    return Number(value).toLocaleString();

};


/* ==========================================================
   FORMAT PERCENTAGE
   ========================================================== */

OrganismSummary.formatPercentage = function (value) {

    if (

        value === null ||

        value === undefined ||

        value === ""

    ) {

        return "-";

    }

    return Number(value).toFixed(2) + "%";

};


/* ==========================================================
   CREATE SL. NO. CELL
   ========================================================== */

OrganismSummary.createSlNoCell = function (value) {

    const td =
        document.createElement("td");

    td.className =
        "sl-no";

    td.textContent =
        value;

    return td;

};


/* ==========================================================
   CREATE TOTAL ROW
   ========================================================== */

OrganismSummary.createTotalRow = function (cellValues) {

    const tr =
        document.createElement("tr");

    tr.className =
        "total-row";


    cellValues.forEach(value => {

        const td =
            document.createElement("td");

        td.textContent =
            value;

        tr.appendChild(td);

    });


    return tr;

};


/* ==========================================================
   CREATE EMPTY ROW
   ========================================================== */

OrganismSummary.createEmptyRow = function (

    colspan,

    message

) {

    const tr =
        document.createElement("tr");


    const td =
        document.createElement("td");


    td.colSpan =
        colspan;


    td.className =
        "table-empty";


    td.textContent =
        message;


    tr.appendChild(td);


    return tr;

};


/* ==========================================================
   UPDATE FILTERS-APPLIED INFO STRIP
   ========================================================== */

OrganismSummary.updateInfoStrip =
    function (culturePositivityData) {

        if (this.filtersAppliedText) {

            const filters =
                this.filters ||
                FilterManager.getFilters();


            /* ------------------------------------------
               Format filter values for display
            ------------------------------------------ */

            const formatFilter = function (value) {

                if (!value) {
                    return "All";
                }


                if (Array.isArray(value)) {

                    const selected =
                        value.filter(

                            item =>
                                String(item)
                                .toLowerCase() !==
                                "all"

                        );


                    if (selected.length === 0) {

                        return "All";

                    }


                    return selected.join(", ");

                }


                return String(value);

            };


            /* ------------------------------------------
               Format "YYYY-MM" as "Jan 2025"
            ------------------------------------------ */

            const formatMonth = function (value) {

                if (!value) {
                    return "";
                }


                const parts =
                    String(value).split("-");


                if (parts.length !== 2) {
                    return String(value);
                }


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


            /* ------------------------------------------
               Period text
            ------------------------------------------ */

            let period = "All";

            if (
                filters.from_month &&
                filters.to_month
            ) {

                period =
                    formatMonth(filters.from_month) +
                    " \u2013 " +
                    formatMonth(filters.to_month);

            }

            else if (filters.from_month) {

                period =
                    "From " +
                    formatMonth(filters.from_month);

            }

            else if (filters.to_month) {

                period =
                    "Up to " +
                    formatMonth(filters.to_month);

            }


            this.filtersAppliedText.textContent =

                "Period: " +

                period +

                "  |  District: " +

                formatFilter(
                    filters.district
                ) +

                "  |  Block: " +

                formatFilter(
                    filters.block
                ) +

                "  |  Sample Type: " +

                formatFilter(
                    filters.sample_type
                ) +

                "  |  Organisms: " +

                formatFilter(
                    filters.organisms
                );

        }


        /* ------------------------------------------
           TOTAL SAMPLES
        ------------------------------------------ */

        if (this.totalSamplesValue) {

            const total =

                (culturePositivityData || [])
                    .reduce(

                        (sum, item) =>

                            sum +
                            (Number(item.Count) || 0),

                        0

                    );


            this.totalSamplesValue.textContent =

                this.formatNumber(total);

        }


        /* ------------------------------------------
           REPORT GENERATED TIME
        ------------------------------------------ */

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
   CLEAR BOTH TABLES
   ========================================================== */

OrganismSummary.clearTables = function () {

    if (this.cultureBody) {

        this.cultureBody.innerHTML = "";

    }


    if (this.organismBody) {

        this.organismBody.innerHTML = "";

    }


    if (this.cultureGroupsContainer) {

        this.cultureGroupsContainer.innerHTML = "";

    }


    if (this.organismBySampleContainer) {

        this.organismBySampleContainer.innerHTML = "";

    }

};


/* ==========================================================
   RESET PAGE
   ========================================================== */

OrganismSummary.reset = function () {

    this.data = null;

    this.clearTables();

};


/* ==========================================================
   REFRESH PAGE
   ========================================================== */

OrganismSummary.refresh = async function () {

    this.reset();

    await this.loadSummary();

};


/* ==========================================================
   GET TOTAL POSITIVE CULTURES
   ========================================================== */

OrganismSummary.getPositiveCount = function () {

    if (!this.data) {

        return 0;

    }


    const table =

        this.data.culture_positivity || [];


    const positive =

        table.find(

            row =>

                row.Result === "Positive"

        );


    return positive

        ? positive.Count

        : 0;

};


/* ==========================================================
   GET TOTAL ORGANISMS
   ========================================================== */

OrganismSummary.getOrganismCount = function () {

    if (!this.data) {

        return 0;

    }


    return (

        this.data.organism_distribution || []

    ).length;

};


/* ==========================================================
   SHOW LOADING
   ========================================================== */

OrganismSummary.showLoading = function () {

    const overlay =
        document.getElementById(
            "loadingOverlay"
        );


    if (overlay) {

        overlay.style.display =
            "flex";

    }

};


/* ==========================================================
   HIDE LOADING
   ========================================================== */

OrganismSummary.hideLoading = function () {

    const overlay =
        document.getElementById(
            "loadingOverlay"
        );


    if (overlay) {

        overlay.style.display =
            "none";

    }

};


/* ==========================================================
   SHOW ERROR
   ========================================================== */

OrganismSummary.showError = function (message) {

    console.error(message);


    this.clearTables();


    if (this.cultureBody) {

        this.cultureBody.appendChild(

            this.createEmptyRow(

                3,

                message

            )

        );

    }


    if (this.organismBody) {

        this.organismBody.appendChild(

            this.createEmptyRow(

                4,

                message

            )

        );

    }

};


/* ==========================================================
   EXPORT OBJECT
   ========================================================== */

window.OrganismSummary =
    OrganismSummary;


/* ==========================================================
   INITIALIZE PAGE
   ========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    async function () {

        try {

            /* -----------------------------------------
               Initialize shared filters
            ----------------------------------------- */

            if (

                typeof FilterManager !==
                "undefined"

            ) {

                await FilterManager.initialise();

            }


            /* -----------------------------------------
               Load organism summary
            ----------------------------------------- */

            await OrganismSummary.initialize();

        }

        catch (error) {

            console.error(error);


            OrganismSummary.showError(

                "Failed to initialize Organism Summary."

            );

        }

    }

);