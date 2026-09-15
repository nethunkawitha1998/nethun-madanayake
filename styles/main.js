/* ===========================================================
   SOC AI Research — main.js
   Site-wide interactivity plus results-page chart rendering.
   =========================================================== */

// Auto-dismiss flash messages after a few seconds.
document.addEventListener("DOMContentLoaded", function () {
    var flashes = document.querySelectorAll(".flash");
    flashes.forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity 0.4s ease";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        }, 6000);
    });
});

// A neutral colour ramp used for the correlation-matrix heatmap.
// Positive correlations shade toward teal, negative toward amber/red.
function correlationColor(value) {
    var v = Math.max(-1, Math.min(1, value));
    if (v >= 0) {
        var alpha = v.toFixed(2);
        return "rgba(14, 155, 138, " + (0.12 + 0.55 * v) + ")";
    } else {
        var a = Math.abs(v);
        return "rgba(192, 57, 43, " + (0.12 + 0.55 * a) + ")";
    }
}

function buildBarChart(canvasId, labels, values, label, color) {
    var ctx = document.getElementById(canvasId);
    if (!ctx || typeof Chart === "undefined") return;
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: color || "#0e9b8a",
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
        },
    });
}

function buildPieChart(canvasId, labels, values) {
    var ctx = document.getElementById(canvasId);
    if (!ctx || typeof Chart === "undefined") return;
    var palette = ["#0e9b8a", "#1a8fbf", "#c8791a", "#2e8b57", "#123b6b", "#c0392b", "#5b6b79"];
    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{ data: values, backgroundColor: palette }],
        },
        options: { responsive: true, plugins: { legend: { position: "bottom" } } },
    });
}

function renderResultsCharts() {
    var dataEl = document.getElementById("results-data");
    if (!dataEl) return; // not on the results page
    var results = JSON.parse(dataEl.textContent);

    // --- Demographics charts ---
    var demoGrid = document.getElementById("demographics-charts");
    if (demoGrid && results.demographics) {
        var i = 0;
        for (var label in results.demographics) {
            if (!results.demographics.hasOwnProperty(label)) continue;
            i += 1;
            var canvasId = "demo-chart-" + i;
            var card = document.createElement("div");
            card.className = "chart-card";
            card.innerHTML = "<h4>" + label + "</h4><canvas id=\"" + canvasId + "\" height=\"200\"></canvas>";
            demoGrid.appendChild(card);
            var d = results.demographics[label];
            buildPieChart(canvasId, d.labels, d.values);
        }
    }

    // --- Construct means chart ---
    if (results.construct_means) {
        var labels = Object.keys(results.construct_means);
        var values = labels.map(function (k) { return results.construct_means[k]; });
        buildBarChart("construct-means-chart", labels, values, "Mean score (1-5)", "#0e9b8a");
    }

    // --- Correlation matrix table ---
    var corrWrapper = document.getElementById("correlation-table-wrapper");
    if (corrWrapper && results.correlation && results.correlation.labels && results.correlation.labels.length) {
        var labels2 = results.correlation.labels;
        var matrix = results.correlation.matrix;
        var html = "<table class=\"data-table\"><thead><tr><th></th>";
        labels2.forEach(function (l) { html += "<th>" + l + "</th>"; });
        html += "</tr></thead><tbody>";
        matrix.forEach(function (row, ri) {
            html += "<tr><th>" + labels2[ri] + "</th>";
            row.forEach(function (val) {
                html += "<td class=\"corr-cell\" style=\"background:" + correlationColor(val) + "\">" + val.toFixed(2) + "</td>";
            });
            html += "</tr>";
        });
        html += "</tbody></table>";
        corrWrapper.innerHTML = html;
    } else if (corrWrapper) {
        corrWrapper.innerHTML = "<p style=\"padding:16px;\">Not enough constructs were available to compute a correlation matrix.</p>";
    }

    // --- Qualitative theme charts ---
    var qualGrid = document.getElementById("qualitative-charts");
    if (qualGrid && results.qualitative) {
        var j = 0;
        for (var qLabel in results.qualitative) {
            if (!results.qualitative.hasOwnProperty(qLabel)) continue;
            j += 1;
            var qCanvasId = "qual-chart-" + j;
            var qCard = document.createElement("div");
            qCard.className = "chart-card";
            qCard.innerHTML = "<h4>" + qLabel + "</h4><canvas id=\"" + qCanvasId + "\" height=\"200\"></canvas>";
            qualGrid.appendChild(qCard);
            var counts = results.qualitative[qLabel];
            var kLabels = Object.keys(counts);
            var kValues = kLabels.map(function (k) { return counts[k]; });
            buildBarChart(qCanvasId, kLabels, kValues, "Mentions", "#1a8fbf");
        }
    }
}

// Exposed globally so results.html can trigger it once Chart.js has loaded.
window.renderResultsCharts = renderResultsCharts;
