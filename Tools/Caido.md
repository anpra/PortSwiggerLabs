# Caido: a lightweight alternative for web security testing

## Intro

Caido is a web security auditing toolkit, and — like Burp Suite — its core is an intercepting proxy. If Burp is the heavyweight veteran, Caido is the newer, lightweight option, with a modern interface and a much smaller footprint.

It's for the same audience as Burp: anyone testing web applications, from beginners solving labs to pentesters and bug bounty hunters. If you are starting in web security, having a second proxy is genuinely useful — you end up understanding the concepts instead of memorizing one tool's menus.

**Similarities with Burp:** an intercepting proxy with an HTTP history, a Repeater-style tool (Replay), automated attacks (Automate), and a plugin system.

**Differences:** Caido is lighter and feels faster, and the UI is more modern.

**License:** Caido is not open source, but it has a generous free plan. The **Basic** plan is free forever and is enough to learn: it allows up to 2 projects, 7 workflows, and 3 plugins. There are also paid Individual, Team, and Enterprise plans, plus a free 1-year education plan for students and teachers.

## Installation

You can download it here:
https://www.caido.io/download/

After downloading, I installed it with `dpkg`. If your distribution is different, or you use macOS or Windows, it is also available on the link above.

```bash
sudo dpkg -i caido-desktop-v0.58.3-linux-x86_64.deb
```

They offer a variety of documentation on how to use it, with guides and tutorials:
https://docs.caido.io/

They also have labs to study and exploit vulnerabilities, like Cross-Site Scripting. It's really worth a look:
https://labs.caido.io/hubs

## What's inside

- **Traffic Interception** — intercept and monitor HTTP and WebSocket traffic.
- **HTTP & WebSocket History** — a complete history of everything that passed through.
- **Replay** — manual testing and request modification (Caido's Repeater).
- **Automate** — automated attacks with payloads and placeholders (Caido's Intruder).
- **Findings** — an issue tracker to save interesting requests and potential vulnerabilities.
- **Match & Replace** — automatically modify requests and responses on the fly.
- **HTTPQL** — a query language to filter traffic.
- **Workflows and Plugins** — automate actions and extend Caido with community plugins.

## Caido vs Burp

They solve the same problem, so the concepts transfer between them. Burp is the industry standard and what most labs and write-ups assume; Caido is a lighter, modern alternative that is worth knowing — especially if your machine struggles with Burp.

Caido even has a dedicated "Migrating from Burp Suite" guide that maps each Burp tool to its Caido equivalent, so you can look up a Burp tool you already know and see what to use here. It's a fantastic resource:
https://docs.caido.io/burp-suite/core/overview

## Closing

If you are learning, try both. Start with whichever feels comfortable, and don't worry too much about the tool: understanding how HTTP works and how to manipulate requests is what matters.
