# Secure Code Review Case Study: Django Blango

A comprehensive secure code review and vulnerability remediation case study of a Python/Django blogging application. Audited the codebase using automated SAST and manual analysis, resolved critical OWASP vulnerabilities, and published a professional PDF report.

---

## 🎯 The Challenge
Analyzing complex logic vulnerabilities, raw SQL usage, insecure settings, and missing authentication/CSRF checks in Python-based web applications, and fixing them without breaking application compatibility.

## 🛡️ The Solution & Hardening
Audited code using Semgrep/Bandit and manual analysis. Patched SQL injections by migrating to Django ORM, resolved XSS with secure auto-escaping templates, secured authentication flows, enforced CSRF tokens, and delivered a complete PDF audit report.

---

## 📊 Summary of Identified Vulnerabilities & Solutions

Below is a snapshot of the vulnerabilities identified during the audit and the remediation applied to secure them:

| Vulnerability ID | Finding | Severity | OWASP Category | Remediation Action |
|---|---|---|---|---|
| **SEC-01** | Raw SQL Queries (SQL Injection) | **Critical** | A03:2021-Injection | Migrated raw database queries to parameterized **Django ORM** queries. |
| **SEC-02** | Stored XSS in Comment Render | **High** | A03:2021-Injection | Removed the unsafe template bypass filter, allowing Django's auto-escaper to sanitize comments. |
| **SEC-03** | Missing CSRF Verification | **High** | A01:2021-Broken Access Control | Replaced `@csrf_exempt` decorators with `@csrf_protect` on state-changing endpoints. |
| **SEC-04** | Broken Access Control in Views | **High** | A01:2021-Broken Access Control | Added ownership verification checks to ensure authors can only edit/delete their own posts. |
| **SEC-05** | Active Debug Mode in Prod | **Medium** | A05:2021-Security Misconfiguration | Configured dynamic configurations loading environment variables to disable debug in prod. |

---

## 🛠️ Secure Code Review Methodology

### 1. Tool-Assisted Analysis (SAST)
We ran automated Static Application Security Testing (SAST) tools to scan the Python code patterns:
- **Bandit**: Identified hardcoded keys, active debug configurations, and insecure system calls.
- **Semgrep**: Scanned for custom rules matching unsafe raw Django SQL queries.

### 2. Manual Analysis (Line-by-Line Audit)
We manually audited:
- Input handling and query builders.
- Template rendering files (checking for custom safe filters and JavaScript outputs).
- View permissions (ensuring `PermissionDenied` exceptions are raised on unauthorized editing).
- Session cookies settings.

---

## 📂 Deliverables & Reports

- **Detailed Security Report**: You can read the full professional audit report containing in-depth vulnerability descriptions, proof-of-concepts, and risk analysis in the [Secure Code Review Report](Secure_Code_Review_Report.md).
- **PDF Version**: A professional formatted PDF version of the report is available under `/reports/Secure_Code_Review_Report.pdf` (compile the Markdown file or check the release section).

---

## 🚀 How to Run the Security Analysis

To replicate the automated security scans performed on this repository:

### 1. Install Dependencies
```bash
pip install bandit semgrep
```

### 2. Run Bandit Scan
```bash
bandit -r blango/
```

### 3. Run Semgrep Scan
```bash
semgrep --config=auto blango/
```
