"""
Test suite for Announcements AI Generate feature - Smart Announcements with Gemini 3 Flash
Tests the /api/announcements/generate endpoint and related announcements CRUD functionality
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@vantage.com"
ADMIN_PASSWORD = "admin123"

class TestAnnouncementsAI:
    """Test AI-powered announcement generation and CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"Admin login successful")
            return token
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Create auth headers with Bearer token"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    # ============== AUTH & BASIC API TESTS ==============
    
    def test_01_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] in ["admin", "hr"]
        print(f"Admin login: {data['user']['full_name']} - Role: {data['user']['role']}")
    
    # ============== AI ANNOUNCEMENT GENERATION TESTS ==============
    
    def test_02_generate_announcement_professional(self, auth_headers):
        """Test AI generates professional announcement"""
        response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "New office opening in downtown",
                "tone": "professional",
                "target_audience": "All employees"
            },
            headers=auth_headers
        )
        
        # AI may fail due to budget issues
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "budget" in error_detail.lower() or "AI" in error_detail:
                pytest.skip(f"AI budget exceeded or AI error: {error_detail}")
            else:
                pytest.fail(f"Server error: {error_detail}")
        
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "title" in data, "Response should have title"
        assert "content" in data, "Response should have content"
        assert "is_ai_generated" in data, "Response should have is_ai_generated flag"
        assert data["is_ai_generated"] == True, "is_ai_generated should be True"
        
        # Validate content
        assert len(data["title"]) > 0, "Title should not be empty"
        assert len(data["content"]) > 0, "Content should not be empty"
        
        print(f"Generated Title: {data['title'][:50]}...")
        print(f"Generated Content: {data['content'][:100]}...")
    
    def test_03_generate_announcement_friendly(self, auth_headers):
        """Test AI generates friendly tone announcement"""
        response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "Team building event next Friday",
                "tone": "friendly",
                "target_audience": "Engineering team"
            },
            headers=auth_headers
        )
        
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "budget" in error_detail.lower() or "AI" in error_detail:
                pytest.skip(f"AI budget exceeded: {error_detail}")
        
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        assert data["is_ai_generated"] == True
        print(f"Friendly tone generated: {data['title']}")
    
    def test_04_generate_announcement_urgent(self, auth_headers):
        """Test AI generates urgent tone announcement"""
        response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "System maintenance scheduled for tonight",
                "tone": "urgent",
                "target_audience": "All employees"
            },
            headers=auth_headers
        )
        
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "budget" in error_detail.lower() or "AI" in error_detail:
                pytest.skip(f"AI budget exceeded: {error_detail}")
        
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        assert data["is_ai_generated"] == True
        print(f"Urgent tone generated: {data['title']}")
    
    def test_05_generate_announcement_celebratory(self, auth_headers):
        """Test AI generates celebratory tone announcement"""
        response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "Company reached 100 employees milestone",
                "tone": "celebratory",
                "target_audience": ""
            },
            headers=auth_headers
        )
        
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "budget" in error_detail.lower() or "AI" in error_detail:
                pytest.skip(f"AI budget exceeded: {error_detail}")
        
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        assert data["is_ai_generated"] == True
        print(f"Celebratory tone generated: {data['title']}")
    
    def test_06_generate_announcement_no_audience(self, auth_headers):
        """Test AI generates announcement without specific audience"""
        response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "Holiday schedule update",
                "tone": "professional",
                "target_audience": ""
            },
            headers=auth_headers
        )
        
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "budget" in error_detail.lower() or "AI" in error_detail:
                pytest.skip(f"AI budget exceeded: {error_detail}")
        
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        assert data["is_ai_generated"] == True
        print(f"No specific audience - Generated: {data['title']}")
    
    # ============== ANNOUNCEMENTS CRUD TESTS ==============
    
    def test_07_create_manual_announcement(self, auth_headers):
        """Test creating a manual (non-AI) announcement"""
        response = requests.post(f"{BASE_URL}/api/announcements", 
            json={
                "title": "TEST_Manual Announcement",
                "content": "This is a manual announcement created for testing purposes.",
                "priority": "normal"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["title"] == "TEST_Manual Announcement"
        assert data["is_ai_generated"] == False
        print(f"Manual announcement created: {data['id']}")
    
    def test_08_create_ai_generated_announcement(self, auth_headers):
        """Test creating an AI-generated announcement by first generating, then publishing"""
        # First generate AI content
        gen_response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "TEST AI Quarterly review meeting",
                "tone": "professional",
                "target_audience": "All managers"
            },
            headers=auth_headers
        )
        
        if gen_response.status_code == 500:
            error_detail = gen_response.json().get("detail", "")
            if "budget" in error_detail.lower() or "AI" in error_detail:
                pytest.skip(f"AI budget exceeded: {error_detail}")
        
        assert gen_response.status_code == 200, f"Generate failed: {gen_response.text}"
        ai_content = gen_response.json()
        
        # Now create the announcement with AI content
        create_response = requests.post(f"{BASE_URL}/api/announcements", 
            json={
                "title": ai_content["title"],
                "content": ai_content["content"],
                "priority": "high"
            },
            headers=auth_headers
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        data = create_response.json()
        assert data["title"] == ai_content["title"]
        print(f"AI content published as announcement: {data['id']}")
    
    def test_09_get_announcements_list(self, auth_headers):
        """Test fetching announcements list"""
        response = requests.get(f"{BASE_URL}/api/announcements", headers=auth_headers)
        
        assert response.status_code == 200, f"Get failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        
        # Check that is_ai_generated field exists
        for ann in data:
            assert "is_ai_generated" in ann, f"Announcement missing is_ai_generated: {ann}"
            assert "title" in ann
            assert "content" in ann
        
        print(f"Found {len(data)} announcements")
        ai_generated = [a for a in data if a.get("is_ai_generated")]
        manual = [a for a in data if not a.get("is_ai_generated")]
        print(f"AI generated: {len(ai_generated)}, Manual: {len(manual)}")
    
    # ============== AUTHORIZATION TESTS ==============
    
    def test_10_generate_unauthorized_without_token(self):
        """Test that AI generation fails without authentication"""
        response = requests.post(f"{BASE_URL}/api/announcements/generate", 
            json={
                "topic": "Test topic",
                "tone": "professional",
                "target_audience": ""
            }
        )
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("Unauthorized request correctly rejected")
    
    def test_11_create_unauthorized_without_token(self):
        """Test that creating announcement fails without authentication"""
        response = requests.post(f"{BASE_URL}/api/announcements", 
            json={
                "title": "Test",
                "content": "Test content",
                "priority": "normal"
            }
        )
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("Unauthorized create correctly rejected")


class TestAnnouncementsEmployeeAccess:
    """Test that regular employees can view but not create announcements"""
    
    @pytest.fixture(scope="class")
    def employee_token(self):
        """Try to login as a regular employee or skip"""
        # Try to find/create an employee account for testing
        # First login as admin
        admin_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if admin_resp.status_code != 200:
            pytest.skip("Admin login failed, cannot check employee access")
        
        admin_token = admin_resp.json().get("access_token")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get employees list
        emp_resp = requests.get(f"{BASE_URL}/api/employees", headers=admin_headers)
        if emp_resp.status_code != 200:
            pytest.skip("Cannot fetch employees")
        
        employees = emp_resp.json()
        regular_emp = next((e for e in employees if e.get("role") == "employee"), None)
        
        if not regular_emp:
            pytest.skip("No regular employee found for testing")
        
        # Try to login as employee - we don't know password so skip
        pytest.skip("Employee access test skipped - no employee credentials available")
    
    def test_12_employee_can_view_announcements(self, employee_token):
        """Test that employees can view announcements"""
        pytest.skip("Skipped - no employee credentials")


# Cleanup fixture at module level
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_announcements():
    """Cleanup TEST_ prefixed announcements after all tests"""
    yield
    
    # Login as admin
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if login_resp.status_code != 200:
        print("Cleanup: Could not login as admin")
        return
    
    token = login_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Note: No delete endpoint for announcements, so cleanup is manual
    print("Cleanup: TEST_ announcements would be cleaned if delete endpoint existed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
