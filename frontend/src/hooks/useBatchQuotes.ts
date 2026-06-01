import { useEffect, useState } from "react";

export interface RealtimeQuote {
  ticker: string;
  current_price: number;
  change: number;
  percent_change: number;
  day_high: number;
  day_low: number;
  day_open: number;
  prev_close: number;
  timestamp: number;
}

interface BatchQuoteResponse {
  quotes: RealtimeQuote[];
  failed: string[];
}

export function useBatchQuotes(
  tickers: string[],
  refreshIntervalMs: number = 30000
) {
  const [quotes, setQuotes] = useState<Record<string, RealtimeQuote>>({});
  const [failed, setFailed] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tickers.length === 0) return;

    let cancelled = false;

    const fetchQuotes = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const url = `${apiBase}/quotes/batch?tickers=${tickers.join(",")}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: BatchQuoteResponse = await res.json();
        if (cancelled) return;

        const map: Record<string, RealtimeQuote> = {};
        data.quotes.forEach((q) => {
          map[q.ticker] = q;
        });
        setQuotes(map);
        setFailed(data.failed || []);
        setError(null);
      } catch (e: any) {
        if (!cancelled) setError(e.message || "Failed to fetch quotes");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchQuotes();
    const interval = setInterval(fetchQuotes, refreshIntervalMs);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [tickers.join(","), refreshIntervalMs]);

  return { quotes, failed, loading, error };
}
