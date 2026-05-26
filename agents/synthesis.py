import logging
import numpy as np
from typing import Dict, List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from agents.base import AgentOutput

logger = logging.getLogger(__name__)

class SynthesisOutput(BaseModel):
    divergence_score: float = Field(..., description="Weighted standard deviation across agent scores.")
    highest_gap_pair: str = Field(..., description="The pair of agents with the highest score difference (e.g. 'Fundamentals vs Technical').")
    bull_thesis: str = Field(..., description="The synthesized bull thesis with cited evidence.")
    bear_thesis: str = Field(..., description="The synthesized bear thesis with cited evidence.")
    overall_score: float = Field(0.0, description="Weighted average of agent scores.")

class SynthesisAgent:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self, agent_results: Dict[str, AgentOutput]) -> SynthesisOutput:
        logger.info(f"[{self.ticker}] SynthesisAgent starting analysis...")
        try:
            # Filter out agents with invalid scores or zero confidence
            valid_agents = {}
            for name, output in agent_results.items():
                if output.score is not None and output.confidence > 0:
                    valid_agents[name] = output
            
            if len(valid_agents) < 2:
                return SynthesisOutput(
                    divergence_score=0.0,
                    highest_gap_pair="N/A",
                    bull_thesis="Insufficient data for synthesis",
                    bear_thesis="Insufficient data for synthesis"
                )

            # Calculate Divergence Score (Weighted Standard Deviation)
            # We'll use confidence as the weight
            scores = []
            weights = []
            for name, output in valid_agents.items():
                scores.append(output.score)
                weights.append(output.confidence + 0.01) # Avoid zero weight
                
            scores = np.array(scores)
            weights = np.array(weights)
            
            weighted_mean = np.average(scores, weights=weights)
            variance = np.average((scores - weighted_mean)**2, weights=weights)
            divergence_score = np.sqrt(variance)
            
            # Find highest gap pair
            max_diff = -1
            highest_pair = ""
            names = list(valid_agents.keys())
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    diff = abs(valid_agents[names[i]].score - valid_agents[names[j]].score)
                    if diff > max_diff:
                        max_diff = diff
                        highest_pair = f"{names[i].capitalize()} vs {names[j].capitalize()}"
            
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
            structured_llm = llm.with_structured_output(SynthesisOutput)
            
            # Prepare context for the LLM
            context = f"Divergence Score: {divergence_score:.2f} (0 is consensus, higher is divergent)\n"
            context += f"Highest Gap Pair: {highest_pair} (Diff: {max_diff:.2f})\n\n"
            
            for name, output in valid_agents.items():
                context += f"--- {name.upper()} AGENT ---\n"
                context += f"Score: {output.score}, Confidence: {output.confidence}\n"
                context += f"Summary: {output.summary}\n"
                context += f"Evidence:\n"
                for ev in output.evidence:
                    context += f"- {ev}\n"
                context += "\n"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are the Synthesis Agent for StockLens. Your job is to take the outputs from 5 specialized agents and generate a comprehensive Bull Thesis and Bear Thesis. You must explicitly cite the evidence from the specialized agents. Maintain the divergence_score and highest_gap_pair provided in the prompt."),
                ("user", "Synthesize the following agent reports for {ticker}:\n\n{context}")
            ])
            
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "ticker": self.ticker,
                "context": context
            })
            
            # Ensure the calculated divergence score and pair are used
            result.divergence_score = round(divergence_score, 2)
            result.highest_gap_pair = highest_pair
            result.overall_score = round(float(weighted_mean), 2)
            
            return result
        except Exception as e:
            logger.error(f"[{self.ticker}] SynthesisAgent failed: {e}")
            return SynthesisOutput(
                divergence_score=0.0,
                highest_gap_pair="Error",
                bull_thesis=f"Analysis failed: {str(e)}",
                bear_thesis=f"Analysis failed: {str(e)}",
                overall_score=0.0
            )
