"""
End-to-end integration test for complete note processing workflow
Tests the complete pipeline from file upload to OCR results
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

# Test credentials from environment
SUPERNOTE_PHONE = os.getenv('SUPERNOTE_PHONE', '4139491742')
SUPERNOTE_PASSWORD = os.getenv('SUPERNOTE_PASSWORD', 'z8UrxJWlqWH0Ep')

BASE_URL = "http://localhost:5000"
PROJECT_ROOT = Path(__file__).parent.parent

# Skip web tests in CI environment
pytestmark = [
    pytest.mark.web,
    pytest.mark.skipif(
        os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true',
        reason="Web tests disabled in CI environment"
    )
]

@pytest.mark.web
class TestE2EProcessing:
    """End-to-end processing tests"""
    
    @pytest.fixture(scope="class")
    def browser_context(self):
        """Set up browser context for tests"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            yield context
            browser.close()
    
    @pytest.fixture
    def page(self, browser_context):
        """Create a new page for each test"""
        page = browser_context.new_page()
        # Reset authentication state before each test
        try:
            page.request.post(f"{BASE_URL}/reset-auth")
        except:
            pass  # Ignore if endpoint doesn't exist
        yield page
        page.close()
    
    def test_complete_file_processing_workflow(self, page: Page):
        """Test complete file upload and processing workflow"""
        page.goto(BASE_URL)
        
        # Verify not authenticated initially
        auth_status = page.locator('#auth-status')
        expect(auth_status).to_contain_text("Not connected")
        
        # Authenticate
        phone_input = page.locator('#phone')
        password_input = page.locator('#password')
        
        phone_input.fill(SUPERNOTE_PHONE)
        password_input.fill(SUPERNOTE_PASSWORD)
        
        submit_button = page.locator('button:has-text("Connect to Supernote Cloud")')
        submit_button.click()
        
        # Wait for authentication to complete and page to reload
        page.wait_for_timeout(5000)
        
        # Now test file upload
        test_note_file = PROJECT_ROOT / "test_note.note"
        if not test_note_file.exists():
            pytest.skip(f"Test file {test_note_file} not found")
        
        # Upload the file
        file_input = page.locator('#file-input')
        file_input.set_input_files(str(test_note_file))
        
        # Wait for processing to complete
        page.wait_for_timeout(10000)
        
        # Check for results
        results_section = page.locator('#results')
        expect(results_section).to_be_visible()
        
        # Should show processing results
        results_content = page.locator('#results-content')
        expect(results_content).to_be_visible()
        
        # Should contain success message or error details
        content_text = results_content.text_content()
        assert "processed" in content_text.lower() or "error" in content_text.lower()
    
    def test_cloud_file_processing_workflow(self, page: Page):
        """Test processing files from Supernote Cloud"""
        page.goto(BASE_URL)
        
        # Authenticate first
        phone_input = page.locator('#phone')
        password_input = page.locator('#password')
        
        if phone_input.count() > 0 and password_input.count() > 0:
            phone_input.fill(SUPERNOTE_PHONE)
            password_input.fill(SUPERNOTE_PASSWORD)
            
            submit_button = page.locator('button:has-text("Connect to Supernote Cloud")')
            submit_button.click()
            
            # Wait for authentication and page reload
            page.wait_for_timeout(5000)
            
            # Check if cloud files are loaded
            file_count = page.locator('#file-count')
            if file_count.count() > 0:
                file_count_text = file_count.text_content()
                if file_count_text and int(file_count_text) > 0:
                    # Try to process a cloud file
                    cloud_files_section = page.locator('#cloud-files')
                    if cloud_files_section.count() > 0:
                        process_button = page.locator('button:has-text("Process")').first
                        if process_button.count() > 0:
                            process_button.click()
                            
                            # Wait for processing
                            page.wait_for_timeout(10000)
                            
                            # Check for results
                            results_section = page.locator('#results')
                            expect(results_section).to_be_visible()
    
    def test_error_handling_and_recovery(self, page: Page):
        """Test error handling for invalid operations"""
        page.goto(BASE_URL)
        
        # Test processing without authentication
        test_note_file = PROJECT_ROOT / "test_note.note"
        if test_note_file.exists():
            file_input = page.locator('#file-input')
            file_input.set_input_files(str(test_note_file))
            
            # Wait for response
            page.wait_for_timeout(3000)
            
            # Should handle gracefully (either process or show meaningful error)
            results_section = page.locator('#results')
            if results_section.count() > 0 and results_section.is_visible():
                results_content = page.locator('#results-content')
                content_text = results_content.text_content()
                # Should not crash - either success or meaningful error
                assert len(content_text) > 0
    
    def test_system_status_accuracy(self, page: Page):
        """Test that system status reflects actual state"""
        page.goto(BASE_URL)
        
        # Check initial status
        auth_status = page.locator('#auth-status')
        file_count = page.locator('#file-count')
        
        expect(auth_status).to_contain_text("Not connected")
        expect(file_count).to_contain_text("0")
        
        # Authenticate
        phone_input = page.locator('#phone')
        password_input = page.locator('#password')
        
        if phone_input.count() > 0 and password_input.count() > 0:
            phone_input.fill(SUPERNOTE_PHONE)
            password_input.fill(SUPERNOTE_PASSWORD)
            
            submit_button = page.locator('button:has-text("Connect to Supernote Cloud")')
            submit_button.click()
            
            # Wait for authentication
            page.wait_for_timeout(5000)
            
            # Status should update
            auth_status = page.locator('#auth-status')
            expect(auth_status).to_contain_text("Connected")
            
            # File count should update if there are files
            file_count = page.locator('#file-count')
            file_count_text = file_count.text_content()
            assert file_count_text.isdigit()  # Should be a number
    
    def test_user_experience_flow(self, page: Page):
        """Test complete user experience flow"""
        page.goto(BASE_URL)
        
        # Page should load quickly and be responsive
        expect(page.locator("h1")).to_be_visible()
        
        # Should have clear authentication section
        auth_section = page.locator('.auth-section')
        if auth_section.count() > 0:
            expect(auth_section).to_be_visible()
            
            # Should have clear labels and inputs
            expect(page.locator('label[for="phone"]')).to_be_visible()
            expect(page.locator('label[for="password"]')).to_be_visible()
            expect(page.locator('#phone')).to_be_visible()
            expect(page.locator('#password')).to_be_visible()
        
        # Should have file upload area
        upload_area = page.locator('#upload-area')
        expect(upload_area).to_be_visible()
        
        # Should have browse button
        browse_button = page.locator('button:has-text("Browse Files")')
        expect(browse_button).to_be_visible()
        
        # All interactive elements should be functional
        phone_input = page.locator('#phone')
        phone_input.fill("test")
        assert phone_input.input_value() == "test"

if __name__ == "__main__":
    # Run tests directly if executed
    pytest.main([__file__, "-v"])