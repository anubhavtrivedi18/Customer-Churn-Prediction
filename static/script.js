const form = document.querySelector("#prediction-form");
const fieldsContainer = document.querySelector("#form-fields");
const submitButton = document.querySelector("#submit-button");
const result = document.querySelector("#result");
const batchForm = document.querySelector("#batch-form");
const batchSubmitButton = document.querySelector("#batch-submit-button");
const batchResult = document.querySelector("#batch-result");
const downloadResults = document.querySelector("#download-results");
const batchFileInput = document.querySelector("#batch-file");
const uploadZone = document.querySelector(".upload-zone");
const selectedFile = document.querySelector("#selected-file");
let resultsDownloadUrl;

const fieldGroups = [
    {
        title: "Usage & activity",
        description: "Monthly usage, calls and service activity.",
        fields: [
            "MonthlyRevenue", "MonthlyMinutes", "TotalRecurringCharge", "RoamingCalls",
            "PercChangeMinutes", "PercChangeRevenues", "DroppedCalls", "BlockedCalls",
            "UnansweredCalls", "CustomerCareCalls", "ThreewayCalls", "ReceivedCalls",
            "OutboundCalls", "InboundCalls", "PeakCallsInOut", "OffPeakCallsInOut",
            "DroppedBlockedCalls", "CallWaitingCalls",
        ],
    },
    {
        title: "Account & service",
        description: "Tenure and account activity details.",
        fields: ["MonthsInService", "UniqueSubs", "ActiveSubs", "ServiceArea"],
    },
    {
        title: "Device details",
        description: "Equipment and handset information.",
        fields: [
            "Handsets", "HandsetModels", "CurrentEquipmentDays", "HandsetRefurbished",
            "HandsetWebCapable", "HandsetPrice",
        ],
    },
    {
        title: "Customer profile",
        description: "Household, credit and customer profile details.",
        fields: ["AgeHH1", "AgeHH2", "CreditRating", "PrizmCode", "MaritalStatus", "IncomeGroup"],
    },
    {
        title: "Retention & engagement",
        description: "Retention outreach and customer engagement.",
        fields: [
            "BuysViaMailOrder", "RespondsToMailOffers", "MadeCallToRetentionTeam",
            "RetentionCalls", "RetentionOffersAccepted", "ReferralsMadeBySubscriber",
            "AdjustmentsToCreditRating",
        ],
    },
];

function addField(name, property, choices, parent) {
    const wrapper = document.createElement("label");
    wrapper.className = "field";

    const title = document.createElement("span");
    title.textContent = name.replace(/([A-Z])/g, " $1").trim();
    wrapper.append(title);

    const description = document.createElement("small");
    description.textContent = property.description || "";
    wrapper.append(description);

    let input;
    const options = property.enum || choices;
    if (options) {
        input = document.createElement("select");
        input.required = true;
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select an option";
        placeholder.disabled = true;
        placeholder.selected = true;
        input.append(placeholder);

        for (const option of options) {
            const element = document.createElement("option");
            element.value = option;
            element.textContent = option;
            input.append(element);
        }
    } else {
        input = document.createElement("input");
        input.type = "number";
        input.step = property.type === "integer" ? "1" : "any";
        input.required = true;
    }

    input.name = name;
    wrapper.append(input);
    parent.append(wrapper);
}

async function loadForm() {
    try {
        const [schemaResponse, optionsResponse] = await Promise.all([
            fetch("/openapi.json"),
            fetch("/options"),
        ]);
        if (!schemaResponse.ok || !optionsResponse.ok) {
            throw new Error("Could not load form fields or category choices.");
        }

        const openapi = await schemaResponse.json();
        const options = await optionsResponse.json();
        const inputSchema = openapi.components.schemas.CustomerInput;

        fieldsContainer.replaceChildren();
        const groupedFields = new Set();
        for (const group of fieldGroups) {
            const availableFields = group.fields.filter((name) => inputSchema.properties[name]);
            if (availableFields.length === 0) {
                continue;
            }

            const section = document.createElement("section");
            section.className = "form-section";
            const heading = document.createElement("div");
            heading.className = "form-section-heading";
            const title = document.createElement("h4");
            title.textContent = group.title;
            const description = document.createElement("p");
            description.textContent = group.description;
            heading.append(title, description);
            const grid = document.createElement("div");
            grid.className = "form-grid";
            for (const name of availableFields) {
                addField(name, inputSchema.properties[name], options[name], grid);
                groupedFields.add(name);
            }
            section.append(heading, grid);
            fieldsContainer.append(section);
        }

        for (const [name, property] of Object.entries(inputSchema.properties)) {
            if (!groupedFields.has(name)) {
                const section = document.createElement("section");
                section.className = "form-section";
                const grid = document.createElement("div");
                grid.className = "form-grid";
                addField(name, property, options[name], grid);
                section.append(grid);
                fieldsContainer.append(section);
            }
        }
        submitButton.disabled = false;
    } catch (error) {
        fieldsContainer.textContent = error.message;
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submitButton.disabled = true;
    result.hidden = false;
    result.textContent = "Making prediction…";
    result.className = "result";

    const customer = Object.fromEntries(new FormData(form).entries());
    for (const [name, value] of Object.entries(customer)) {
        const input = form.elements.namedItem(name);
        if (input.type === "number") {
            customer[name] = input.step === "1" ? Number.parseInt(value, 10) : Number(value);
        }
    }

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(customer),
        });
        const body = await response.json();
        if (!response.ok) {
            throw new Error(body.detail || "Prediction request failed.");
        }
        renderSingleResult(body);
    } catch (error) {
        result.textContent = error.message;
        result.classList.add("error");
    } finally {
        submitButton.disabled = false;
    }
});

loadForm();

function renderSingleResult(data) {
    result.replaceChildren();
    result.hidden = false;
    result.className = `result single-result ${data.churn_prediction === "Yes" ? "risk-high" : "risk-low"}`;

    const heading = document.createElement("div");
    heading.className = "result-heading";
    const title = document.createElement("h4");
    title.textContent = "Prediction complete";
    const badge = document.createElement("span");
    badge.className = "prediction-badge";
    badge.textContent = data.churn_prediction === "Yes" ? "At risk" : "Likely to stay";
    heading.append(title, badge);
    result.append(heading);

    const churnPercent = Number(data.churn_probability_percent);
    const nonChurnPercent = Number(data.non_churn_probability_percent);
    for (const metric of [
        { label: "Churn estimate", value: churnPercent, style: "churn" },
        { label: "Non-churn estimate", value: nonChurnPercent, style: "stay" },
    ]) {
        const row = document.createElement("div");
        row.className = "probability-row";
        const label = document.createElement("div");
        label.className = "probability-label";
        const name = document.createElement("span");
        name.textContent = metric.label;
        const value = document.createElement("strong");
        value.textContent = `${metric.value}%`;
        label.append(name, value);
        const track = document.createElement("div");
        track.className = "probability-track";
        const fill = document.createElement("span");
        fill.className = `probability-fill ${metric.style}`;
        fill.style.width = `${Math.max(0, Math.min(100, metric.value))}%`;
        track.append(fill);
        row.append(label, track);
        result.append(row);
    }

    const note = document.createElement("p");
    note.className = "result-note";
    note.textContent = "Model estimates are indicators, not guarantees.";
    result.append(note);
}

function csvCell(value) {
    let text = String(value ?? "");
    if (/^[\t\r ]*[=+\-@]/.test(text)) {
        text = `'${text}`;
    }
    return `"${text.replace(/"/g, '""')}"`;
}

function showBatchResults(data) {
    batchResult.replaceChildren();
    batchResult.className = "result success";
    batchResult.hidden = false;

    const summary = document.createElement("p");
    summary.textContent = `Predictions complete for ${data.row_count} customers.`;
    batchResult.append(summary);

    if (data.ignored_columns.length > 0) {
        const ignored = document.createElement("p");
        ignored.className = "file-note";
        ignored.textContent = `Not used for prediction: ${data.ignored_columns.join(", ")}`;
        batchResult.append(ignored);
    }

    const tableWrapper = document.createElement("div");
    tableWrapper.className = "table-wrapper";
    const table = document.createElement("table");
    const headers = [
        "Record ID",
        "Prediction",
        "Churn probability",
        "Non-churn probability",
    ];
    const thead = document.createElement("thead");
    const headingRow = document.createElement("tr");
    for (const header of headers) {
        const cell = document.createElement("th");
        cell.textContent = header;
        headingRow.append(cell);
    }
    thead.append(headingRow);
    table.append(thead);

    const tbody = document.createElement("tbody");
    for (const item of data.predictions) {
        const row = document.createElement("tr");
        const values = [
            item.record_id ?? "",
            item.prediction,
            `${item.churn_probability_percent}%`,
            `${item.non_churn_probability_percent}%`,
        ];
        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent = String(value);
            row.append(cell);
        }
        tbody.append(row);
    }
    table.append(tbody);
    tableWrapper.append(table);
    batchResult.append(tableWrapper);

    if (resultsDownloadUrl) {
        URL.revokeObjectURL(resultsDownloadUrl);
    }
    const csvRows = [
        headers.map(csvCell).join(","),
        ...data.predictions.map((item) =>
            [
                item.record_id,
                item.prediction,
                item.churn_probability_percent,
                item.non_churn_probability_percent,
            ].map(csvCell).join(","),
        ),
    ];
    resultsDownloadUrl = URL.createObjectURL(
        new Blob([csvRows.join("\r\n")], { type: "text/csv;charset=utf-8" }),
    );
    downloadResults.href = resultsDownloadUrl;
    downloadResults.download = "churn-predictions.csv";
    downloadResults.hidden = false;
}

batchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    batchSubmitButton.disabled = true;
    downloadResults.hidden = true;
    batchResult.hidden = false;
    batchResult.className = "result";
    batchResult.textContent = "Uploading file and predicting…";

    try {
        const response = await fetch("/predict-file", {
            method: "POST",
            body: new FormData(batchForm),
        });

        batchFileInput.addEventListener("change", () => {
            const file = batchFileInput.files[0];
            if (!file) {
                selectedFile.hidden = true;
                uploadZone.classList.remove("has-file");
                return;
            }

            selectedFile.textContent = `${file.name} · ${(file.size / (1024 * 1024)).toFixed(2)} MB`;
            selectedFile.hidden = false;
            uploadZone.classList.add("has-file");
        });

        for (const eventName of ["dragenter", "dragover"]) {
            uploadZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                uploadZone.classList.add("dragging");
            });
        }

        for (const eventName of ["dragleave", "drop"]) {
            uploadZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                uploadZone.classList.remove("dragging");
            });
        }

        uploadZone.addEventListener("drop", (event) => {
            const [file] = event.dataTransfer.files;
            if (!file) {
                return;
            }
            const transfer = new DataTransfer();
            transfer.items.add(file);
            batchFileInput.files = transfer.files;
            batchFileInput.dispatchEvent(new Event("change", { bubbles: true }));
        });
        const body = await response.json();
        if (!response.ok) {
            const detail = typeof body.detail === "string"
                ? body.detail
                : JSON.stringify(body.detail);
            throw new Error(detail || "Batch prediction failed.");
        }
        showBatchResults(body);
    } catch (error) {
        batchResult.className = "result error";
        batchResult.textContent = error.message;
    } finally {
        batchSubmitButton.disabled = false;
    }
});
