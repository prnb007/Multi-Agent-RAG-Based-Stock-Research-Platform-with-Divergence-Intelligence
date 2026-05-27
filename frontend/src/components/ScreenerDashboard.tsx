"use client";
import React from 'react';
import { useRouter } from 'next/navigation';
import { useAnalysisContext } from '@/context/AnalysisContext';
import MarketTickerBar from "@/components/MarketTickerBar";
import ScreenerTable from "@/components/ScreenerTable";
import BreakingNews from "@/components/BreakingNews";
import MarketSentimentPanel from "@/components/MarketSentimentPanel";

export function ScreenerDashboard() {
  const router = useRouter();
  const { setTicker, analyzeTicker } = useAnalysisContext();
  return (
    <>
      <main className="pt-[120px] px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto pb-32 flex flex-col gap-8">
        {/* Section A: Market Pulse */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75" />
            </div>
            <span className="text-xs tracking-widest text-neutral-500">
              LIVE · REFRESHES EVERY 30S
            </span>
          </div>
          <MarketTickerBar />
        </section>

        {/* Top Row: Sentiment & News */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Section B: Market Sentiment */}
          <section className="md:col-span-1">
            <MarketSentimentPanel />
          </section>

          {/* Section C: News */}
          <section className="md:col-span-2">
            <BreakingNews />
          </section>
        </div>


        <ScreenerTable
          onAnalyze={(ticker) => {
            setTicker(ticker);
            analyzeTicker(ticker);
            router.push('/overview');
          }}
        />
      </main>
    </>
  );
}
