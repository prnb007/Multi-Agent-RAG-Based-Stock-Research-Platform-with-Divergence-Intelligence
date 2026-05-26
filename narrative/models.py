"""
SQLite schema for narrative signals.
Stores one row per (ticker, quarter) with all 7 signals as JSON.
"""

import sqlite3
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "narrative_signals.db")


@dataclass
class NarrativeSignal:
    ticker:               str
    quarter:              str          # e.g. "2025-Q3"
    filing_date:          str          # e.g. "2025-08-01"
    management_tone:      str          # "optimistic" | "cautious" | "defensive"
    margin_language:      str          # "expanding" | "stable" | "pressured"
    ai_monetization:      str          # "strong" | "emerging" | "absent"
    demand_signals:       str          # "strong" | "mixed" | "weak"
    hiring_language:      str          # "expanding" | "stable" | "freezing"
    regulatory_concern:   str          # "high" | "moderate" | "low"
    recurring_concerns:   list[str]    # top 3 phrases of concern
    key_quotes:           list[str]    # 2-3 direct quotes from management
    confidence:           float        # 0.0-1.0, how much text was available
    raw_text_length:      int          # chars of MD&A extracted
    processed_at:         str


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS narrative_signals (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker           TEXT NOT NULL,
            quarter          TEXT NOT NULL,
            filing_date      TEXT,
            management_tone  TEXT,
            margin_language  TEXT,
            ai_monetization  TEXT,
            demand_signals   TEXT,
            hiring_language  TEXT,
            regulatory_concern TEXT,
            recurring_concerns TEXT,   -- JSON array
            key_quotes       TEXT,     -- JSON array
            confidence       REAL,
            raw_text_length  INTEGER,
            processed_at     TEXT,
            UNIQUE(ticker, quarter)
        )
    """)
    conn.commit()
    conn.close()


def save_signal(signal: NarrativeSignal):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO narrative_signals
        (ticker, quarter, filing_date, management_tone, margin_language,
         ai_monetization, demand_signals, hiring_language, regulatory_concern,
         recurring_concerns, key_quotes, confidence, raw_text_length, processed_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        signal.ticker, signal.quarter, signal.filing_date,
        signal.management_tone, signal.margin_language,
        signal.ai_monetization, signal.demand_signals,
        signal.hiring_language, signal.regulatory_concern,
        json.dumps(signal.recurring_concerns),
        json.dumps(signal.key_quotes),
        signal.confidence, signal.raw_text_length,
        signal.processed_at,
    ))
    conn.commit()
    conn.close()


def get_signals_for_ticker(ticker: str) -> list[NarrativeSignal]:
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM narrative_signals
        WHERE ticker = ?
        ORDER BY quarter ASC
    """, (ticker.upper(),)).fetchall()
    conn.close()
    return [
        NarrativeSignal(
            ticker=r["ticker"],
            quarter=r["quarter"],
            filing_date=r["filing_date"],
            management_tone=r["management_tone"],
            margin_language=r["margin_language"],
            ai_monetization=r["ai_monetization"],
            demand_signals=r["demand_signals"],
            hiring_language=r["hiring_language"],
            regulatory_concern=r["regulatory_concern"],
            recurring_concerns=json.loads(r["recurring_concerns"] or "[]"),
            key_quotes=json.loads(r["key_quotes"] or "[]"),
            confidence=r["confidence"],
            raw_text_length=r["raw_text_length"],
            processed_at=r["processed_at"],
        )
        for r in rows
    ]


def ticker_is_cached(ticker: str) -> bool:
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM narrative_signals WHERE ticker = ?",
        (ticker.upper(),)
    ).fetchone()[0]
    conn.close()
    return count >= 2  # At least 2 quarters processed


# Initialize DB on import
init_db()
