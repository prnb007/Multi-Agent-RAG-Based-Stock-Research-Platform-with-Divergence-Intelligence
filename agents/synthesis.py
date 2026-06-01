import logging
import numpy as np
from typing import Dict
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

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

    async def analyze(self, agent_results: Dict[str, any]) -> SynthesisOutput:
        logger.info(f"[{self.ticker}] SynthesisAgent starting analysis...")

        # Step 1: Normalize agent outputs to dicts
        normalized = {}
        for name, output in agent_results.items():
            if hasattr(output, 'model_dump'):
                normalized[name] = output.model_dump()
            elif isinstance(output, dict):
                normalized[name] = output
            else:
                logger.warning(f"[{self.ticker}] Skipping invalid output for agent '{name}': {type(output)}")

        # Step 2: Filter to agents with valid scores and non-zero confidence
        valid_agents = {
            name: output
            for name, output in normalized.items()
            if output.get('score') is not None and output.get('confidence', 0) > 0
        }

        logger.info(f"[{self.ticker}] Valid agents: {list(valid_agents.keys())} ({len(valid_agents)}/5)")

        if len(valid_agents) < 2:
            return SynthesisOutput(
                divergence_score=0.0,
                highest_gap_pair="N/A",
                bull_thesis="Insufficient data for synthesis",
                bear_thesis="Insufficient data for synthesis",
                overall_score=0.0
            )

        # Step 3: Compute divergence score — this never touches the LLM
        scores  = np.array([o['score'] for o in valid_agents.values()])
        weights = np.array([o.get('confidence', 0) + 0.01 for o in valid_agents.values()])

        weighted_mean   = np.average(scores, weights=weights)
        variance        = np.average((scores - weighted_mean) ** 2, weights=weights)
        divergence_score = round(float(np.sqrt(variance)), 2)
        overall_score   = round(float(weighted_mean), 2)

        names = list(valid_agents.keys())
        max_diff, highest_pair = -1, ""
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                diff = abs(valid_agents[names[i]]['score'] - valid_agents[names[j]]['score'])
                if diff > max_diff:
                    max_diff, highest_pair = diff, f"{names[i].capitalize()} vs {names[j].capitalize()}"

        logger.info(
            f"[{self.ticker}] Divergence={divergence_score}, "
            f"Gap='{highest_pair}' ({max_diff:.2f}), Overall={overall_score}"
        )

        # Step 4: LLM thesis generation — isolated so numerical results always return
        try:
            context  = f"Divergence Score: {divergence_score:.2f} (0=consensus, higher=divergent)\n"
            context += f"Highest Gap Pair: {highest_pair} (Diff: {max_diff:.2f})\n\n"

            for name, output in valid_agents.items():
                context += f"--- {name.upper()} AGENT ---\n"
                context += f"Score: {output['score']}, Confidence: {output.get('confidence', 0)}\n"
                context += f"Summary: {output.get('summary', '')}\n"
                context += "Evidence:\n"
                for ev in output.get('evidence', []):
                    context += f"- {ev}\n"
                context += "\n"

            logger.info(f"[{self.ticker}] Sending context to LLM (preview): {context[:400]}")

            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
            structured_llm = llm.with_structured_output(SynthesisOutput)

            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are the Synthesis Agent for StockLens. "
                    "Take the outputs from 5 specialized agents and generate a comprehensive "
                    "Bull Thesis and Bear Thesis, explicitly citing agent evidence. "
                    "Return the divergence_score and highest_gap_pair exactly as provided."
                )),
                ("user", "Synthesize the following agent reports for {ticker}:\n\n{context}")
            ])

            chain = prompt | structured_llm
            result = await chain.ainvoke({"ticker": self.ticker, "context": context})

            logger.info(
                f"[{self.ticker}] LLM success. "
                f"Bull preview: {result.bull_thesis[:120]} | "
                f"Bear preview: {result.bear_thesis[:120]}"
            )

            # Always override with locally computed values — LLM may drift
            result.divergence_score = divergence_score
            result.highest_gap_pair = highest_pair
            result.overall_score    = overall_score
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"[{self.ticker}] LLM thesis generation failed ({type(e).__name__}): {e}")

            # Smart fallback: derive readable thesis from agent signal data
            bullish = [(n, o) for n, o in valid_agents.items() if o.get('score', 0) >  0.3]
            bearish = [(n, o) for n, o in valid_agents.items() if o.get('score', 0) < -0.3]

            if bullish:
                parts = [
                    f"{n.capitalize()} ({o['score']:+.2f}): {o.get('summary', '')[:120]}"
                    for n, o in bullish
                ]
                bull_thesis = "Bullish signals — " + " | ".join(parts)
            else:
                bull_thesis = "No strong bullish signals detected across agents."

            if bearish:
                parts = [
                    f"{n.capitalize()} ({o['score']:+.2f}): {o.get('summary', '')[:120]}"
                    for n, o in bearish
                ]
                bear_thesis = "Bearish signals — " + " | ".join(parts)
            else:
                bear_thesis = "No strong bearish signals detected across agents."

            return SynthesisOutput(
                divergence_score=divergence_score,
                highest_gap_pair=highest_pair,
                bull_thesis=bull_thesis,
                bear_thesis=bear_thesis,
                overall_score=overall_score,
            )
