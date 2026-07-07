#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B2B Prospect Finder - Google Search Lead Generation Tool

Searches Google via Serper.dev API, filters out large platforms,
visits prospect websites to extract contact info, outputs CSV.

Usage:
    python prospect_search.py "leather gloves importer" -o leads.csv
    python prospect_search.py "safety gloves buyer" --countries DE,FR,UK -o leads.csv
    python prospect_search.py "gloves importer" --no-visit -o domains_only.csv
"""

import sys
import os
import json
import re
import csv
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
import ssl

# ============================================================
# Playwright (optional, for JS-rendered sites)
# ============================================================
def _find_chromium():
    """Auto-detect Chromium executable across platforms."""
    # 1. Explicit env override
    env_path = os.environ.get("PLAYWRIGHT_CHROME_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Scan Playwright browser cache for any chromium version
    candidates = []
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.path.join(home, "AppData", "Local", "ms-playwright")
        candidates.append(os.path.join(base, "chromium-*", "chrome-win", "chrome.exe"))
        candidates.append(os.path.join(base, "chromium-*", "chrome-win64", "chrome.exe"))
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Caches", "ms-playwright")
        candidates.append(os.path.join(base, "chromium-*", "chrome-mac", "Chromium.app",
                                       "Contents", "MacOS", "Chromium"))
    else:  # Linux
        base = os.path.join(home, ".cache", "ms-playwright")
        candidates.append(os.path.join(base, "chromium-*", "chrome-linux", "chrome"))

    import glob
    for pattern in candidates:
        matches = sorted(glob.glob(pattern), reverse=True)
        if matches:
            return matches[0]
    return None  # Let Playwright auto-resolve


CHROME_PATH = _find_chromium()
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

# ============================================================
# Domain Blocklist
# ============================================================

BLOCKLIST = {
    # B2B Marketplaces
    "alibaba.com", "made-in-china.com", "globalsources.com", "tradekey.com",
    "dhgate.com", "ec21.com", "ecplaza.net", "exportersindia.com",
    "indiamart.com", "tradeindia.com", "go4worldbusiness.com",
    "fibre2fashion.com", "busytrade.com", "chinabrands.com",
    "eworldtrade.com", "hktdc.com", "1688.com",
    "volza.com", "tradeimex.in", "seair.co.in", "usimportdata.com",
    # E-commerce
    "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.it",
    "amazon.es", "amazon.co.jp", "amazon.in", "amazon.ca", "amazon.com.au",
    "amazon.com.mx", "ebay.com", "ebay.co.uk", "ebay.de", "etsy.com",
    "walmart.com", "target.com", "bestbuy.com", "homedepot.com",
    "lowes.com", "wayfair.com", "shopify.com", "aliexpress.com", "wish.com",
    "shopee.com", "lazada.com", "flipkart.com", "temu.com", "shein.com",
    "overstock.com", "costco.com", "newegg.com",
    # Social Media
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "tiktok.com", "reddit.com", "pinterest.com", "youtube.com", "tumblr.com",
    "snapchat.com", "whatsapp.com", "telegram.org", "discord.com",
    "medium.com", "quora.com", "vk.com", "weibo.com", "weixin.qq.com",
    "threads.net",
    # Search Engines
    "google.com", "bing.com", "yahoo.com", "duckduckgo.com", "baidu.com",
    "yandex.com", "yandex.ru", "ask.com", "aol.com",
    # News / Reference
    "wikipedia.org", "wikimedia.org", "britannica.com", "nytimes.com",
    "bbc.com", "cnn.com", "reuters.com", "bloomberg.com", "forbes.com",
    "businessinsider.com", "wsj.com", "ft.com", "economist.com",
    "theguardian.com", "usatoday.com", "huffpost.com", "buzzfeed.com",
    "techcrunch.com", "theverge.com", "wired.com",
    # Job Boards
    "indeed.com", "monster.com", "glassdoor.com", "ziprecruiter.com",
    "careerbuilder.com", "simplyhired.com", "naukri.com", "seek.com.au",
    "stepstone.de",
    # Directories
    "yellowpages.com", "yelp.com", "manta.com", "kompass.com", "hotfrog.com",
    "cylex.us.com", "brownbook.net", "infobel.com", "europages.com",
    "thomasnet.com",
    # Forums / Code
    "stackexchange.com", "stackoverflow.com", "github.com", "gitlab.com",
    "bitbucket.org", "sourceforge.net", "wordpress.org", "wordpress.com",
    "blogspot.com", "blogger.com", "substack.com", "ghost.org",
    # Domain / Hosting / Builders
    "godaddy.com", "namecheap.com", "bluehost.com", "hostgator.com",
    "wix.com", "weebly.com", "squarespace.com", "webflow.com",
}

# TLD suffixes that indicate non-commercial sites
GOV_TLDS = {".gov", ".gov.uk", ".gov.au", ".gov.in", ".gov.cn",
             ".gov.sg", ".gov.hk", ".mil"}

# ============================================================
# Constants
# ============================================================

SERPER_API_URL = "https://google.serper.dev/search"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/125.0.0.0 Safari/537.36")
MAX_RESPONSE_SIZE = 1024 * 1024  # 1 MB
REQUEST_TIMEOUT = 15

EMAIL_RE = re.compile(
    r'[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9]'
    r'(?:[a-zA-Z0-9-]*[a-zA-Z0-9])?'
    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)+',
    re.IGNORECASE
)

PHONE_RE = re.compile(
    r'(?:\+\d{1,4}[\s.-]?)?'
    r'(?:\(?\d{1,4}\)?[\s.-]?)?'
    r'(?:\d{1,5}[\s.-]?){1,3}\d{1,5}'
    r'(?:\s*(?:ext|extension|x)\s*\d{1,5})?',
    re.IGNORECASE
)

# Email patterns to skip (false positives)
SKIP_EMAIL_DOMAINS = {"example.com", "domain.com", "yourcompany.com",
                      "yoursite.com", "email.com", "test.com"}
SKIP_EMAIL_PREFIXES = {"noreply", "no-reply", "donotreply", "donot-reply"}

# ============================================================
# TLD to Country mapping
# ============================================================

TLD_COUNTRY = {
    ".de": "DE", ".fr": "FR", ".it": "IT", ".es": "ES", ".nl": "NL",
    ".be": "BE", ".at": "AT", ".ch": "CH", ".se": "SE", ".no": "NO",
    ".dk": "DK", ".fi": "FI", ".pl": "PL", ".cz": "CZ", ".pt": "PT",
    ".gr": "GR", ".ie": "IE", ".lu": "LU", ".sk": "SK", ".hu": "HU",
    ".ro": "RO", ".bg": "BG", ".hr": "HR", ".si": "SI", ".ee": "EE",
    ".lv": "LV", ".lt": "LT", ".co.uk": "UK", ".uk": "UK",
    ".us": "US", ".com": "US", ".ca": "CA", ".com.au": "AU", ".au": "AU",
    ".co.nz": "NZ", ".nz": "NZ", ".co.jp": "JP", ".jp": "JP",
    ".co.kr": "KR", ".kr": "KR", ".in": "IN", ".com.br": "BR",
    ".br": "BR", ".com.mx": "MX", ".mx": "MX", ".ar": "AR",
    ".co.za": "ZA", ".za": "ZA", ".ae": "AE", ".sa": "SA",
    ".com.tr": "TR", ".tr": "TR", ".ru": "RU", ".com.sg": "SG",
    ".sg": "SG", ".com.hk": "HK", ".hk": "HK", ".tw": "TW",
    ".com.my": "MY", ".my": "MY", ".th": "TH", ".id": "ID",
    ".ph": "PH", ".vn": "VN",
}


# ============================================================
# Utility Functions
# ============================================================

def extract_domain(url: str) -> str:
    """Extract clean domain (with TLD) from a URL."""
    if not url:
        return ""
    # Add scheme if missing
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc or parsed.path
    # Remove port
    domain = domain.split(":")[0]
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower().strip()


def is_blocked(domain: str) -> bool:
    """Check if domain should be filtered out."""
    if not domain:
        return True
    domain = domain.lower().strip()
    # Check government/military TLDs
    for gov_tld in GOV_TLDS:
        if domain.endswith(gov_tld):
            return True
    # Check blocklist
    for blocked in BLOCKLIST:
        if domain == blocked or domain.endswith("." + blocked):
            return True
    return False


def detect_country(domain: str) -> str:
    """Detect country from domain TLD."""
    domain = domain.lower()
    # Check multi-part TLDs first
    for tld in sorted(TLD_COUNTRY.keys(), key=len, reverse=True):
        if domain.endswith(tld):
            return TLD_COUNTRY[tld]
    return ""


def get_api_key(cli_key: str = None) -> str:
    """
    Get Serper.dev API key from CLI arg, environment, or .env file.
    Priority: CLI arg > environment > .env file
    """
    # 1. CLI argument (highest priority)
    if cli_key:
        return cli_key.strip()

    # 2. Environment variable
    key = os.environ.get("SERPER_API_KEY")
    if key:
        return key.strip()

    # 3. .env file (script directory or working directory)
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.expanduser("~"), ".workbuddy", "skills",
                     "google-prospect-finder", ".env"),
    ]
    for env_path in env_paths:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                k, v = line.split("=", 1)
                                if k.strip() == "SERPER_API_KEY" and v.strip():
                                    return v.strip()
            except Exception:
                continue

    # Not found
    print("Error: Serper.dev API key required.", file=sys.stderr)
    print("  1. Register at https://serper.dev (free 2,500 credits)",
          file=sys.stderr)
    print("  2. Set env: set SERPER_API_KEY=your_key", file=sys.stderr)
    print("  3. Or pass: --apikey your_key", file=sys.stderr)
    print("  4. Or create .env file with: SERPER_API_KEY=your_key",
          file=sys.stderr)
    sys.exit(1)


# ============================================================
# Serper.dev Search
# ============================================================

def search_serper(query: str, api_key: str, num: int = 20,
                  gl: str = "us", hl: str = "en") -> list:
    """Call Serper.dev search API and return organic results."""
    import subprocess

    payload = json.dumps({
        "q": query,
        "num": num,
        "gl": gl,
        "hl": hl,
    }, ensure_ascii=False)

    # Use curl with -d (direct data) instead of @file
    curl_cmd = [
        "curl", "-s", "-S", "-X", "POST", SERPER_API_URL,
        "-H", f"X-API-KEY: {api_key}",
        "-H", "Content-Type: application/json",
        "-d", payload,
        "--max-time", str(REQUEST_TIMEOUT),
        "--tlsv1.2",
    ]

    try:
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Fix Windows GBK encoding issue
            timeout=REQUEST_TIMEOUT + 5,
            shell=False,
        )
        if result.returncode != 0:
            print(f"  [API Error] curl exit {result.returncode}: "
                  f"{result.stderr[:200]}", file=sys.stderr)
            return []
        if not result.stdout.strip():
            print(f"  [API Error] Empty response from API",
                  file=sys.stderr)
            return []
        data = json.loads(result.stdout)
        return data.get("organic", [])
    except subprocess.TimeoutExpired:
        print(f"  [API Error] Request timeout ({REQUEST_TIMEOUT}s)",
              file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"  [API Error] Invalid JSON response: {e}",
              file=sys.stderr)
        print(f"  Response preview: {result.stdout[:200]}",
              file=sys.stderr)
        return []
    except Exception as e:
        print(f"  [API Error] {type(e).__name__}: {e}",
              file=sys.stderr)
        return []


# ============================================================
# Website Fetching & Contact Extraction
# ============================================================

def fetch_page(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """Fetch HTML content of a URL. Return None on failure."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8,fr;q=0.7",
        },
        method="GET",
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return None
            # Limit response size
            data = resp.read(MAX_RESPONSE_SIZE + 1)
            if len(data) > MAX_RESPONSE_SIZE:
                data = data[:MAX_RESPONSE_SIZE]
            # Try different encodings
            for encoding in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]:
                try:
                    return data.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    continue
            return data.decode("utf-8", errors="ignore")
    except Exception:
        return None


def strip_html(html: str) -> str:
    """Remove HTML tags and decode basic entities."""
    # Remove script and style blocks
    html = re.sub(r'<script[^>]*>.*?</script>', '', html,
                  flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html,
                  flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    html = re.sub(r'<!--[^>]*-->', '', html)
    # Replace mailto links with visible email
    html = re.sub(r'href=["\']mailto:([^"\']+)["\']', r' \1 ',
                  html, flags=re.IGNORECASE)
    # Remove remaining tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    text = text.replace("&auml;", "\u00e4").replace("&ouml;", "\u00f6")
    text = text.replace("&uuml;", "\u00fc").replace("&szlig;", "\u00df")
    text = text.replace("&Auml;", "\u00c4").replace("&Ouml;", "\u00d6")
    text = text.replace("&Uuml;", "\u00dc")
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_emails(text: str) -> list:
    """Extract valid email addresses from text."""
    found = EMAIL_RE.findall(text)
    emails = []
    seen = set()
    for email in found:
        email = email.lower().strip()
        if email in seen:
            continue
        # Skip false positives
        domain_part = email.split("@")[-1] if "@" in email else ""
        prefix = email.split("@")[0] if "@" in email else ""
        if domain_part in SKIP_EMAIL_DOMAINS:
            continue
        if prefix in SKIP_EMAIL_PREFIXES and len(emails) > 0:
            continue
        # Skip image file references
        if any(email.endswith(ext) for ext in [".png", ".jpg", ".gif",
                                                ".webp", ".svg"]):
            continue
        seen.add(email)
        emails.append(email)
    return emails


def extract_phones(text: str) -> list:
    """Extract phone numbers from text."""
    # Look for phone patterns near keywords like Tel, Phone, etc.
    phones = []
    seen = set()

    # Pattern: keyword followed by number
    keyword_pattern = re.compile(
        r'(?:tel|phone|tel\.|tel\.nr\.|telephone|tlf|fon|fax|mobile)'
        r'[\s.:]*(\+?\d[\d\s().-]{6,20})',
        re.IGNORECASE
    )
    for match in keyword_pattern.finditer(text):
        phone = match.group(1).strip().rstrip(".)")
        digits = re.sub(r'\D', '', phone)
        if 7 <= len(digits) <= 20:
            if phone not in seen:
                seen.add(phone)
                phones.append(phone)

    # Fallback: standalone international format (+XX...)
    if not phones:
        intl_pattern = re.compile(r'\+\d{1,4}[\s.-]?\d[\d\s().-]{5,18}')
        for match in intl_pattern.finditer(text):
            phone = match.group(0).strip().rstrip(".)")
            digits = re.sub(r'\D', '', phone)
            if 7 <= len(digits) <= 20:
                if phone not in seen:
                    seen.add(phone)
                    phones.append(phone)

    return phones[:3]  # Limit to 3 phone numbers


def extract_company_name(html: str, domain: str) -> str:
    """Extract company name from HTML meta tags or title."""
    # Try og:site_name
    match = re.search(
        r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    # Try <title>
    match = re.search(r'<title[^>]*>(.*?)</title>', html,
                      re.DOTALL | re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        # Remove common suffixes
        title = re.split(r'\s*[|\-–—]\s*', title)[0].strip()
        if title and len(title) < 200:
            return title

    # Try first <h1>
    match = re.search(r'<h1[^>]*>(.*?)</h1>', html,
                      re.DOTALL | re.IGNORECASE)
    if match:
        h1 = strip_html(match.group(1)).strip()
        if h1 and len(h1) < 200:
            return h1

    # Fallback: domain name capitalized
    name = domain.split(".")[0].replace("-", " ").replace("_", " ")
    return name.title()


# Pages to try when visiting a site
CONTACT_PAGES = [
    "/contact", "/contact-us", "/contactus", "/kontakt",
    "/impressum", "/about", "/about-us", "/imprint",
    "/contatto", "/contatto/", "/contacto", "/contact-us/",
]


def visit_site_playwright(domain: str, browser=None,
                          timeout: int = 15) -> dict:
    """
    Visit website using Playwright for JS rendering.
    If browser is None, creates a temporary browser instance.
    """
    result = {
        "company_name": "",
        "emails": [],
        "phones": [],
        "contact_page": "",
    }

    if not PLAYWRIGHT_AVAILABLE:
        return result

    own_browser = browser is None
    pw_ctx = None
    try:
        if own_browser:
            pw_ctx = sync_playwright().start()
            launch_opts = {"headless": True, "args": ["--no-sandbox", "--disable-gpu"]}
            if CHROME_PATH:
                launch_opts["executable_path"] = CHROME_PATH
            browser = pw_ctx.chromium.launch(**launch_opts)

        page = browser.new_page()
        page.set_default_timeout(timeout * 1000)

        # Try homepage
        scheme_used = None
        for scheme in ["https", "http"]:
            url = f"{scheme}://{domain}/"
            try:
                page.goto(url, wait_until="domcontentloaded")
                # Wait for potential JS rendering
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                html = page.content()
                if html and len(html) > 500:
                    scheme_used = scheme
                    result["company_name"] = extract_company_name(html, domain)
                    plain = strip_html(html)
                    result["emails"] = extract_emails(plain)
                    result["phones"] = extract_phones(plain)
                    break
            except Exception:
                continue

        if not scheme_used:
            return result

        # Try contact pages if no contacts found yet
        if not result["emails"] and not result["phones"]:
            for path in CONTACT_PAGES:
                url = f"{scheme_used}://{domain}{path}"
                try:
                    page.goto(url, wait_until="domcontentloaded")
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    html = page.content()
                    if not html:
                        continue
                    plain = strip_html(html)
                    new_emails = extract_emails(plain)
                    new_phones = extract_phones(plain)
                    if new_emails or new_phones:
                        for e in new_emails:
                            if e not in result["emails"]:
                                result["emails"].append(e)
                        for p in new_phones:
                            if p not in result["phones"]:
                                result["phones"].append(p)
                        if not result["contact_page"]:
                            result["contact_page"] = url
                        if result["emails"] and result["phones"]:
                            break
                except Exception:
                    continue

        page.close()

    except Exception:
        pass
    finally:
        if own_browser and browser:
            try:
                browser.close()
            except Exception:
                pass
        if pw_ctx:
            try:
                pw_ctx.stop()
            except Exception:
                pass

    return result


def visit_site(domain: str, delay: float = 1.5,
               browser=None, use_playwright: bool = False) -> dict:
    """
    Visit a website's homepage and contact pages.
    Extract emails, phones, and company name.

    If use_playwright=True, uses Playwright for JS rendering.
    If browser is provided, reuses it (for batch processing).
    Falls back to Playwright if urllib finds no contacts.
    """
    result = {
        "company_name": "",
        "emails": [],
        "phones": [],
        "contact_page": "",
    }

    # --- Playwright-only mode ---
    if use_playwright and PLAYWRIGHT_AVAILABLE:
        pw_result = visit_site_playwright(domain, browser=browser)
        if pw_result["emails"] or pw_result["phones"] or pw_result["company_name"]:
            return pw_result
        # Fall through to urllib if Playwright found nothing

    # --- urllib mode (default) ---
    base_url = None
    for scheme in ["https", "http"]:
        html = fetch_page(f"{scheme}://{domain}/")
        if html:
            base_url = scheme
            result["company_name"] = extract_company_name(html, domain)
            plain = strip_html(html)
            result["emails"] = extract_emails(plain)
            result["phones"] = extract_phones(plain)
            break
        time.sleep(0.3)

    if not base_url:
        # urllib failed completely, try Playwright as last resort
        if PLAYWRIGHT_AVAILABLE and not use_playwright:
            pw_result = visit_site_playwright(domain, browser=browser)
            if pw_result["emails"] or pw_result["phones"]:
                return pw_result
        return result

    # Visit contact pages
    pages_to_try = CONTACT_PAGES
    if result["emails"]:
        pages_to_try = CONTACT_PAGES[:3]

    for path in pages_to_try:
        if delay > 0:
            time.sleep(delay)
        url = f"{base_url}://{domain}{path}"
        html = fetch_page(url)
        if not html:
            continue
        plain = strip_html(html)
        new_emails = extract_emails(plain)
        new_phones = extract_phones(plain)

        if new_emails or new_phones:
            for e in new_emails:
                if e not in result["emails"]:
                    result["emails"].append(e)
            for p in new_phones:
                if p not in result["phones"]:
                    result["phones"].append(p)
            if not result["contact_page"]:
                result["contact_page"] = url
            if result["emails"] and result["phones"]:
                break

    # --- Fallback: if urllib found nothing, try Playwright ---
    if not result["emails"] and not result["phones"]:
        if PLAYWRIGHT_AVAILABLE and not use_playwright:
            pw_result = visit_site_playwright(domain, browser=browser)
            if pw_result["emails"] or pw_result["phones"]:
                if pw_result["company_name"] and not result["company_name"]:
                    result["company_name"] = pw_result["company_name"]
                result["emails"] = pw_result["emails"]
                result["phones"] = pw_result["phones"]
                result["contact_page"] = pw_result["contact_page"]

    return result


# ============================================================
# Keyword Expansion
# ============================================================

ROLE_KEYWORDS = [
    "importer", "buyer", "distributor", "wholesaler",
    "import company", "trading company",
]

COUNTRY_GL = {
    "us": ("us", "en"), "uk": ("uk", "en"), "de": ("de", "de"),
    "fr": ("fr", "fr"), "it": ("it", "it"), "es": ("es", "es"),
    "nl": ("nl", "nl"), "be": ("be", "nl"), "at": ("at", "de"),
    "ch": ("ch", "de"), "se": ("se", "sv"), "no": ("no", "no"),
    "dk": ("dk", "da"), "fi": ("fi", "fi"), "pl": ("pl", "pl"),
    "pt": ("pt", "pt"), "ie": ("ie", "en"), "cz": ("cz", "cs"),
    "au": ("au", "en"), "nz": ("nz", "en"), "ca": ("ca", "en"),
    "jp": ("jp", "ja"), "kr": ("kr", "ko"), "in": ("in", "en"),
    "br": ("br", "pt"), "mx": ("mx", "es"), "ae": ("ae", "en"),
    "sa": ("sa", "ar"), "za": ("za", "en"), "tr": ("tr", "tr"),
    "sg": ("sg", "en"), "hk": ("hk", "en"), "ru": ("ru", "ru"),
}


def expand_keywords(product: str, countries: list) -> list:
    """Generate search queries from product + countries + role templates."""
    queries = []
    for country in countries:
        gl_hl = COUNTRY_GL.get(country.lower(), ("us", "en"))
        for role in ROLE_KEYWORDS:
            query = f'"{product}" {role}'
            if country != "all":
                country_name = country.upper()
                query += f" {country_name}"
            queries.append((query, gl_hl[0], gl_hl[1]))
    return queries


# ============================================================
# CSV Output
# ============================================================

CSV_FIELDS = [
    "Domain", "Title", "URL", "Snippet", "Country",
    "Company Name", "Email", "Phone", "Secondary Email",
    "Contact Page", "Search Query",
]


def write_csv(results: list, output_path: str):
    """Write results to CSV file (UTF-8 BOM for Excel)."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS,
                                extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)
            f.flush()


def result_to_row(result: dict) -> dict:
    """Convert a result dict to CSV row."""
    emails = result.get("emails", [])
    phones = result.get("phones", [])
    return {
        "Domain": result.get("domain", ""),
        "Title": result.get("title", ""),
        "URL": result.get("url", ""),
        "Snippet": result.get("snippet", ""),
        "Country": result.get("country", ""),
        "Company Name": result.get("company_name", ""),
        "Email": emails[0] if emails else "",
        "Phone": phones[0] if phones else "",
        "Secondary Email": emails[1] if len(emails) > 1 else "",
        "Contact Page": result.get("contact_page", ""),
        "Search Query": result.get("search_query", ""),
    }


# ============================================================
# Main Pipeline
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="B2B Prospect Finder - Google Search Lead Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "leather gloves importer" -o leads.csv
  %(prog)s "safety gloves buyer" --countries DE,FR,UK -o leads.csv
  %(prog)s "gloves importer" --no-visit -o domains_only.csv
  %(prog)s "work gloves" --countries DE,FR --max-sites 20 --delay 2
        """,
    )
    parser.add_argument("keywords", nargs="?", default=None,
                        help="Search keyword(s). Use commas for multiple.")
    parser.add_argument("--apikey", "-k", default=None,
                        help="Serper.dev API key (or set SERPER_API_KEY env)")
    parser.add_argument("--output", "-o", default="prospects.csv",
                        help="Output CSV path (default: prospects.csv)")
    parser.add_argument("--max-sites", "-m", type=int, default=30,
                        help="Max domains to visit for contact info (default: 30)")
    parser.add_argument("--countries", "-c", default="all",
                        help="Country codes: DE,FR,UK (default: all)")
    parser.add_argument("--delay", "-d", type=float, default=1.5,
                        help="Delay between website visits in seconds (default: 1.5)")
    parser.add_argument("--num-results", "-n", type=int, default=20,
                        help="Results per search query (default: 20)")
    parser.add_argument("--no-visit", action="store_true",
                        help="Skip website visiting, output search results only")
    parser.add_argument("--use-browser", action="store_true",
                        help="Use Playwright browser for JS-rendered sites (slower but more thorough)")
    parser.add_argument("--product", "-p", default=None,
                        help="Product name for keyword expansion (e.g., 'gloves')")
    parser.add_argument("--keyword-file", "-f", default=None,
                        help="Read keywords from file (one per line)")
    parser.add_argument("--gl", default="us",
                        help="Google location parameter (default: us)")

    args = parser.parse_args()

    # Get API key
    api_key = get_api_key(args.apikey)

    # Collect keywords
    queries = []
    if args.keyword_file:
        with open(args.keyword_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    queries.append((line, args.gl, "en"))
    elif args.keywords:
        for kw in args.keywords.split(","):
            kw = kw.strip()
            if kw:
                queries.append((kw, args.gl, "en"))
    elif args.product:
        countries = [c.strip() for c in args.countries.split(",")
                     if c.strip()]
        queries = expand_keywords(args.product, countries)
    else:
        parser.print_help()
        sys.exit(1)

    if not queries:
        print("Error: No search keywords provided.", file=sys.stderr)
        sys.exit(1)

    print(f"=== B2B Prospect Finder ===")
    print(f"Search queries: {len(queries)}")
    print(f"Results per query: {args.num_results}")
    print(f"Visit websites: {'No' if args.no_visit else 'Yes'}")
    if not args.no_visit:
        print(f"Max sites to visit: {args.max_sites}")
        print(f"Delay between visits: {args.delay}s")
    print(f"Output: {args.output}")
    print()

    # ============================================================
    # Phase 1: Search
    # ============================================================
    all_results = {}  # domain -> result dict (for dedup)
    total_found = 0
    total_blocked = 0

    for i, (query, gl, hl) in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Searching: {query}")
        results = search_serper(query, api_key, args.num_results, gl, hl)

        for item in results:
            url = item.get("link", "")
            domain = extract_domain(url)
            if not domain:
                continue

            if is_blocked(domain):
                total_blocked += 1
                continue

            total_found += 1

            # Deduplicate: keep first occurrence
            if domain not in all_results:
                all_results[domain] = {
                    "domain": domain,
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get("snippet", ""),
                    "country": detect_country(domain),
                    "company_name": "",
                    "emails": [],
                    "phones": [],
                    "contact_page": "",
                    "search_query": query,
                }
            else:
                # Append search query to existing
                existing = all_results[domain]
                if query not in existing["search_query"]:
                    existing["search_query"] += f" | {query}"

        if len(results) == 0:
            print(f"  -> No results or API error")
        else:
            unique_new = sum(1 for d in all_results
                             if all_results[d]["search_query"] == query)
            print(f"  -> {len(results)} results, "
                  f"{sum(1 for d in all_results if query in all_results[d].get('search_query', ''))} unique domains")

        # Small delay between API calls
        if i < len(queries):
            time.sleep(0.5)

    print(f"\n--- Search Summary ---")
    print(f"Total results: {total_found}")
    print(f"Blocked (in blocklist): {total_blocked}")
    print(f"Unique domains: {len(all_results)}")

    if not all_results:
        print("No prospects found. Try different keywords.", file=sys.stderr)
        sys.exit(0)

    # ============================================================
    # Phase 2: Visit websites (optional)
    # ============================================================
    if not args.no_visit:
        print(f"\n--- Visiting Websites ---")
        if args.use_browser and PLAYWRIGHT_AVAILABLE:
            print(f"[Browser mode: Playwright + JS rendering]")
        elif args.use_browser and not PLAYWRIGHT_AVAILABLE:
            print(f"[Warning: --use-browser but Playwright not installed, using urllib]")
        domains = list(all_results.values())
        visited = 0
        with_contacts = 0
        errors = 0

        # Create a shared browser instance for batch processing
        shared_browser = None
        pw_ctx = None
        if args.use_browser and PLAYWRIGHT_AVAILABLE:
            try:
                pw_ctx = sync_playwright().start()
                launch_opts = {"headless": True, "args": ["--no-sandbox", "--disable-gpu"]}
                if CHROME_PATH:
                    launch_opts["executable_path"] = CHROME_PATH
                shared_browser = pw_ctx.chromium.launch(**launch_opts)
            except Exception as e:
                print(f"[Warning: Failed to start browser: {e}]")
                shared_browser = None

        for i, result in enumerate(domains[:args.max_sites], 1):
            domain = result["domain"]
            print(f"[{i}/{min(len(domains), args.max_sites)}] "
                  f"Visiting: {domain}", end="", flush=True)

            try:
                contact = visit_site(
                    domain, args.delay,
                    browser=shared_browser,
                    use_playwright=args.use_browser,
                )
                result["company_name"] = contact.get("company_name", "")
                result["emails"] = contact.get("emails", [])
                result["phones"] = contact.get("phones", [])
                result["contact_page"] = contact.get("contact_page", "")

                if result["emails"] or result["phones"]:
                    with_contacts += 1
                    email_str = result["emails"][0] if result["emails"] else "no email"
                    phone_str = result["phones"][0] if result["phones"] else "no phone"
                    print(f" -> {email_str} | {phone_str}")
                else:
                    print(f" -> no contact found")

            except Exception as e:
                errors += 1
                print(f" -> ERROR: {e}", file=sys.stderr)

            visited += 1

        # Clean up browser
        if shared_browser:
            try:
                shared_browser.close()
            except Exception:
                pass
        if pw_ctx:
            try:
                pw_ctx.stop()
            except Exception:
                pass

        print(f"\n--- Visit Summary ---")
        print(f"Visited: {visited}")
        print(f"With contacts: {with_contacts}")
        print(f"Errors: {errors}")
    else:
        print("\n[--no-visit] Skipping website visits.")

    # ============================================================
    # Phase 3: Output CSV
    # ============================================================
    final_results = [result_to_row(r) for r in all_results.values()]

    # Sort: results with emails first, then by domain
    final_results.sort(
        key=lambda r: (0 if r.get("emails") else 1, r.get("domain", ""))
    )

    write_csv(final_results, args.output)

    print(f"\n=== Done ===")
    print(f"Output: {args.output}")
    print(f"Total prospects: {len(final_results)}")

    # Print top results with contacts
    with_email = [r for r in final_results if r.get("emails")]
    if with_email:
        print(f"\n--- Top Prospects with Email ---")
        for r in with_email[:10]:
            print(f"  {r['domain']} | {r['emails'][0]} | "
                  f"{r.get('company_name', '')}")

    print(f"\nCSV file ready for CRM import: {args.output}")


if __name__ == "__main__":
    main()
