/* ===========================================================
   main.js — All configurations
   Site-wide config, navigation, flash messages, and a client-side
   (localStorage-based) "auth" layer.

   IMPORTANT: This site is fully static (HTML/CSS/JS only, no
   server), so there is no real backend authentication. The
   sign-up / sign-in flow below is a front-end convenience gate
   only — it stores account info in the visitor's own browser
   (localStorage) and is easily bypassed by anyone with dev
   tools open. Do not rely on it to protect sensitive data.
   =========================================================== */

const SITE_CONFIG = {
    googleFormUrl:
        "https://docs.google.com/forms/d/e/1FAIpQLSfSrEEgZFvEDY9pm6mpI5Saim4IU0-24xSkcU8sBl87AbG4ig/viewform?usp=sharing&ouid=114509313058798884619",

    mitreAttackUrl: "https://attack.mitre.org/",

    researcher: {
        name: "Nethun Kawitha Madanayake",
        role: "Senior Information Security Engineer",
        affiliation: "SentryLabs Pvt. Ltd.",
        // Fill in the exact degree titles and awarding institutions here.
        qualifications: [
            "MSc in Cybersecurity (in progress) — [University Name]",
            "[BSc / undergraduate degree — University Name]",
            "[Relevant industry certifications, e.g. CEH / CISSP / OSCP]",
        ],
        linkedin: "https://www.linkedin.com/in/nethun-madanayake/",
        email: "nethunkawitha5@gmail.com",
        contact: "+94 76 329 3776 (Mobile & WhatsApp)",
        photo: "nethun.jpg",
    },
};

/* ---------------- Local-storage "auth" helpers ---------------- */
const AUTH_USERS_KEY = "soc_ai_users";
const AUTH_SESSION_KEY = "soc_ai_current_user";

const Auth = {
    _readUsers() {
        try {
            return JSON.parse(localStorage.getItem(AUTH_USERS_KEY)) || {};
        } catch (e) {
            return {};
        }
    },

    _writeUsers(users) {
        localStorage.setItem(AUTH_USERS_KEY, JSON.stringify(users));
    },

    // NOTE: password is stored as-typed in the browser's localStorage.
    // This is fine for a portfolio / demo gate but must NOT be treated
    // as secure credential storage — there is no hashing and no server.
    signUp(fullName, email, password) {
        const users = this._readUsers();
        const key = email.trim().toLowerCase();
        if (users[key]) {
            return { ok: false, error: "An account with that email already exists." };
        }
        users[key] = { fullName: fullName.trim(), email: key, password };
        this._writeUsers(users);
        return { ok: true };
    },

    signIn(email, password) {
        const users = this._readUsers();
        const key = email.trim().toLowerCase();
        const user = users[key];
        if (!user || user.password !== password) {
            return { ok: false, error: "Invalid email or password." };
        }
        sessionStorage.setItem(AUTH_SESSION_KEY, JSON.stringify({ fullName: user.fullName, email: user.email }));
        return { ok: true };
    },

    currentUser() {
        try {
            return JSON.parse(sessionStorage.getItem(AUTH_SESSION_KEY));
        } catch (e) {
            return null;
        }
    },

    signOut() {
        sessionStorage.removeItem(AUTH_SESSION_KEY);
    },

    requireLogin(redirectTo) {
        if (!this.currentUser()) {
            window.location.href = redirectTo || "sign-In.html";
            return false;
        }
        return true;
    },
};

/* ---------------- Flash / toast messages ---------------- */
function showFlash(message, category) {
    category = category || "info";
    let container = document.querySelector(".flash-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "flash-container";
        const main = document.querySelector("main.page-content") || document.body;
        main.insertBefore(container, main.firstChild);
    }
    const el = document.createElement("div");
    el.className = "flash flash-" + category;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(function () {
        el.style.transition = "opacity 0.4s ease";
        el.style.opacity = "0";
        setTimeout(function () { el.remove(); }, 400);
    }, 6000);
}

/* ---------------- Shared nav / footer rendering ---------------- */
// basePath: "" when called from index.html at the repo root,
// "../" when called from a page inside templates/.
function renderHeaderFooter(basePath) {
    basePath = basePath || "";
    const user = Auth.currentUser();

    const headerEl = document.getElementById("site-header");
    if (headerEl) {
        headerEl.innerHTML = `
            <div class="container header-inner">
                <a href="${basePath}index.html" class="brand">
                    <span class="brand-icon">&#128274;</span>
                    <span class="brand-text">SOC&nbsp;AI&nbsp;Research</span>
                </a>
                <nav class="main-nav">
                    <a href="${basePath}index.html">Home</a>
                    <a href="${basePath}templates/analysis.html">Analysis</a>
                    ${user
                        ? `<span class="nav-user">Hi, ${user.fullName}</span>
                           <a href="#" id="nav-signout" class="btn btn-outline btn-sm">Sign out</a>`
                        : `<a href="${basePath}templates/sign-In.html" class="btn btn-outline btn-sm">Sign in</a>
                           <a href="${basePath}templates/sign-Up.html" class="btn btn-primary btn-sm">Sign up</a>`
                    }
                </nav>
            </div>`;

        const signoutLink = document.getElementById("nav-signout");
        if (signoutLink) {
            signoutLink.addEventListener("click", function (e) {
                e.preventDefault();
                Auth.signOut();
                window.location.href = basePath + "index.html";
            });
        }
    }

    const footerEl = document.getElementById("site-footer");
    if (footerEl) {
        footerEl.innerHTML = `
            <div class="container footer-inner">
                <p>&copy; 2026 The Impact of AI-Based Solutions on Incident Response Efficiency in SOC Environments.</p>
                <p class="mitre-credit">
                    Powered by MITRE ATT&amp;CK&reg; |
                    <a href="${SITE_CONFIG.mitreAttackUrl}" target="_blank" rel="noopener">${SITE_CONFIG.mitreAttackUrl}</a>
                </p>
            </div>`;
    }
}
