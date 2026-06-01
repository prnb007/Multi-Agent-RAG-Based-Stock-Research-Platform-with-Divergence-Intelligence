"use client";

import React, { useState } from 'react';
import { useAnalysis } from '@/hooks/useAnalysis';

export function DivergenceMatrix() {
  const { agents: agentsMap } = useAnalysis();
  const agentList = Object.values(agentsMap);
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null);

  if (!agentList || agentList.length < 2) {
    return (
      <div className="text-center py-16 text-neutral-500">
        Run an analysis to see the divergence matrix
      </div>
    );
  }

  const matrixData = agentList.map(a => 
    agentList.map(b => 
      a.agent === b.agent ? null : Math.abs(a.score - b.score)
    )
  );

  let defaultRow = 0;
  let defaultCol = 1;
  let maxGap = -1;
  for (let i = 0; i < agentList.length; i++) {
    for (let j = i + 1; j < agentList.length; j++) {
      const gap = Math.abs(agentList[i].score - agentList[j].score);
      if (gap > maxGap) {
        maxGap = gap;
        defaultRow = i;
        defaultCol = j;
      }
    }
  }

  const currentSelected = selectedCell || { row: defaultRow, col: defaultCol };
  const agentA = agentList[currentSelected.row];
  const agentB = agentList[currentSelected.col];
  const currentGap = Math.abs(agentA.score - agentB.score);

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
              <div className="grid gap-2 mb-2 font-label-caps text-label-caps text-on-surface-variant/50"
                   style={{ gridTemplateColumns: `100px repeat(${agentList.length}, minmax(0, 1fr))` }}>
                <div className="flex items-center justify-end pr-4"></div>
                {agentList.map((agent) => (
                  <div key={agent.agent} className="text-center pb-2 capitalize truncate">{agent.agent}</div>
                ))}
              </div>
              
              {/* Rows */}
              {agentList.map((agentRow, rowIndex) => (
                <div key={agentRow.agent} className="grid gap-2 mb-2"
                     style={{ gridTemplateColumns: `100px repeat(${agentList.length}, minmax(0, 1fr))` }}>
                  <div className="flex items-center justify-end pr-4 font-label-caps text-label-caps text-on-surface-variant/50 capitalize truncate">
                    {agentRow.agent}
                  </div>
                  {matrixData[rowIndex].map((val, colIndex) => {
                    const isSelected = currentSelected.row === rowIndex && currentSelected.col === colIndex;
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
          {currentGap >= 0.6 && (
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-[50px] -mr-16 -mt-16 pointer-events-none"></div>
          )}
          
          <div className="flex items-center justify-between mb-8 relative z-10">
            <div className={`font-label-caps text-label-caps flex items-center gap-2 ${currentGap >= 0.6 ? 'text-primary' : 'text-on-surface-variant'}`}>
              {currentGap >= 0.6 && <span className="material-symbols-outlined font-light text-[16px]">warning</span>}
              {currentGap >= 0.6 ? 'Critical Conflict Detected' : 'Agent Divergence Analysis'}
            </div>
            <div className="px-3 py-1 rounded-full border border-white/20 text-[10px] font-label-caps uppercase text-white/50">
              ID: DIV-{agentA.agent.substring(0, 2).toUpperCase()}{agentB.agent.substring(0, 2).toUpperCase()}
            </div>
          </div>
          
          <div className="mb-8 relative z-10">
            <h2 className="font-headline-md text-[32px] text-primary mb-1 capitalize">
              {agentA.agent} <span className="text-on-surface-variant italic font-light lowercase">vs.</span> {agentB.agent}
            </h2>
            <div className="flex items-center gap-4 mt-4">
              <div className="flex-1 bg-white/5 rounded-lg p-4 border border-white/5">
                <div className="font-label-caps text-label-caps text-on-surface-variant mb-1 capitalize">{agentA.agent} Score</div>
                <div className={`font-body-lg text-body-lg ${agentA.score >= 0.5 ? 'text-green-400' : 'text-red-400'}`}>
                  {agentA.score.toFixed(2)} ({agentA.score >= 0.5 ? 'Bullish' : 'Bearish'})
                </div>
              </div>
              <div className="flex-1 bg-white/5 rounded-lg p-4 border border-white/5">
                <div className="font-label-caps text-label-caps text-on-surface-variant mb-1 capitalize">{agentB.agent} Score</div>
                <div className={`font-body-lg text-body-lg ${agentB.score >= 0.5 ? 'text-green-400' : 'text-red-400'}`}>
                  {agentB.score.toFixed(2)} ({agentB.score >= 0.5 ? 'Bullish' : 'Bearish'})
                </div>
              </div>
            </div>
          </div>
          
          <div className="mb-8 relative z-10">
            <div className="font-label-caps text-label-caps text-on-surface-variant mb-3">Divergence Gap</div>
            <div className="flex items-end gap-3">
              <span className={`font-display-lg-mobile text-[48px] leading-none ${currentGap >= 0.6 ? 'text-red-500' : currentGap >= 0.3 ? 'text-amber-500' : 'text-green-500'}`}>
                {currentGap.toFixed(2)}
              </span>
              <span className="text-sm text-on-surface-variant pb-1">
                {currentGap >= 0.6 ? 'Extremely High' : currentGap >= 0.3 ? 'Moderate' : 'Low'}
              </span>
            </div>
            
            {/* Mini visualization of the gap */}
            <div className="h-1 w-full bg-white/10 rounded-full mt-4 overflow-hidden relative">
              <div 
                className={`absolute left-0 top-0 h-full bg-gradient-to-r ${currentGap >= 0.6 ? 'from-red-500/20 to-red-500/80' : currentGap >= 0.3 ? 'from-amber-500/20 to-amber-500/80' : 'from-green-500/20 to-green-500/80'}`} 
                style={{ width: `${Math.min(currentGap * 100, 100)}%` }}
              ></div>
              <div 
                className="absolute top-1/2 w-2 h-2 bg-white rounded-full -translate-y-1/2 -translate-x-1/2 shadow-[0_0_10px_white]"
                style={{ left: `${Math.min(currentGap * 100, 100)}%` }}
              ></div>
            </div>
          </div>
          
          <div className="space-y-4 relative z-10">
            <div className="font-label-caps text-label-caps text-on-surface-variant">Intelligence Synthesis</div>
            <p className="font-body-md text-body-md text-on-surface leading-relaxed text-sm">
              {agentA.agent === agentB.agent ? 'Same agent selected.' : 
                ((agentA.score >= 0.5) === (agentB.score >= 0.5) ? 
                  `Both agents are showing ${agentA.score >= 0.5 ? 'bullish' : 'bearish'} signals, suggesting alignment in their core analysis.` : 
                  `${agentA.agent} is ${agentA.score >= 0.5 ? 'bullish' : 'bearish'} while ${agentB.agent} is ${agentB.score >= 0.5 ? 'bullish' : 'bearish'} — this suggests conflicting signals from these perspectives.`
                )
              }
            </p>
          </div>
          
        </div>
      </div>
    </div>
  );
}
