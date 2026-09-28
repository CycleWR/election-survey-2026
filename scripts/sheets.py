"""Downloads Google Sheet tabs as CSV text.

With a service account key in the GOOGLE_SERVICE_ACCOUNT_KEY environment variable (the
JSON key file's contents), tabs are read through the Google Sheets API, so the sheet can
stay private: share it with the service account's email as a Viewer. Without a key,
falls back to the public CSV export, which needs "Anyone with the link can view".
"""
import csv, functools, io, json, os, sys, urllib.error, urllib.parse, urllib.request

API = "https://sheets.googleapis.com/v4/spreadsheets"
_token, _email = None, None


def _service_account():
    """Returns (access token, service account email), or (None, None) without a key."""
    global _token, _email
    key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "").strip()
    if not key:
        return None, None
    if _token is None:
        from google.oauth2 import service_account  # pip install google-auth requests
        from google.auth.transport.requests import Request
        info = json.loads(key)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        creds.refresh(Request())
        _token, _email = creds.token, info.get("client_email")
    return _token, _email


def _api(url, token, email):
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        if "SERVICE_DISABLED" in detail or "has not been used" in detail:
            sys.exit("The Google Sheets API isn't enabled for the service account's Cloud project: "
                     "enable it in Google Cloud console > APIs & Services.")
        if e.code in (403, 404):
            sys.exit(f"The service account can't open the sheet: share it with {email} (Viewer).")
        sys.exit(f"Google Sheets API error {e.code}: {detail[:500]}")


@functools.cache
def list_tabs(sheet_id):
    """[(gid, title)] for every tab. Needs the service account."""
    token, email = _service_account()
    meta = _api(f"{API}/{sheet_id}?fields=sheets.properties(sheetId,title)", token, email)
    return tuple((str(s["properties"]["sheetId"]), s["properties"]["title"]) for s in meta["sheets"])


def fetch_tab_csv(sheet_id, gid):
    token, email = _service_account()
    if token:
        titles = dict(list_tabs(sheet_id))
        if gid not in titles:
            sys.exit(f"No tab with gid {gid} in the sheet (tabs: {titles}).")
        rng = urllib.parse.quote(f"'{titles[gid]}'", safe="")
        values = _api(f"{API}/{sheet_id}/values/{rng}?valueRenderOption=FORMATTED_VALUE", token, email).get("values", [])
        width = max((len(r) for r in values), default=0)  # the API drops trailing empty cells
        out = io.StringIO()
        csv.writer(out).writerows(r + [""] * (width - len(r)) for r in values)
        return out.getvalue()

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        text = urllib.request.urlopen(url, timeout=60).read().decode("utf-8-sig")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit("Google refused access to the sheet. Either set up the service account "
                     "(GOOGLE_SERVICE_ACCOUNT_KEY secret) or share the sheet as 'Anyone with the link can view'.")
        raise
    if text.lstrip().lower().startswith(("<!doctype", "<html")):
        sys.exit("Google returned a web page, not CSV: the sheet isn't public and no service account key is set.")
    return text
