#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════╗
║   PHANTOM  //  OSINT RECON FRAMEWORK             ║
║   v3.3  —  Windows & Linux compatible            ║
║   by Ibnhalwa  ▸  discord.gg/9EHyxS8vus          ║
╚══════════════════════════════════════════════════╝
Usage:
  python phantom.py               → Interactive menu
  python phantom.py setkey KEY V  → Save an API key
"""

import sys, os, time, socket, json, re, threading, subprocess
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote_plus
import ipaddress

# ──────────────────────────────────────────────────────────────────────────────
#  AUTO-INSTALL dependencies
# ──────────────────────────────────────────────────────────────────────────────
def _ensure(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

_ensure("colorama")
_ensure("readchar")
_ensure("dnspython", "dns")
_ensure("python-whois", "whois")

import colorama
from colorama import Fore, Back, Style
import readchar
import dns.resolver
import dns.reversename
import dns.exception

colorama.init()

# ──────────────────────────────────────────────────────────────────────────────
#  DNS HELPER  (replaces dig — pure Python, works on Windows)
# ──────────────────────────────────────────────────────────────────────────────
def dns_query(name, rtype, timeout=5):
    """Return list of string records, or empty list on failure."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        answers = resolver.resolve(name, rtype)
        return [str(r) for r in answers]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
            dns.resolver.NoNameservers, dns.exception.Timeout,
            Exception):
        return []

# ──────────────────────────────────────────────────────────────────────────────
#  COLORS
# ──────────────────────────────────────────────────────────────────────────────
R  = Fore.RED    + Style.BRIGHT
V  = Fore.MAGENTA+ Style.BRIGHT
C  = Fore.CYAN   + Style.BRIGHT
G  = Fore.GREEN  + Style.BRIGHT
Y  = Fore.YELLOW + Style.BRIGHT
D  = Style.DIM   + Fore.WHITE
W  = Fore.WHITE  + Style.BRIGHT
RS = Style.RESET_ALL

def red(s):    return f"{R}{s}{RS}"
def vio(s):    return f"{V}{s}{RS}"
def cyn(s):    return f"{C}{s}{RS}"
def grn(s):    return f"{G}{s}{RS}"
def yel(s):    return f"{Y}{s}{RS}"
def dim(s):    return f"{D}{s}{RS}"
def bld(s):    return f"{Style.BRIGHT}{s}{RS}"

def clrscr():
    os.system("cls" if os.name == "nt" else "clear")

def getch():
    """Cross-platform single keypress — returns readchar key."""
    return readchar.readkey()

def hide_cursor():
    if os.name == "nt":
        import ctypes
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_int), ("bVisible", ctypes.c_int)]
        ci = CONSOLE_CURSOR_INFO(1, 0)
        h = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.SetConsoleCursorInfo(h, ctypes.byref(ci))
    else:
        sys.stdout.write("\033[?25l"); sys.stdout.flush()

def show_cursor():
    if os.name == "nt":
        import ctypes
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_int), ("bVisible", ctypes.c_int)]
        ci = CONSOLE_CURSOR_INFO(1, 1)
        h = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.SetConsoleCursorInfo(h, ctypes.byref(ci))
    else:
        sys.stdout.write("\033[?25h"); sys.stdout.flush()

def get_terminal_size():
    try:
        s = os.get_terminal_size()
        return s.columns, s.lines
    except Exception:
        return 100, 30

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.expanduser("~/.phantom_config.json")

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def save_cfg(c):
    with open(CONFIG_FILE, "w") as f: json.dump(c, f, indent=2)

CFG = load_cfg()

# ──────────────────────────────────────────────────────────────────────────────
#  UI PRIMITIVES
# ──────────────────────────────────────────────────────────────────────────────
BANNER = [
    r" ██████╗ ██╗  ██╗ █████╗ ███╗  ██╗████████╗ ██████╗ ███╗  ███╗",
    r" ██╔══██╗██║  ██║██╔══██╗████╗ ██║╚══██╔══╝██╔═══██╗████╗████║",
    r" ██████╔╝███████║███████║██╔██╗██║   ██║   ██║   ██║██╔████╔██║",
    r" ██╔═══╝ ██╔══██║██╔══██║██║╚████║   ██║   ██║   ██║██║╚██╔╝██║",
    r" ██║     ██║  ██║██║  ██║██║ ╚███║   ██║   ╚██████╔╝██║ ╚═╝ ██║",
    r" ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝",
]

def print_banner():
    for i, line in enumerate(BANNER):
        color = R if i % 2 == 0 else V
        print(f"  {color}{line}{RS}")

def hline(width=None, color=V):
    w = width or get_terminal_size()[0] - 4
    print(f"  {color}{'─' * w}{RS}")

def section(title):
    w = get_terminal_size()[0] - 4
    pad = (w - len(title) - 2) // 2
    print(f"\n  {V}{'─'*pad}{RS} {R}{Style.BRIGHT}{title}{RS} {V}{'─'*pad}{RS}\n")

TAG_COLORS = {
    "INFO": C, "HIT!": R, "OK  ": G, "WARN": Y,
    "ERR!": R, "DATA": V, "MISS": D, "FETC": V,
    "DONE": G, "USER": V, "DORK": C, "LINK": G,
    "MAIL": V, "PORT": G, "SSL ": G, "SAN ": D,
    "SUB!": R, "WHOI": V, "BREA": R, " !! ": Y,
    "CVE!": R, "MX  ": G, "SMTP": G, "RESV": C,
    "A   ": G, "AAAA": G, "NS  ": G, "TXT ": G,
    "SOA ": G, "MX  ": G, "CNAM": G,
}

def log(tag, msg):
    tc = TAG_COLORS.get(tag[:4].upper(), W)
    ts = dim(datetime.now().strftime("%H:%M:%S"))
    t  = f"{tc}[{tag[:4].upper().center(4)}]{RS}"
    print(f"  {ts} {t} {W}{msg}{RS}")

def spinner_line(msg, done=False):
    frames = ["◐ ","◓ ","◑ ","◒ "]
    frame  = "● " if done else frames[int(time.time()*4) % 4]
    color  = G if done else Y
    print(f"\r  {color}{frame}{msg}{RS}", end="", flush=True)

# ──────────────────────────────────────────────────────────────────────────────
#  HTTP HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def http_json(url, headers=None, timeout=8):
    h = {"User-Agent": "Mozilla/5.0"}
    if headers: h.update(headers)
    try:
        with urlopen(Request(url, headers=h), timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def http_code(url, timeout=6):
    try:
        with urlopen(Request(url, headers={"User-Agent":"Mozilla/5.0"}), timeout=timeout) as r:
            return r.getcode()
    except HTTPError as e: return e.code
    except Exception:      return 0

# ──────────────────────────────────────────────────────────────────────────────
#  OSINT MODULES
# ──────────────────────────────────────────────────────────────────────────────
def module_ip(target):
    section("IP / GEOIP RECON")
    ip = target
    try: ipaddress.ip_address(target)
    except ValueError:
        try:
            ip = socket.gethostbyname(target)
            log("RESV", f"Resolved {cyn(target)} → {cyn(ip)}")
        except Exception:
            log("ERR!", f"Cannot resolve: {red(target)}"); return
    try:
        if ipaddress.ip_address(ip).is_private:
            log("WARN", f"{yel(ip)} is a {yel('private')} address")
    except Exception: pass

    token = CFG.get("ipinfo_token","")
    url   = f"https://ipinfo.io/{ip}/json" + (f"?token={token}" if token else "")
    log("FETC", f"Querying {dim('ipinfo.io')}...")
    data  = http_json(url)
    if data and "ip" in data:
        for k,v in [("IP",data.get("ip")),("Hostname",data.get("hostname")),
                    ("City",data.get("city")),("Region",data.get("region")),
                    ("Country",data.get("country")),("Location",data.get("loc")),
                    ("ASN/Org",data.get("org")),("Timezone",data.get("timezone"))]:
            if v: log("DATA", f"{dim(k.ljust(12))} {vio(v)}")
    else:
        log("WARN", "ipinfo.io returned no data — add a free token in Config")

    log("INFO", "Reverse DNS...")
    try:
        log("HIT!", f"PTR → {vio(socket.gethostbyaddr(ip)[0])}")
    except Exception:
        log("MISS", "No PTR record found")

    skey = CFG.get("shodan_key")
    if skey:
        log("FETC", "Querying Shodan...")
        sd = http_json(f"https://api.shodan.io/shodan/host/{ip}?key={skey}")
        if sd and "ports" in sd:
            log("HIT!", f"Open ports: {red(', '.join(map(str, sd['ports'])))}")
            for item in sd.get("data",[])[:4]:
                log("PORT", f":{cyn(str(item.get('port','?')))}  {dim(str(item.get('data',''))[:55].replace(chr(10),' '))}")
            for cve in list(sd.get("vulns",{}))[:3]:
                log("CVE!", red(cve))
        else: log("MISS", "No Shodan data for this host")
    else:
        log("INFO", dim("Shodan skipped — add key in Config"))
    log("DONE", grn("IP recon complete ✓"))

def module_domain(target):
    target = re.sub(r'^https?://','',target).split('/')[0].strip()
    # Root domain (used for WHOIS, SecurityTrails, etc.)
    parts = target.split('.')
    root  = '.'.join(parts[-2:]) if len(parts) >= 2 else target

    section("DOMAIN RECON")
    log("INFO", f"Target : {red(target)}")
    log("INFO", f"Root   : {vio(root)}")

    # ── DNS Records ──────────────────────────────────────────────────────────
    section("DNS RECORDS")
    for rtype in ["A","AAAA","MX","NS","TXT","SOA"]:
        records = dns_query(target, rtype)
        if records:
            for rec in records[:3]:
                log(rtype.ljust(4), grn(rec))
        else:
            log(rtype.ljust(4), dim("no record"))

    # ── WHOIS (python-whois) ──────────────────────────────────────────────────
    section("WHOIS")
    try:
        import whois as pywhois
        w = pywhois.whois(root)
        fields = [
            ("Registrar",      w.registrar),
            ("Registrant",     getattr(w, 'registrant_name', None) or getattr(w, 'org', None)),
            ("Registrant Org", getattr(w, 'org', None)),
            ("Registrant Email", w.emails),
            ("Registrant Country", getattr(w, 'country', None)),
            ("Created",        w.creation_date),
            ("Expires",        w.expiration_date),
            ("Updated",        w.updated_date),
            ("Name servers",   w.name_servers),
            ("Status",         w.status),
        ]
        any_found = False
        for label, val in fields:
            if val:
                any_found = True
                if isinstance(val, list):
                    val = val[0] if len(val)==1 else ', '.join(str(x) for x in val[:3])
                log("WHOI", f"{dim(label.ljust(18))} {vio(str(val)[:70])}")
        if not any_found:
            log("MISS", dim("WHOIS returned no data (privacy protection active?)"))
    except Exception as e:
        log("WARN", yel(f"WHOIS: {str(e)[:60]}"))

    # ── SecurityTrails ────────────────────────────────────────────────────────
    st_key = CFG.get("securitytrails_key")
    section("SECURITYTRAILS")
    if st_key:
        headers = {"APIKEY": st_key, "User-Agent": "phantom-osint"}

        # General info
        log("FETC", "General domain info...")
        info = http_json(f"https://api.securitytrails.com/v1/domain/{root}", headers=headers)
        if info:
            apex = info.get("apex_domain","")
            if apex: log("ST  ", f"Apex domain     {vio(apex)}")

            # Registrant from SecurityTrails
            whois_st = info.get("whois", {})
            for k, label in [("registrant","Registrant"), ("registrar","Registrar"),
                              ("registrantOrg","Registrant Org"), ("registrantEmail","Registrant Email"),
                              ("createdDate","Created"), ("expiresDate","Expires")]:
                v = whois_st.get(k)
                if v: log("ST  ", f"{dim(label.ljust(18))} {vio(str(v)[:70])}")

            # Current DNS from ST
            dns_st = info.get("current_dns", {})
            for rtype, rdata in dns_st.items():
                vals = rdata.get("values", [])[:3]
                for entry in vals:
                    ip   = entry.get("ip") or entry.get("value","")
                    org  = entry.get("ip_organization","")
                    line = f"{ip}" + (f"  {dim('('+org+')')}" if org else "")
                    log(rtype.upper().ljust(4), grn(line))
        else:
            log("WARN", yel("SecurityTrails: no data (check API key)"))

        # Subdomains from SecurityTrails
        log("FETC", "Subdomain list from SecurityTrails...")
        subs = http_json(f"https://api.securitytrails.com/v1/domain/{root}/subdomains?children_only=false&include_inactive=false", headers=headers)
        if subs and subs.get("subdomains"):
            sub_list = subs["subdomains"]
            log("HIT!", red(f"{len(sub_list)} subdomains found in SecurityTrails database!"))
            for s in sub_list[:20]:
                full = f"{s}.{root}"
                try:
                    ip = socket.gethostbyname(full)
                    log("SUB!", f"{vio(full.ljust(40))} {cyn(ip)}")
                except Exception:
                    log("SUB ", f"{dim(full)}")
            if len(sub_list) > 20:
                log("INFO", dim(f"... and {len(sub_list)-20} more subdomains"))
        else:
            log("MISS", dim("No subdomains in SecurityTrails"))

        # Historical WHOIS
        log("FETC", "Historical WHOIS...")
        hist = http_json(f"https://api.securitytrails.com/v1/history/{root}/whois?page=1", headers=headers)
        if hist and hist.get("result"):
            records_h = hist["result"].get("items", [])
            if records_h:
                log("HIT!", red(f"{len(records_h)} historical WHOIS records found!"))
                for item in records_h[:5]:
                    date = item.get("date","?")
                    contact = item.get("registrant_contact",{})
                    name  = contact.get("name","?")
                    email = contact.get("email","")
                    org   = contact.get("organization","")
                    line  = f"{dim(date)}  {vio(name)}"
                    if org:   line += f"  {dim(org)}"
                    if email: line += f"  {cyn(email)}"
                    log("HIST", line)
            else:
                log("MISS", dim("No historical WHOIS records"))

        # Historical DNS (A records)
        log("FETC", "Historical DNS (A records)...")
        hdns = http_json(f"https://api.securitytrails.com/v1/history/{root}/dns/a", headers=headers)
        if hdns and hdns.get("records"):
            log("HIT!", red(f"Historical IPs found:"))
            for rec in hdns["records"][:6]:
                first = rec.get("first_seen","?")
                last  = rec.get("last_seen","?")
                for v in rec.get("values",[])[:2]:
                    ip = v.get("ip","?")
                    log("HDNS", f"{cyn(ip.ljust(18))} {dim(first)} → {dim(last)}")
        else:
            log("MISS", dim("No historical DNS data"))

    else:
        log("INFO", dim("SecurityTrails key not set"))
        log("INFO", dim("Free key (50 req/month): securitytrails.com/app/signup"))
        log("INFO", dim("python phantom.py setkey securitytrails_key TACLÉ"))

    # ── URLScan.io ────────────────────────────────────────────────────────────
    section("URLSCAN.IO")
    urlscan_key = CFG.get("urlscan_key")

    def _urlscan_submit(url_target):
        import json as _j
        body = _j.dumps({"url": f"https://{url_target}", "visibility": "public"}).encode()
        req  = Request("https://urlscan.io/api/v1/scan/", data=body,
                       headers={"API-Key": urlscan_key,
                                "Content-Type": "application/json",
                                "User-Agent": "phantom-osint"})
        try:
            with urlopen(req, timeout=10) as resp:
                sr = _j.loads(resp.read().decode())
            return sr.get("uuid"), sr.get("message","")
        except HTTPError as e:
            msg = e.read().decode(errors="ignore")[:80]
            log("WARN", yel(f"URLScan HTTP {e.code}: {msg}"))
            return None, ""
        except Exception as e:
            log("WARN", yel(f"URLScan: {str(e)[:60]}"))
            return None, ""

    # 1. Search existing scans (no key needed)
    log("FETC", f"Recherche de scans existants pour {root}...")
    search = http_json(
        f"https://urlscan.io/api/v1/search/?q=domain:{root}&size=5",
        headers={"User-Agent": "phantom-osint"}
    )
    if search and search.get("results"):
        results = search["results"]
        log("HIT!", red(f"{len(results)} scan(s) existant(s) trouvé(s)!"))
        for r in results[:3]:
            page      = r.get("page", {})
            task      = r.get("task", {})
            scan_time = task.get("time","?")[:10]
            url_s     = page.get("url","?")[:65]
            ip        = page.get("ip","")
            server    = page.get("server","")
            country   = page.get("country","")
            asn       = page.get("asn","")
            asnname   = page.get("asnname","")
            uuid_s    = task.get("uuid","")
            log("SCAN", f"{dim(scan_time)}  {vio(url_s)}")
            if ip:     log("  IP ", f"{cyn(ip)}  {dim(country)}  {dim(asn)} {dim(asnname)}")
            if server: log("  SRV", vio(server))
            dom_list  = r.get("lists", {})
            ips_found = dom_list.get("ips", [])[:4]
            if ips_found: log("  IPs", dim(", ".join(ips_found)))
            if uuid_s:    log("  RPT", cyn(f"https://urlscan.io/result/{uuid_s}/"))
            print()
    else:
        log("MISS", dim(f"Aucun scan existant pour {root}"))

    # 2. Submit fresh scan — TOUJOURS si la clé est définie
    if urlscan_key:
        log("FETC", f"Soumission d'un nouveau scan → https://{target}")
        uuid_new, msg = _urlscan_submit(target)
        if uuid_new:
            log("OK  ", grn("Scan soumis avec succès !"))
            log("RPT ", cyn(f"https://urlscan.io/result/{uuid_new}/"))
            log("INFO", dim("Résultats dans ~30s : screenshot, technologies, requêtes, cookies, scripts..."))
        elif not uuid_new and not msg:
            log("MISS", dim("Scan non soumis (réponse vide)"))
        # Si le target était un sous-domaine, scanner aussi le root
        if target != root:
            log("FETC", f"Scan du domaine racine → https://{root}")
            uuid_root, _ = _urlscan_submit(root)
            if uuid_root:
                log("RPT ", cyn(f"https://urlscan.io/result/{uuid_root}/"))
    else:
        log("INFO", dim("Ajoute une clé URLScan pour soumettre des scans"))
        log("INFO", dim("Gratuit : urlscan.io/user/signup"))
        log("INFO", dim("python phantom.py setkey urlscan_key TACLÉ"))

    # ── Subdomain enum (fallback wordlist si pas SecurityTrails) ──────────────
    if not st_key:
        section("SUBDOMAIN ENUM (wordlist)")
        wordlist = ["www","mail","ftp","smtp","api","dev","staging","test","admin","portal",
                    "vpn","ns1","ns2","cdn","static","assets","blog","shop","app","mobile",
                    "secure","login","dashboard","support","docs","git","status","beta"]
        log("INFO", f"{len(wordlist)} probes...")
        found = 0
        for sub in wordlist:
            host = f"{sub}.{root}"
            try:
                ip = socket.gethostbyname(host)
                log("SUB!", f"{vio(host.ljust(40))} {cyn(ip)}")
                found += 1
            except Exception: pass
        log("OK  ", grn(f"{found} live subdomains found"))

    # ── SSL ───────────────────────────────────────────────────────────────────
    section("SSL CERTIFICATE")
    import ssl
    try:
        ctx  = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.socket(), server_hostname=target)
        conn.settimeout(5); conn.connect((target, 443))
        cert = conn.getpeercert(); conn.close()
        subj = dict(x[0] for x in cert.get('subject',[]))
        issu = dict(x[0] for x in cert.get('issuer',[]))
        log("SSL ", grn(f"CN       {subj.get('commonName','?')}"))
        log("SSL ", grn(f"Issuer   {issu.get('organizationName','?')}"))
        log("SSL ", cyn(f"Expires  {cert.get('notAfter','?')}"))
        sans = [x[1] for x in cert.get('subjectAltName',[]) if x[0]=='DNS']
        if sans: log("SAN ", dim(', '.join(sans[:8])))
    except Exception as e:
        log("MISS", dim(f"SSL: {str(e)[:65]}"))

    log("DONE", grn("Domain recon complete ✓"))

def module_email(target):
    section("EMAIL ANALYSIS")
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', target):
        log("ERR!", red("Invalid email format")); return
    log("OK  ", grn("Email format valid"))
    domain = target.split('@')[1]
    user   = target.split('@')[0]

    log("INFO", "Checking MX records...")
    mx_records = dns_query(domain, "MX")
    if mx_records:
        for rec in mx_records[:3]:
            log("MX  ", grn(rec))
        log("OK  ", grn(f"{domain} has mail servers → likely deliverable"))
    else:
        # fallback: try resolving mail.domain
        try:
            socket.gethostbyname(f"mail.{domain}")
            log("MX  ", grn(f"mail.{domain} resolves"))
        except Exception:
            log("WARN", yel(f"No MX records found for {domain}"))

    log("INFO", "SMTP probe port 25...")
    try:
        sock   = socket.create_connection((domain, 25), timeout=4)
        banner = sock.recv(1024).decode(errors='ignore').strip()
        log("SMTP", grn(f"Banner: {banner[:75]}")); sock.close()
    except: log("MISS", dim("Port 25 closed/filtered (normal for most hosts)"))

    lc = CFG.get("leakcheck_key")

    def _display_leakcheck(found, items, fields=None):
        log("BREA", red(f"{found} leak(s) trouvé(s) !"))
        if fields:
            log("DATA", vio(f"Données exposées : {', '.join(fields)}"))
        for item in (items or [])[:15]:
            if "source" in item:
                src   = item.get("source", {})
                name  = src.get("name", "?")
                date  = src.get("breach_date", "?")
                extra = ""
                for f in ["username","first_name","last_name","password","phone"]:
                    if item.get(f): extra += f"  {dim(f+':')+vio(str(item[f])[:20])}"
                log(" !! ", yel(f"{name:<28} {dim(date)}{extra}"))
            else:
                log(" !! ", yel(f"{item.get('name','?'):<28} {dim(item.get('date','?'))}"))

    def _leakcheck_public():
        """API publique — gratuite, pas de clé."""
        data = http_json(
            f"https://leakcheck.io/api/public?check={quote_plus(target)}",
            headers={"User-Agent": "phantom-osint"}
        )
        if data and data.get("success"):
            if data.get("found", 0) > 0:
                _display_leakcheck(data["found"], data.get("sources",[]), data.get("fields",[]))
            else:
                log("OK  ", grn("Aucun leak trouvé dans l'API publique ✓"))
            return True
        else:
            err = data.get("error","no response") if data else "connexion échouée"
            log("WARN", yel(f"API publique: {err}"))
            return False

    # Toujours commencer par l'API publique (gratuite, pas de plan requis)
    log("FETC", "Checking LeakCheck.io (API publique gratuite)...")
    _leakcheck_public()

    # Si clé dispo, tenter aussi l'API v2 (plan payant — donne plus de détails)
    if lc:
        log("FETC", "Tentative API v2 privée (plan Pro)...")
        import json as _j
        try:
            req = Request(
                f"https://leakcheck.io/api/v2/query/{quote_plus(target)}",
                headers={"X-API-Key": lc, "User-Agent": "phantom-osint",
                         "Accept": "application/json"}
            )
            with urlopen(req, timeout=8) as resp:
                data = _j.loads(resp.read().decode())
            if data.get("success") and data.get("found", 0) > 0:
                log("INFO", vio(f"API v2 — {data['found']} résultat(s) détaillé(s) :"))
                _display_leakcheck(data["found"], data.get("result",[]))
                quota = data.get("quota")
                if quota is not None:
                    log("INFO", dim(f"Quota restant : {quota} requêtes"))
            elif data.get("success"):
                log("OK  ", grn("API v2 : aucun résultat supplémentaire"))
            else:
                log("WARN", yel(f"API v2 : {data.get('error','?')}"))
        except HTTPError as e:
            body = e.read().decode(errors="ignore")[:100]
            if "paid" in body.lower() or e.code == 402:
                log("INFO", dim("API v2 nécessite un plan payant — résultats publics affichés ci-dessus"))
            else:
                log("WARN", yel(f"API v2 HTTP {e.code}: {body}"))
        except Exception as e:
            log("WARN", yel(f"API v2 : {str(e)[:60]}"))

    log("INFO", "Username pattern derivation:")
    for p in list(dict.fromkeys(filter(None, [
        user, user.split('.')[0] if '.' in user else None,
        user.replace('.',''), user.replace('_','')
    ]))):
        log("USER", vio(f"Possible username: {p}"))
    log("DONE", grn("Email recon complete ✓"))

PLATFORMS = {
    "GitHub":    "https://github.com/{}",
    "GitLab":    "https://gitlab.com/{}",
    "Twitter/X": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Reddit":    "https://www.reddit.com/user/{}",
    "TikTok":    "https://www.tiktok.com/@{}",
    "YouTube":   "https://www.youtube.com/@{}",
    "Twitch":    "https://www.twitch.tv/{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Medium":    "https://medium.com/@{}",
    "Dev.to":    "https://dev.to/{}",
    "HackerNews":"https://news.ycombinator.com/user?id={}",
    "Steam":     "https://steamcommunity.com/id/{}",
    "Patreon":   "https://www.patreon.com/{}",
    "Linktree":  "https://linktr.ee/{}",
    "Keybase":   "https://keybase.io/{}",
    "HackerOne": "https://hackerone.com/{}",
    "BugCrowd":  "https://bugcrowd.com/{}",
    "Replit":    "https://replit.com/@{}",
    "CodePen":   "https://codepen.io/{}",
    "Behance":   "https://www.behance.net/{}",
    "Dribbble":  "https://dribbble.com/{}",
    "Gravatar":  "https://en.gravatar.com/{}",
    "About.me":  "https://about.me/{}",
    "Tumblr":    "https://{}.tumblr.com",
}

def module_username(target):
    section("USERNAME HUNT")
    log("INFO", f"Checking {yel(str(len(PLATFORMS)))} platforms for {vio('@'+target)}")
    print()
    found = 0
    for platform, url_tpl in PLATFORMS.items():
        url  = url_tpl.format(target)
        code = http_code(url)
        if code == 200:
            log("HIT!", f"{grn(platform.ljust(16))} {cyn(url)}")
            found += 1
        elif code in (404, 410):
            log("MISS", dim(f"{platform.ljust(16)} not found"))
        else:
            log("????", yel(f"{platform.ljust(16)} inconclusive (HTTP {code})"))
        time.sleep(0.15)
    log("DONE", grn(f"Username scan complete — {found} profiles found ✓"))

def module_person(first, last):
    section("PERSON SEARCH")
    full = f"{first} {last}"
    log("INFO", f"Target: {red(full)}")
    log("WARN", yel("Ethical/legal use only — respect GDPR & privacy laws"))
    time.sleep(0.3)
    f, l = first.lower(), last.lower()

    log("INFO", "Username permutations:")
    for p in list(dict.fromkeys(filter(None,[
        f"{f}{l}", f"{f}.{l}", f"{f}_{l}", f"{f[0]}{l}",
        f"{f}{l[0]}", f"{f[0]}.{l}", f"{l}{f}", f"{f[:3]}{l[:3]}"
    ]))):
        log("USER", vio(p))

    log("INFO", "Google dork queries (copy & paste):")
    for d in [
        f'"{full}"', f'"{full}" site:linkedin.com',
        f'"{full}" site:twitter.com', f'"{full}" email',
        f'"{full}" filetype:pdf', f'"{full}" site:github.com',
        f'intext:"{full}" site:pastebin.com',
    ]: log("DORK", cyn(d))

    log("INFO", "Direct search links:")
    enc = quote_plus(full)
    for name, url in [
        ("Google",     f"https://www.google.com/search?q={enc}"),
        ("LinkedIn",   f"https://www.linkedin.com/search/results/people/?keywords={enc}"),
        ("Twitter/X",  f"https://twitter.com/search?q={enc}"),
        ("Pipl",       f"https://pipl.com/search/?q={enc}"),
        ("Spokeo",     f"https://www.spokeo.com/{first}-{last}"),
        ("TruePeople", f"https://www.truepeoplesearch.com/results?name={enc}"),
    ]: log("LINK", f"{grn(name.ljust(14))} {dim(url)}")

    log("INFO", "Email pattern guesses (replace company.com):")
    for pat in [f"{f}@company.com", f"{f}.{l}@company.com",
                f"{f[0]}{l}@company.com", f"{l}@company.com"]:
        log("MAIL", vio(pat))

    log("DONE", grn("Person recon complete ✓"))

def module_phone(target):
    section("PHONE NUMBER ANALYSIS")

    # ── Nettoyage / normalisation ────────────────────────────────────────────
    raw   = re.sub(r'[\s\-\.\(\)]', '', target)
    # Ajoute + si pas présent et commence par 00
    if raw.startswith('00'): raw = '+' + raw[2:]
    # Format international attendu
    e164  = raw if raw.startswith('+') else None
    local = re.sub(r'^\+\d{1,3}', '', raw) if e164 else raw

    log("INFO", f"Numéro brut    : {vio(target)}")
    log("INFO", f"Normalisé      : {vio(e164 or raw)}")

    if not re.match(r'^\+?[\d]{6,15}$', raw):
        log("ERR!", red("Format invalide — utilise le format international : +33612345678"))
        return

    # ── AbstractAPI (infos opérateur/pays/type) — gratuit 1000 req/mois ─────
    section("INFOS OPÉRATEUR")
    ab_key = CFG.get("abstractapi_key")
    if ab_key:
        log("FETC", "Interrogation AbstractAPI...")
        # Numéro en format E.164 sans + pour AbstractAPI
        num_for_api = re.sub(r"[^\d]", "", e164 or raw)
        try:
            import json as _abj
            url_ab = f"https://phonevalidation.abstractapi.com/v1/?api_key={ab_key}&phone={num_for_api}"
            req_ab = Request(url_ab, headers={"User-Agent": "phantom-osint"})
            with urlopen(req_ab, timeout=12) as resp_ab:
                data = _abj.loads(resp_ab.read().decode())
        except HTTPError as e_ab:
            body_ab = e_ab.read().decode(errors="ignore")[:120]
            log("WARN", yel(f"AbstractAPI HTTP {e_ab.code}: {body_ab}"))
            data = None
        except Exception as e_ab:
            log("WARN", yel(f"AbstractAPI: {str(e_ab)[:80]}"))
            data = None

        if data:
            valid   = data.get("valid", False)
            country = data.get("country", {})
            carrier = data.get("carrier", "")
            ltype   = data.get("type", "")
            intl    = data.get("format", {}).get("international","")
            local_f = data.get("format", {}).get("local","")

            log("OK  " if valid else "WARN",
                grn("Numéro valide ✓") if valid else yel("Numéro invalide ou inactif"))
            if intl:    log("DATA", f"{dim('Format intl  ')} {vio(intl)}")
            if local_f: log("DATA", f"{dim('Format local ')} {vio(local_f)}")
            if country:
                log("DATA", f"{dim('Pays         ')} {vio(country.get('name','?'))} ({cyn(country.get('code','?'))})")
            if carrier: log("DATA", f"{dim('Opérateur    ')} {vio(carrier)}")
            if ltype:
                type_color = R if ltype in ('mobile','cellular') else C
                log("DATA", f"{dim('Type         ')} {type_color}{ltype}{RS}")
    else:
        log("INFO", dim("AbstractAPI non configuré — opérateur/pays/type non disponibles"))
        log("INFO", dim("Gratuit 1000 req/mois : app.abstractapi.com/api/phone-validation"))
        log("INFO", dim("python phantom.py setkey abstractapi_key TACLÉ"))

        # Fallback : détection manuelle du préfixe pays
        log("INFO", "Détection du pays par préfixe...")
        prefixes = {
            "+33":"France 🇫🇷", "+32":"Belgique 🇧🇪", "+41":"Suisse 🇨🇭",
            "+1":"USA/Canada 🇺🇸", "+44":"UK 🇬🇧", "+49":"Allemagne 🇩🇪",
            "+34":"Espagne 🇪🇸", "+39":"Italie 🇮🇹", "+31":"Pays-Bas 🇳🇱",
            "+212":"Maroc 🇲🇦", "+213":"Algérie 🇩🇿", "+216":"Tunisie 🇹🇳",
            "+221":"Sénégal 🇸🇳", "+225":"Côte d'Ivoire 🇨🇮",
            "+7":"Russie 🇷🇺", "+86":"Chine 🇨🇳", "+81":"Japon 🇯🇵",
            "+82":"Corée du Sud 🇰🇷", "+55":"Brésil 🇧🇷", "+52":"Mexique 🇲🇽",
        }
        if e164:
            found_prefix = False
            for prefix, country in sorted(prefixes.items(), key=lambda x: -len(x[0])):
                if e164.startswith(prefix):
                    log("DATA", f"{dim('Pays estimé  ')} {vio(country)}")
                    log("DATA", f"{dim('Préfixe      ')} {cyn(prefix)}")
                    found_prefix = True
                    break
            if not found_prefix:
                log("MISS", dim("Préfixe pays non reconnu"))
        else:
            log("WARN", yel("Ajoute le préfixe international (+33...) pour la détection pays"))

    # ── LeakCheck — vérif breach ─────────────────────────────────────────────
    section("LEAK CHECK")
    log("FETC", "Vérification dans les bases de leaks (API publique)...")
    # LeakCheck ne reconnait pas le + — on envoie les chiffres uniquement
    lc_phone = re.sub(r"[^\d]", "", e164 or raw)
    pub = http_json(
        f"https://leakcheck.io/api/public?check={quote_plus(lc_phone)}",
        headers={"User-Agent": "phantom-osint"}
    )
    if pub and pub.get("success"):
        if pub.get("found", 0) > 0:
            log("BREA", red(f"{pub['found']} leak(s) trouvé(s) !"))
            fields = pub.get("fields", [])
            if fields: log("DATA", vio(f"Données exposées : {', '.join(fields)}"))
            for s in pub.get("sources", [])[:10]:
                log(" !! ", yel(f"{s.get('name','?'):<28} {dim(s.get('date','?'))}"))
        else:
            log("OK  ", grn("Numéro non trouvé dans les leaks connus ✓"))
    else:
        err = pub.get("error","no response") if pub else "connexion échouée"
        log("WARN", yel(f"LeakCheck: {err}"))

    # ── Réseaux sociaux ───────────────────────────────────────────────────────
    section("RECHERCHE RÉSEAUX SOCIAUX")
    num_clean = re.sub(r'[^\d]', '', raw)  # chiffres uniquement
    num_plus  = e164 or raw
    enc_plus  = quote_plus(num_plus)
    enc_clean = quote_plus(num_clean)

    log("INFO", "Liens de recherche par numéro :")
    social_links = [
        ("WhatsApp",      f"https://wa.me/{num_clean}"),
        ("Telegram",      f"https://t.me/{num_plus}"),
        ("Google",        f"https://www.google.com/search?q=%22{enc_plus}%22"),
        ("Google (local)",f"https://www.google.com/search?q=%22{enc_clean}%22"),
        ("Twitter/X",     f"https://twitter.com/search?q=%22{enc_plus}%22"),
        ("Facebook",      f"https://www.facebook.com/search/top?q={enc_plus}"),
        ("Truecaller",    f"https://www.truecaller.com/search/fr/{num_clean}"),
        ("NumLookup",     f"https://www.numlookup.com/+{num_clean}"),
        ("Sync.me",       f"https://sync.me/search/?number={num_clean}"),
        ("Pages Blanches",f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={enc_plus}"),
        ("Spokeo",        f"https://www.spokeo.com/phone/{num_clean}"),
        ("AnyWho",        f"https://www.anywho.com/reverse-lookup/{num_clean}"),
    ]
    for name, url in social_links:
        log("LINK", f"{grn(name.ljust(18))} {dim(url)}")

    print()
    log("INFO", "Google Dorks :")
    for d in [
        f'"{num_plus}"',
        f'"{num_clean}"',
        f'"{num_plus}" site:facebook.com',
        f'"{num_plus}" site:twitter.com',
        f'"{num_clean}" site:linkedin.com',
        f'intext:"{num_plus}" site:pastebin.com',
    ]:
        log("DORK", cyn(d))

    log("DONE", grn("Phone analysis complete ✓"))



def show_config():
    section("CONFIGURATION")
    items = [
        ("ipinfo_token",        "ipinfo.io Token",          "50k req/month free",          "https://ipinfo.io/signup"),
        ("shodan_key",          "Shodan API Key",            "Free tier available",          "https://account.shodan.io/register"),
        ("leakcheck_key",       "LeakCheck.io API Key",      "Optionnel — public API dispo", "https://leakcheck.io/register"),
        ("abstractapi_key",     "AbstractAPI Phone Key",     "1000 req/mois gratuit",        "https://app.abstractapi.com/api/phone-validation"),
        ("securitytrails_key",  "SecurityTrails API Key",    "50 req/month free",            "https://securitytrails.com/app/signup"),
        ("urlscan_key",         "URLScan.io API Key",        "Gratuit",                      "https://urlscan.io/user/signup"),
    ]
    for key, label, tier, url in items:
        val    = CFG.get(key, "")
        masked = ("*" * 8 + val[-4:]) if len(val) > 4 else (val or dim("[ not set ]"))
        status = grn("✓ SET") if val else red("✗ MISSING")
        print(f"  {V}{label}{RS}")
        print(f"    Status  : {status}  {masked}")
        print(f"    Plan    : {dim(tier)}")
        print(f"    Register: {cyn(url)}")
        print()
    print(f"  {Y}Commande pour ajouter une cle :{RS}")
    for k in ["ipinfo_token","shodan_key","leakcheck_key","abstractapi_key","securitytrails_key","urlscan_key"]:
        print(f"  {dim(f'python phantom.py setkey {k:<22} YOUR_KEY')}")
    print()

# ──────────────────────────────────────────────────────────────────────────────
#  DATABASE SEARCH MODULE
# ──────────────────────────────────────────────────────────────────────────────

DB_SUBMENU = [
    ("◈  Recherche Simple",    "simple"),
    ("◉  Recherche Avancée",   "advanced"),
    ("◫  Coming Soon  ···",    "soon1"),
    ("◫  Coming Soon  ···",    "soon2"),
    ("←  Retour au menu",      "back"),
]

def db_banner():
    clrscr()
    print()
    print_banner()
    print(f"\n  {D}{'─'*62}{RS}")
    print(f"  {V}◫  DATABASE SEARCH{RS}  {D}—  Recherche dans les sources publiques{RS}")
    print(f"  {D}{'─'*62}{RS}\n")

def draw_db_menu(sel):
    db_banner()
    print(f"  {D}Sélectionne un type de recherche :{RS}\n")
    for i, (label, action) in enumerate(DB_SUBMENU):
        is_soon = action.startswith("soon")
        if is_soon:
            print(f"  {D}     {label}   {Style.DIM}[prochaine mise à jour]{RS}")
        elif i == sel:
            print(f"  {Back.MAGENTA}{Fore.BLACK}{Style.BRIGHT}  ▶  {label.ljust(30)}{RS}")
        else:
            print(f"  {D}     {label}{RS}")
        print()
    hline()
    print(f"\n  {D}↑↓ Navigate   ENTER Select   Q Retour{RS}")
    print(f"  {D}by {RS}{V}Ibnhalwa{RS}  {D}▸{RS}  {C}discord.gg/9EHyxS8vus{RS}\n")

def db_ask_field(prompt, optional=False):
    """Ask a single field. Returns empty string if skipped (optional)."""
    opt_label = f"  {D}(optionnel — appuie sur ENTER pour passer){RS}" if optional else ""
    if opt_label:
        print(opt_label)
    print(f"  {V}{prompt}{RS}")
    print(f"  {R}› {RS}", end="", flush=True)
    show_cursor()
    val = input().strip()
    hide_cursor()
    print()
    return val

def db_simple_search():
    """Simple search: first name + last name."""
    db_banner()
    section("RECHERCHE SIMPLE")
    print(f"  {D}Remplis les champs. Laisse vide si non connu.{RS}\n")

    first = db_ask_field("Prénom", optional=True)
    last  = db_ask_field("Nom",    optional=True)

    if not first and not last:
        print(f"  {Y}⚠  Au moins un champ requis.{RS}\n")
        input(f"  {D}ENTER pour continuer...{RS}")
        return

    db_banner()
    section("RÉSULTATS — RECHERCHE SIMPLE")

    query_parts = []
    if first: query_parts.append(first)
    if last:  query_parts.append(last)
    query = " ".join(query_parts)
    enc   = quote_plus(query)

    print(f"  {D}Requête :{RS} {red(query)}\n")

    log("INFO", f"Génération des permutations...")
    f = first.lower() if first else ""
    l = last.lower()  if last  else ""
    if f and l:
        perms = list(dict.fromkeys(filter(None, [
            f"{f}{l}", f"{f}.{l}", f"{f}_{l}", f"{f[0]}{l}",
            f"{f}{l[0]}", f"{f[0]}.{l}", f"{l}{f}", f"{f[:3]}{l[:3]}"
        ])))
        for p in perms:
            log("USER", vio(p))
        print()

    log("INFO", "Liens de recherche directs :")
    links = [
        ("Google",        f"https://www.google.com/search?q={enc}"),
        ("Bing",          f"https://www.bing.com/search?q={enc}"),
        ("LinkedIn",      f"https://www.linkedin.com/search/results/people/?keywords={enc}"),
        ("Twitter / X",   f"https://twitter.com/search?q={enc}&src=typed_query&f=user"),
        ("Facebook",      f"https://www.facebook.com/search/people/?q={enc}"),
        ("Instagram",     f"https://www.instagram.com/explore/search/keyword/?q={enc}"),
        ("TikTok",        f"https://www.tiktok.com/search/user?q={enc}"),
        ("Pipl",          f"https://pipl.com/search/?q={enc}"),
        ("Spokeo",        f"https://www.spokeo.com/{first}-{last}" if first and last else f"https://www.spokeo.com/search?q={enc}"),
        ("TruePeopleSearch", f"https://www.truepeoplesearch.com/results?name={enc}"),
        ("FastPeopleSearch", f"https://www.fastpeoplesearch.com/name/{(first+'-'+last).lower()}" if first and last else ""),
        ("WhitePages",    f"https://www.whitepages.com/name/{enc}"),
        ("Webmii",        f"https://webmii.com/people?n=%22{enc}%22"),
        ("Pastebin",      f"https://www.google.com/search?q=intext%3A%22{enc}%22+site%3Apastebin.com"),
    ]
    for name, url in links:
        if url:
            log("LINK", f"{grn(name.ljust(20))} {dim(url)}")

    print()
    log("INFO", "Google Dorks :")
    dorks = [
        f'"{query}"',
        f'"{query}" email OR contact',
        f'"{query}" filetype:pdf',
        f'"{query}" site:linkedin.com',
        f'"{query}" site:github.com',
        f'intext:"{query}" site:pastebin.com',
    ]
    if first and last:
        dorks.append(f'"{first}" "{last}" téléphone OR phone')
    for d in dorks:
        log("DORK", cyn(d))

    print()
    log("DONE", grn("Recherche simple terminée ✓"))

def db_advanced_search():
    """Advanced search: multiple optional fields."""
    db_banner()
    section("RECHERCHE AVANCÉE")
    print(f"  {D}Tous les champs sont optionnels. Appuie sur ENTER pour passer.{RS}\n")

    first    = db_ask_field("Prénom",          optional=True)
    last     = db_ask_field("Nom",             optional=True)
    dob      = db_ask_field("Date de naissance  (ex: 15/03/1995 ou 1995)", optional=True)
    postal   = db_ask_field("Code postal       (ex: 75001, 91000, 34000)", optional=True)
    year     = db_ask_field("Année de naissance (ex: 1990)",               optional=True)
    city     = db_ask_field("Ville             (ex: Paris, Lyon)",         optional=True)

    # Combine year from dob if not given
    if not year and dob:
        m = re.search(r'\b(19|20)\d{2}\b', dob)
        if m:
            year = m.group(0)

    filled = [v for v in [first, last, dob, postal, year, city] if v]
    if not filled:
        print(f"  {Y}⚠  Au moins un champ requis.{RS}\n")
        input(f"  {D}ENTER pour continuer...{RS}")
        return

    db_banner()
    section("RÉSULTATS — RECHERCHE AVANCÉE")

    # Build query strings
    name_query  = " ".join(filter(None, [first, last]))
    full_query  = " ".join(filter(None, [first, last, city, year]))
    enc_name    = quote_plus(name_query)  if name_query  else ""
    enc_full    = quote_plus(full_query)  if full_query  else ""

    # Summary
    print(f"  {D}Critères utilisés :{RS}")
    for label, val in [("Prénom", first), ("Nom", last), ("Naissance", dob or year),
                       ("Code postal", postal), ("Ville", city)]:
        if val:
            print(f"    {D}{label.ljust(14)}{RS} {vio(val)}")
    print()

    # ── Username permutations ──────────────────────────────────────────────────
    if first or last:
        log("INFO", "Permutations de pseudos :")
        f = first.lower() if first else "x"
        l = last.lower()  if last  else "x"
        perms = []
        if first and last:
            perms = list(dict.fromkeys([
                f"{f}{l}", f"{f}.{l}", f"{f}_{l}", f"{f[0]}{l}",
                f"{f}{l[0]}", f"{f[0]}.{l}", f"{l}{f}", f"{f[:3]}{l[:3]}",
            ]))
            if year:
                perms += [f"{f}{l}{year[-2:]}", f"{f}.{l}{year[-2:]}",
                          f"{f}{l}{year}"]
        for p in perms[:10]:
            log("USER", vio(p))
        print()

    # ── Email guesses ──────────────────────────────────────────────────────────
    if first and last:
        f, l = first.lower(), last.lower()
        log("INFO", "Patterns d'email probables (remplace company.com) :")
        pats = [f"{f}@company.com", f"{f}.{l}@company.com",
                f"{f[0]}{l}@company.com", f"{l}{f[0]}@company.com",
                f"{f}@gmail.com", f"{f}.{l}@gmail.com",
                f"{f}.{l}@hotmail.com", f"{f}{l}@yahoo.fr"]
        for p in pats:
            log("MAIL", vio(p))
        print()

    # ── Search links ──────────────────────────────────────────────────────────
    log("INFO", "Liens de recherche :")

    links = []
    if enc_name:
        links += [
            ("Google",        f"https://www.google.com/search?q={enc_full}"),
            ("Bing",          f"https://www.bing.com/search?q={enc_full}"),
            ("LinkedIn",      f"https://www.linkedin.com/search/results/people/?keywords={enc_name}"),
            ("Twitter / X",   f"https://twitter.com/search?q={enc_name}&src=typed_query&f=user"),
            ("Facebook",      f"https://www.facebook.com/search/people/?q={enc_name}"),
            ("Pipl",          f"https://pipl.com/search/?q={enc_full}"),
            ("Webmii",        f"https://webmii.com/people?n=%22{enc_name}%22"),
            ("TruePeopleSearch", f"https://www.truepeoplesearch.com/results?name={enc_name}" +
                                  (f"&citystatezip={quote_plus(postal)}" if postal else "")),
            ("WhitePages",    f"https://www.whitepages.com/name/{enc_name}" +
                               (f"/{quote_plus(city)}" if city else "")),
        ]
    if postal:
        links += [
            ("Annuaire 118",  f"https://www.118000.fr/search?who={enc_name}&where={quote_plus(postal)}"),
            ("PagesJaunes",   f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={enc_name}&ou={quote_plus(postal)}"),
        ]
    if city:
        links += [
            ("Pages Blanches", f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={enc_name}&ou={quote_plus(city)}"),
        ]
    for name, url in links:
        log("LINK", f"{grn(name.ljust(22))} {dim(url)}")
    print()

    # ── Advanced dorks ────────────────────────────────────────────────────────
    log("INFO", "Google Dorks avancés :")
    dorks = []
    if name_query:
        dorks.append(f'"{name_query}"')
        if city:     dorks.append(f'"{name_query}" "{city}"')
        if postal:   dorks.append(f'"{name_query}" "{postal}"')
        if year:     dorks.append(f'"{name_query}" "{year}"')
        if dob:      dorks.append(f'"{name_query}" "{dob}"')
        dorks.append(f'"{name_query}" email OR contact')
        dorks.append(f'"{name_query}" filetype:pdf')
        dorks.append(f'intext:"{name_query}" site:pastebin.com')
        if first and last:
            f2, l2 = first.lower(), last.lower()
            dorks.append(f'"{name_query}" site:linkedin.com')
            dorks.append(f'allintext:"{first}" "{last}" {postal if postal else ""}')
    for d in dorks:
        log("DORK", cyn(d.strip()))

    print()
    log("DONE", grn("Recherche avancée terminée ✓"))

def database_menu():
    """Database sub-menu loop."""
    sel = 0
    # Skip "soon" entries when navigating
    navigable = [i for i, (_, a) in enumerate(DB_SUBMENU) if not a.startswith("soon")]
    nav_idx   = 0

    while True:
        sel = navigable[nav_idx]
        draw_db_menu(sel)
        k = getch()

        if k in (readchar.key.UP, 'k', '\x1b[A'):
            nav_idx = (nav_idx - 1) % len(navigable)
        elif k in (readchar.key.DOWN, 'j', '\x1b[B'):
            nav_idx = (nav_idx + 1) % len(navigable)
        elif k in (readchar.key.ENTER, '\r', '\n', ' '):
            _, action = DB_SUBMENU[sel]
            if action == "back":
                return
            elif action == "simple":
                db_simple_search()
                print(f"\n  {D}Press ENTER to return...{RS}")
                show_cursor(); input(); hide_cursor()
            elif action == "advanced":
                db_advanced_search()
                print(f"\n  {D}Press ENTER to return...{RS}")
                show_cursor(); input(); hide_cursor()
        elif k in ('q', 'Q', '\x1b'):
            return

# ──────────────────────────────────────────────────────────────────────────────
#  INTERACTIVE MENU
# ──────────────────────────────────────────────────────────────────────────────
# ── Menu groups ──────────────────────────────────────────────────────────────
# Each entry: (display_label, action, group)
# Groups: "analysis" | "tools" | "system"
MENU = [
    ("[1] IP / GeoIP Recon",   "ip",       "analysis"),
    ("[2] Domain Recon",       "domain",   "analysis"),
    ("[3] Email Analysis",     "email",    "analysis"),
    ("[4] Phone Analysis",     "phone",    "analysis"),
    ("[5] Username Hunt",      "username", "tools"),
    ("[6] Person Search",      "person",   "tools"),
    ("[7] Database Search",    "database", "tools"),
    ("[8] Configuration",      "config",   "system"),
    ("[0] Exit",               "exit",     "system"),
]

def draw_menu(sel):
    clrscr()
    print()
    print()

    # ── Full ASCII banner ─────────────────────────────────────────────────────
    BL = [
        r" ██████╗ ██╗  ██╗ █████╗ ███╗  ██╗████████╗ ██████╗ ███╗  ███╗",
        r" ██╔══██╗██║  ██║██╔══██╗████╗ ██║╚══██╔══╝██╔═══██╗████╗████║",
        r" ██████╔╝███████║███████║██╔██╗██║   ██║   ██║   ██║██╔████╔██║",
        r" ██╔═══╝ ██╔══██║██╔══██║██║╚████║   ██║   ██║   ██║██║╚██╔╝██║",
        r" ██║     ██║  ██║██║  ██║██║ ╚███║   ██║   ╚██████╔╝██║ ╚═╝ ██║",
        r" ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝",
    ]
    for i, line in enumerate(BL):
        c = R if i % 2 == 0 else V
        print(f"  {c}{Style.BRIGHT}{line}{RS}")

    print(f"  {D}  OSINT RECON FRAMEWORK  v3.3{RS}  |  {R}by Ibnhalwa{RS}  |  {C}discord.gg/9EHyxS8vus{RS}")
    print(f"  {D}  Use responsibly and legally only{RS}")
    print()

    # ── Menu — fixed width columns, color OUTSIDE ljust ──────────────────────
    COL = 34   # visible chars per column

    analysis = [(i,l) for i,(l,a,g) in enumerate(MENU) if g=="analysis"]
    tools    = [(i,l) for i,(l,a,g) in enumerate(MENU) if g=="tools"]
    system   = [(i,l) for i,(l,a,g) in enumerate(MENU) if g=="system"]

    def render(idx, label, width=COL):
        """Render a menu item. ljust on plain text THEN add color."""
        padded = label.ljust(width)
        if idx == sel:
            return f"{Back.MAGENTA}{Fore.BLACK}{Style.BRIGHT} > {padded} {RS}"
        else:
            return f"{D}   {padded} {RS}"

    # Header row
    ah = f"{R}{Style.BRIGHT}{'ANALYSIS':-<{COL+4}}{RS}"
    th = f"{V}{Style.BRIGHT}{'TOOLS':-<{COL+4}}{RS}"
    print(f"  {ah}  {th}")

    max_rows = max(len(analysis), len(tools))
    for row in range(max_rows):
        l_str = render(*analysis[row]) if row < len(analysis) else " " * (COL + 4)
        r_str = render(*tools[row])    if row < len(tools)    else ""
        print(f"  {l_str}  {r_str}")

    print()
    print(f"  {R}{Style.BRIGHT}{'SYSTEM':-<{COL*2+8}}{RS}")
    # System items side by side
    sys_items = list(system)
    for i in range(0, len(sys_items), 2):
        l_str = render(*sys_items[i])
        r_str = render(*sys_items[i+1]) if i+1 < len(sys_items) else ""
        print(f"  {l_str}  {r_str}")

    # ── API keys status ───────────────────────────────────────────────────────
    print()
    ks = []
    key_map = [
        ("ipinfo_token",       "ipinfo"),
        ("shodan_key",         "shodan"),
        ("leakcheck_key",      "leakcheck"),
        ("abstractapi_key",    "abstractapi"),
        ("securitytrails_key", "sectrails"),
        ("urlscan_key",        "urlscan"),
    ]
    for cfg_key, label in key_map:
        if CFG.get(cfg_key):
            ks.append(grn(f"{label}[+]"))
        else:
            ks.append(dim(f"{label}[ ]"))
    hline()
    ts = dim(datetime.now().strftime("%H:%M:%S"))
    print(f"  {ts}   {'  '.join(ks)}")
    print(f"  {D}Up/Down Navigate   ENTER Select   Q Quit{RS}")

def ask_input(prompts, title):
    """Show an input form and return list of values."""
    clrscr()
    print()
    print_banner()
    section(title)
    values = []
    for prompt in prompts:
        print(f"  {V}{prompt}{RS}")
        print(f"  {R}› {RS}", end="", flush=True)
        show_cursor()
        val = input()
        hide_cursor()
        values.append(val.strip())
        print()
    return values

def run_with_header(title, fn, *args):
    clrscr()
    print()
    print_banner()
    print(f"\n  {D}{'─'*62}{RS}")
    print(f"  {R}{'▶':>3} {Style.BRIGHT}{title}{RS}")
    print(f"  {D}{'─'*62}{RS}\n")
    fn(*args)
    print()
    hline()
    print(f"\n  {D}Press ENTER to return to menu...{RS}")
    show_cursor()
    input()
    hide_cursor()

def interactive_menu():
    sel = 0
    hide_cursor()
    try:
        while True:
            draw_menu(sel)
            k = getch()

            if k in (readchar.key.UP,    'k', '\x1b[A'): sel = (sel-1) % len(MENU)
            elif k in (readchar.key.DOWN,'j', '\x1b[B'): sel = (sel+1) % len(MENU)
            elif k in (readchar.key.ENTER, '\r', '\n', ' '):
                _, action, _ = MENU[sel]

                if action == "exit":
                    clrscr(); show_cursor()
                    print(f"\n  {V}PHANTOM{RS} — {dim('Session ended.')}\n")
                    sys.exit(0)

                else:
                    # Wrap every action — crash = back to menu, never exits
                    try:
                        show_cursor()
                        if action == "config":
                            clrscr(); print(); print_banner()
                            show_config()
                            print(f"\n  {D}Appuie sur ENTER pour revenir...{RS}")
                            input()

                        elif action == "ip":
                            vals = ask_input(["Target IP or hostname"], "IP / GEOIP RECON")
                            run_with_header("IP / GEOIP RECON", module_ip, vals[0])

                        elif action == "domain":
                            vals = ask_input(["Domain name  (ex: google.com)"], "DOMAIN RECON")
                            run_with_header("DOMAIN RECON", module_domain, vals[0])

                        elif action == "email":
                            vals = ask_input(["Email address"], "EMAIL ANALYSIS")
                            run_with_header("EMAIL ANALYSIS", module_email, vals[0])

                        elif action == "phone":
                            vals = ask_input(["Phone number  (ex: +33612345678)"], "PHONE ANALYSIS")
                            run_with_header("PHONE ANALYSIS", module_phone, vals[0])

                        elif action == "username":
                            vals = ask_input(["Username / handle  (without @)"], "USERNAME HUNT")
                            run_with_header("USERNAME HUNT", module_username, vals[0])

                        elif action == "person":
                            vals = ask_input(["First name", "Last name"], "PERSON SEARCH")
                            run_with_header("PERSON SEARCH", module_person, vals[0], vals[1])

                        elif action == "database":
                            database_menu()

                    except (KeyboardInterrupt, EOFError):
                        pass  # ESC/Ctrl+C inside a module -> back to menu
                    except Exception as _err:
                        print(f"\n  {Y}Error: {_err}{RS}")
                        input(f"  {D}ENTER to return to menu...{RS}")
                    finally:
                        hide_cursor()

            elif k in ('q','Q'):
                clrscr(); show_cursor()
                print(f"\n  {V}PHANTOM{RS} — {dim('Session ended.')}\n")
                sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        show_cursor(); clrscr()
        print(f"\n  {V}PHANTOM{RS} — {dim('Interrupted.')}\n")
        sys.exit(0)

# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) >= 3 and args[0] == "setkey":
        CFG[args[1]] = args[2]
        save_cfg(CFG)
        print(f"{grn('✓')} Key {vio(args[1])} saved to {dim(CONFIG_FILE)}")

    elif len(args) >= 1 and args[0] in ("--help","-h","help"):
        print(__doc__)

    else:
        interactive_menu()
