import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';

export interface AgentResult {
  agent: string;
  score: number;
  confidence: number;
  summary: string;
  evidence: string[];
}

export interface DivergencePanelProps {
  agents: AgentResult[];
  divergenceScore: number;
  highestGapPair: string;
}

const AGENT_ORDER = ['fundamentals', 'sentiment', 'insider', 'technical', 'macro'];

export function DivergencePanel({ agents, divergenceScore, highestGapPair }: DivergencePanelProps) {
  const [selectedPair, setSelectedPair] = useState<[AgentResult, AgentResult] | null>(null);
  const [displayScore, setDisplayScore] = useState(0);

  React.useEffect(() => {
    let startTime: number;
    const duration = 1000;
    
    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 4); // easeOutQuart
      setDisplayScore(divergenceScore * ease);
      
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        setDisplayScore(divergenceScore); // Ensure exact final value
      }
    };
    
    requestAnimationFrame(step);
  }, [divergenceScore]);

  // Ensure we have exactly these 5 agents in order, if they exist in the props
  const orderedAgents = AGENT_ORDER.map(name => agents.find(a => a.agent.toLowerCase() === name)).filter(Boolean) as AgentResult[];

  const getConsensusLabel = (score: number) => {
    if (score < 0.3) return { label: 'Consensus', color: 'text-green-500' };
    if (score <= 0.6) return { label: 'Mild Divergence', color: 'text-amber-500' };
    return { label: 'High Conflict', color: 'text-red-500' };
  };

  const status = getConsensusLabel(divergenceScore);

  const getGapColor = (gap: number) => {
    if (gap < 0.3) return 'bg-green-500/20 hover:bg-green-500/30 text-green-500';
    if (gap <= 0.6) return 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-500';
    return 'bg-red-500/20 hover:bg-red-500/30 text-red-500';
  };

  const getExplanation = (agent1: AgentResult, agent2: AgentResult) => {
    const isBullish1 = agent1.score >= 0.5;
    const isBullish2 = agent2.score >= 0.5;
    const name1 = agent1.agent.charAt(0).toUpperCase() + agent1.agent.slice(1);
    const name2 = agent2.agent.charAt(0).toUpperCase() + agent2.agent.slice(1);

    const attitude1 = isBullish1 ? 'bullish' : 'bearish';
    const attitude2 = isBullish2 ? 'bullish' : 'bearish';

    if (attitude1 === attitude2) {
       return `${name1} and ${name2} are both ${attitude1} (${agent1.score.toFixed(2)} and ${agent2.score.toFixed(2)}), showing alignment in their core analysis.`;
    } else {
       return `${name1} is ${attitude1} (${agent1.score.toFixed(2)}) while ${name2} is ${attitude2} (${agent2.score.toFixed(2)}) — this suggests conflicting signals from these perspectives.`;
    }
  };

  if (orderedAgents.length === 0) {
    return <div className="p-8 text-center text-muted-foreground">Waiting for agent data...</div>;
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Top Summary Bar */}
      <div className="flex items-center justify-between p-6 bg-card/50 backdrop-blur-sm border rounded-xl shadow-sm">
        <div>
          <p className="text-sm font-medium text-muted-foreground mb-1">Overall Divergence Score</p>
          <div className="flex items-baseline gap-3">
            <h3 className="text-4xl font-bold tracking-tight">{displayScore.toFixed(2)}</h3>
            <span className={`font-semibold text-lg ${status.color}`}>
              {status.label}
            </span>
          </div>
        </div>
        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium text-muted-foreground mb-1">Highest Gap Pair</p>
          <p className="text-lg font-medium bg-secondary/50 px-3 py-1 rounded-md">{highestGapPair || "N/A"}</p>
        </div>
      </div>

      <div className="flex justify-center overflow-x-auto pb-4">
        <div 
          className="grid gap-1" 
          style={{ gridTemplateColumns: `100px repeat(${orderedAgents.length}, minmax(80px, 1fr))` }}
        >
          {/* Header Row */}
          <div className="h-20" /> {/* Empty top-left cell */}
          {orderedAgents.map(colAgent => (
            <div 
              key={`header-col-${colAgent.agent}`} 
              className="h-20 flex flex-col items-center justify-end pb-2 text-xs font-semibold tracking-wider uppercase text-muted-foreground"
            >
              <span className="truncate w-full text-center px-1">
                {colAgent.agent.substring(0, 4)}
              </span>
            </div>
          ))}

          {/* Grid Rows */}
          {orderedAgents.map(rowAgent => (
            <React.Fragment key={`row-${rowAgent.agent}`}>
              <div className="h-20 flex items-center justify-end pr-4 text-xs font-semibold tracking-wider uppercase text-muted-foreground">
                {rowAgent.agent}
              </div>
              {orderedAgents.map(colAgent => {
                const isDiagonal = rowAgent.agent === colAgent.agent;
                const gap = Math.abs(rowAgent.score - colAgent.score) / 2.0;
                
                if (isDiagonal) {
                  return (
                    <div 
                      key={`cell-${rowAgent.agent}-${colAgent.agent}`} 
                      className="h-20 w-full min-w-[80px] rounded-md border border-border/10 bg-muted/30 flex items-center justify-center text-muted-foreground/30 pointer-events-none"
                    >
                      -
                    </div>
                  );
                }

                const isSelected = selectedPair?.[0].agent === rowAgent.agent && selectedPair?.[1].agent === colAgent.agent;

                return (
                  <button
                    key={`cell-${rowAgent.agent}-${colAgent.agent}`}
                    onClick={() => setSelectedPair([rowAgent, colAgent])}
                    title={`${rowAgent.agent.toUpperCase()} vs ${colAgent.agent.toUpperCase()}\nGap: ${gap.toFixed(2)}\n\n${getExplanation(rowAgent, colAgent)}`}
                    className={`h-20 w-full min-w-[80px] rounded-md border border-border/50 transition-all duration-150 flex flex-col items-center justify-center font-mono text-base font-medium cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background hover:scale-[1.08] hover:shadow-md hover:z-20 ${getGapColor(gap)} ${isSelected ? 'ring-2 ring-primary scale-[1.08] shadow-lg z-10' : ''}`}
                  >
                    {gap.toFixed(2)}
                  </button>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Expanded Detail Panel */}
      {selectedPair && (
        <div className="animate-in fade-in slide-in-from-top-8 duration-500">
          <Card className="bg-card/50 backdrop-blur-sm border-primary/20 shadow-lg overflow-hidden relative">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
            <CardContent className="p-6 sm:p-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                <h4 className="text-2xl font-bold flex items-center gap-3">
                  <span className="capitalize">{selectedPair[0].agent}</span>
                  <span className="text-muted-foreground text-sm font-normal italic px-2">vs</span>
                  <span className="capitalize">{selectedPair[1].agent}</span>
                </h4>
                <div className="flex flex-col items-end">
                  <p className="text-sm font-medium text-muted-foreground mb-1 uppercase tracking-wider">Calculated Gap</p>
                  <p className="font-mono text-3xl font-bold text-primary">
                    {(Math.abs(selectedPair[0].score - selectedPair[1].score) / 2.0).toFixed(2)}
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 sm:gap-8 mb-8">
                <div className="bg-secondary/30 p-4 rounded-xl border border-border/50">
                  <span className="text-muted-foreground uppercase text-xs font-semibold tracking-wider block mb-2">{selectedPair[0].agent} Score</span>
                  <p className="font-mono text-2xl">{selectedPair[0].score.toFixed(2)}</p>
                </div>
                <div className="bg-secondary/30 p-4 rounded-xl border border-border/50">
                  <span className="text-muted-foreground uppercase text-xs font-semibold tracking-wider block mb-2">{selectedPair[1].agent} Score</span>
                  <p className="font-mono text-2xl">{selectedPair[1].score.toFixed(2)}</p>
                </div>
              </div>

              <div className="p-5 bg-primary/5 rounded-xl text-base leading-relaxed border border-primary/10 text-foreground/90">
                {getExplanation(selectedPair[0], selectedPair[1])}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
