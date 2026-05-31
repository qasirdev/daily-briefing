# Google Calendar OAuth Setup – Beginner Step-by-Step Guide

This guide helps you set up **Google Calendar API** access using OAuth 2.0 and obtain a refresh token for the Daily Briefing calendar MCP server.

**Important:** The Client ID, Client Secret, and Refresh token must all come from the **same** OAuth client. Mixing credentials (e.g. Desktop client ID with a Playground refresh token) causes `unauthorized_client` errors at runtime.

---

## Step 1: Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)

2. **Create a new project** (or select an existing one)
   - Click the project dropdown at the top → **New Project**
   - Give it a meaningful name (e.g. `dailybriefing`) → Click **Create**

3. **Enable Google Calendar API**
   - Go to **APIs & Services** → **Library**
   - Search for **Google Calendar API**
   - Click on it → Click **Enable**

4. **Configure OAuth Consent Screen**
   - Go to **APIs & Services** → **OAuth consent screen**
   - Select **User type** → **External** → Click **Create**
   - Fill in:
     - **App name** (e.g. `dailybriefing`)
     - **User support email** (your email)
     - **Developer contact information** (your email)
   - Click **Save and Continue**
   - Under **Scopes**, click **Add or Remove Scopes**
     - Add one of:
       - `https://www.googleapis.com/auth/calendar` (read/write — recommended for dev)
       - `https://www.googleapis.com/auth/calendar.readonly` (read-only)
   - Click **Save and Continue**
   - Under **Test users**, click **+ Add users**
     - Add the **exact Gmail address** you will sign in with in OAuth Playground
     - This is required while the app is in **Testing** mode (default for new apps)
   - Click **Save and Continue**

   > While **Publishing status** is **Testing**, only emails listed under **Test users** can authorize. If you see `Error 403: access_denied`, add your Google account here and retry.

5. **Create OAuth 2.0 Web Application Credentials**

   OAuth Playground requires a **Web application** client with a specific redirect URI. A **Desktop app** client will cause `redirect_uri_mismatch`.

   - Go to **APIs & Services** → **Credentials**
   - Click **+ Create Credentials** → **OAuth client ID**
   - Choose **Application type** → **Web application**
   - Name: e.g. `Daily Briefing OAuth Playground`
   - Under **Authorized redirect URIs**, click **+ Add URI** and enter exactly:

     ```
     https://developers.google.com/oauthplayground
     http://localhost:8088
     http://localhost:3010
     ```

     - `oauthplayground` — for obtaining the refresh token (Step 2)
     - `8088` / `3010` — for the in-app consent popup when granting calendar access

   - Click **Create**
   - Copy and save safely:
     - **Client ID**
     - **Client Secret**

---

## Step 2: Get Refresh Token via OAuth 2.0 Playground

1. Open [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground)

2. Click the **gear icon** (top right) and configure:
   - Check **Use your own OAuth credentials**
   - Paste the **Web application** Client ID and Client Secret from Step 1
   - Leave **OAuth flow** as **Server-side**
   - **Access type:** Offline
   - **Force prompt:** Consent Screen (ensures a refresh token is issued)

3. On the left panel:
   - Expand **Google Calendar API v3**
   - Select the scope you added on the consent screen (e.g. `https://www.googleapis.com/auth/calendar`)

4. Click **Authorize APIs**

5. Sign in with the **same Google account** you added as a **Test user** in Step 1

6. If you see **"Google hasn't verified this app"**:
   - Click **Advanced**
   - Click **Go to dailybriefing (unsafe)** — normal for apps in Testing mode

7. Click **Allow** to grant permission

8. Click **Exchange authorization code for tokens**

9. Copy the **Refresh token** from the response (not the access token)

---

## Step 3: Add Credentials to `.env`

Add all three values from the **same Web application client** to your project root `.env`:

```env
GOOGLE_CLIENT_ID=your_web_client_id_here
GOOGLE_CLIENT_SECRET=your_web_client_secret_here
GOOGLE_REFRESH_TOKEN=your_refresh_token_here
CALENDAR_ID=primary
# Optional — redirect after in-app consent popup (must match Google Cloud redirect URIs)
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8088
```

Do not put inline comments on the same line as values (breaks Docker `--env-file`).

---

## Step 4: Verify Before Running the App

Run this from the project root. You should get **200** and an `access_token` in the response:

```bash
uv run python -c "
import httpx
from backend.settings import get_settings
get_settings.cache_clear()
s = get_settings()
r = httpx.post('https://oauth2.googleapis.com/token', data={
    'client_id': s.google_client_id,
    'client_secret': s.google_client_secret,
    'refresh_token': s.google_refresh_token,
    'grant_type': 'refresh_token',
})
print(r.status_code)
print(r.text[:300])
"
```

If this succeeds, the calendar MCP server should start without credential validation errors.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `redirect_uri_mismatch` | Using a **Desktop app** client, or missing redirect URI | Create a **Web application** client; add `https://developers.google.com/oauthplayground` under **Authorized redirect URIs** |
| `403: access_denied` — app in Testing | Your Google account is not a **Test user** | OAuth consent screen → **Test users** → add your Gmail → retry (use incognito if needed) |
| `401: unauthorized_client` | Client ID/secret do not match the refresh token | Re-issue the refresh token using the **same** Client ID and Secret now in `.env`; update all three together |
| Calendar MCP crashes in Docker | Stale token or wrong client | Re-run Step 4; restart the container with `--env-file .env` |
| No refresh token in Playground | Consent already granted without offline access | Gear icon → **Force prompt: Consent Screen**; revoke app at [Third-party access](https://myaccount.google.com/permissions) and re-authorize |

---

## Docker note

After updating `.env`, restart the container so it picks up new credentials:

```bash
docker rm -f briefing-smoke
docker run -d --name briefing-smoke \
  --env-file .env \
  -e CORS_ORIGINS=http://localhost \
  -p 8088:80 \
  briefing:latest
```

Check logs for calendar MCP startup:

```bash
docker logs briefing-smoke 2>&1 | grep -i calendar
```

You should **not** see repeated `Failed to validate Google Calendar credentials` messages.
