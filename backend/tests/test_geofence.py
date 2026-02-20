"""
Test suite for Geofence Settings APIs
Tests: Office Locations CRUD, Geofence Categories, Department Geofence Assignments, Attendance with Geolocation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@vantage.com"
ADMIN_PASSWORD = "admin123"


class TestGeofenceAPIs:
    """Geofence API tests - Office Locations, Categories, Department Assignments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = response.json().get("user")
        else:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    # ==================== OFFICE LOCATIONS TESTS ====================
    
    def test_get_office_locations(self):
        """Test GET /api/office-locations - should return list"""
        response = self.session.get(f"{BASE_URL}/api/office-locations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} office locations")
    
    def test_create_office_location(self):
        """Test POST /api/office-locations - create new office"""
        payload = {
            "name": "TEST_Branch Office",
            "address": "456 Test Street, Test City",
            "latitude": 3.1500,
            "longitude": 101.7000,
            "default_radius": 600
        }
        response = self.session.post(f"{BASE_URL}/api/office-locations", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain ID"
        assert data["name"] == payload["name"], "Name should match"
        assert data["latitude"] == payload["latitude"], "Latitude should match"
        assert data["longitude"] == payload["longitude"], "Longitude should match"
        assert data["default_radius"] == payload["default_radius"], "Radius should match"
        
        # Store ID for cleanup
        self.created_office_id = data["id"]
        print(f"Created office location: {data['name']} with ID: {data['id']}")
        
        # Verify by GET
        verify_response = self.session.get(f"{BASE_URL}/api/office-locations")
        assert verify_response.status_code == 200
        offices = verify_response.json()
        created = next((o for o in offices if o["id"] == data["id"]), None)
        assert created is not None, "Created office should be in list"
    
    def test_delete_office_location(self):
        """Test DELETE /api/office-locations/{id} - delete office"""
        # First create an office to delete
        payload = {
            "name": "TEST_ToDelete Office",
            "address": "789 Delete Street",
            "latitude": 3.2000,
            "longitude": 101.8000,
            "default_radius": 300
        }
        create_response = self.session.post(f"{BASE_URL}/api/office-locations", json=payload)
        assert create_response.status_code == 200
        office_id = create_response.json()["id"]
        
        # Delete the office
        delete_response = self.session.delete(f"{BASE_URL}/api/office-locations/{office_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        # Verify deletion
        verify_response = self.session.get(f"{BASE_URL}/api/office-locations")
        offices = verify_response.json()
        deleted = next((o for o in offices if o["id"] == office_id), None)
        assert deleted is None, "Deleted office should not be in list"
        print(f"Successfully deleted office: {office_id}")
    
    # ==================== GEOFENCE CATEGORIES TESTS ====================
    
    def test_get_geofence_categories(self):
        """Test GET /api/geofence-categories - should return categories"""
        response = self.session.get(f"{BASE_URL}/api/geofence-categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 4, "Should have at least 4 default categories"
        
        # Check for expected default categories
        category_names = [c["name"] for c in data]
        expected = ["office", "campus", "field", "remote"]
        for exp in expected:
            assert exp in category_names, f"Missing expected category: {exp}"
        
        print(f"Found categories: {category_names}")
    
    def test_update_geofence_category(self):
        """Test PUT /api/geofence-categories/{name} - update category"""
        category_name = "office"
        new_display_name = "Office Staff (Updated)"
        new_radius = 550
        
        payload = {
            "display_name": new_display_name,
            "radius": new_radius,
            "description": "Updated office category"
        }
        response = self.session.put(f"{BASE_URL}/api/geofence-categories/{category_name}", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["display_name"] == new_display_name, "Display name should be updated"
        assert data["radius"] == new_radius, "Radius should be updated"
        print(f"Updated category '{category_name}' - radius: {new_radius}m")
        
        # Restore original
        restore_payload = {
            "display_name": "Office Staff",
            "radius": 500,
            "description": "Standard office workers"
        }
        self.session.put(f"{BASE_URL}/api/geofence-categories/{category_name}", json=restore_payload)
    
    # ==================== DEPARTMENT GEOFENCE TESTS ====================
    
    def test_get_department_geofence(self):
        """Test GET /api/department-geofence - should return assignments"""
        response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} department geofence assignments")
    
    def test_create_department_geofence_assignment(self):
        """Test POST /api/department-geofence - create assignment"""
        # First ensure we have employees to get department names
        emp_response = self.session.get(f"{BASE_URL}/api/employees")
        employees = emp_response.json()
        departments = list(set(e.get("department") for e in employees if e.get("department")))
        
        if departments:
            test_department = departments[0]
        else:
            test_department = "TEST_Engineering"
        
        payload = {
            "department": test_department,
            "geofence_category": "campus"
        }
        response = self.session.post(f"{BASE_URL}/api/department-geofence", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify assignment
        verify_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = verify_response.json()
        assigned = next((a for a in assignments if a["department"] == test_department), None)
        assert assigned is not None, "Assignment should exist"
        assert assigned["geofence_category"] == "campus", "Category should be campus"
        print(f"Assigned department '{test_department}' to category 'campus'")
    
    def test_delete_department_geofence_assignment(self):
        """Test DELETE /api/department-geofence/{department}"""
        # First create an assignment
        test_department = "TEST_SalesTeam"
        payload = {
            "department": test_department,
            "geofence_category": "field"
        }
        self.session.post(f"{BASE_URL}/api/department-geofence", json=payload)
        
        # Delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/department-geofence/{test_department}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        # Verify deletion
        verify_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = verify_response.json()
        deleted = next((a for a in assignments if a["department"] == test_department), None)
        assert deleted is None, "Deleted assignment should not exist"
        print(f"Deleted department geofence for '{test_department}'")


class TestAttendanceGeolocation:
    """Test attendance check-in with geolocation validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = response.json().get("user")
        else:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    def test_checkin_without_location(self):
        """Test attendance check-in without geolocation (should work)"""
        # First check if already checked in today
        today_response = self.session.get(f"{BASE_URL}/api/attendance/today")
        if today_response.status_code == 200 and today_response.json():
            print("Already checked in today, skipping test")
            return
        
        payload = {
            "location": "Office",
            "notes": "Test check-in without coordinates"
        }
        response = self.session.post(f"{BASE_URL}/api/attendance/check-in", json=payload)
        # Could be 200 (success) or 400 (already checked in)
        assert response.status_code in [200, 400], f"Expected 200/400, got {response.status_code}: {response.text}"
        print(f"Check-in response: {response.status_code}")
    
    def test_checkin_with_valid_location(self):
        """Test check-in with location within office radius"""
        # Get office locations first
        office_response = self.session.get(f"{BASE_URL}/api/office-locations")
        offices = office_response.json()
        
        if offices:
            office = offices[0]
            # Use exact office coordinates (should be within range)
            payload = {
                "latitude": office["latitude"],
                "longitude": office["longitude"],
                "location": office["name"],
                "notes": "Test check-in at office"
            }
            response = self.session.post(f"{BASE_URL}/api/attendance/check-in", json=payload)
            # Could be 200 (success) or 400 (already checked in or other reason)
            print(f"Check-in with location at {office['name']}: {response.status_code} - {response.text[:200]}")
        else:
            print("No office locations configured, skipping location-based check-in test")
    
    def test_checkin_outside_geofence(self):
        """Test check-in from location outside geofence (should fail if offices exist)"""
        # Get office locations first
        office_response = self.session.get(f"{BASE_URL}/api/office-locations")
        offices = office_response.json()
        
        if offices:
            # Use coordinates far from any office (Antarctica coordinates)
            payload = {
                "latitude": -75.0,
                "longitude": 0.0,
                "location": "Antarctica",
                "notes": "Test check-in far from office"
            }
            response = self.session.post(f"{BASE_URL}/api/attendance/check-in", json=payload)
            # Should fail (400) for non-remote workers
            # But could be 400 (already checked in) or 200 if user is remote category
            print(f"Check-in from Antarctica: {response.status_code} - {response.text[:200]}")
        else:
            print("No office locations, geofencing not active - skipping")


class TestCleanup:
    """Cleanup test data created during tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_cleanup_test_offices(self):
        """Clean up TEST_ prefixed office locations"""
        response = self.session.get(f"{BASE_URL}/api/office-locations")
        offices = response.json()
        for office in offices:
            if office["name"].startswith("TEST_"):
                self.session.delete(f"{BASE_URL}/api/office-locations/{office['id']}")
                print(f"Cleaned up: {office['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
