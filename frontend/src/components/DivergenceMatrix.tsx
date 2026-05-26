"use client";

import React, { useState } from 'react';

// Mock data to match the HTML design
const agents = ['Fund.', 'Sent.', 'Insid.', 'Tech.', 'Macro'];

const matrixData = [
  [null, 0.42, 0.15, 0.51, 0.22], // Fund.
  [0.42, null, 0.85, 0.28, 0.45], // Sent.
  [0.15, 0.85, null, 0.33, 0.19], // Insid.
  [0.51, 0.28, 0.33, null, 0.72], // Tech.
  [0.22, 0.45, 0.19, 0.72, null], // Macro
];

export function DivergenceMatrix() {
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>({ row: 1, col: 2 }); // Default Sent. vs Insid. (0.85)

  const getCellClass = (val: number | null, isSelected: boolean) => {
    if (val === null) return 'bg-white/5 border border-white/5 text-white/30 cursor-default';
    
    let baseClass = '';
    if (val < 0.3) baseClass = 'bg-green-500/10 border border-green-500/20 text-green-500 hover:bg-green-500/20';
    else if (val <= 0.6) baseClass = 'bg-amber-500/10 border border-amber-500/20 text-amber-500 hover:bg-amber-500/20';
    else baseClass = 'bg-red-500/15 border border-red-500/30 text-red-500 hover:bg-red-500/25';

    if (isSelected) {
      baseClass += ' ring-1 ring-white/50 z-20 shadow-[0_0_15px_rgba(239,68,68,0.3)] transform scale-110';
    }

    return `${baseClass} transition-all duration-200 cursor-pointer`;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
      {/* Heatmap Grid Container */}
      <div className="lg:col-span-2">
        <div className="bg-surface-overlay backdrop-blur-[50px] border border-glass-border-dim rounded-xl p-8 liquid-glass">
          <div className="flex justify-between items-center mb-8">
            <div className="font-label-caps text-label-caps text-on-surface-variant tracking-widest">Divergence Matrix</div>
            <div className="flex space-x-4 font-label-caps text-[10px] text-on-surface-variant">
              <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-green-500/50 mr-2"></span> &lt; 0.3</div>
              <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-amber-500/50 mr-2"></span> 0.3 - 0.6</div>
              <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-red-500/50 mr-2"></span> &gt; 0.6</div>
            </div>
          </div>
          
          {/* Grid Setup */}
          <div className="w-full overflow-x-auto">
            <div className="min-w-[600px]">
              {/* Header Row */}
              <div className="grid grid-cols-6 gap-2 mb-2 font-label-caps text-label-caps text-on-surface-variant/50">
                <div className="flex items-center justify-end pr-4"></div>
                {agents.map((agent) => (
                  <div key={agent} className="text-center pb-2">{agent}</div>
                ))}
              </div>
              
              {/* Rows */}
              {agents.map((agentRow, rowIndex) => (
                <div key={agentRow} className="grid grid-cols-6 gap-2 mb-2">
                  <div className="flex items-center justify-end pr-4 font-label-caps text-label-caps text-on-surface-variant/50">
                    {agentRow}
                  </div>
                  {matrixData[rowIndex].map((val, colIndex) => {
                    const isSelected = selectedCell?.row === rowIndex && selectedCell?.col === colIndex;
                    return (
                      <div
                        key={`${rowIndex}-${colIndex}`}
                        onClick={() => val !== null && setSelectedCell({ row: rowIndex, col: colIndex })}
                        className={`h-16 rounded-lg flex items-center justify-center font-body-md text-sm ${getCellClass(val, isSelected)}`}
                      >
                        {val === null ? '-' : val.toFixed(2)}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detail Panel */}
      <div className="lg:col-span-1 flex flex-col">
        <div className="bg-surface-overlay backdrop-blur-[50px] border border-glass-border-dim rounded-xl p-8 flex-1 shadow-2xl relative overflow-hidden liquid-glass">
          {/* Subtle background accent for high divergence */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-[50px] -mr-16 -mt-16 pointer-events-none"></div>
          
          <div className="flex items-center justify-between mb-8 relative z-10">
            <div className="font-label-caps text-label-caps text-primary flex items-center gap-2">
              <span className="material-symbols-outlined font-light text-[16px]">warning</span>
              Critical Conflict Detected
            </div>
            <div className="px-3 py-1 rounded-full border border-white/20 text-[10px] font-label-caps uppercase text-white/50">
              ID: DIV-94A
            </div>
          </div>
          
          <div className="mb-8 relative z-10">
            <h2 className="font-headline-md text-[32px] text-primary mb-1">
              {agents[selectedCell?.row ?? 1]} <span className="text-on-surface-variant italic font-light">vs.</span> {agents[selectedCell?.col ?? 2]}
            </h2>
            <div className="flex items-center gap-4 mt-4">
              <div className="flex-1 bg-white/5 rounded-lg p-4 border border-white/5">
                <div className="font-label-caps text-label-caps text-on-surface-variant mb-1">{agents[selectedCell?.row ?? 1]} Score</div>
                <div className="font-body-lg text-body-lg text-green-400">+82 (Bullish)</div>
              </div>
              <div className="flex-1 bg-white/5 rounded-lg p-4 border border-white/5">
                <div className="font-label-caps text-label-caps text-on-surface-variant mb-1">{agents[selectedCell?.col ?? 2]} Score</div>
                <div className="font-body-lg text-body-lg text-red-400">-45 (Bearish)</div>
              </div>
            </div>
          </div>
          
          <div className="mb-8 relative z-10">
            <div className="font-label-caps text-label-caps text-on-surface-variant mb-3">Divergence Gap</div>
            <div className="flex items-end gap-3">
              <span className="font-display-lg-mobile text-[48px] text-red-500 leading-none">
                {matrixData[selectedCell?.row ?? 1][selectedCell?.col ?? 2]?.toFixed(2) ?? '0.85'}
              </span>
              <span className="text-sm text-on-surface-variant pb-1">Extremely High</span>
            </div>
            
            {/* Mini visualization of the gap */}
            <div className="h-1 w-full bg-white/10 rounded-full mt-4 overflow-hidden relative">
              <div 
                className="absolute left-0 top-0 h-full bg-gradient-to-r from-red-500/20 to-red-500/80" 
                style={{ width: `${(matrixData[selectedCell?.row ?? 1][selectedCell?.col ?? 2] ?? 0) * 100}%` }}
              ></div>
              <div 
                className="absolute top-1/2 w-2 h-2 bg-white rounded-full -translate-y-1/2 -translate-x-1/2 shadow-[0_0_10px_white]"
                style={{ left: `${(matrixData[selectedCell?.row ?? 1][selectedCell?.col ?? 2] ?? 0) * 100}%` }}
              ></div>
            </div>
          </div>
          
          <div className="space-y-4 relative z-10">
            <div className="font-label-caps text-label-caps text-on-surface-variant">Intelligence Synthesis</div>
            <p className="font-body-md text-body-md text-on-surface leading-relaxed text-sm">
              Sentiment agent is highly bullish based on social velocity, while Insider agent detects heavy selling from C-suite executives.
            </p>
            <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed text-sm mt-2 opacity-70">
              Historical correlation suggests insider selling preceding retail sentiment spikes often precedes a medium-term correction.
            </p>
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/10 relative z-10">
            <button className="w-full py-3 px-6 bg-white/5 hover:bg-white/10 border border-white/10 transition-colors rounded-lg flex items-center justify-center gap-2 font-label-caps text-label-caps text-primary">
              <span>Analyze Conflict Depth</span>
              <span className="material-symbols-outlined font-light text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
