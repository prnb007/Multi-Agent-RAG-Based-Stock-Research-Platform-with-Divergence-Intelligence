export interface GlossaryTerm {
  term: string;
  short: string;
  full: string;
  example?: string;
}

export const GLOSSARY: Record<string, GlossaryTerm> = {
  divergence_score: {
    term: "Divergence Score",
    short: "How much our 5 AI agents disagree about this stock",
    full: "Measures conflict between specialized agents analyzing different signals. Score ranges 0.0 (full consensus) to 1.0+ (extreme conflict). High divergence often reveals overlooked opportunities or hidden risks.",
    example: "A divergence of 0.7 might mean Fundamentals is bullish while Insider data is bearish — worth investigating why.",
  },
  synthesis_thesis: {
    term: "Synthesis Thesis",
    short: "AI-generated investment narrative combining all agent insights",
    full: "After all 5 agents complete their analysis, the Synthesis Agent generates a Bull Thesis (reasons to buy) and Bear Thesis (reasons to be cautious). Read both for the complete picture.",
  },
  bull_thesis: {
    term: "Bull Thesis",
    short: "The case FOR investing in this stock",
    full: "Reasons why this stock might go up, based on positive signals from the agents (strong fundamentals, positive sentiment, bullish technicals, insider buying, sector outperformance).",
  },
  bear_thesis: {
    term: "Bear Thesis",
    short: "The case AGAINST this stock",
    full: "Reasons why this stock might decline, based on negative signals (weak financials, negative news, bearish technicals, insider selling, sector underperformance).",
  },
  wall_street_consensus: {
    term: "Wall Street Consensus",
    short: "Aggregated buy/sell ratings from professional analysts",
    full: "Combines ratings from investment bank analysts. Consensus score from -1 (Strong Sell) to +1 (Strong Buy). Useful as a baseline but analysts often miss key signals that our agents catch.",
  },
  confidence: {
    term: "Confidence",
    short: "How sure the agent is about its analysis",
    full: "Reflects the quality and quantity of data available. 80%+ means rich data and high certainty. Below 50% means the agent had limited information and the conclusion should be treated cautiously.",
  },
  highest_gap_pair: {
    term: "Highest Gap Pair",
    short: "The two agents with the biggest disagreement",
    full: "Identifies which two agents see the stock most differently. Investigating these gaps often surfaces the most important insights — for example, when fundamentals look strong but insiders are dumping shares.",
  },
  fundamentals_agent: {
    term: "Fundamentals Agent",
    short: "Analyzes the company's financial health",
    full: "Reviews revenue, profit margins, debt levels, cash flow, and growth rates from SEC filings. Strong fundamentals = stable, profitable business with sustainable competitive advantages.",
  },
  sentiment_agent: {
    term: "Sentiment Agent",
    short: "Gauges market mood from recent news",
    full: "Analyzes news headlines, article tone, and coverage volume to measure how the market currently perceives this stock. Sentiment can shift quickly and often precedes price moves.",
  },
  technical_agent: {
    term: "Technical Agent",
    short: "Reads price charts and momentum indicators",
    full: "Uses indicators like RSI, MACD, and Bollinger Bands to identify trends, momentum, and potential reversal points. Technicals reveal what the chart is saying regardless of fundamentals.",
  },
  insider_agent: {
    term: "Insider Agent",
    short: "Tracks buying and selling by company executives",
    full: "Monitors SEC Form 4 filings to see when executives buy or sell their own company's stock. Heavy insider selling can signal concerns about future performance.",
  },
  macro_agent: {
    term: "Macro Agent",
    short: "Compares the stock to its sector and peers",
    full: "Measures how the stock performs relative to its sector ETF and peer companies. A stock underperforming its sector might be losing competitive ground.",
  },
  rsi: {
    term: "RSI",
    short: "Relative Strength Index — momentum gauge (0–100)",
    full: "Above 70 = overbought (might be due for a pullback). Below 30 = oversold (might be due for a bounce). 50 is neutral.",
    example: "RSI of 78.79 suggests the stock is overbought and could see a short-term correction.",
  },
  macd: {
    term: "MACD",
    short: "Moving Average Convergence Divergence — trend strength",
    full: "When MACD crosses above its signal line = bullish momentum building. When it crosses below = bearish. The histogram measures the gap between them.",
  },
  bollinger_bands: {
    term: "Bollinger Bands",
    short: "Price channels showing the typical trading range",
    full: "Price near the upper band suggests overbought conditions. Price near the lower band suggests oversold. Bands widening = increasing volatility.",
  },
  net_margin: {
    term: "Net Margin",
    short: "Percentage of revenue that becomes profit",
    full: "Higher = more efficient business. Software companies often have 20%+ margins. Retailers typically run 3–5%. Apple's 26.9% is exceptional for a hardware company.",
  },
  roe: {
    term: "Return on Equity (ROE)",
    short: "Profit generated per dollar of shareholder equity",
    full: "Measures how efficiently the company uses shareholder capital. Above 15% is generally considered good. Above 25% is excellent.",
  },
  pe_ratio: {
    term: "P/E Ratio",
    short: "Price-to-Earnings — how much investors pay per $ of earnings",
    full: "High P/E (above 25) can mean overvalued OR high growth expectations. Low P/E (below 15) can mean cheap OR a struggling business. Always compare to the sector average.",
  },
  free_cash_flow: {
    term: "Free Cash Flow",
    short: "Cash generated after all expenses and investments",
    full: "The 'real' money the business produces. Higher FCF = more financial flexibility for dividends, buybacks, and acquisitions.",
  },
  consensus: {
    term: "Consensus",
    short: "All agents agree on the direction",
    full: "Low divergence score (under 0.3) means all 5 agents see the stock similarly. This usually means the signal is reliable but may already be priced in.",
  },
  high_conflict: {
    term: "High Conflict",
    short: "Major disagreement between agents",
    full: "Divergence above 0.6 means the agents see fundamentally different stories. This is often where the most valuable insights hide — when conventional wisdom misses something the data shows.",
  },
};
