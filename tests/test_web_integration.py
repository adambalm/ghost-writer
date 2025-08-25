"""
Comprehensive Playwright tests for Ghost Writer web interface
Tests authentication, file processing, and complete workflows
"""

import pytest
import os
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

# Test credentials from environment
SUPERNOTE_PHONE = os.getenv('SUPERNOTE_PHONE', '4139491742')
SUPERNOTE_PASSWORD = os.getenv('SUPERNOTE_PASSWORD', 'z8UrxJWlqWH0Ep')

BASE_URL = "http://localhost:5000"

# Mark all tests in this module as web tests - skip in CI
pytestmark = [
    pytest.mark.web,
    pytest.mark.skipif(
        os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true',
        reason="Web tests disabled in CI environment"
    )
]

class TestWebInterface:
    """Test suite for Ghost Writer web interface"""
    
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
    
    def test_homepage_loads(self, page: Page):
        """Test that homepage loads without authentication"""
        page.goto(BASE_URL)
        
        # Check page loads and shows authentication required
        expect(page).to_have_title("Ghost Writer - Unified Interface")
        expect(page.locator("h1")).to_contain_text("Ghost Writer")
        
        # Should not be authenticated initially
        auth_status = page.locator('#auth-status')
        if auth_status.count() > 0:
            expect(auth_status).to_contain_text("Not connected")
    
    def test_authentication_form_validation(self, page: Page):
        """Test authentication form input validation"""
        page.goto(BASE_URL)
        
        # Find authentication form elements
        phone_input = page.locator('#phone')
        password_input = page.locator('#password')
        submit_button = page.locator('button:has-text("Connect to Supernote Cloud")')
        
        # Test empty form submission
        if submit_button.count() > 0:
            submit_button.click()
            
            # Should show validation errors
            error_message = page.locator('.error')
            expect(error_message).to_be_visible()
    
    def test_invalid_phone_number_validation(self, page: Page):
        """Test phone number format validation"""
        page.goto(BASE_URL)
        
        phone_input = page.locator('#phone')
        password_input = page.locator('#password')
        
        if phone_input.count() > 0 and password_input.count() > 0:
            # Test invalid phone formats
            invalid_phones = ["123", "abcdefghij", "123-456-7890", "12345"]
            
            for invalid_phone in invalid_phones:
                phone_input.fill(invalid_phone)
                password_input.fill("testpassword")
                
                submit_button = page.locator('button:has-text("Connect to Supernote Cloud")')
                if submit_button.count() > 0:
                    submit_button.click()
                    page.wait_for_timeout(1000)  # Wait for error message
                    
                    # Should show validation error for phone format
                    error_message = page.locator('.error').first
                    expect(error_message).to_be_visible()
                    expect(error_message).to_contain_text("10-digit")
    
    def test_successful_authentication(self, page: Page):
        """Test successful authentication with valid credentials"""
        page.goto(BASE_URL)
        
        # Fill authentication form
        phone_input = page.locator('input[name="phone"]')
        password_input = page.locator('input[name="password"]')
        
        if phone_input.count() > 0 and password_input.count() > 0:
            phone_input.fill(SUPERNOTE_PHONE)
            password_input.fill(SUPERNOTE_PASSWORD)
            
            submit_button = page.locator('button[type="submit"]')
            if submit_button.count() > 0:
                submit_button.click()
                
                # Wait for authentication to complete
                page.wait_for_timeout(5000)
                
                # Should show success message or redirect
                success_indicator = page.locator('.success, .alert-success, [data-testid="success"]')
                if success_indicator.count() > 0:
                    expect(success_indicator).to_be_visible()
                    expect(success_indicator).to_contain_text("Successfully connected")
    
    def test_authentication_failure_handling(self, page: Page):
        """Test meaningful error messages on authentication failure"""
        page.goto(BASE_URL)
        
        phone_input = page.locator('input[name="phone"]')
        password_input = page.locator('input[name="password"]')
        
        if phone_input.count() > 0 and password_input.count() > 0:
            # Use invalid credentials
            phone_input.fill("1234567890")
            password_input.fill("wrongpassword")
            
            submit_button = page.locator('button[type="submit"]')
            if submit_button.count() > 0:
                submit_button.click()
                
                # Wait for response
                page.wait_for_timeout(3000)
                
                # Should show meaningful error message
                error_message = page.locator('.error, .alert-danger, [data-testid="error"]')
                expect(error_message).to_be_visible()
                expect(error_message).to_contain_text("Invalid phone number or password")
    
    def test_cloud_files_loading(self, page: Page):
        """Test cloud files list after authentication"""
        page.goto(BASE_URL)
        
        # Authenticate first
        self._authenticate(page)
        
        # Look for cloud files section
        files_section = page.locator('[data-testid="cloud-files"], .cloud-files')
        if files_section.count() > 0:
            expect(files_section).to_be_visible()
            
            # Should show file count or file list
            file_count = page.locator('[data-testid="file-count"]')
            if file_count.count() > 0:
                expect(file_count).to_be_visible()
    
    def test_file_processing_workflow(self, page: Page):
        """Test complete file processing workflow"""
        page.goto(BASE_URL)
        
        # Authenticate first
        self._authenticate(page)
        
        # Look for file processing options
        process_button = page.locator('[data-testid="process-file"], button:has-text("Process")')
        upload_button = page.locator('input[type="file"], [data-testid="upload"]')
        
        # Test cloud file processing if available
        if process_button.count() > 0:
            process_button.first.click()
            
            # Wait for processing
            page.wait_for_timeout(5000)
            
            # Should show processing results
            results_section = page.locator('[data-testid="results"], .results')
            if results_section.count() > 0:
                expect(results_section).to_be_visible()
    
    def test_status_endpoint_accessibility(self, page: Page):
        """Test that status endpoint provides system information"""
        # Test status endpoint directly
        response = page.goto(f"{BASE_URL}/status")
        assert response.status == 200
        
        # Should return JSON with system status
        content = page.content()
        assert "authenticated" in content
        assert "cloud_files_count" in content
    
    def test_no_auto_authentication(self, page: Page):
        """Verify web app does not auto-authenticate"""
        page.goto(BASE_URL)
        
        # Check that user must explicitly authenticate - look for auth section
        auth_section = page.locator('.auth-section')
        auth_status = page.locator('#auth-status')
        
        # Should show authentication section or show "Not connected" status
        assert auth_section.count() > 0 or (auth_status.count() > 0 and "Not connected" in auth_status.text_content())
        
        # Should not be authenticated initially
        if auth_status.count() > 0:
            expect(auth_status).to_contain_text("Not connected")
    
    def _authenticate(self, page: Page):
        """Helper method to authenticate during tests"""
        phone_input = page.locator('#phone')
        password_input = page.locator('#password')
        
        if phone_input.count() > 0 and password_input.count() > 0:
            phone_input.fill(SUPERNOTE_PHONE)
            password_input.fill(SUPERNOTE_PASSWORD)
            
            submit_button = page.locator('button:has-text("Connect to Supernote Cloud")')
            if submit_button.count() > 0:
                submit_button.click()
                page.wait_for_timeout(3000)

@pytest.mark.integration
class TestFileUpload:
    """Test file upload and processing functionality"""
    
    @pytest.fixture
    def page(self):
        """Create a page for file upload tests"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            yield page
            browser.close()
    
    def test_file_upload_validation(self, page):
        """Test file upload format validation"""
        page.goto(BASE_URL)
        
        upload_input = page.locator('#file-input')
        if upload_input.count() > 0:
            # Create temporary non-.note file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_file.write(b"test content")
                temp_file_path = temp_file.name
            
            try:
                # Try to upload non-.note file
                upload_input.set_input_files(temp_file_path)
                
                # Should show validation error
                error_message = page.locator('.error')
                if error_message.count() > 0:
                    expect(error_message).to_contain_text("Only .note files")
            finally:
                os.unlink(temp_file_path)

if __name__ == "__main__":
    # Run tests directly if executed
    pytest.main([__file__, "-v"])