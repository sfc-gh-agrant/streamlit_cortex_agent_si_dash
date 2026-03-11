# streamlit_cortex_agent_si_dash
A dashboard that lets you see usage by user for cortex agents and snowflake intelligence. There is an option to include simulated data if so desired. 


# AI Usage Monitoring Dashboard

A Streamlit in Snowflake (SiS) dashboard for monitoring **Snowflake Intelligence** and **Cortex Agent** usage across your account.

## Features

- **KPI Summary** — Total requests, credits, tokens, unique users, and active agents
- **Top 10 Users** — Ranked by credit consumption with role, business area, and most-used agent
- **Usage by Role & Business Area** — Credit breakdown by organizational dimensions
- **User-Agent Credit Matrix** — Cross-tabulation of top 15 users against all agents
- **Credits Over Time** — Daily trend area chart
- **Agent Breakdown** — Credits by agent and average tokens per agent
- **Request Detail** — Full request-level table with filtering

Includes a simulated data mode (250 users, 5000 requests) for demo purposes.

## Data Sources

| View | Database |
|------|----------|
| `SNOWFLAKE_INTELLIGENCE_USAGE_HISTORY` | `SNOWFLAKE.ACCOUNT_USAGE` |
| `CORTEX_AGENT_USAGE_HISTORY` | `SNOWFLAKE.ACCOUNT_USAGE` |

## Deployment

### Prerequisites

- Snowflake account with `ACCOUNTADMIN` role (or access to `SNOWFLAKE.ACCOUNT_USAGE`)
- A warehouse for query execution

### Deploy to Snowflake

```sql
-- 1. Create database and schema (if needed)
CREATE DATABASE IF NOT EXISTS STREAMLIT_DB;
CREATE SCHEMA IF NOT EXISTS STREAMLIT_DB.STREAMLIT_SCHEMA;

-- 2. Create stage and upload files
CREATE STAGE IF NOT EXISTS STREAMLIT_DB.STREAMLIT_SCHEMA.USAGE_DASHBOARD_STAGE;
-- Upload streamlit_app.py and environment.yml to the stage via Snowsight or CLI:
-- snowflake stage copy streamlit_app.py @STREAMLIT_DB.STREAMLIT_SCHEMA.USAGE_DASHBOARD_STAGE --overwrite
-- snowflake stage copy environment.yml @STREAMLIT_DB.STREAMLIT_SCHEMA.USAGE_DASHBOARD_STAGE --overwrite

-- 3. Create the Streamlit app
CREATE OR REPLACE STREAMLIT STREAMLIT_DB.STREAMLIT_SCHEMA.USAGE_MONITORING_DASHBOARD
  ROOT_LOCATION = '@STREAMLIT_DB.STREAMLIT_SCHEMA.USAGE_DASHBOARD_STAGE'
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = 'ANALYST_WH'
  TITLE = 'AI Usage Monitoring Dashboard';
```

## Files

| File | Description |
|------|-------------|
| `streamlit_app.py` | Main dashboard application |
| `environment.yml` | Conda environment specification for SiS |

## Compatibility

Built for **Streamlit in Snowflake** runtime (Streamlit ~1.22). Avoids newer API parameters (`color`, `horizontal`, `hide_index`, `st.toggle`) that are not yet available in the SiS environment.
