/* ==========================================================
   AMSP - ANTIBIOGRAM
   ========================================================== */

"use strict";


/* ==========================================================
   ANTIBIOGRAM OBJECT
   ========================================================== */

const Antibiogram = {

    endpoint: "http://127.0.0.1:5000/antibiogram",

    data: null,

    filters: null

};


/* ==========================================================
   INITIALIZE PAGE
   ========================================================== */

Antibiogram.initialize = async function () {

    this.cacheElements();

    this.registerEvents();

    await this.loadReport();

};


/* ==========================================================
   CACHE DOM ELEMENTS
   ========================================================== */

Antibiogram.cacheElements = function () {

    this.container =
        document.getElementById(
            "antibiogramContainer"
        );

    this.filtersAppliedText =
        document.getElementById(
            "filtersAppliedText"
        );

    this.organismCount =
        document.getElementById(
            "organismCount"
        );

    this.antibioticCount =
        document.getElementById(
            "antibioticCount"
        );

    this.reportGeneratedValue =
        document.getElementById(
            "reportGeneratedValue"
        );

};


/* ==========================================================
   REGISTER EVENTS
   ========================================================== */

Antibiogram.registerEvents = function () {

    document.addEventListener(

        "filtersChanged",

        async () => {

            await this.loadReport();

        }

    );

    const exportButton =

        document.getElementById(
            "exportAntibiogram"
        );

    if (exportButton) {

        exportButton.addEventListener(

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

    }

};


/* ==========================================================
   LOAD REPORT
   ========================================================== */

Antibiogram.loadReport = async function () {

    try {

        this.showLoading();

        this.filters =
            FilterManager.getFilters();

        const query =
            this.buildQueryString();

        const response =
            await fetch(

                this.endpoint + query

            );

        if (!response.ok) {

            throw new Error(

                "Unable to fetch antibiogram."

            );

        }

        this.data =
            await response.json();

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
   ========================================================== */

Antibiogram.buildQueryString = function () {

    const params =
        new URLSearchParams();


    // =================================================
    // DISTRICT
    // =================================================

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


    // =================================================
    // BLOCK
    // =================================================

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


    // =================================================
    // SAMPLE TYPE
    // =================================================

    const sampleTypes =
        Array.isArray(this.filters.sample_type)
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


    // =================================================
    // ORGANISMS
    // =================================================

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


    // =================================================
    // ANTIBIOTICS
    // =================================================

    const antibiotics =
        Array.isArray(this.filters.antibiotics)
            ? this.filters.antibiotics
            : [this.filters.antibiotics];


    antibiotics.forEach(antibiotic => {

        if (
            antibiotic &&
            antibiotic.toLowerCase() !== "all"
        ) {

            params.append(
                "antibiotics",
                antibiotic
            );

        }

    });

        // =================================================
    // DATE RANGE
    // =================================================

    const fromMonth =
        document.getElementById("fromMonth")?.value;

    const toMonth =
        document.getElementById("toMonth")?.value;

    if (fromMonth) {

        params.append(
            "from_month",
            fromMonth
        );

    }

    if (toMonth) {

        params.append(
            "to_month",
            toMonth
        );

    }


    return "?" + params.toString();

};



/* ==========================================================
   RENDER COMPLETE REPORT
   ========================================================== */

Antibiogram.render = function () {

    this.clearReport();

    this.renderTables();

    this.updateInfoStrip();

};


/* ==========================================================
   RENDER ALL ORGANISM TABLES
   ========================================================== */

Antibiogram.renderTables = function () {

    if (!this.container) {

        return;

    }


    /*
       The backend returns:

           {
               overall: {              // all selected sample types pooled
                   heading, samples_analysed,
                   combined:  { title, samples_analysed, rows } | null,
                   organisms: [ { title, samples_analysed, rows }, ... ]
               },
               sample_types: [         // one block per sample type
                   { heading, samples_analysed, combined, organisms },
                   ...
               ]
           }
    */

    const overall =
        this.data && this.data.overall;

    const sampleTypes =
        (this.data && this.data.sample_types) || [];


    if (
        !overall ||
        !(overall.organisms || []).length
    ) {

        this.container.appendChild(

            this.createEmptyMessage(

                "No antibiogram data available."

            )

        );

        return;

    }


    /* ------------------------------------------
       How to read "Samples analysed"
    ------------------------------------------ */

    this.container.appendChild(

        this.createNote(

            "Samples analysed = number of positive culture " +
            "reports included in a table. The Total column " +
            "shows how many of them had a valid result for " +
            "that antibiotic."

        )

    );


    /* ------------------------------------------
       Section 1: all selected sample types pooled
    ------------------------------------------ */

    this.renderBlock(
        overall
    );


    /* ------------------------------------------
       One section per sample type
    ------------------------------------------ */

    sampleTypes.forEach(

        block => {

            this.renderBlock(
                block
            );

        }

    );

};


/* ==========================================================
   RENDER ONE BLOCK (heading + combined table + organism tables)
   ========================================================== */

Antibiogram.renderBlock = function (block) {

    this.container.appendChild(

        this.createBlockHeading(

            block.heading,

            block.samples_analysed

        )

    );


    const combined =
        block.combined;

    if (
        combined &&
        (combined.rows || []).length > 0
    ) {

        this.container.appendChild(

            this.createOrganismSection(

                combined.title,

                combined.rows,

                combined.samples_analysed

            )

        );

    }


    (block.organisms || []).forEach(

        table => {

            this.container.appendChild(

                this.createOrganismSection(

                    table.title,

                    table.rows,

                    table.samples_analysed

                )

            );

        }

    );

};


/* ==========================================================
   CREATE BLOCK HEADING
   ========================================================== */

Antibiogram.createBlockHeading = function (title, samplesAnalysed) {

    const wrapper =
        document.createElement("div");

    wrapper.style.margin =
        "32px 0 14px 0";

    wrapper.style.padding =
        "4px 0 4px 14px";

    wrapper.style.borderLeft =
        "4px solid #1d5fa8";


    const heading =
        document.createElement("h2");

    heading.textContent =
        title || "";

    heading.style.margin =
        "0";

    heading.style.fontSize =
        "20px";

    wrapper.appendChild(
        heading
    );


    const subtitle =
        document.createElement("p");

    subtitle.textContent =
        "Samples analysed: " +
        this.formatCount(samplesAnalysed);

    subtitle.style.margin =
        "4px 0 0 0";

    subtitle.style.fontSize =
        "13.5px";

    subtitle.style.color =
        "#64748b";

    wrapper.appendChild(
        subtitle
    );

    return wrapper;

};


/* ==========================================================
   CREATE EXPLANATORY NOTE
   ========================================================== */

Antibiogram.createNote = function (text) {

    const note =
        document.createElement("p");

    note.textContent =
        text;

    note.style.margin =
        "0 0 6px 0";

    note.style.fontSize =
        "13px";

    note.style.color =
        "#64748b";

    return note;

};


/* ==========================================================
   FORMAT A COUNT
   ========================================================== */

Antibiogram.formatCount = function (value) {

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
   CREATE ORGANISM SECTION
   ========================================================== */

Antibiogram.createOrganismSection = function (
    title,
    rows,
    samplesAnalysed
) {

    const wrapper =
        document.createElement("section");

    wrapper.className =
        "report-card";


    /* ------------------------------------------
       Title
    ------------------------------------------ */

    const heading =
        document.createElement("h3");

    heading.textContent =
        title;

    heading.style.margin =
        "0 0 4px 0";

    heading.style.fontSize =
        "17px";

    wrapper.appendChild(
        heading
    );


    /* ------------------------------------------
       Number of samples analysed
    ------------------------------------------ */

    const subtitle =
        document.createElement("p");

    subtitle.textContent =
        "Samples analysed: " +
        this.formatCount(samplesAnalysed);

    subtitle.style.margin =
        "0 0 14px 0";

    subtitle.style.fontSize =
        "13.5px";

    subtitle.style.color =
        "#64748b";

    wrapper.appendChild(
        subtitle
    );


    /* ------------------------------------------
       Table container
    ------------------------------------------ */

    const tableContainer =
        document.createElement("div");

    tableContainer.className =
        "table-container";

    const table =
        document.createElement("table");

    table.className =
        "summary-table";

    table.appendChild(
        this.createTableHeader()
    );

    table.appendChild(
        this.createTableBody(
            rows
        )
    );

    tableContainer.appendChild(
        table
    );

    wrapper.appendChild(
        tableContainer
    );

    return wrapper;

};


/* ==========================================================
   CREATE TABLE HEADER
   ========================================================== */

Antibiogram.createTableHeader = function () {

    const thead =
        document.createElement("thead");

    const row =
        document.createElement("tr");

    [

        "Antibiotic",

        "Susceptible",

        "Intermediate",

        "Resistant",

        "Total"

    ].forEach(

        text => {

            const th =
                document.createElement("th");

            th.textContent =
                text;

            row.appendChild(th);

        }

    );

    thead.appendChild(
        row
    );

    return thead;

};


/* ==========================================================
   CREATE TABLE BODY
   ========================================================== */

Antibiogram.createTableBody = function (

    rows

) {

    const tbody =
        document.createElement("tbody");

    rows.forEach(

        row => {

            const tr =
                document.createElement("tr");

            tr.appendChild(

                this.createCell(

                    row.Antibiotic

                )

            );

            tr.appendChild(

                this.createCenterCell(

                    row.Susceptible

                )

            );

            tr.appendChild(

                this.createCenterCell(

                    row.Intermediate

                )

            );

            tr.appendChild(

                this.createCenterCell(

                    row.Resistant

                )

            );

            tr.appendChild(

                this.createCenterCell(

                    row.Total

                )

            );

            tbody.appendChild(
                tr
            );

        }

    );

    return tbody;

};

/* ==========================================================
   CREATE STANDARD TABLE CELL
   ========================================================== */

Antibiogram.createCell = function (value) {

    const td =
        document.createElement("td");

    td.textContent =
        value ?? "";

    return td;

};


/* ==========================================================
   CREATE CENTER-ALIGNED TABLE CELL
   ========================================================== */

Antibiogram.createCenterCell = function (value) {

    const td =
        document.createElement("td");

    td.className =
        "text-center";

    td.textContent =
        value ?? "-";

    return td;

};


/* ==========================================================
   CREATE EMPTY MESSAGE
   ========================================================== */

Antibiogram.createEmptyMessage = function (message) {

    const div =
        document.createElement("div");

    div.className =
        "table-empty";

    div.textContent =
        message;

    return div;

};


/* ==========================================================
   UPDATE INFORMATION STRIP
   ========================================================== */

Antibiogram.updateInfoStrip = function () {

    if (this.filtersAppliedText) {

        const filters =
            this.filters ||
            FilterManager.getFilters();

        this.filtersAppliedText.textContent =

            "District: " +
            (filters.district || "All") +

            "  |  Block: " +
            (filters.block || "All") +

            "  |  Sample Type: " +
            (filters.sample_type || "All");

    }

    const overallBlock =

        (this.data && this.data.overall) || {};

    if (this.organismCount) {

        this.organismCount.textContent =

            (overallBlock.organisms || []).length;

    }


    if (this.antibioticCount) {

        const antibiotics =
            new Set();

        (overallBlock.organisms || []).forEach(

            table => {

                (table.rows || []).forEach(

                    row => {

                        antibiotics.add(
                            row.Antibiotic
                        );

                    }

                );

            }

        );

        this.antibioticCount.textContent =

            antibiotics.size;

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
   CLEAR REPORT
   ========================================================== */

Antibiogram.clearReport = function () {

    if (this.container) {

        this.container.innerHTML = "";

    }

};


/* ==========================================================
   RESET REPORT
   ========================================================== */

Antibiogram.reset = function () {

    this.data = null;

    this.clearReport();

};


/* ==========================================================
   REFRESH REPORT
   ========================================================== */

Antibiogram.refresh = async function () {

    this.reset();

    await this.loadReport();

};

/* ==========================================================
   SHOW LOADING
   ========================================================== */

Antibiogram.showLoading = function () {

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

Antibiogram.hideLoading = function () {

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

Antibiogram.showError = function (message) {

    console.error(message);

    this.clearReport();

    if (!this.container) {

        return;

    }

    this.container.appendChild(

        this.createEmptyMessage(

            message

        )

    );

};


/* ==========================================================
   EXPORT OBJECT
   ========================================================== */

window.Antibiogram =
    Antibiogram;


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
               Load antibiogram report
            ----------------------------------------- */

            await Antibiogram.initialize();

        }

        catch (error) {

            console.error(error);

            Antibiogram.showError(

                "Failed to initialize Antibiogram."

            );

        }

    }

);