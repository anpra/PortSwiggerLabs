# Burp Suite: a beginner's guide to web security testing

## Intro

If you are a beginner in web security — or just curious about the subject and landed here — I would suggest you start getting familiar with tools like Burp Suite and Caido. Besides the Network tab in Firefox, they will be extremely useful when analysing requests.

I noticed the need to write this because I'm publishing my PortSwigger lab write-ups and I keep talking about the tools inside Burp Suite. I'll write one about Caido as well, to give you other options.

## What is Burp Suite?

Burp Suite is a suite of tools for testing web applications, and its core is an intercepting web proxy. It sits between your browser and the target, letting you see, intercept, modify, and resend the HTTP traffic. It comes in two main editions:

- **Community** — free, and more than enough to learn and to solve the Academy labs.
- **Pro** — paid, adds an automated scanner, Burp Collaborator, and removes the Intruder rate limit.

For requirements, download instructions, and everything else, the official documentation is excellent:
https://portswigger.net/burp/documentation/desktop

They have a huge, well-documented set of functionalities and walkthroughs.

## Why not just the browser Network tab?

The Network tab is great for seeing requests, but it is read-only. Burp lets you:

- intercept a request before it reaches the server and change it;
- resend the same request as many times as you want (Repeater);
- automate payloads (Intruder);
- encode/decode data (Decoder) and compare responses (Comparer).

That difference — being able to change and replay requests — is what makes a proxy like Burp (or Caido) essential.

## The tools I use the most

- **Proxy** — the heart of Burp. Everything your browser sends passes through it, and the HTTP history is where I usually spot the interesting requests.
- **Repeater** — where I spend most of my time. I send a request here and modify it by hand, changing headers, parameters, filenames, and payloads.
- **Intruder** — for automated attacks and fuzzing (payload positions and lists). In Community it is rate-limited, but it still works.
- **Decoder** — quick encoding/decoding (URL, Base64, hex...). Useful when a payload needs to be encoded.
- **Comparer** — highlights the difference between two responses, handy when a tiny change matters.
- **Extensions** — Burp has a store (BApp Store). Two I use: **Hackvertor** (tags to encode payloads inline) and the **MCP Server** extension, which connects Burp to AI clients.

## Community vs Pro

Start with Community. It is free and covers everything you need for the Academy labs. Move to Pro when you want the scanner, Collaborator, or a faster Intruder.

## Getting started

1. Download Burp (Community or Pro) from https://portswigger.net/burp/releases.
2. Configure your browser to use Burp as its proxy (FoxyProxy is a common choice).
3. Install Burp's CA certificate so HTTPS traffic is intercepted without errors.
4. Open the built-in browser or your own, and start exploring.

## Where to practice

The best place to practice is the PortSwigger Web Security Academy (https://portswigger.net/web-security) — free labs that cover every topic, from file upload to SQL injection. That is exactly what I'm documenting here.

## Closing

Burp Suite is one of those tools that pays off the more you use it. Start with the Proxy and Repeater, add the rest as you need them, and practice on the Academy labs.

Next, I'll write about Caido, a lighter alternative with a modern interface.
