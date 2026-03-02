import { extractMetrics } from "./company-facts.js";

const STATEMENT_TAGS: Record<string, string[]> = {
  revenue: ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
  grossProfit: ["GrossProfit"],
  operatingIncome: ["OperatingIncomeLoss"],
  netIncome: ["NetIncomeLoss"],
  cashAndEquivalents: ["CashAndCashEquivalentsAtCarryingValue"],
  totalAssets: ["Assets"],
  totalLiabilities: ["Liabilities"],
  totalEquity: ["StockholdersEquity"],
  longTermDebt: ["LongTermDebtNoncurrent", "LongTermDebt"],
  sharesDiluted: ["WeightedAverageNumberOfDilutedSharesOutstanding"]
};

export function mapFinancialStatements(companyFacts: Record<string, unknown>): {
  incomeStatement: Record<string, unknown>;
  balanceSheet: Record<string, unknown>;
  cashFlow: Record<string, unknown>;
  missingFields: string[];
} {
  const metrics = extractMetrics(companyFacts, STATEMENT_TAGS);

  const incomeStatement = {
    revenue: metrics.revenue,
    grossProfit: metrics.grossProfit,
    operatingIncome: metrics.operatingIncome,
    netIncome: metrics.netIncome
  };

  const balanceSheet = {
    cashAndEquivalents: metrics.cashAndEquivalents,
    totalAssets: metrics.totalAssets,
    totalLiabilities: metrics.totalLiabilities,
    totalEquity: metrics.totalEquity,
    longTermDebt: metrics.longTermDebt,
    sharesDiluted: metrics.sharesDiluted
  };

  const cashFlow = {
    note: "Use filing statement tables for complete cash flow line-item mapping"
  };

  const missingFields = Object.entries(metrics)
    .filter(([, value]) => value.value === null)
    .map(([key]) => key);

  return { incomeStatement, balanceSheet, cashFlow, missingFields };
}
