/* ==========================================================
   AMSP Dashboard
   Shared functionality for every page
   ========================================================== */

"use strict";

/* ==========================================================
   CONFIGURATION
   ========================================================== */

const API_BASE = "http://127.0.0.1:5000";


/* ==========================================================
   DOM READY
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    initialiseDashboard();

});


/* ==========================================================
   INITIALISE
   ========================================================== */

function initialiseDashboard() {

    initialiseSidebar();

    initialiseNavigation();

}


/* ==========================================================
   SIDEBAR
   ========================================================== */

function initialiseSidebar() {

    const toggleButton = document.getElementById("sidebarToggle");

    const sidebar = document.querySelector(".sidebar");

    if (!toggleButton || !sidebar)
        return;

    toggleButton.addEventListener("click", () => {

        sidebar.classList.toggle("collapsed");

    });

}


/* ==========================================================
   ACTIVE NAVIGATION
   ========================================================== */

function initialiseNavigation() {

    const currentPage =
        window.location.pathname
        .split("/")
        .pop();

    const links =
        document.querySelectorAll(".sidebar a");

    links.forEach(link => {

        link.classList.remove("active");

        const href = link.getAttribute("href");

        if (href === currentPage) {

            link.classList.add("active");

        }

    });

}


/* ==========================================================
   LOADING
   ========================================================== */

function showLoading() {

    const loader =
        document.getElementById("loadingOverlay");

    if (loader) {

        loader.style.display = "flex";

    }

}


function hideLoading() {

    const loader =
        document.getElementById("loadingOverlay");

    if (loader) {

        loader.style.display = "none";

    }

}


/* ==========================================================
   MESSAGE BOX
   ========================================================== */

function showMessage(message, type = "info") {

    const box =
        document.getElementById("messageBox");

    if (!box)
        return;

    box.innerHTML = message;

    box.className = "message " + type;

    box.style.display = "block";

}


function clearMessage() {

    const box =
        document.getElementById("messageBox");

    if (!box)
        return;

    box.style.display = "none";

    box.innerHTML = "";

}


/* ==========================================================
   API GET
   ========================================================== */

async function apiGet(endpoint) {

    showLoading();

    clearMessage();

    try {

        const response =
            await fetch(API_BASE + endpoint);

        const data =
            await response.json();

        hideLoading();

        if (!response.ok) {

            showMessage(
                data.error || "Request failed.",
                "error"
            );

            return null;

        }

        return data;

    }

    catch (error) {

        hideLoading();

        showMessage(
            error.message,
            "error"
        );

        return null;

    }

}


/* ==========================================================
   API POST
   ========================================================== */

async function apiPost(endpoint, payload) {

    showLoading();

    clearMessage();

    try {

        const response = await fetch(

            API_BASE + endpoint,

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify(payload)

            }

        );

        const data =
            await response.json();

        hideLoading();

        if (!response.ok) {

            showMessage(

                data.error || "Request failed.",

                "error"

            );

            return null;

        }

        return data;

    }

    catch (error) {

        hideLoading();

        showMessage(
            error.message,
            "error"
        );

        return null;

    }

}


/* ==========================================================
   CREATE OPTION
   ========================================================== */

function createOption(value, text) {

    const option =
        document.createElement("option");

    option.value = value;

    option.textContent = text;

    return option;

}


/* ==========================================================
   FILL SELECT
   ========================================================== */

function populateSelect(select, values) {

    if (!select)
        return;

    select.innerHTML = "";

    values.forEach(value => {

        select.appendChild(

            createOption(value, value)

        );

    });

}


/* ==========================================================
   GET MULTIPLE VALUES
   ========================================================== */

function getSelectedValues(selectId) {

    const select =
        document.getElementById(selectId);

    if (!select)
        return [];

    return Array.from(select.selectedOptions)

        .map(option => option.value);

}


/* ==========================================================
   RESET SELECT
   ========================================================== */

function resetSelect(selectId) {

    const select =
        document.getElementById(selectId);

    if (!select)
        return;

    Array.from(select.options)

        .forEach(option => {

            option.selected = false;

        });

}


/* ==========================================================
   FORMAT NUMBER
   ========================================================== */

function formatNumber(value) {

    if (value === null || value === undefined)
        return "";

    return Number(value)

        .toLocaleString();

}


/* ==========================================================
   FORMAT PERCENTAGE
   ========================================================== */

function formatPercentage(value) {

    if (value === null || value === undefined)
        return "";

    return Number(value)

        .toFixed(2) + "%";

}


/* ==========================================================
   EXPORTS
   ========================================================== */

window.apiGet = apiGet;

window.apiPost = apiPost;

window.populateSelect = populateSelect;

window.getSelectedValues = getSelectedValues;

window.resetSelect = resetSelect;

window.showLoading = showLoading;

window.hideLoading = hideLoading;

window.showMessage = showMessage;

window.clearMessage = clearMessage;

window.formatNumber = formatNumber;

window.formatPercentage = formatPercentage;