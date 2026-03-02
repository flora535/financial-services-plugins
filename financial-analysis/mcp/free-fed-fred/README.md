# Free FED FRED MCP Server

Local MCP server for FRED/ALFRED macro data workflows.

## Required env

```bash
FRED_API_KEY="your_fred_api_key"
```

## Install + build

```bash
cd mcp/free-fed-fred
npm install
npm run build
```

## Run locally

```bash
npm start
```

## Exposed tools

- `fred.search_series`
- `fred.get_series_meta`
- `fred.get_observations`
- `fred.get_latest`
- `fred.get_vintages`
- `fred.get_release_observations`

## Tool behavior

- Uses official FRED API with ALFRED realtime/vintage support.
- Normalizes missing value `"."` to `null`.
- Returns provenance metadata with each response.
