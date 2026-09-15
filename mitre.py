"""
mitre.py
----------
Countermeasures, recommendations and future-direction content for the
"Impact of AI-Based Solutions on Incident Response Efficiency in SOC
Environments" research site.

Technique references are drawn from the MITRE ATT&CK Enterprise matrix
(https://attack.mitre.org/). Technique IDs, names and tactics below are
kept aligned with the public MITRE ATT&CK knowledge base; always verify
against attack.mitre.org for the most current version before citing in
a formal report, since ATT&CK content is updated periodically by MITRE.
"""

MITRE_ATTACK_URL = "https://attack.mitre.org/"

# A curated set of ATT&CK Enterprise techniques most relevant to SOC
# incident-response workflows and commonly referenced in AI-assisted
# detection and response literature.
COUNTERMEASURES = [
    {
        "id": "T1566",
        "name": "Phishing",
        "tactic": "Initial Access (TA0001)",
        "description": (
            "Adversaries send phishing messages to gain access to victim systems, "
            "often as the opening move of an intrusion."
        ),
        "ai_relevance": (
            "AI-based email and URL classifiers can triage suspected phishing at a "
            "volume no manual process can match, directly shortening MTTD for this "
            "very common entry vector."
        ),
        "mitigation": (
            "Deploy AI-assisted email filtering and URL sandboxing, enforce user "
            "training, and use DMARC/DKIM/SPF alongside automated triage of "
            "reported phishing emails."
        ),
        "url": "https://attack.mitre.org/techniques/T1566/",
    },
    {
        "id": "T1078",
        "name": "Valid Accounts",
        "tactic": "Defense Evasion / Persistence / Privilege Escalation (TA0005/TA0003/TA0004)",
        "description": (
            "Adversaries obtain and abuse legitimate credentials to blend in with "
            "normal activity and evade detection."
        ),
        "ai_relevance": (
            "User- and entity-behaviour analytics (UEBA) models can flag anomalous "
            "use of valid credentials that rule-based SIEM correlation typically misses."
        ),
        "mitigation": (
            "Enforce MFA, monitor for impossible-travel and off-hours logins with "
            "behavioural analytics, and rotate/disable credentials promptly after "
            "role changes or departures."
        ),
        "url": "https://attack.mitre.org/techniques/T1078/",
    },
    {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access (TA0001)",
        "description": (
            "Adversaries exploit weaknesses in internet-facing systems (web apps, "
            "APIs, VPN gateways) to gain a foothold."
        ),
        "ai_relevance": (
            "AI-driven vulnerability prioritisation helps SOC teams focus patching "
            "effort on the exposures most likely to be exploited, improving "
            "triage accuracy for perimeter alerts."
        ),
        "mitigation": (
            "Maintain a rigorous patch-management cadence, deploy a Web Application "
            "Firewall (WAF), and run continuous external attack-surface scanning."
        ),
        "url": "https://attack.mitre.org/techniques/T1190/",
    },
    {
        "id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution (TA0002)",
        "description": (
            "Adversaries abuse command and scripting interpreters (PowerShell, "
            "Bash, Python, etc.) to execute commands and payloads."
        ),
        "ai_relevance": (
            "Machine-learning models trained on command-line telemetry can "
            "distinguish malicious scripting patterns from legitimate admin "
            "activity far faster than manual log review."
        ),
        "mitigation": (
            "Enable script-block logging, apply constrained-language mode / "
            "application control, and alert on encoded or obfuscated command "
            "lines."
        ),
        "url": "https://attack.mitre.org/techniques/T1059/",
    },
    {
        "id": "T1027",
        "name": "Obfuscated Files or Information",
        "tactic": "Defense Evasion (TA0005)",
        "description": (
            "Adversaries encode, encrypt or otherwise obfuscate content to evade "
            "signature-based detection."
        ),
        "ai_relevance": (
            "Static and behavioural ML classifiers can flag obfuscation patterns "
            "that signature-based antivirus tools miss, reducing false negatives "
            "in the triage queue."
        ),
        "mitigation": (
            "Use behavioural (not purely signature-based) endpoint detection, "
            "and sandbox-detonate suspicious files before allow-listing."
        ),
        "url": "https://attack.mitre.org/techniques/T1027/",
    },
    {
        "id": "T1003",
        "name": "OS Credential Dumping",
        "tactic": "Credential Access (TA0006)",
        "description": (
            "Adversaries dump credentials from operating system memory or "
            "storage (e.g., LSASS) to obtain account access."
        ),
        "ai_relevance": (
            "Anomaly-detection models on process-access patterns (e.g., unusual "
            "handles opened on LSASS) can catch dumping attempts that evade "
            "static rules."
        ),
        "mitigation": (
            "Enable Credential Guard, restrict local admin rights, and monitor "
            "for LSASS access from non-standard processes."
        ),
        "url": "https://attack.mitre.org/techniques/T1003/",
    },
    {
        "id": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control (TA0011)",
        "description": (
            "Adversaries use common application-layer protocols (HTTP, DNS, "
            "etc.) to blend command-and-control traffic with legitimate traffic."
        ),
        "ai_relevance": (
            "AI-based network traffic analysis (beaconing detection, JA3/JA3S "
            "fingerprinting, DNS entropy scoring) helps surface disguised C2 "
            "channels that keyword or IP-blocklist rules miss."
        ),
        "mitigation": (
            "Deploy network detection and response (NDR) tooling, inspect TLS "
            "metadata for beaconing patterns, and enforce egress filtering."
        ),
        "url": "https://attack.mitre.org/techniques/T1071/",
    },
    {
        "id": "T1486",
        "name": "Data Encrypted for Impact",
        "tactic": "Impact (TA0040)",
        "description": (
            "Adversaries encrypt data on target systems to disrupt availability, "
            "typically as part of a ransomware operation."
        ),
        "ai_relevance": (
            "Rapid, AI-assisted detection of mass file-encryption behaviour "
            "directly shortens MTTR by triggering automated isolation before "
            "encryption spreads across the environment."
        ),
        "mitigation": (
            "Maintain offline, tested backups, deploy behavioural ransomware "
            "canaries, and enable automated host-isolation playbooks triggered "
            "by mass file-modification alerts."
        ),
        "url": "https://attack.mitre.org/techniques/T1486/",
    },
    {
        "id": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration (TA0010)",
        "description": (
            "Adversaries exfiltrate data over the same channel already used for "
            "command and control, avoiding the need for a separate channel."
        ),
        "ai_relevance": (
            "Volumetric and behavioural anomaly detection on outbound traffic "
            "improves triage accuracy for slow, low-and-slow exfiltration that "
            "static DLP thresholds often miss."
        ),
        "mitigation": (
            "Deploy data-loss prevention (DLP) tooling, monitor for abnormal "
            "outbound data volumes, and apply strict egress proxy controls."
        ),
        "url": "https://attack.mitre.org/techniques/T1041/",
    },
    {
        "id": "T1021",
        "name": "Remote Services",
        "tactic": "Lateral Movement (TA0008)",
        "description": (
            "Adversaries use valid accounts to log into services (RDP, SSH, "
            "SMB) accessible remotely, moving laterally within a network."
        ),
        "ai_relevance": (
            "Graph-based and behavioural analytics can flag unusual lateral "
            "authentication paths across the estate, an area where AI-assisted "
            "correlation consistently outperforms manual log review at scale."
        ),
        "mitigation": (
            "Segment networks, restrict RDP/SSH exposure, and monitor for "
            "atypical internal authentication chains."
        ),
        "url": "https://attack.mitre.org/techniques/T1021/",
    },
]


def get_countermeasures():
    """Return the full curated ATT&CK countermeasure reference list."""
    return COUNTERMEASURES


def generate_recommendations(construct_means):
    """
    Given a dict of construct_name -> mean score (1-5 Likert scale),
    generate plain-language recommendations. Thresholds:
        < 3.00        -> weak / priority area
        3.00 - 3.75   -> moderate / worth reinforcing
        > 3.75        -> strong / maintain
    Falls back gracefully if a construct is missing from the input.
    """
    recs = []

    def band(score):
        if score is None:
            return None
        if score < 3.00:
            return "priority"
        if score <= 3.75:
            return "moderate"
        return "strong"

    trust = construct_means.get("Trust")
    explain = construct_means.get("Explainability")
    maturity = construct_means.get("AdoptionMaturity")
    org = construct_means.get("OrgFactors")

    b = band(trust)
    if b == "priority":
        recs.append({
            "title": "Invest in analyst trust-building",
            "detail": (
                "Trust in AI outputs scored low in this sample. Prioritise "
                "transparent model documentation, structured onboarding for "
                "new AI tooling, and a visible escalation path for analysts "
                "who disagree with an AI recommendation. Trust has been shown "
                "to moderate whether AI adoption translates into measurable "
                "efficiency gains, so this is a high-leverage area."
            ),
        })
    elif b == "moderate":
        recs.append({
            "title": "Reinforce trust through consistent feedback loops",
            "detail": (
                "Trust is moderate. Close the loop with analysts by tracking "
                "and sharing AI recommendation accuracy over time, and by "
                "involving analysts in periodic model review sessions."
            ),
        })
    elif b == "strong":
        recs.append({
            "title": "Maintain current trust-building practice",
            "detail": (
                "Trust in AI outputs is already strong in this sample. "
                "Maintain current transparency and onboarding practices as "
                "AI tooling is expanded to new use cases."
            ),
        })

    b = band(explain)
    if b == "priority":
        recs.append({
            "title": "Improve explainability of AI outputs",
            "detail": (
                "Explainability scored low. Favour AI tools that surface the "
                "evidence behind a verdict (matched indicators, contributing "
                "features) rather than a bare score, and provide analysts with "
                "a short reference guide to how each deployed model reaches "
                "its conclusions."
            ),
        })
    elif b == "moderate":
        recs.append({
            "title": "Extend explainability documentation",
            "detail": (
                "Explainability is moderate. Consider adding worked examples "
                "of AI decision paths to analyst training materials."
            ),
        })

    b = band(maturity)
    if b == "priority":
        recs.append({
            "title": "Progress AI adoption maturity deliberately",
            "detail": (
                "AI adoption maturity is still early-stage. Rather than adding "
                "more point tools, focus on integrating existing AI capability "
                "into standard operating procedures and playbooks so its "
                "output is consistently used, not just occasionally consulted."
            ),
        })
    elif b == "strong":
        recs.append({
            "title": "Scale mature AI capability to adjacent workflows",
            "detail": (
                "AI adoption maturity is strong. Consider extending proven "
                "AI-assisted triage or correlation capability to adjacent "
                "workflows such as vulnerability prioritisation or threat "
                "hunting."
            ),
        })

    b = band(org)
    if b == "priority":
        recs.append({
            "title": "Address organisational readiness barriers",
            "detail": (
                "Organisational factors and challenges scored low, suggesting "
                "barriers such as budget, staffing, or legacy-system "
                "integration are limiting the return on AI investment. Address "
                "these structural constraints alongside any further tooling "
                "purchases."
            ),
        })

    if not recs:
        recs.append({
            "title": "Insufficient data for tailored recommendations",
            "detail": (
                "Upload a dataset containing the Trust, Explainability, "
                "AdoptionMaturity and OrgFactors constructs to generate "
                "tailored recommendations."
            ),
        })

    return recs


def get_future_directions():
    """Static list of future research / practice directions for the results page."""
    return [
        {
            "title": "Longitudinal tracking",
            "detail": (
                "Track the same SOC teams over multiple quarters as AI adoption "
                "deepens, to test whether trust and efficiency gains reported "
                "here hold up, grow, or fade over time."
            ),
        },
        {
            "title": "Cross-market replication",
            "detail": (
                "Repeat the survey in other South Asian markets to test whether "
                "the relationships found here are specific to one country or "
                "reflect a wider regional pattern."
            ),
        },
        {
            "title": "Operational log triangulation",
            "detail": (
                "Combine this survey instrument with objective MTTD/MTTR log "
                "data from SIEM/SOAR platforms to reduce reliance on "
                "self-reported efficiency measures."
            ),
        },
        {
            "title": "Mediation testing for explainability",
            "detail": (
                "Use structural equation modelling or a mediation-focused "
                "design to test directly whether explainability's effect on "
                "efficiency runs primarily through trust."
            ),
        },
        {
            "title": "Multi-user platform maturity",
            "detail": (
                "Extend this research tool from a single-session analysis "
                "utility into a persistent, database-backed benchmarking "
                "platform that a sector body (e.g., a national CERT) could "
                "operate on an ongoing basis."
            ),
        },
    ]
