# Tuning SEC-EDGAR MCP
1. get_financial_statements ignores key inputs (accession, periodMode, normalize) and always pulls generic companyfacts; output is not filing-specific. This makes DCF/3-statement consistency weak.                                                                                                            
     get-financial-statements.ts:15
     get-financial-statements.ts:16                                                                                                                          
2. Cash flow extraction is not implemented (placeholder note only), so one-third of “financial statements” is effectively missing.                         
     statements.ts:40                                                                                                                                        
3. taxonomy input is accepted but unused in get_company_facts, so caller cannot control data scope as promised by schema.                                  
     types.ts:16                                                                                                                                             
     get-company-facts.ts:23                                                                                                                                 
4. Metric selection logic is accuracy-risky: takes first available unit + latest end date only, without form/period filtering (10-K vs 10-Q), so can mix incompatible points.                                                                                                                                    
     company-facts.ts:41                                                                                                                                     
     company-facts.ts:21                                                                                                                                     
5. get_filing_section only searches filings.recent and uses naive keyword snippet extraction, so older accessions fail and extracted text quality is unstable.      
     get-filing-section.ts:36                                                                                                                                
     get-filing-section.ts:45 
# For fed data api
Add free-nyfed-liquidity MCP for SOFR/ON RRP/TGA.                                                                                                        
 - Add cross-source join tool (FRED + NY Fed + Treasury harmonization).
 - Add watchlist preset tools for macro regimes (inflation, labor, liquidity, growth
