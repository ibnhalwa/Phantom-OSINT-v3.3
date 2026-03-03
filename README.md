```
 ██████╗ ██╗  ██╗ █████╗ ███╗  ██╗████████╗ ██████╗ ███╗  ███╗
 ██╔══██╗██║  ██║██╔══██╗████╗ ██║╚══██╔══╝██╔═══██╗████╗████║
 ██████╔╝███████║███████║██╔██╗██║   ██║   ██║   ██║██╔████╔██║
 ██╔═══╝ ██╔══██║██╔══██║██║╚████║   ██║   ██║   ██║██║╚██╔╝██║
 ██║     ██║  ██║██║  ██║██║ ╚███║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
```

<div align="center">

**Open-Source OSINT Recon Framework — v3.3**

by [Ibnhalwa](https://github.com/Ibnhalwa) · [Discord](https://discord.gg/9EHyxS8vus)

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## About

**Phantom** is an interactive terminal-based OSINT framework built for reconnaissance and open-source intelligence gathering on public targets. It features a full keyboard-navigable TUI (Terminal UI), runs entirely in Python, and works natively on both Windows and Linux — no `curses` required.

> **For legal use only.** This tool is intended for educational purposes, cybersecurity research, and investigation of publicly available data. Always comply with applicable laws (GDPR, CFAA, etc.) and never use this tool against systems or individuals without proper authorization.

---

## Features

| Module | Description |
|--------|-------------|
| **IP / GeoIP Recon** | Geolocation, reverse DNS, open ports via Shodan, CVE lookup |
| **Domain Recon** | Full DNS records, WHOIS, subdomain enum, SSL cert, SecurityTrails, URLScan |
| **Email Analysis** | Format validation, MX records, SMTP probe, breach check via LeakCheck.io |
| **Phone Analysis** | Carrier & country info (AbstractAPI), breach check, social media links |
| **Username Hunt** | Checks 25 platforms: GitHub, Twitter, Instagram, TikTok, Reddit and more |
| **Person Search** | Username permutations, Google dorks, direct search links |
| **Database Search** | Simple & advanced search (name, postal code, date of birth...) |

---

## Installation

### Requirements

- Python 3.8+
- pip

### Run

```bash
git clone https://github.com/Ibnhalwa/phantom.git
cd phantom
pip install -r requirements.txt
python phantom.py
```

Dependencies are installed automatically on first launch:
- `colorama` — cross-platform terminal colors
- `readchar` — keyboard input handling
- `dnspython` — DNS resolution without system dependencies
- `python-whois` — WHOIS lookups without external binaries

---

## API Keys Setup

API keys are optional but unlock significantly more data. Keys are stored locally in `~/.phantom_config.json`.

```bash
python phantom.py setkey ipinfo_token       YOUR_KEY
python phantom.py setkey shodan_key         YOUR_KEY
python phantom.py setkey leakcheck_key      YOUR_KEY
python phantom.py setkey abstractapi_key    YOUR_KEY
python phantom.py setkey securitytrails_key YOUR_KEY
python phantom.py setkey urlscan_key        YOUR_KEY
```

| Service | Used For | Free Tier | Link |
|---------|----------|-----------|------|
| **ipinfo.io** | GeoIP, ASN, organization | 50,000 req/month | [ipinfo.io/signup](https://ipinfo.io/signup) |
| **Shodan** | Open ports, CVEs, banners | Free tier available | [account.shodan.io](https://account.shodan.io/register) |
| **LeakCheck.io** | Email & phone breach lookup | Public API — no key needed | [leakcheck.io/register](https://leakcheck.io/register) |
| **AbstractAPI** | Carrier, country, line type | 1,000 req/month free | [abstractapi.com](https://app.abstractapi.com/api/phone-validation) |
| **SecurityTrails** | Subdomains, DNS & WHOIS history | 50 req/month free | [securitytrails.com](https://securitytrails.com/app/signup) |
| **URLScan.io** | Screenshots, tech stack, requests | Free | [urlscan.io/user/signup](https://urlscan.io/user/signup) |

---

## Navigation

| Key | Action |
|-----|--------|
| `↑` / `↓` or `j` / `k` | Navigate menu |
| `ENTER` | Select |
| `Q` | Quit / back to menu |
| `ESC` or `Ctrl+C` | Cancel / back to menu |

---

## Compatibility

| OS | Status |
|----|--------|
| Windows 10 / 11 | ✅ Tested |
| Linux (Debian/Ubuntu) | ✅ Tested |
| macOS | ✅ Should work |

> **Windows users:** No `curses` needed. Phantom uses `colorama` + `readchar` which work natively on Windows terminals.

---

## Project Structure

```
phantom/
├── phantom.py      # Everything in a single file
└── README.md
```

---

## Roadmap

- [x] IP / GeoIP Recon
- [x] Domain Recon (DNS, WHOIS, SSL, SecurityTrails, URLScan)
- [x] Email Analysis (MX, SMTP, LeakCheck)
- [x] Phone Analysis (AbstractAPI, LeakCheck, social media)
- [x] Username Hunt (25 platforms)
- [x] Person Search
- [x] Database Search (simple + advanced)
- [ ] Database Search — additional modules (next update)
- [ ] Export results to JSON / TXT
- [ ] Multi-target scanning
- [ ] Silent mode (no TUI)

---

## Disclaimer

Phantom is provided **as-is** for educational purposes only. The author takes no responsibility for any illegal or malicious use of this tool. Use it responsibly, ethically, and within the bounds of the law.

---

<div align="center">

Made with ❤️ by **Ibnhalwa** · [discord.gg/9EHyxS8vus](https://discord.gg/9EHyxS8vus)

</div>
