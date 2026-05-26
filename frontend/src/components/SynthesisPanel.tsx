import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { SynthesisData, AgentData } from '@/hooks/useAnalysis';
interface SynthesisPanelProps {
  synthesis: SynthesisData;
  agents: Record<string, AgentData>;
}

export function SynthesisPanel({ synthesis, agents }: SynthesisPanelProps) {
  const [displayScore, setDisplayScore] = React.useState(0);

  React.useEffect(() => {
    let startTime: number;
    const duration = 1000;
    
    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 4);
      setDisplayScore(synthesis.divergence_score * ease);
      
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        setDisplayScore(synthesis.divergence_score);
      }
    };
    
    requestAnimationFrame(step);
  }, [synthesis.divergence_score]);

  const getStatus = (score: number) => {
    if (score < 0.3) return { label: 'Consensus', color: 'text-green-500', icon: 'check_circle' };
    if (score <= 0.6) return { label: 'Mild Divergence', color: 'text-amber-500', icon: 'warning' };
    return { label: 'High Conflict', color: 'text-red-500', icon: 'warning' };
  };
  const status = getStatus(synthesis.divergence_score);
  
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px] text-primary">monitoring</span>
            Divergence Intelligence
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Divergence Score</p>
              <h3 className="text-3xl font-bold">{displayScore.toFixed(2)}</h3>
            </div>
            <div className={`flex items-center gap-2 ${status.color}`}>
              <span className="material-symbols-outlined text-[24px]">{status.icon}</span>
              <span className="font-semibold">{status.label}</span>
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-muted-foreground mb-2">Highest Gap Pair</h4>
            <div className="p-3 bg-secondary rounded text-sm font-medium">
              {synthesis.highest_gap_pair}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Synthesis Thesis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h4 className="flex items-center gap-2 text-green-500 font-semibold mb-2">
              <span className="material-symbols-outlined text-[16px]">trending_up</span> Bull Thesis
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {synthesis.bull_thesis}
            </p>
          </div>
          <div className="h-px bg-border w-full" />
          <div>
            <h4 className="flex items-center gap-2 text-red-500 font-semibold mb-2">
              <span className="material-symbols-outlined text-[16px]">trending_down</span> Bear Thesis
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {synthesis.bear_thesis}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
