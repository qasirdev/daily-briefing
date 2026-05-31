# Google Calendar OAuth Setup – Beginner Step-by-Step Guide

This guide will help you set up **Google Calendar API** access using OAuth 2.0 and obtain a refresh token for use in scripts, desktop apps, or backend services.

---

## Step 1: Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)

2. **Create a new project**
   - Click the project dropdown at the top → **New Project**
   - Give it a meaningful name (e.g., "My Calendar App") → Click **Create**

3. **Enable Google Calendar API**
   - Go to **APIs & Services** → **Library**
   - Search for "**Google Calendar API**"
   - Click on it → Click **Enable**

4. **Configure OAuth Consent Screen**
   - Go to **APIs & Services** → **OAuth consent screen**
   - Select **User type** → **External** → Click **Create**
   - Fill in the following:
     - **App name** (e.g., "My Calendar Tool")
     - **User support email** (your email)
     - **Developer contact information** (your email)
   - Click **Save and Continue**
   - Under **Scopes**, click **Add or Remove Scopes**
     - Add the scope: `https://www.googleapis.com/auth/calendar` (full access) or `https://www.googleapis.com/auth/calendar.events`
   - Click **Save and Continue**
   - Add your own email under **Test users** → **Save and Continue**

5. **Create OAuth 2.0 Client Credentials**
   - Go to **APIs & Services** → **Credentials**
   - Click **+ Create Credentials** → **OAuth client ID**
   - Choose **Application type** → **Desktop app**
   - Give it a name → Click **Create**
   - Copy and save safely:
     - **Client ID**
     - **Client Secret**

---

## Step 2: Get Refresh Token (Easiest Method)

### Using OAuth 2.0 Playground

1. Open [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
2. Click the **gear icon** (top right) → Check "**Use your own OAuth credentials**"
3. Paste your **Client ID** and **Client Secret**
4. On the left panel:
   - Expand **Google Calendar API v3**
   - Select the scopes you need (recommended: `https://www.googleapis.com/auth/calendar`)
5. Click **Authorize APIs**
6. Sign in with your Google account and **grant permission**
7. Click **Exchange authorization code for tokens**
8. Copy the **Refresh token**

---

## Step 3: Add Credentials to `.env` File

Create a `.env` file in your project root:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REFRESH_TOKEN=your_refresh_token_here
