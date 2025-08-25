"""
Tests for database functionality
"""

import pytest
import sqlite3
from datetime import datetime


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseManager:
    
    def test_database_initialization(self, test_db):
        """Test database creates proper schema"""
        with test_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {'notes', 'embeddings', 'expansions', 'ocr_usage'}
            assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    def test_insert_and_get_note(self, test_db, sample_notes_data):
        """Test note insertion and retrieval"""
        note_data = sample_notes_data[0]
        
        # Insert note
        success = test_db.insert_note(**note_data)
        assert success, "Failed to insert note"
        
        # Retrieve note
        retrieved = test_db.get_note(note_data["note_id"])
        assert retrieved is not None, "Failed to retrieve note"
        assert retrieved["source_file"] == note_data["source_file"]
        assert retrieved["ocr_provider"] == note_data["ocr_provider"]
        assert abs(retrieved["ocr_confidence"] - note_data["ocr_confidence"]) < 0.001

    def test_get_all_notes(self, test_db, sample_notes_data):
        """Test retrieving all notes"""
        # Insert multiple notes
        for note_data in sample_notes_data:
            test_db.insert_note(**note_data)
        
        # Get all notes
        all_notes = test_db.get_all_notes()
        assert len(all_notes) == len(sample_notes_data)
        
        # Test limit
        limited_notes = test_db.get_all_notes(limit=1)
        assert len(limited_notes) == 1

    def test_update_note_text(self, test_db, sample_notes_data):
        """Test updating note text"""
        note_data = sample_notes_data[0]
        test_db.insert_note(**note_data)
        
        new_text = "Updated clean text"
        success = test_db.update_note_text(note_data["note_id"], new_text)
        assert success
        
        retrieved = test_db.get_note(note_data["note_id"])
        assert retrieved["clean_text"] == new_text

    def test_embedding_operations(self, test_db, sample_notes_data):
        """Test embedding storage and retrieval"""
        note_data = sample_notes_data[0]
        test_db.insert_note(**note_data)
        
        # Create dummy embedding
        embedding_data = b"dummy_embedding_vector"
        
        # Insert embedding
        success = test_db.insert_embedding(note_data["note_id"], embedding_data)
        assert success
        
        # Retrieve embedding
        retrieved_embedding = test_db.get_embedding(note_data["note_id"])
        assert retrieved_embedding == embedding_data

    def test_expansion_operations(self, test_db, sample_notes_data):
        """Test expansion creation and retrieval"""
        note_data = sample_notes_data[0]
        test_db.insert_note(**note_data)
        
        prompt = "Expand this note"
        output = "This is the expanded content"
        
        # Insert expansion
        expansion_id = test_db.insert_expansion(note_data["note_id"], prompt, output)
        assert expansion_id, "Failed to create expansion"
        
        # Retrieve expansion
        expansion = test_db.get_expansion(expansion_id)
        assert expansion is not None
        assert expansion["prompt"] == prompt
        assert expansion["output"] == output
        
        # Test getting expansions for note
        expansions = test_db.get_expansions_for_note(note_data["note_id"])
        assert len(expansions) == 1
        assert expansions[0]["expansion_id"] == expansion_id

    def test_ocr_usage_tracking(self, test_db):
        """Test OCR cost tracking"""
        # Track usage
        success = test_db.track_ocr_usage("cloud_vision", 0.0015, 1)
        assert success
        
        success = test_db.track_ocr_usage("tesseract", 0.0, 5)
        assert success
        
        # Get daily costs
        costs = test_db.get_daily_ocr_cost()
        assert "cloud_vision" in costs
        assert "tesseract" in costs
        assert costs["cloud_vision"]["cost"] == 0.0015
        assert costs["tesseract"]["cost"] == 0.0

    def test_text_search(self, test_db, sample_notes_data):
        """Test text search functionality"""
        # Insert notes
        for note_data in sample_notes_data:
            test_db.insert_note(**note_data)
        
        # Search for text
        results = test_db.search_notes_by_text("OCR")
        assert len(results) > 0
        
        # Search for non-existent text
        results = test_db.search_notes_by_text("nonexistent")
        assert len(results) == 0

    def test_database_stats(self, test_db, sample_notes_data):
        """Test database statistics"""
        # Insert test data
        for note_data in sample_notes_data:
            test_db.insert_note(**note_data)
        
        test_db.track_ocr_usage("tesseract", 0.0, 1)
        test_db.track_ocr_usage("cloud_vision", 0.0015, 1)
        
        # Get stats
        stats = test_db.get_database_stats()
        
        assert stats["total_notes"] == len(sample_notes_data)
        assert "notes_by_provider" in stats
        assert "tesseract" in stats["notes_by_provider"]
        assert "cloud_vision" in stats["notes_by_provider"]
        assert stats["total_ocr_cost"] == 0.0015

    def test_error_handling(self, test_db):
        """Test error handling for invalid operations"""
        # Try to get non-existent note
        result = test_db.get_note("nonexistent")
        assert result is None
        
        # Try to get non-existent expansion
        result = test_db.get_expansion("nonexistent")
        assert result is None
        
        # Try to update non-existent note
        success = test_db.update_note_text("nonexistent", "new text")
        assert not success


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    
    def test_full_workflow(self, test_db):
        """Test complete database workflow"""
        # 1. Insert note
        note_id = "workflow_test"
        test_db.insert_note(
            note_id=note_id,
            source_file="test.png",
            raw_text="raw",
            clean_text="clean",
            ocr_provider="tesseract",
            ocr_confidence=0.8
        )
        
        # 2. Add embedding
        embedding = b"test_embedding"
        test_db.insert_embedding(note_id, embedding)
        
        # 3. Create expansion
        expansion_id = test_db.insert_expansion(note_id, "test prompt", "test output")
        
        # 4. Track usage
        test_db.track_ocr_usage("tesseract", 0.0, 1)
        
        # 5. Verify everything is connected
        note = test_db.get_note(note_id)
        assert note is not None
        
        retrieved_embedding = test_db.get_embedding(note_id)
        assert retrieved_embedding == embedding
        
        expansions = test_db.get_expansions_for_note(note_id)
        assert len(expansions) == 1
        assert expansions[0]["expansion_id"] == expansion_id
        
        stats = test_db.get_database_stats()
        assert stats["total_notes"] >= 1
        assert stats["total_expansions"] >= 1
        assert stats["total_embeddings"] >= 1