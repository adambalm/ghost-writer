"""
Database utilities for Ghost Writer - SQLite operations with enhanced schema for hybrid OCR
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "data/database/ghost_writer.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def init_database(self) -> None:
        """Initialize database with enhanced schema for hybrid OCR tracking"""
        with self.get_connection() as conn:
            # Notes table with OCR provider metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    source_file TEXT NOT NULL,
                    raw_text TEXT,
                    clean_text TEXT,
                    ocr_provider TEXT,
                    ocr_confidence REAL,
                    processing_cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Embeddings table for semantic search
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    note_id TEXT,
                    vector BLOB,
                    model_name TEXT DEFAULT 'all-MiniLM-L6-v2',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(note_id) REFERENCES notes(note_id)
                )
            """)

            # Expansions table for LLM-generated content
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expansions (
                    expansion_id TEXT PRIMARY KEY,
                    note_id TEXT,
                    prompt TEXT,
                    output TEXT,
                    llm_model TEXT DEFAULT 'llama3:latest',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(note_id) REFERENCES notes(note_id)
                )
            """)

            # OCR usage tracking for cost monitoring
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ocr_usage (
                    usage_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    cost REAL NOT NULL,
                    images_processed INTEGER DEFAULT 1,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_provider ON notes(ocr_provider)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_date ON ocr_usage(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_provider ON ocr_usage(provider)")
            
            conn.commit()
            logger.info("Database initialized successfully")

    def insert_note(self, note_id: str, source_file: str, raw_text: str, 
                   clean_text: str, ocr_provider: str, ocr_confidence: float, 
                   processing_cost: float = 0.0) -> bool:
        """Insert a new note record with OCR metadata"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO notes 
                    (note_id, source_file, raw_text, clean_text, ocr_provider, 
                     ocr_confidence, processing_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (note_id, source_file, raw_text, clean_text, 
                     ocr_provider, ocr_confidence, processing_cost))
                conn.commit()
                logger.info(f"Inserted note {note_id} from {source_file}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting note {note_id}: {e}")
            return False

    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a note by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM notes WHERE note_id = ?
                """, (note_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving note {note_id}: {e}")
            return None

    def get_all_notes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve all notes, optionally limited"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM notes ORDER BY created_at DESC"
                if limit:
                    query += f" LIMIT {limit}"
                cursor = conn.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving notes: {e}")
            return []

    def update_note_text(self, note_id: str, clean_text: str) -> bool:
        """Update cleaned text for a note"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE notes SET clean_text = ? WHERE note_id = ?
                """, (clean_text, note_id))
                conn.commit()
                # Return True only if a row was actually updated
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating note {note_id}: {e}")
            return False

    def insert_embedding(self, note_id: str, vector: bytes, model_name: str = "all-MiniLM-L6-v2") -> bool:
        """Insert embedding vector for a note"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO embeddings (note_id, vector, model_name)
                    VALUES (?, ?, ?)
                """, (note_id, vector, model_name))
                conn.commit()
                logger.info(f"Inserted embedding for note {note_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting embedding for {note_id}: {e}")
            return False

    def get_embedding(self, note_id: str) -> Optional[bytes]:
        """Retrieve embedding vector for a note"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT vector FROM embeddings WHERE note_id = ?
                """, (note_id,))
                row = cursor.fetchone()
                return row[0] if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving embedding for {note_id}: {e}")
            return None

    def insert_expansion(self, note_id: str, prompt: str, output: str, 
                        llm_model: str = "llama3:latest") -> str:
        """Insert a new expansion record, return expansion_id"""
        expansion_id = str(uuid.uuid4())
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO expansions (expansion_id, note_id, prompt, output, llm_model)
                    VALUES (?, ?, ?, ?, ?)
                """, (expansion_id, note_id, prompt, output, llm_model))
                conn.commit()
                logger.info(f"Inserted expansion {expansion_id} for note {note_id}")
                return expansion_id
        except sqlite3.Error as e:
            logger.error(f"Error inserting expansion for {note_id}: {e}")
            return ""

    def get_expansion(self, expansion_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an expansion by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM expansions WHERE expansion_id = ?
                """, (expansion_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving expansion {expansion_id}: {e}")
            return None

    def get_expansions_for_note(self, note_id: str) -> List[Dict[str, Any]]:
        """Get all expansions for a specific note"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM expansions WHERE note_id = ? ORDER BY created_at DESC
                """, (note_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving expansions for {note_id}: {e}")
            return []

    def track_ocr_usage(self, provider: str, cost: float, images_processed: int = 1) -> bool:
        """Track OCR usage for cost monitoring"""
        usage_id = str(uuid.uuid4())
        today = datetime.now().date()
        
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO ocr_usage (usage_id, provider, cost, images_processed, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (usage_id, provider, cost, images_processed, today))
                conn.commit()
                logger.info(f"Tracked {provider} usage: ${cost} for {images_processed} images")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error tracking OCR usage: {e}")
            return False

    def get_daily_ocr_cost(self, date: Optional[str] = None) -> Dict[str, float]:
        """Get OCR costs by provider for a specific date (default: today)"""
        if not date:
            date = datetime.now().date().isoformat()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT provider, SUM(cost) as total_cost, SUM(images_processed) as total_images
                    FROM ocr_usage 
                    WHERE date = ?
                    GROUP BY provider
                """, (date,))
                
                result = {}
                for row in cursor.fetchall():
                    result[row[0]] = {
                        'cost': row[1],
                        'images': row[2]
                    }
                return result
        except sqlite3.Error as e:
            logger.error(f"Error retrieving daily OCR costs: {e}")
            return {}

    def get_monthly_ocr_stats(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly OCR statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        provider,
                        SUM(cost) as total_cost,
                        SUM(images_processed) as total_images,
                        COUNT(*) as usage_count
                    FROM ocr_usage 
                    WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                    GROUP BY provider
                """, (str(year), str(month).zfill(2)))
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = {
                        'total_cost': row[1],
                        'total_images': row[2],
                        'usage_count': row[3]
                    }
                return stats
        except sqlite3.Error as e:
            logger.error(f"Error retrieving monthly OCR stats: {e}")
            return {}

    def search_notes_by_text(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Simple text search in notes (fallback for when vector search unavailable)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM notes 
                    WHERE clean_text LIKE ? OR raw_text LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (f"%{text}%", f"%{text}%", limit))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error searching notes: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Notes count by provider
                cursor = conn.execute("""
                    SELECT ocr_provider, COUNT(*) as count, AVG(ocr_confidence) as avg_confidence
                    FROM notes 
                    GROUP BY ocr_provider
                """)
                stats['notes_by_provider'] = {row[0]: {'count': row[1], 'avg_confidence': row[2]} 
                                           for row in cursor.fetchall()}
                
                # Total counts
                cursor = conn.execute("SELECT COUNT(*) FROM notes")
                stats['total_notes'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM expansions")
                stats['total_expansions'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
                stats['total_embeddings'] = cursor.fetchone()[0]
                
                # Cost totals
                cursor = conn.execute("SELECT SUM(cost) FROM ocr_usage")
                total_cost = cursor.fetchone()[0]
                stats['total_ocr_cost'] = total_cost if total_cost else 0.0
                
                return stats
        except sqlite3.Error as e:
            logger.error(f"Error retrieving database stats: {e}")
            return {}