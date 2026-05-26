"use client";
import { useBatchQuotes } from "@/hooks/useBatchQuotes";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

// Map ticker symbols to display labels
const TICKER_LABELS: Record<string, string> = {
  SPY:  "S&P 500",       // ETF tracking S&P 500
  QQQ:  "NASDAQ",        // ETF tracking NASDAQ-100
  VXX:  "VIX",           // ETF tracking VIX volatility
  TLT:  "20Y BONDS",     // Long-term treasury ETF
  IBIT: "BITCOIN",       // BlackRock Bitcoin ETF
};

const TICKERS = Object.keys(TICKER_LABELS);

function formatPrice(value: number, ticker: string): string {
  if (ticker === "TLT") return `${value.toFixed(2)}`;
  if (ticker === "IBIT") return `${value.toFixed(2)}`;
  if (ticker === "VXX") return value.toFixed(2);
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function TickerTile({ ticker, label, quote, loading }: {
  ticker: string;
  label: string;
  quote: any;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="rounded-2xl bg-neutral-900/60 border border-neutral-800/60 px-5 py-4">
        <div className="text-[10px] tracking-widest text-neutral-500 mb-2">
          {label}
        </div>
        <div className="h-6 w-24 bg-neutral-800 animate-pulse rounded" />
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="rounded-2xl bg-neutral-900/60 border border-neutral-800/60 px-5 py-4">
        <div className="text-[10px] tracking-widest text-neutral-500 mb-2">
          {label}
        </div>
        <div className="flex items-baseline gap-3">
          <div className="text-2xl font-semibold text-neutral-100">—</div>
          <div className="text-xs text-neutral-500">data unavailable</div>
        </div>
      </div>
    );
  }

  const pct = quote.percent_change;
  const isUp = pct > 0.001;
  const isDown = pct < -0.001;
  const color = isUp ? "text-emerald-400" : isDown ? "text-rose-400" : "text-neutral-400";
  const Icon = isUp ? ArrowUp : isDown ? ArrowDown : Minus;

  return (
    <div className="rounded-2xl bg-neutral-900/60 border border-neutral-800/60 px-5 py-4">
      <div className="text-[10px] tracking-widest text-neutral-500 mb-2">
        {label}
      </div>
      <div className="flex items-baseline justify-between gap-3">
        <div className="text-2xl font-semibold text-neutral-100">
          {formatPrice(quote.current_price, ticker)}
        </div>
        <div className={`flex items-center gap-1 text-sm ${color}`}>
          <Icon className="w-3.5 h-3.5" />
          <span>{Math.abs(pct).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}

export default function MarketTickerBar() {
  const { quotes, loading } = useBatchQuotes(TICKERS, 30000);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
      {TICKERS.map((ticker) => (
        <TickerTile
          key={ticker}
          ticker={ticker}
          label={TICKER_LABELS[ticker]}
          quote={quotes[ticker]}
          loading={loading}
        />
      ))}
    </div>
  );
}
