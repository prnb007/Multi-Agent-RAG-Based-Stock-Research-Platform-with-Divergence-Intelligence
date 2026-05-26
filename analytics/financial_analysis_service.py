"""
FinancialAnalysisService
Computes derived financial metrics from normalized statements.
Used by FundamentalsAgent. Pure computation — no API calls.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from providers.models import (
    CompanyOverview, IncomeStatement,
    BalanceSheet, CashFlowStatement
)

logger = logging.getLogger(__name__)


@dataclass
class FinancialMetrics:
    ticker: str
    # Profitability
    gross_margin: Optional[float]
    operating_margin: Optional[float]
    net_margin: Optional[float]
    return_on_equity: Optional[float]
    return_on_assets: Optional[float]
    # Growth
    revenue_growth: Optional[float]
    earnings_growth: Optional[float]
    # Financial health
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    free_cash_flow: Optional[float]
    cash_to_debt: Optional[float]
    # Valuation
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    price_to_book: Optional[float]
    # Signals
    financial_health_score: float    # 0.0 to 1.0
    profitability_score: float       # 0.0 to 1.0
    growth_score: float              # 0.0 to 1.0
    overall_score: float             # -1.0 to +1.0 for agent use
    key_strengths: list[str]
    key_risks: list[str]


class FinancialAnalysisService:

    def compute(
        self,
        overview: CompanyOverview,
        income: Optional[IncomeStatement] = None,
        balance: Optional[BalanceSheet] = None,
        cashflow: Optional[CashFlowStatement] = None,
    ) -> FinancialMetrics:

        ticker = overview.ticker
        strengths, risks = [], []

        # Margins
        gross_margin = operating_margin = net_margin = None
        if income and income.total_revenue and income.total_revenue > 0:
            if income.gross_profit:
                gross_margin = round(income.gross_profit / income.total_revenue, 4)
            if income.operating_income:
                operating_margin = round(income.operating_income / income.total_revenue, 4)
            if income.net_income:
                net_margin = round(income.net_income / income.total_revenue, 4)

        # Return on assets
        return_on_assets = None
        if income and income.net_income and balance and balance.total_assets:
            return_on_assets = round(income.net_income / balance.total_assets, 4)

        # Cash to debt ratio
        cash_to_debt = None
        if balance and balance.cash_and_equivalents and balance.total_debt:
            if balance.total_debt > 0:
                cash_to_debt = round(
                    balance.cash_and_equivalents / balance.total_debt, 4
                )

        # Scoring
        health_scores, profit_scores, growth_scores = [], [], []

        # Financial health scoring
        if overview.debt_to_equity is not None:
            de = overview.debt_to_equity
            if de < 0.5:
                health_scores.append(1.0)
                strengths.append(f"Low debt-to-equity ratio ({de:.2f})")
            elif de < 1.5:
                health_scores.append(0.6)
            else:
                health_scores.append(0.2)
                risks.append(f"High debt-to-equity ratio ({de:.2f})")

        if balance and balance.current_ratio:
            cr = balance.current_ratio
            if cr > 2.0:
                health_scores.append(1.0)
                strengths.append(f"Strong current ratio ({cr:.2f})")
            elif cr > 1.0:
                health_scores.append(0.7)
            else:
                health_scores.append(0.2)
                risks.append(f"Weak current ratio ({cr:.2f})")

        if cashflow and cashflow.free_cash_flow:
            if cashflow.free_cash_flow > 0:
                health_scores.append(0.9)
                strengths.append(
                    f"Positive free cash flow "
                    f"(${cashflow.free_cash_flow/1e9:.1f}B)"
                )
            else:
                health_scores.append(0.2)
                risks.append("Negative free cash flow")

        # Profitability scoring
        if net_margin is not None:
            if net_margin > 0.20:
                profit_scores.append(1.0)
                strengths.append(f"High net margin ({net_margin:.1%})")
            elif net_margin > 0.10:
                profit_scores.append(0.7)
            elif net_margin > 0:
                profit_scores.append(0.4)
            else:
                profit_scores.append(0.0)
                risks.append(f"Negative net margin ({net_margin:.1%})")

        if overview.return_on_equity is not None:
            roe = overview.return_on_equity
            if roe > 0.20:
                profit_scores.append(1.0)
                strengths.append(f"Strong ROE ({roe:.1%})")
            elif roe > 0.10:
                profit_scores.append(0.6)
            else:
                profit_scores.append(0.2)

        # Growth scoring
        if overview.revenue_growth is not None:
            rg = overview.revenue_growth
            if rg > 0.15:
                growth_scores.append(1.0)
                strengths.append(f"Strong revenue growth ({rg:.1%})")
            elif rg > 0.05:
                growth_scores.append(0.6)
            elif rg > 0:
                growth_scores.append(0.3)
            else:
                growth_scores.append(0.0)
                risks.append(f"Declining revenue ({rg:.1%})")

        if overview.earnings_growth is not None:
            eg = overview.earnings_growth
            if eg > 0.15:
                growth_scores.append(1.0)
                strengths.append(f"Strong earnings growth ({eg:.1%})")
            elif eg > 0:
                growth_scores.append(0.5)
            else:
                growth_scores.append(0.0)
                risks.append(f"Declining earnings ({eg:.1%})")

        # Valuation risks
        if overview.pe_ratio and overview.pe_ratio > 40:
            risks.append(f"High P/E ratio ({overview.pe_ratio:.1f}x) — stretched valuation")
        if overview.price_to_book and overview.price_to_book > 10:
            risks.append(f"High Price-to-Book ({overview.price_to_book:.1f}x)")

        def avg(lst): return sum(lst) / len(lst) if lst else 0.5

        health_score      = round(avg(health_scores), 3)
        profitability_score = round(avg(profit_scores), 3)
        growth_score       = round(avg(growth_scores), 3)

        # Overall score: -1.0 to +1.0
        composite = (
            health_score * 0.3 +
            profitability_score * 0.4 +
            growth_score * 0.3
        )
        overall_score = round((composite - 0.5) * 2, 3)

        return FinancialMetrics(
            ticker=ticker,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            return_on_equity=overview.return_on_equity,
            return_on_assets=return_on_assets,
            revenue_growth=overview.revenue_growth,
            earnings_growth=overview.earnings_growth,
            debt_to_equity=overview.debt_to_equity,
            current_ratio=balance.current_ratio if balance else None,
            free_cash_flow=cashflow.free_cash_flow if cashflow else None,
            cash_to_debt=cash_to_debt,
            pe_ratio=overview.pe_ratio,
            forward_pe=overview.forward_pe,
            price_to_book=overview.price_to_book,
            financial_health_score=health_score,
            profitability_score=profitability_score,
            growth_score=growth_score,
            overall_score=overall_score,
            key_strengths=strengths[:5],
            key_risks=risks[:5],
        )


financial_analysis_service = FinancialAnalysisService()
