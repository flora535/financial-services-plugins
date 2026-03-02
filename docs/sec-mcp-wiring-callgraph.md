# SEC MCP Wiring Callgraph

## /3-statements
1. `sec.resolve_company`
2. `sec.list_filings`
3. `sec.get_financial_statements`
4. `sec.get_filing_section` (optional note extraction)

If required fields are missing: keep template formulas; mark missing inputs `data unavailable`.

## /comps
For each company:
1. `sec.resolve_company`
2. `sec.get_company_facts`
3. `sec.list_filings`

If a metric is missing: mark only that metric `data unavailable`, use explicit fallback per skill hierarchy.

## /dcf
1. `sec.resolve_company`
2. `sec.list_filings`
3. `sec.get_financial_statements`
4. `sec.get_company_facts`
5. `sec.get_filing_section` (`debt_note` when needed)

If critical values are missing: continue with warnings and reduced confidence.
