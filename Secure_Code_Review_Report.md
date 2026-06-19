# Secure Code Review & Vulnerability Remediation Report
**Target Application:** Django Blango (Blogging Web Application)  
**Assigned Auditor:** Ohoud Alawad (Security Consultant)  
**Date:** June 2, 2026  
**Status:** Completed & Remediated  

---

## 1. Executive Summary

### 1.1 Objective
The objective of this assessment was to perform a comprehensive **Secure Code Review (SCR)** of the Django Blango web application, identifying security flaws, logical vulnerabilities, and deviations from secure development practices, and implementing appropriate **Remediation (Fixes)** to secure the application.

### 1.2 Scope
The scope of this audit covers all backend Python/Django source code, templates, database configurations, and authentication settings of the Blango repository.

### 1.3 Methodology
A hybrid methodology was adopted, combining:
1. **Automated Static Application Security Testing (SAST)**: Using tools like `Semgrep` and `Bandit` to scan the codebase for known vulnerability patterns, insecure libraries, and configuration issues.
2. **Manual Code Auditing**: Reviewing input handling logic, authorization verification, authentication sessions, and database queries for logical flaws (OWASP Top 10) not easily caught by automated scanners.

### 1.4 Vulnerability Breakdown Summary
| Vulnerability ID | Vulnerability Name | Severity | OWASP 2021 Category | Status |
|---|---|---|---|---|
| **SEC-01** | Raw SQL Queries (SQL Injection) | **Critical** | A03:2021-Injection | **Remediated** |
| **SEC-02** | Stored Cross-Site Scripting (XSS) in Comments | **High** | A03:2021-Injection | **Remediated** |
| **SEC-03** | Missing CSRF Protection Decorators | **High** | A01:2021-Broken Access Control | **Remediated** |
| **SEC-04** | Broken Access Control (Insecure Views) | **High** | A01:2021-Broken Access Control | **Remediated** |
| **SEC-05** | Insecure Settings Configuration (DEBUG Mode Active) | **Medium** | A05:2021-Security Misconfiguration | **Remediated** |

---

## 2. Detailed Vulnerability Findings & Remediations

### SEC-01: SQL Injection via Raw SQL Queries (Critical)
- **Vulnerability Type:** SQL Injection (SQLi)
- **Location:** `blango/views.py` (Search/Filter function)
- **Impact:** An attacker can manipulate search inputs to bypass authentication, dump database tables, or execute administrative commands inside the database system.

#### Vulnerable Code Example (Before):
```python
# blango/views.py
from django.db import connection
from django.shortcuts import render

def search_posts(request):
    query = request.GET.get('q', '')
    # VULNERABLE: Direct string interpolation into raw SQL query
    sql_query = f"SELECT * FROM blango_post WHERE title LIKE '%{query}%' AND published = TRUE"
    
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        posts = cursor.fetchall()
        
    return render(request, "blog/search_results.html", {"posts": posts, "query": query})
```

#### Remediation Strategy:
Avoid building SQL queries via string interpolation. Instead, leverage **Django ORM** which automatically parameterizes queries, or use parameter placeholders (`%s` or `params`) in cursor execution to separate user input from SQL commands.

#### Remediated Code (After):
```python
# blango/views.py
from django.shortcuts import render
from blango.models import Post

def search_posts(request):
    query = request.GET.get('q', '')
    
    # SECURE: Django ORM parameterizes variables and prevents SQL injection
    posts = Post.objects.filter(title__icontains=query, published=True)
    
    # ALTERNATIVE (If raw SQL is strictly required):
    # with connection.cursor() as cursor:
    #     cursor.execute("SELECT * FROM blango_post WHERE title LIKE %s AND published = TRUE", [f'%{query}%'])
        
    return render(request, "blog/search_results.html", {"posts": posts, "query": query})
```

---

### SEC-02: Stored Cross-Site Scripting (XSS) in Comments (High)
- **Vulnerability Type:** Stored Cross-Site Scripting (XSS)
- **Location:** `templates/blog/post-detail.html` (Comments rendering block)
- **Impact:** Attackers can submit comments containing malicious JavaScript code (e.g., `<script>stealCookies()</script>`). When other users view the blog post, the script runs in their browsers, potentially stealing session tokens or hijacking accounts.

#### Vulnerable Code Example (Before):
```html
<!-- templates/blog/post-detail.html -->
<div class="comments-section">
    {% for comment in comments %}
        <div class="comment">
            <strong>{{ comment.author }}</strong>: 
            <!-- VULNERABLE: 'safe' filter bypasses Django HTML escaping, allowing scripts to execute -->
            <p>{{ comment.content|safe }}</p>
        </div>
    {% endfor %}
</div>
```

#### Remediation Strategy:
Do not use the `safe` filter on user-provided inputs unless it is thoroughly sanitized first. Django's default behavior is to automatically escape variable outputs. If rich text is required, sanitize inputs using a robust HTML sanitizer library like `bleach` before saving or rendering.

#### Remediated Code (After):
```html
<!-- templates/blog/post-detail.html -->
<div class="comments-section">
    {% for comment in comments %}
        <div class="comment">
            <strong>{{ comment.author }}</strong>: 
            <!-- SECURE: Removed safe filter. Django auto-escapes html markup tags -->
            <p>{{ comment.content }}</p>
        </div>
    {% endfor %}
</div>
```

---

### SEC-03: Missing CSRF Protection Decorators (High)
- **Vulnerability Type:** Cross-Site Request Forgery (CSRF)
- **Location:** `blango/views.py` (Comment Submission endpoint)
- **Impact:** If CSRF validation is disabled or omitted on state-changing endpoints, an attacker can trick authenticated users into executing unintended actions on the web application (e.g., submitting posts or changing account credentials).

#### Vulnerable Code Example (Before):
```python
# blango/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# VULNERABLE: Exempting state-changing POST endpoint from CSRF validation
@csrf_exempt
def submit_comment(request, post_id):
    if request.method == "POST":
        content = request.POST.get('content')
        # Logic to save comment...
        return HttpResponse("Comment submitted successfully.")
```

#### Remediation Strategy:
Never use `@csrf_exempt` on `POST`, `PUT`, or `DELETE` requests unless explicit security controls (like OAuth tokens or custom authorization headers) are implemented. Always ensure the `{% csrf_token %}` template tag is included inside all HTML forms.

#### Remediated Code (After):
```python
# blango/views.py
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# SECURE: Explicitly enforce CSRF verification and ensure authentication
@login_required
@csrf_protect
def submit_comment(request, post_id):
    if request.method == "POST":
        content = request.POST.get('content')
        # Logic to save comment securely...
        return HttpResponse("Comment submitted successfully.")
```

---

### SEC-04: Broken Access Control (Insecure Views) (High)
- **Vulnerability Type:** Privilege Escalation / Unauthorized Data Access
- **Location:** `blango/views.py` (Post Edit / Delete endpoints)
- **Impact:** Unauthenticated users or regular authors can edit or delete blog posts belonging to other users simply by navigating to the editing URLs, bypassing intended permission restrictions.

#### Vulnerable Code Example (Before):
```python
# blango/views.py
from django.shortcuts import get_object_or_404, redirect
from blango.models import Post

# VULNERABLE: No authorization check to ensure the user is logged in or is the author of the post
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.save()
        return redirect('post_detail', post_id=post.pk)
```

#### Remediation Strategy:
Enforce authorization rules by validating that:
1. The user is authenticated (`login_required` decorator).
2. The user has ownership rights over the requested object, or has global administrator privileges.

#### Remediated Code (After):
```python
# blango/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from blango.models import Post

# SECURE: Verified user session and strict ownership checks
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # Ownership Validation
    if post.author != request.user and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to edit this post.")
        
    if request.method == "POST":
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.save()
        return redirect('post_detail', post_id=post.pk)
```

---

### SEC-05: Security Misconfiguration - Active DEBUG Mode (Medium)
- **Vulnerability Type:** Information Disclosure
- **Location:** `blango/settings.py`
- **Impact:** Running Django with `DEBUG = True` in production environments exposes full stack trace dumps, database schemas, local directory paths, and configuration variables to the public upon application errors.

#### Vulnerable Code Example (Before):
```python
# blango/settings.py

# VULNERABLE: Debugging flags left enabled in production settings
DEBUG = True

ALLOWED_HOSTS = ['*']
```

#### Remediation Strategy:
Disable `DEBUG` flag in production environments. Explicitly list valid hosting domain names in `ALLOWED_HOSTS` to prevent Host Header Injection attacks, and load critical configuration flags using environment variables.

#### Remediated Code (After):
```python
# blango/settings.py
import os

# SECURE: Debug mode disabled in production, controlled via environment variables
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ["true", "1"]

# Enforce secure host header checks
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "yourdomain.com,www.yourdomain.com").split(",")
```

---

## 3. General Security Recommendations

1. **Dependency Auditing**: Integrate tools like `pip-audit` or `safety` into the local pre-commit hook and CI/CD pipelines to monitor and patch vulnerable third-party dependencies automatically.
2. **Secure Session Cookie Flags**: Enforce SSL cookies inside production Django settings:
   ```python
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   ```
3. **Continuous SAST Scanning**: Set up automated Semgrep scans inside GitHub Actions workflows to block commits containing raw SQL queries or disabled CSRF tokens before integration.
