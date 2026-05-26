import React from 'react';

export function ScreenerDashboard() {
  return (
    <>
      <main className="pt-[120px] px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto pb-32 flex flex-col gap-8">
        {/* Section A: Market Pulse */}
        <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="liquid-glass rounded-xl p-4 flex flex-col gap-2">
            <div className="text-on-surface-variant text-sm font-label-caps">S&P 500</div>
            <div className="flex items-end justify-between">
              <div className="text-xl font-bold text-primary">5,123.41</div>
              <div className="text-sm text-[#22c55e] flex items-center">
                <span className="material-symbols-outlined text-[16px]">arrow_upward</span> 0.8%
              </div>
            </div>
          </div>
          <div className="liquid-glass rounded-xl p-4 flex flex-col gap-2">
            <div className="text-on-surface-variant text-sm font-label-caps">NASDAQ</div>
            <div className="flex items-end justify-between">
              <div className="text-xl font-bold text-primary">16,234.50</div>
              <div className="text-sm text-[#22c55e] flex items-center">
                <span className="material-symbols-outlined text-[16px]">arrow_upward</span> 1.2%
              </div>
            </div>
          </div>
          <div className="liquid-glass rounded-xl p-4 flex flex-col gap-2">
            <div className="text-on-surface-variant text-sm font-label-caps">VIX</div>
            <div className="flex items-end justify-between">
              <div className="text-xl font-bold text-primary">13.24</div>
              <div className="text-sm text-[#ef4444] flex items-center">
                <span className="material-symbols-outlined text-[16px]">arrow_downward</span> 4.5%
              </div>
            </div>
          </div>
          <div className="liquid-glass rounded-xl p-4 flex flex-col gap-2">
            <div className="text-on-surface-variant text-sm font-label-caps">10Y YIELD</div>
            <div className="flex items-end justify-between">
              <div className="text-xl font-bold text-primary">4.12%</div>
              <div className="text-sm text-on-surface-variant flex items-center">
                <span className="material-symbols-outlined text-[16px]">horizontal_rule</span> 0.0%
              </div>
            </div>
          </div>
          <div className="liquid-glass rounded-xl p-4 flex flex-col gap-2">
            <div className="text-on-surface-variant text-sm font-label-caps">BITCOIN</div>
            <div className="flex items-end justify-between">
              <div className="text-xl font-bold text-primary">64,200</div>
              <div className="text-sm text-[#22c55e] flex items-center">
                <span className="material-symbols-outlined text-[16px]">arrow_upward</span> 2.1%
              </div>
            </div>
          </div>
        </section>

        {/* Top Row: Sentiment & News */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Section B: Market Sentiment */}
          <section className="liquid-glass rounded-2xl p-6 flex flex-col gap-6 md:col-span-1">
            <h2 className="font-headline-md text-2xl italic text-primary">Market Sentiment</h2>
            <div className="relative w-full aspect-[2/1] overflow-hidden flex items-end justify-center mb-4">
              <div className="w-[90%] h-[180%] rounded-full border-[16px] border-surface-container absolute top-[10%]"></div>
              <div className="w-[90%] h-[180%] rounded-full border-[16px] border-transparent border-t-[#22c55e] absolute top-[10%] rotate-45 transform origin-center transition-transform duration-1000"></div>
              <div className="flex flex-col items-center z-10 pb-4">
                <div className="text-4xl font-bold text-[#22c55e]">72</div>
                <div className="text-on-surface-variant font-label-caps tracking-widest mt-1">GREED</div>
              </div>
            </div>
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center bg-surface-container-low px-4 py-3 rounded-xl border border-glass-border-dim">
                <span className="text-sm text-on-surface-variant">Momentum</span>
                <span className="text-sm font-bold text-[#22c55e]">Strong</span>
              </div>
              <div className="flex justify-between items-center bg-surface-container-low px-4 py-3 rounded-xl border border-glass-border-dim">
                <span className="text-sm text-on-surface-variant">Breadth</span>
                <span className="text-sm font-bold text-primary">Neutral</span>
              </div>
              <div className="flex justify-between items-center bg-surface-container-low px-4 py-3 rounded-xl border border-glass-border-dim">
                <span className="text-sm text-on-surface-variant">Put/Call Ratio</span>
                <span className="text-sm font-bold text-[#22c55e]">0.82 (Bullish)</span>
              </div>
            </div>
          </section>

          {/* Section C: News */}
          <section className="md:col-span-2 flex flex-col gap-4">
            <h2 className="font-headline-md text-2xl italic text-primary">Breaking News</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
              <div className="liquid-glass rounded-xl p-5 flex flex-col justify-between group cursor-pointer hover:bg-surface-container-high transition-colors">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="px-2 py-1 bg-primary/10 text-primary text-[10px] font-label-caps rounded border border-primary/20">MACRO</span>
                    <span className="text-xs text-on-surface-variant">10m ago</span>
                  </div>
                  <h3 className="text-lg font-bold text-primary mb-2 group-hover:text-primary/80 transition-colors">Fed Signals Potential Rate Cuts Later This Year as Inflation Cools</h3>
                </div>
                <div className="text-sm text-on-surface-variant">Reuters</div>
              </div>
              <div className="liquid-glass rounded-xl p-5 flex flex-col justify-between group cursor-pointer hover:bg-surface-container-high transition-colors">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="px-2 py-1 bg-[#ef4444]/10 text-[#ef4444] text-[10px] font-label-caps rounded border border-[#ef4444]/20">TECH</span>
                    <span className="text-xs text-on-surface-variant">45m ago</span>
                  </div>
                  <h3 className="text-lg font-bold text-primary mb-2 group-hover:text-primary/80 transition-colors">Regulatory Scrutiny Increases for Major AI Developers Over Data Usage</h3>
                </div>
                <div className="text-sm text-on-surface-variant">Bloomberg</div>
              </div>
              <div className="liquid-glass rounded-xl p-5 flex flex-col justify-between group cursor-pointer hover:bg-surface-container-high transition-colors">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="px-2 py-1 bg-[#22c55e]/10 text-[#22c55e] text-[10px] font-label-caps rounded border border-[#22c55e]/20">EARNINGS</span>
                    <span className="text-xs text-on-surface-variant">2h ago</span>
                  </div>
                  <h3 className="text-lg font-bold text-primary mb-2 group-hover:text-primary/80 transition-colors">Semiconductor Giant Posts Record Q3 Revenue on Surging AI Demand</h3>
                </div>
                <div className="text-sm text-on-surface-variant">Wall Street Journal</div>
              </div>
              <div className="liquid-glass rounded-xl p-5 flex flex-col justify-between group cursor-pointer hover:bg-surface-container-high transition-colors">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="px-2 py-1 bg-primary/10 text-primary text-[10px] font-label-caps rounded border border-primary/20">ENERGY</span>
                    <span className="text-xs text-on-surface-variant">3h ago</span>
                  </div>
                  <h3 className="text-lg font-bold text-primary mb-2 group-hover:text-primary/80 transition-colors">Crude Prices Stabilize After Unrest in Middle East Disrupts Supply Chains</h3>
                </div>
                <div className="text-sm text-on-surface-variant">Financial Times</div>
              </div>
            </div>
          </section>
        </div>

        <header className="mt-8 mb-6 flex justify-between items-end border-b border-glass-border-dim pb-4">
          <div>
            <h1 className="font-headline-md text-headline-md italic text-primary">Screener</h1>
            <p className="text-on-surface-variant mt-2">142 Stocks Matched</p>
          </div>
          <div className="flex gap-4">
            <button className="liquid-glass-strong px-6 py-2 rounded-full font-label-caps text-label-caps text-primary hover:opacity-80 transition-opacity flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">filter_list</span>
              Filter
            </button>
            <button className="px-6 py-2 rounded-full border border-white/20 font-label-caps text-label-caps text-primary hover:bg-white/5 transition-all">
              Export
            </button>
          </div>
        </header>

        <div className="liquid-glass rounded-lg overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1000px]">
            <thead>
              <tr className="border-b border-glass-border-dim text-on-surface-variant font-label-caps text-label-caps uppercase">
                <th className="p-4 font-normal tracking-widest">Company</th>
                <th className="p-4 font-normal tracking-widest text-right">Last Price</th>
                <th className="p-4 font-normal tracking-widest text-right">7D Return</th>
                <th className="p-4 font-normal tracking-widest text-right">1Y Return</th>
                <th className="p-4 font-normal tracking-widest text-right">Market Cap</th>
                <th className="p-4 font-normal tracking-widest">Analysts Target</th>
                <th className="p-4 font-normal tracking-widest">Valuation</th>
                <th className="p-4 font-normal tracking-widest">Growth</th>
                <th className="p-4 font-normal tracking-widest text-right">Div Yield</th>
              </tr>
            </thead>
            <tbody>
              {/* Row 1 */}
              <tr className="border-b border-glass-border-dim hover:bg-zinc-800/30 transition-colors group cursor-pointer">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-white/30 transition-colors">
                    <span className="material-symbols-outlined text-[16px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>token</span>
                  </div>
                  <div>
                    <div className="font-bold text-primary">AAPL</div>
                    <div className="text-sm text-on-surface-variant">Apple Inc.</div>
                  </div>
                </td>
                <td className="p-4 text-right">$189.43</td>
                <td className="p-4 text-right text-[#22c55e]">+2.4%</td>
                <td className="p-4 text-right text-[#22c55e]">+18.2%</td>
                <td className="p-4 text-right">2.9T</td>
                <td className="p-4">
                  <div className="w-24 h-1.5 bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[70%]"></div>
                  </div>
                </td>
                <td className="p-4">
                  <span className="px-2 py-1 rounded-full border border-white/20 font-label-caps text-[10px] text-primary bg-surface-overlay">FAIR</span>
                </td>
                <td className="p-4">
                  <span className="material-symbols-outlined text-[#22c55e]">trending_up</span>
                </td>
                <td className="p-4 text-right">0.5%</td>
              </tr>
              {/* Row 2 */}
              <tr className="border-b border-glass-border-dim hover:bg-zinc-800/30 transition-colors group cursor-pointer">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-white/30 transition-colors">
                    <span className="material-symbols-outlined text-[16px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>cloud</span>
                  </div>
                  <div>
                    <div className="font-bold text-primary">MSFT</div>
                    <div className="text-sm text-on-surface-variant">Microsoft Corp.</div>
                  </div>
                </td>
                <td className="p-4 text-right">$376.17</td>
                <td className="p-4 text-right text-[#ef4444]">-1.2%</td>
                <td className="p-4 text-right text-[#22c55e]">+42.1%</td>
                <td className="p-4 text-right">2.8T</td>
                <td className="p-4">
                  <div className="w-24 h-1.5 bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[85%]"></div>
                  </div>
                </td>
                <td className="p-4">
                  <span className="px-2 py-1 rounded-full border border-white/20 font-label-caps text-[10px] text-primary bg-surface-overlay">OVERVALUED</span>
                </td>
                <td className="p-4">
                  <span className="material-symbols-outlined text-[#22c55e]">trending_up</span>
                </td>
                <td className="p-4 text-right">0.8%</td>
              </tr>
              {/* Row 3 */}
              <tr className="border-b border-glass-border-dim hover:bg-zinc-800/30 transition-colors group cursor-pointer">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-white/30 transition-colors">
                    <span className="material-symbols-outlined text-[16px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>shopping_cart</span>
                  </div>
                  <div>
                    <div className="font-bold text-primary">AMZN</div>
                    <div className="text-sm text-on-surface-variant">Amazon.com Inc.</div>
                  </div>
                </td>
                <td className="p-4 text-right">$146.71</td>
                <td className="p-4 text-right text-[#22c55e]">+5.1%</td>
                <td className="p-4 text-right text-[#22c55e]">+55.8%</td>
                <td className="p-4 text-right">1.5T</td>
                <td className="p-4">
                  <div className="w-24 h-1.5 bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[90%]"></div>
                  </div>
                </td>
                <td className="p-4">
                  <span className="px-2 py-1 rounded-full border border-white/20 font-label-caps text-[10px] text-primary bg-surface-overlay">UNDERVALUED</span>
                </td>
                <td className="p-4">
                  <span className="material-symbols-outlined text-[#22c55e]">trending_up</span>
                </td>
                <td className="p-4 text-right">--</td>
              </tr>
              {/* Row 4 */}
              <tr className="hover:bg-zinc-800/30 transition-colors group cursor-pointer">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-white/30 transition-colors">
                    <span className="material-symbols-outlined text-[16px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>electric_car</span>
                  </div>
                  <div>
                    <div className="font-bold text-primary">TSLA</div>
                    <div className="text-sm text-on-surface-variant">Tesla Inc.</div>
                  </div>
                </td>
                <td className="p-4 text-right">$238.45</td>
                <td className="p-4 text-right text-[#ef4444]">-4.8%</td>
                <td className="p-4 text-right text-[#ef4444]">-12.4%</td>
                <td className="p-4 text-right">750B</td>
                <td className="p-4">
                  <div className="w-24 h-1.5 bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[40%]"></div>
                  </div>
                </td>
                <td className="p-4">
                  <span className="px-2 py-1 rounded-full border border-white/20 font-label-caps text-[10px] text-primary bg-surface-overlay">OVERVALUED</span>
                </td>
                <td className="p-4">
                  <span className="material-symbols-outlined text-[#ef4444]">trending_down</span>
                </td>
                <td className="p-4 text-right">--</td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
