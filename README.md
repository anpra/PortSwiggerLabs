# PortSwigger Web Security Labs

Documentation and notes from completing the [PortSwigger Web Security Academy](https://portswigger.net/web-security) labs.

## Goal

This repository contains my walkthroughs, solutions, and notes for the PortSwigger Web Security labs, covering various web application vulnerabilities and attack techniques.

Each write-up follows the same structure: reconnaissance, exploitation, root cause, impact, remediation, and key takeaways.

## Labs covered

| Done | Section | Labs | Folder |
|---|---|---|---|
| [x] | File Upload Vulnerabilities | 7 | [File Upload Vulnerability](File%20Upload%20Vulnerability) |
| [x] | XML External Entity (XXE) | 6 | [XXE](XXE) |
| [x] | NoSQL Injection | 4 | [NOSQL](NOSQL) |
| [x] | Business Logic | 11 | [Business_Logic](Business_Logic) |
| [x] | Information Disclosure | 5 | [Information_Disclosure](Information_Disclosure) |

## Scripts

| Script | Purpose |
|---|---|
| `Information_Disclosure/scripts/find_debug_secret.py` | finds hidden debug links in HTML comments and extracts `SECRET_KEY` |
| `Information_Disclosure/scripts/find_backup_leaks.py` | follows `robots.txt` to backup files and extracts credentials |
| `Information_Disclosure/scripts/git_disclosure.py` | dumps an exposed `.git` and searches the history for secrets |
| `Business_Logic/scripts/content_discovery.py` | content discovery (free alternative to Burp Pro's "Discover content") |
| `Business_Logic/scripts/low_level_logic_overflow.py` | integer overflow in the cart total |
| `Business_Logic/scripts/infinite_money_gift_card.py` | gift card + coupon money loop |
| `Business_Logic/scripts/encryption_oracle_bypass.py` | cookie forgery via an encryption oracle |
| `File Upload Vulnerability/scritps/racecondition.py` | race condition in the file upload |

## Tools

- [Burp Suite](Tools/BurpSuite.md)
- [Caido](Tools/Caido.md)
- [Turbo Intruder](Tools/TurboIntruder.md)

## References

- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [Burp Suite Documentation](https://portswigger.net/burp/documentation)

## Disclaimer

This repository was created for educational purposes only. All testing was performed in authorized PortSwigger Web Security Academy laboratory environments. Never test systems without explicit authorization.
