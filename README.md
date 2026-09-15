# SOC AI Research Site

**The Impact of AI-Based Solutions on Incident Response Efficiency in SOC Environments**

A Flask website that hosts the project questionnaire, accepts an exported CSV of
responses, runs the full statistical analysis (reliability, correlation,
hypothesis testing) used in the underlying research, and presents
MITRE ATT&CK&reg;-aligned recommendations based on the results.

## Directory structure

```
main.py            Flask app, routes, configuration, authentication
analysis.py         Statistical analysis logic (pandas / scipy / statsmodels)
mitre.py             Countermeasures, recommendations, future directions (MITRE ATT&CK)
templates/
  base.html          Shared layout (nav + footer)
  index.html         Home page, questionnaire embed, researcher profile
  sign-in.html
  sign-up.html
  analysis.html      CSV upload page
  results.html       Results & Discussion page
styles/
  styles.css
  main.js
images/
  nethun.jpg         Researcher profile photo (placeholder — replace, see below)
data_dictionary.csv   Reference for expected CSV column codes
requirements.txt
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Open **http://127.0.0.1:5000** in a browser. A SQLite database (`users.db`) is
created automatically on first run for the sign-in / sign-up accounts.

## Before you push to GitHub / deploy

1. **Replace the profile photo.** `images/nethun.jpg` is currently a generated
   placeholder. Replace it with the actual photo of Nethun Kawitha Madanayake
   (same filename, or update `RESEARCHER["photo"]` in `main.py`).

2. **Fill in the researcher's qualifications.** In `main.py`, the
   `RESEARCHER["qualifications"]` list contains bracketed placeholders for the
   exact degree titles, awarding universities, and any certifications, since
   these weren't specified. Replace them with the real details, e.g.:
   ```python
   "qualifications": [
       "MSc in Cybersecurity — [University Name]",
       "BSc (Hons) in [Subject] — [University Name]",
       "CEH / CISSP / OSCP (if applicable)",
   ],
   ```

3. **Set a real secret key** before deploying anywhere public:
   ```bash
   export SECRET_KEY="a-long-random-value"
   ```
   `main.py` falls back to a development key otherwise, which is not safe for
   production use.

4. **Do not commit `users.db`** or any uploaded CSVs — both are already
   excluded via `.gitignore`.

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

If a scale's columns are only partially present, `analysis.py` computes the
composite from whatever items are available and reports this on the Results
page rather than failing. If none of the expected columns are found at all,
the upload is rejected with a clear error message.

## Data handling note

The raw uploaded CSV is deleted from the server immediately after analysis;
only the aggregated, non-identifying statistical results are kept (in
`uploads/results/`, keyed to the browser session) so the Results page can be
revisited without re-uploading.

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Initial commit: SOC AI research site"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Credits

Countermeasure and technique references are drawn from the
[MITRE ATT&CK&reg; framework](https://attack.mitre.org/). Powered by
MITRE ATT&CK&reg; | https://attack.mitre.org/
