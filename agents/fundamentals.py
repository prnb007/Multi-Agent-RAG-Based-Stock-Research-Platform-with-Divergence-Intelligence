import logging
from typing import List
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agents.base import BaseAgent, AgentOutput
from fetchers import fetch_stock_info, fetch_financials, fetch_sec_filings, read_filing_text, _list_filing_paths

logger = logging.getLogger(__name__)

class FundamentalsAgent(BaseAgent):
    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] FundamentalsAgent starting analysis...")
        try:
            # 1. Fetch Basic Info & Financials
            info = fetch_stock_info(self.ticker)
            financials = fetch_financials(self.ticker)
            
            # 2. Fetch & RAG over SEC Filings (10-K, 10-Q)
            # sec_filings downloads the filings to disk
            fetch_sec_filings(self.ticker)
            
            paths_10k = _list_filing_paths(self.ticker, "10-K")
            paths_10q = _list_filing_paths(self.ticker, "10-Q")
            all_paths = paths_10k + paths_10q
            
            documents = []
            for path in all_paths:
                text = read_filing_text(path, max_chars=100_000) # Read up to 100k chars for RAG
                if text:
                    documents.append(text)
            
            rag_context = "No SEC filings found."
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
                splits = text_splitter.create_documents(documents)
                
                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
                retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                
                query = "What is the revenue growth, margins, debt situation, and future guidance?"
                docs = retriever.invoke(query)
                rag_context = "\n\n".join([d.page_content for d in docs])
                # Clean up vectorstore for ephemeral usage
                vectorstore.delete_collection()
            
            # 3. LLM Evaluation
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            structured_llm = llm.with_structured_output(AgentOutput)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert fundamental analysis AI agent. Your job is to evaluate a stock's fundamentals, focusing on revenue growth, margins, debt, and management guidance. Return a score from -1.0 (very bearish) to +1.0 (very bullish), a confidence score (0 to 1), a short summary, and a list of evidence bullet points."),
                ("user", "Analyze {ticker}.\n\nBasic Info:\n{info}\n\nFinancials (Sample):\n{financials}\n\nSEC Filings Context (RAG):\n{rag_context}")
            ])
            
            # Convert objects to string representations to avoid token limits with huge dicts
            financials_str = str(financials)[:5000] 
            
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "ticker": self.ticker,
                "info": info.model_dump_json(),
                "financials": financials_str,
                "rag_context": rag_context
            })
            
            return result
        except Exception as e:
            logger.error(f"[{self.ticker}] FundamentalsAgent failed: {e}")
            return AgentOutput(
                score=0.0,
                confidence=0.0,
                summary=f"Analysis failed: {str(e)}",
                evidence=[]
            )
