# SEC MCP Tool Contract

## Common response metadata

All SEC tools return:

- `meta.source`
- `meta.as_of`
- `meta.freshness`
- `meta.confidence`
- `meta.fallback_used`
- `meta.missing_fields`

## Tools

### sec.resolve_company
- Input: `ticker` or `cik`
- Output: normalized identity (`cik`, `ticker`, `name`, optional profile fields)

### sec.list_filings
- Input: `cik`, `forms[]`, `limit`
- Output: recent filing list with accession, dates, and primary doc URL

### sec.get_company_facts
- Input: `cik`, optional `taxonomy`, optional `metrics[]`
- Output: normalized metric map from SEC companyfacts

### sec.get_financial_statements
- Input: `cik`, `accession`, `periodMode`, `normalize`
- Output: normalized IS/BS/CF blocks and `missingFields`

### sec.get_filing_section
- Input: `cik`, `accession`, `section`
- Output: section snippet text and `missingFields`

## Error model

- Bad input: tool returns `isError: true` with validation message.
- Upstream/API failure: tool returns `isError: true` with retry-safe message.
- Partial data: success response with explicit `missingFields`.
