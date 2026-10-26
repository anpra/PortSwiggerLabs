# PortSwigger Lab: Low-level logic flaw

# TAGS: Business Logic, Integer Overflow, Cart Manipulation, Burp Suite

Category: Business Logic
Date: October 23, 2026
Day: Friday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-low-level
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. Here the flaw is low-level: the cart total is stored in a 32-bit integer that overflows when the value gets too large. I show the two phases — first detecting the overflow, then adjusting the cart so the total lands inside the affordable range.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application does not adequately validate user input and that there is a logic flaw in the purchase workflow. The goal is to buy the **Lightweight l33t leather jacket** ($1,337.00).

I logged in with the credentials provided by the lab (`wiener:peter`) and had a store credit of **$100.00**. I added the jacket (`productId=1`) to the cart and studied the `POST /cart` request:

```http
POST /cart HTTP/2
Host: 0a03008a042214ef8126b1cb00fb0021.web-security-academy.net
Cookie: session=ieaWfSv2LeOa7XcsYUQK3mQON9ftD5mT
Content-Type: application/x-www-form-urlencoded

productId=1&redir=PRODUCT&quantity=1
```

Useful details:

- The `quantity` parameter is limited to **two digits** — the largest positive value accepted is `99` (`quantity=100` returns a 400).
- A **negative** quantity is accepted and removes units from the cart, but it cannot take the quantity below zero.
- The cart total is `price × quantity`, stored in a **32-bit signed integer** (in cents). It wraps at `2³¹ − 1` cents ≈ `$21,474,836.47`.

So a single request can't overflow the total; the item has to be added many times.

---

## Exploitation:

#### Step 1: Detect the overflow

I kept adding the jacket 99 at a time. At some point the total no longer grew as expected — it wrapped around to a **negative** value:

```text
... total $21,178,080.00
total after wrap: $-21,242,140.96
```

That jump is the signature of an integer overflow. When I tried to check out with the negative total, the application rejected it:

> Cart total price cannot be less than zero

So the total must land **between $0 and $100** (the store credit), not just be negative.

#### Step 2: Adjust the quantity to land in [0, $100]

After the wrap, the total is a small-ish wrapped value (in my case `$2,536.48`). Since it is still above the credit, I **removed** some units of a cheaper item with a negative quantity until the total dropped into the affordable range:

```http
POST /cart HTTP/2
Host: 0a03008a042214ef8126b1cb00fb0021.web-security-academy.net
Cookie: session=ieaWfSv2LeOa7XcsYUQK3mQON9ftD5mT
Content-Type: application/x-www-form-urlencoded

productId=16&redir=CART&quantity=-146
```

The total went from `$2,536.48` to **`$7.76`** — inside `[0, $100]`.

> Tip: the adjustment works in both directions — add units when the total is negative, remove units when it is positive but above the credit. The negative quantity is capped at the existing quantity, so you can only remove what is in the cart.

#### Step 3: Checkout

With the total inside the credit, the checkout succeeds:

```http
POST /cart/checkout HTTP/2
Host: 0a03008a042214ef8126b1cb00fb0021.web-security-academy.net
Cookie: session=ieaWfSv2LeOa7XcsYUQK3mQON9ftD5mT
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>
```

The response was the order confirmation ("Congratulations, you solved the lab!") and the lab was solved.

#### Automating with a script

Because the quantity is capped at 99, the overflow requires hundreds of `POST /cart` requests — painfully slow by hand (or with Burp Community's rate-limited Intruder). So I automated the whole flow in `scripts/low_level_logic_overflow.py`: it adds a buffer of the cheap item, overflows the total with the jacket, fine-tunes the total into `[0, $100]`, and checks out.

---

## Root Cause

The application stores the cart total in a fixed-width 32-bit signed integer and never validates the quantity against the total. Because the total is `price × quantity` and the quantity can grow without bound (in increments of 99), the value overflows and wraps. The checkout only checks that the total is not negative; it does not detect that the value is the result of an overflow, so a wrapped total within the credit is accepted.

---

## Impact

An attacker can buy expensive items for an arbitrary (tiny) price — here, a $1,337 jacket (and thousands of units) for a few dollars. This is a low-level implementation flaw (a data type too small) that causes direct revenue loss and can produce inconsistent order totals.

---

## Remediation

To prevent this issue, applications should:

- Use a data type large enough for the total (or arbitrary-precision integers);
- Validate the quantity server-side and enforce a sensible upper bound;
- Recompute and validate the order total on the server before processing payment;
- Reject totals that are the result of an overflow (e.g. check for negative or unexpectedly small values relative to the items).

---

## Key Takeaways

1. First **detect** the overflow: the total wraps and jumps to a negative value.
2. The checkout rejects negative totals, so the total has to land in `[0, $100]`.
3. After the wrap, **adjust the quantity** (add or remove items) to bring the total into the affordable range.
4. A negative quantity can remove units but cannot go below zero — and it is a handy way to fine-tune the total.
5. The quantity cap (99) made the bulk overflow slow; a script or Intruder is needed to automate the repeated adds.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Low-level logic flaw (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-low-level)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
