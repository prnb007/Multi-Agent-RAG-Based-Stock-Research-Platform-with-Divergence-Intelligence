import { useState, useEffect } from "react";

export function useScreenerQuotes(tickers: string[], refreshMs = 30000) {
  const [quotes, setQuotes] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetch_ = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(
          `${apiBase}/quotes/batch?tickers=${tickers.join(",")}`
        );
        const data = await res.json();
        if (cancelled) return;
        const map: Record<string, any> = {};
        data.quotes?.forEach((q: any) => { map[q.ticker] = q; });
        setQuotes(map);
      } catch (e) {
        console.error("[ScreenerQuotes] failed:", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetch_();
    const interval = setInterval(fetch_, refreshMs);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return { quotes, loading };
}
