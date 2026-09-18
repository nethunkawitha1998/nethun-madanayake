/* ===========================================================
   analysis.js — Analysis logic
   Client-side CSV parsing (PapaParse) and statistical analysis
   (construct scoring, Cronbach's alpha, correlation, regression-
   based hypothesis testing). Runs entirely in the browser — the
   uploaded file is never sent anywhere.
   =========================================================== */

/* ---------------- Construct definitions (mirrors data_dictionary.csv) --------------- */
const SCALES = {
    AdoptionTAM: { label: "AI Tool Adoption (TAM)", cols: range("B", 1, 10), reverse: [] },
    AdoptionMaturity: { label: "AI Adoption Maturity", cols: range("C", 1, 10), reverse: [] },
    MTTD: { label: "Mean Time to Detect (MTTD)", cols: range("D1_", 1, 5), reverse: [] },
    MTTR: { label: "Mean Time to Respond (MTTR)", cols: range("D2_", 1, 5), reverse: [] },
    TriageAccuracy: { label: "Alert Triage Accuracy", cols: range("E", 1, 10), reverse: [] },
    Productivity: { label: "Analyst Productivity", cols: range("F", 1, 10), reverse: [] },
    Trust: { label: "Trust in AI", cols: range("G1_", 1, 8), reverse: [] },
    Explainability: { label: "Explainability & Transparency", cols: range("G2_", 1, 8), reverse: ["G2_5"] },
    OrgFactors: { label: "Organisational Factors & Challenges", cols: range("H", 1, 10), reverse: [] },
};

const DEMOGRAPHIC_COLS = {
    A5_JobRole: "Job Role",
    A6_YearsInCybersecurity: "Years in Cybersecurity",
    A8_IndustrySector: "Industry Sector",
    A9_OrganizationSize: "Organisation Size",
};

const OPEN_TEXT_KEYWORDS = {
    O2_BiggestChallenge: {
        label: "Biggest challenge",
        keywords: ["explainab", "false positive", "tun", "train", "trust", "integrat", "cost", "skill"],
    },
    O1_MostValuableAIUseCase: {
        label: "Most valuable AI use case",
        keywords: ["triage", "detect", "correlat", "prioriti", "phishing", "anomal"],
    },
};

function range(prefix, start, end) {
    const out = [];
    for (let i = start; i <= end; i++) out.push(prefix + i);
    return out;
}

class AnalysisError extends Error {}

/* ---------------- Numeric / statistics helpers ---------------- */

function mean(arr) {
    return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function variance(arr) {
    const m = mean(arr);
    return arr.reduce((a, b) => a + (b - m) * (b - m), 0) / (arr.length - 1);
}

function stddev(arr) {
    return Math.sqrt(variance(arr));
}

function pearson(x, y) {
    const n = x.length;
    const mx = mean(x), my = mean(y);
    let num = 0, dx2 = 0, dy2 = 0;
    for (let i = 0; i < n; i++) {
        const dx = x[i] - mx, dy = y[i] - my;
        num += dx * dy;
        dx2 += dx * dx;
        dy2 += dy * dy;
    }
    const denom = Math.sqrt(dx2 * dy2);
    return denom === 0 ? 0 : num / denom;
}

// Regularized incomplete beta function I_x(a,b) — standard continued-fraction
// implementation (Numerical Recipes), used to compute Student-t and F
// distribution p-values without an external stats library.
function logGamma(x) {
    const cof = [
        76.18009172947146, -86.50532032941677, 24.01409824083091,
        -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5,
    ];
    let y = x, tmp = x + 5.5;
    tmp -= (x + 0.5) * Math.log(tmp);
    let ser = 1.000000000190015;
    for (let j = 0; j < 6; j++) { y += 1; ser += cof[j] / y; }
    return -tmp + Math.log(2.5066282746310005 * ser / x);
}

function betacf(x, a, b) {
    const MAXIT = 200, EPS = 3e-9, FPMIN = 1e-30;
    const qab = a + b, qap = a + 1, qam = a - 1;
    let c = 1, d = 1 - (qab * x) / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    d = 1 / d;
    let h = d;
    for (let m = 1; m <= MAXIT; m++) {
        const m2 = 2 * m;
        let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
        d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
        c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
        d = 1 / d; h *= d * c;
        aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
        d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
        c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
        d = 1 / d;
        const del = d * c; h *= del;
        if (Math.abs(del - 1) < EPS) break;
    }
    return h;
}

function betainc(x, a, b) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const bt = Math.exp(
        logGamma(a + b) - logGamma(a) - logGamma(b) +
        a * Math.log(x) + b * Math.log(1 - x)
    );
    if (x < (a + 1) / (a + b + 2)) {
        return (bt * betacf(x, a, b)) / a;
    }
    return 1 - (bt * betacf(1 - x, b, a)) / b;
}

// Two-tailed p-value for a Student-t statistic with `df` degrees of freedom.
function tTestPValue(t, df) {
    const x = df / (df + t * t);
    return betainc(x, df / 2, 0.5);
}

// Upper-tail p-value for an F statistic with (df1, df2) degrees of freedom.
function fTestPValue(f, df1, df2) {
    if (f <= 0) return 1;
    const x = df2 / (df2 + df1 * f);
    return betainc(x, df2 / 2, df1 / 2);
}

/* ---------------- Small matrix helpers for OLS regression ---------------- */

function matTranspose(A) {
    return A[0].map((_, j) => A.map(row => row[j]));
}

function matMultiply(A, B) {
    const result = [];
    for (let i = 0; i < A.length; i++) {
        result.push([]);
        for (let j = 0; j < B[0].length; j++) {
            let sum = 0;
            for (let k = 0; k < B.length; k++) sum += A[i][k] * B[k][j];
            result[i].push(sum);
        }
    }
    return result;
}

// Gauss-Jordan matrix inverse (small matrices only — up to ~5x5 here).
function matInverse(M) {
    const n = M.length;
    const A = M.map((row, i) => [...row, ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))]);
    for (let col = 0; col < n; col++) {
        let pivotRow = col;
        for (let r = col + 1; r < n; r++) {
            if (Math.abs(A[r][col]) > Math.abs(A[pivotRow][col])) pivotRow = r;
        }
        [A[col], A[pivotRow]] = [A[pivotRow], A[col]];
        const pivot = A[col][col];
        if (Math.abs(pivot) < 1e-12) throw new AnalysisError("Singular matrix in regression (predictors may be collinear).");
        for (let j = 0; j < 2 * n; j++) A[col][j] /= pivot;
        for (let r = 0; r < n; r++) {
            if (r === col) continue;
            const factor = A[r][col];
            for (let j = 0; j < 2 * n; j++) A[r][j] -= factor * A[col][j];
        }
    }
    return A.map(row => row.slice(n));
}

/**
 * Ordinary least squares regression with an intercept.
 * predictors: array of column arrays (each same length as y).
 * Returns coefficients (intercept first), standard errors, t-stats,
 * p-values, R-squared, and the overall F-test.
 */
function olsFit(predictors, y) {
    const n = y.length;
    const k = predictors.length;
    const X = [];
    for (let i = 0; i < n; i++) {
        const row = [1];
        for (let p = 0; p < k; p++) row.push(predictors[p][i]);
        X.push(row);
    }
    const Xt = matTranspose(X);
    const XtX = matMultiply(Xt, X);
    const XtXinv = matInverse(XtX);
    const XtY = matMultiply(Xt, y.map(v => [v]));
    const betaMat = matMultiply(XtXinv, XtY);
    const beta = betaMat.map(r => r[0]);

    const yHat = X.map(row => row.reduce((s, v, j) => s + v * beta[j], 0));
    const residuals = y.map((v, i) => v - yHat[i]);
    const sse = residuals.reduce((s, r) => s + r * r, 0);
    const yMean = mean(y);
    const sst = y.reduce((s, v) => s + (v - yMean) * (v - yMean), 0);
    const r2 = 1 - sse / sst;

    const dfModel = k;
    const dfResid = n - k - 1;
    const mse = sse / dfResid;

    const se = [];
    for (let i = 0; i <= k; i++) se.push(Math.sqrt(mse * XtXinv[i][i]));
    const tStats = beta.map((b, i) => b / se[i]);
    const pValues = tStats.map(t => tTestPValue(t, dfResid));

    const fStat = (r2 / dfModel) / ((1 - r2) / dfResid);
    const fP = fTestPValue(fStat, dfModel, dfResid);

    return { beta, se, tStats, pValues, r2, n, dfModel, dfResid, fStat, fP };
}

/* ---------------- Cronbach's alpha ---------------- */

function cronbachAlpha(itemsMatrix) {
    // itemsMatrix: array of rows, each row an array of item scores (no NaN)
    const k = itemsMatrix[0].length;
    if (k < 2 || itemsMatrix.length < 3) return NaN;
    const itemVars = [];
    for (let c = 0; c < k; c++) {
        itemVars.push(variance(itemsMatrix.map(row => row[c])));
    }
    const totalScores = itemsMatrix.map(row => row.reduce((a, b) => a + b, 0));
    const totalVar = variance(totalScores);
    if (totalVar === 0) return NaN;
    const sumItemVar = itemVars.reduce((a, b) => a + b, 0);
    return (k / (k - 1)) * (1 - sumItemVar / totalVar);
}

/* ---------------- Core analysis pipeline ---------------- */

function toNumberOrNaN(v) {
    if (v === null || v === undefined || v === "") return NaN;
    const n = Number(v);
    return Number.isFinite(n) ? n : NaN;
}

function computeComposites(rows) {
    const composites = {};
    const missingReport = [];
    const columns = Object.keys(rows[0] || {});

    for (const [key, spec] of Object.entries(SCALES)) {
        const present = spec.cols.filter(c => columns.includes(c));
        const missing = spec.cols.filter(c => !columns.includes(c));
        if (present.length < Math.max(2, Math.floor(spec.cols.length / 2))) {
            missingReport.push(
                `${spec.label}: only ${present.length}/${spec.cols.length} items found in the uploaded file — this construct was skipped.`
            );
            continue;
        }
        const values = rows.map(row => {
            const vals = present.map(c => {
                let v = toNumberOrNaN(row[c]);
                if (spec.reverse.includes(c) && Number.isFinite(v)) v = 6 - v;
                return v;
            });
            // Match pandas' default skipna row-mean behaviour: average
            // whichever items are present for this respondent rather than
            // discarding the whole composite when just one item is missing.
            // Only return NaN if none of the items were answered at all.
            const validVals = vals.filter(Number.isFinite);
            if (validVals.length === 0) return NaN;
            return mean(validVals);
        });
        composites[key] = values;
        if (missing.length) {
            missingReport.push(
                `${spec.label}: ${missing.length} item(s) missing (${missing.join(", ")}) — composite computed from the remaining ${present.length} item(s).`
            );
        }
    }
    return { composites, missingReport };
}

function reliabilityTable(rows) {
    const columns = Object.keys(rows[0] || {});
    const out = [];
    for (const [key, spec] of Object.entries(SCALES)) {
        const present = spec.cols.filter(c => columns.includes(c));
        if (present.length < 2) continue;
        const itemsMatrix = rows
            .map(row => present.map(c => {
                let v = toNumberOrNaN(row[c]);
                if (spec.reverse.includes(c) && Number.isFinite(v)) v = 6 - v;
                return v;
            }))
            .filter(rowVals => rowVals.every(v => Number.isFinite(v)));

        if (itemsMatrix.length < 3) continue;
        const flatVals = itemsMatrix.flat();
        out.push({
            construct: spec.label,
            items: present.length,
            mean: round2(mean(flatVals)),
            sd: round2(stddev(flatVals)),
            alpha: round3(cronbachAlpha(itemsMatrix)),
        });
    }
    return out;
}

function demographicsSummary(rows) {
    const columns = Object.keys(rows[0] || {});
    const summary = {};
    for (const [col, label] of Object.entries(DEMOGRAPHIC_COLS)) {
        if (!columns.includes(col)) continue;
        const counts = {};
        rows.forEach(row => {
            const v = row[col];
            if (v === undefined || v === null || v === "") return;
            counts[v] = (counts[v] || 0) + 1;
        });
        summary[label] = { labels: Object.keys(counts), values: Object.values(counts) };
    }
    return summary;
}

function correlationMatrix(composites) {
    const keys = Object.keys(composites).filter(k => composites[k].some(Number.isFinite));
    if (keys.length < 2) return { labels: [], matrix: [] };

    // build a row mask: only rows where all constructs are present
    const n = composites[keys[0]].length;
    const rowIdx = [];
    for (let i = 0; i < n; i++) {
        if (keys.every(k => Number.isFinite(composites[k][i]))) rowIdx.push(i);
    }
    const series = {};
    keys.forEach(k => { series[k] = rowIdx.map(i => composites[k][i]); });

    const matrix = keys.map(k1 => keys.map(k2 => round2(pearson(series[k1], series[k2]))));
    return { labels: keys, matrix };
}

function pairedSeries(composites, keys) {
    const n = composites[keys[0]].length;
    const rowIdx = [];
    for (let i = 0; i < n; i++) {
        if (keys.every(k => Number.isFinite(composites[k][i]))) rowIdx.push(i);
    }
    const out = {};
    keys.forEach(k => { out[k] = rowIdx.map(i => composites[k][i]); });
    out.__n = rowIdx.length;
    return out;
}

function hypothesisTests(composites) {
    const results = [];
    const has = (...keys) => keys.every(k => composites[k]);

    if (has("MTTD", "AdoptionMaturity")) {
        const s = pairedSeries(composites, ["MTTD", "AdoptionMaturity"]);
        if (s.__n >= 10) {
            const fit = olsFit([s.AdoptionMaturity], s.MTTD);
            results.push({
                id: "H1",
                statement: "AI adoption maturity is associated with faster detection (MTTD)",
                test: "Simple regression",
                result: `β = ${round3(fit.beta[1])}, R² = ${round3(fit.r2)}, F(${fit.dfModel},${fit.dfResid}) = ${round2(fit.fStat)}`,
                p: fit.fP,
            });
        }
    }

    if (has("MTTR", "AdoptionMaturity")) {
        const s = pairedSeries(composites, ["MTTR", "AdoptionMaturity"]);
        if (s.__n >= 10) {
            const fit = olsFit([s.AdoptionMaturity], s.MTTR);
            results.push({
                id: "H2",
                statement: "AI adoption maturity is associated with faster response (MTTR)",
                test: "Simple regression",
                result: `β = ${round3(fit.beta[1])}, R² = ${round3(fit.r2)}, F(${fit.dfModel},${fit.dfResid}) = ${round2(fit.fStat)}`,
                p: fit.fP,
            });
        }
    }

    if (has("TriageAccuracy", "AdoptionMaturity")) {
        const s = pairedSeries(composites, ["TriageAccuracy", "AdoptionMaturity"]);
        if (s.__n >= 10) {
            const fit = olsFit([s.AdoptionMaturity], s.TriageAccuracy);
            results.push({
                id: "H3",
                statement: "AI adoption maturity is associated with alert-triage accuracy",
                test: "Simple regression",
                result: `β = ${round3(fit.beta[1])}, R² = ${round3(fit.r2)}, F(${fit.dfModel},${fit.dfResid}) = ${round2(fit.fStat)}`,
                p: fit.fP,
            });
        }
    }

    if (has("Productivity", "AdoptionMaturity")) {
        const s = pairedSeries(composites, ["Productivity", "AdoptionMaturity"]);
        if (s.__n >= 10) {
            const r = pearson(s.Productivity, s.AdoptionMaturity);
            const t = r * Math.sqrt((s.__n - 2) / (1 - r * r));
            const p = tTestPValue(t, s.__n - 2);
            results.push({
                id: "H4",
                statement: "AI adoption maturity correlates with analyst productivity",
                test: "Pearson correlation",
                result: `r = ${round3(r)}`,
                p,
            });
        }
    }

    if (has("MTTD", "MTTR", "TriageAccuracy", "Productivity", "AdoptionMaturity", "Trust")) {
        const s = pairedSeries(composites, ["MTTD", "MTTR", "TriageAccuracy", "Productivity", "AdoptionMaturity", "Trust"]);
        if (s.__n >= 15) {
            const irEff = s.MTTD.map((_, i) => mean([s.MTTD[i], s.MTTR[i], s.TriageAccuracy[i], s.Productivity[i]]));
            const amMean = mean(s.AdoptionMaturity), trMean = mean(s.Trust);
            const amC = s.AdoptionMaturity.map(v => v - amMean);
            const trC = s.Trust.map(v => v - trMean);
            const interaction = amC.map((v, i) => v * trC[i]);

            const model1 = olsFit([amC, trC], irEff);
            const model2 = olsFit([amC, trC, interaction], irEff);
            const deltaR2 = model2.r2 - model1.r2;

            results.push({
                id: "H5",
                statement: "Analyst trust moderates the adoption-maturity → efficiency relationship",
                test: "Hierarchical regression",
                result: `ΔR² = ${round3(deltaR2)}, interaction β = ${round3(model2.beta[3])}`,
                p: model2.pValues[3],
            });
        }
    }

    return results;
}

function qualitativeThemes(rows) {
    const columns = Object.keys(rows[0] || {});
    const themes = {};
    for (const [col, spec] of Object.entries(OPEN_TEXT_KEYWORDS)) {
        if (!columns.includes(col)) continue;
        const texts = rows.map(r => (r[col] || "").toString().toLowerCase()).filter(t => t.length > 0);
        const counts = {};
        spec.keywords.forEach(kw => {
            counts[kw] = texts.filter(t => t.includes(kw)).length;
        });
        themes[spec.label] = counts;
    }
    return themes;
}

function round2(v) { return Number.isFinite(v) ? Math.round(v * 100) / 100 : null; }
function round3(v) { return Number.isFinite(v) ? Math.round(v * 1000) / 1000 : null; }

/**
 * Entry point: takes parsed CSV rows (array of objects, as returned by
 * PapaParse with header:true) and returns the full results object used
 * by results.html.
 */
function runFullAnalysis(rows) {
    if (!rows || rows.length === 0) {
        throw new AnalysisError("The uploaded CSV file is empty.");
    }

    const { composites, missingReport } = computeComposites(rows);
    const availableKeys = Object.keys(composites);
    if (availableKeys.length === 0) {
        throw new AnalysisError(
            "None of the expected construct columns were found in this file. " +
            "Please check that your CSV columns follow the codes in data_dictionary.csv " +
            "(e.g. B1..B10, C1..C10, D1_1..D1_5, ...)."
        );
    }

    const constructMeans = {};
    availableKeys.forEach(k => {
        const valid = composites[k].filter(Number.isFinite);
        if (valid.length) constructMeans[k] = round2(mean(valid));
    });

    return {
        n_responses: rows.length,
        missing_report: missingReport,
        reliability: reliabilityTable(rows),
        demographics: demographicsSummary(rows),
        correlation: correlationMatrix(composites),
        hypotheses: hypothesisTests(composites),
        qualitative: qualitativeThemes(rows),
        construct_means: constructMeans,
    };
}

/**
 * Reads a File object (from an <input type="file">), parses it as CSV
 * with PapaParse, runs the full analysis, and returns a Promise resolving
 * to the results object (or rejecting with an AnalysisError).
 */
function analyzeCsvFile(file) {
    return new Promise((resolve, reject) => {
        if (!file) { reject(new AnalysisError("No file selected.")); return; }
        if (!file.name.toLowerCase().endsWith(".csv")) {
            reject(new AnalysisError("Please upload a .csv file.")); return;
        }
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            dynamicTyping: false,
            complete: function (parsed) {
                try {
                    const rows = parsed.data.filter(r => Object.values(r).some(v => v !== ""));
                    const results = runFullAnalysis(rows);
                    resolve(results);
                } catch (err) {
                    reject(err);
                }
            },
            error: function (err) {
                reject(new AnalysisError("Could not read CSV file: " + err.message));
            },
        });
    });
}
