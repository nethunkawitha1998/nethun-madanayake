# SOC AI Research Site (Static)

**The Impact of AI-Based Solutions on Incident Response Efficiency in SOC Environments**

A fully static HTML/CSS/JS website — no backend, no build step — that hosts the
project questionnaire, accepts an exported CSV of responses, runs the full
statistical analysis (reliability, correlation, hypothesis testing) entirely
in the visitor's browser, and presents MITRE ATT&CK&reg;-aligned
recommendations based on the results.

Because everything runs client-side, this repo can be hosted directly on
**GitHub Pages** with no server of any kind.

## Directory structure

```
index.html              Home page: overview, questionnaire embed, researcher profile
templates/
  sign-In.html           Sign-in page (client-side "auth", see note below)
  sign-Up.html           Sign-up page
  analysis.html          CSV upload page
  results.html           Results & Discussion page
styles/
  styles.css             Cybersecurity-themed stylesheet (light, no dark mode)
  main.js                All configurations: site config, nav/footer, auth helpers
  analysis.js             Analysis logic: CSV parsing + statistics engine
  mitre.js                Countermeasures, recommendations, future directions
images/
  nethun.jpg              Researcher profile photo (placeholder — replace, see below)
data_dictionary.csv       Reference for expected CSV column codes
```

## Running locally

Because the pages use `fetch`/relative paths and load a CSV, open them
through a local server rather than double-clicking the file (some browsers
block certain features on `file://` URLs):

```bash
# from the repo root
python3 -m http.server 8000
# then open http://localhost:8000 in a browser
```

No build step, no dependencies to install — everything (PapaParse, Chart.js)
loads from a CDN in the HTML files.

## Important: this is a front-end-only demo, not real security

- **Authentication is not real.** `sign-In.html` / `sign-Up.html` store
  accounts in the visitor's own browser (`localStorage`), unhashed, with no
  server to verify anything against. It's a UX gate to match the requested
  page flow, not a security boundary — do not use it to protect sensitive
  data, and do not present it as authentication in a security-focused
  portfolio piece without this caveat.
- **Nothing is uploaded anywhere.** The CSV you select on the Analysis page
  is parsed and analysed entirely in your browser (PapaParse + hand-rolled
  regression/statistics code in `analysis.js`). This is actually a genuine
  privacy advantage worth highlighting: respondent data never leaves the
  visitor's machine.
- **Results are per-browser-tab.** Analysis output is kept in
  `sessionStorage`, so it persists across the Analysis → Results navigation
  but clears when the tab closes.

## Before you push to GitHub / share publicly

1. **Replace the profile photo.** `images/nethun.jpg` is currently a
   generated placeholder. Replace it with the actual photo of Nethun
   Kawitha Madanayake (same filename, or update `SITE_CONFIG.researcher.photo`
   in `styles/main.js`).

2. **Fill in the researcher's qualifications.** In `styles/main.js`, the
   `SITE_CONFIG.researcher.qualifications` array contains bracketed
   placeholders for the exact degree titles, awarding universities, and any
   certifications, since these weren't specified. Replace them, e.g.:
   ```js
   qualifications: [
       "MSc in Cybersecurity — [University Name]",
       "BSc (Hons) in [Subject] — [University Name]",
       "CEH / CISSP / OSCP (if applicable)",
   ],
   ```

## CSV format for the Analysis page

Google Forms exports the *full question text* as column headers. Before
uploading, rename the columns to the short codes defined in
`data_dictionary.csv`, for example:

| Code | Meaning |
|---|---|
| `A5_JobRole`, `A6_YearsInCybersecurity`, `A8_IndustrySector`, `A9_OrganizationSize` | Demographics |
| `B1`…`B10` | AI Tool Adoption (TAM) |
| `C1`…`C10` | AI Adoption Maturity |
| `D1_1`…`D1_5` | Mean Time to Detect |
| `D2_1`…`D2_5` | Mean Time to Respond |
| `E1`…`E10` | Alert Triage Accuracy |
| `F1`…`F10` | Analyst Productivity |
| `G1_1`…`G1_8` | Trust in AI |
| `G2_1`…`G2_8` | Explainability (item 5 is reverse-worded and is recoded automatically) |
| `H1`…`H10` | Organisational Factors & Challenges |
| `O1`…`O4` | Open-ended responses (optional, used for qualitative theme counts) |

If a scale's columns are only partially present, `analysis.js` computes the
composite from whatever items are available (matching a respondent-level
average of answered items) and reports this on the Results page rather than
failing. If none of the expected columns are found at all, the upload is
rejected with a clear error message.

## Hosting on GitHub Pages

1. **Create the repo and push.**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: SOC AI research site (static)"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Enable Pages.** On GitHub, go to your repository's **Settings** →
   **Pages** (left sidebar, under "Code and automation").

3. Under **Build and deployment**, set **Source** to **Deploy from a
   branch**, then set **Branch** to `main` and the folder to **/ (root)**
   (since `index.html` sits at the repo root). Click **Save**.

4. GitHub builds and publishes the site — this typically takes a minute or
   two. The Pages tab will then show your live URL, in the form:
   ```
   https://<your-username>.github.io/<repo-name>/
   ```

5. **Re-check relative links after first deploy.** Because GitHub Pages
   serves project sites from a `/<repo-name>/` sub-path (unless you're using
   a custom domain or a `<username>.github.io` repo specifically), all links
   in this project use *relative* paths (`styles/...`, `../styles/...`,
   `templates/...`) rather than absolute ones, so they work correctly under
   a sub-path without any changes.

6. Every subsequent `git push` to `main` redeploys the site automatically.

## Credits

Countermeasure and technique references are drawn from the
[MITRE ATT&CK&reg; framework](https://attack.mitre.org/). Powered by
MITRE ATT&CK&reg; | https://attack.mitre.org/
