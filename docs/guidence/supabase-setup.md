# Supabase Gate 2 Configuration Guide

This guide helps you set up your environment variables for your Supabase project, specifically using the Supavisor connection string required for Gate 2.

## Step 1: Prerequisites
Ensure you have your **Database Password** ready (you should have saved this when you created your project).

## Step 2: Your Connection Details
You have successfully identified your pooler connection settings:
- **Host:** `aws-0-eu-west-1.pooler.supabase.com`
- **Port:** `6543`
- **User:** `postgres.bnvbzbferziluoigznno`

## Step 3: Configure your `.env` File
Open your project's `.env` file and replace `[YOUR-PASSWORD]` with your actual database password. 

**Copy and paste the following into your `.env` file:**

```env
# Supabase Database URLs
# Replace [YOUR-PASSWORD] with your actual database password
DATABASE_URL=postgresql+asyncpg://postgres.bnvbzbferziluoigznno:[YOUR-PASSWORD]@[aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require](https://aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require)
MCP_POSTGRES_URL=postgresql://postgres.bnvbzbferziluoigznno:[YOUR-PASSWORD]@[aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require](https://aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require)

# Calendar Configuration
CALENDAR_ID=primary
