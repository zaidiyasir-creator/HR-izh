"""
Test suite for Departments CRUD APIs
Tests: Create, Read, Update, Delete departments with geofence integration
Feature: When adding employees, department dropdown shows only configured departments
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@vantage.com"
ADMIN_PASSWORD = "admin123"


class TestDepartmentsCRUD:
    """Departments CRUD API tests - Create, Read, Update, Delete"""
    
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
    
    # ==================== GET DEPARTMENTS ====================
    
    def test_get_departments(self):
        """Test GET /api/departments - should return list of departments"""
        response = self.session.get(f"{BASE_URL}/api/departments")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} departments: {[d['name'] for d in data]}")
        
        # Verify structure of each department
        if data:
            dept = data[0]
            assert "id" in dept, "Department should have id"
            assert "name" in dept, "Department should have name"
            assert "geofence_category" in dept, "Department should have geofence_category"
    
    def test_existing_departments_have_correct_structure(self):
        """Test that existing departments have all required fields"""
        response = self.session.get(f"{BASE_URL}/api/departments")
        assert response.status_code == 200
        
        data = response.json()
        expected_depts = ["Engineering", "Sales", "Remote Team"]
        
        for dept_name in expected_depts:
            dept = next((d for d in data if d["name"] == dept_name), None)
            if dept:
                print(f"Found department: {dept_name} - category: {dept.get('geofence_category')}")
                assert "id" in dept
                assert "name" in dept
                assert "geofence_category" in dept
    
    # ==================== CREATE DEPARTMENT ====================
    
    def test_create_department_with_office_category(self):
        """Test POST /api/departments - create new department with office geofence"""
        unique_name = f"TEST_Marketing_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Marketing and communications team",
            "geofence_category": "office"
        }
        response = self.session.post(f"{BASE_URL}/api/departments", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert data["name"] == unique_name, "Name should match"
        assert data["description"] == payload["description"], "Description should match"
        assert data["geofence_category"] == "office", "Geofence category should be office"
        
        # Verify department-geofence assignment was created
        geofence_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = geofence_response.json()
        assignment = next((a for a in assignments if a["department"] == unique_name), None)
        assert assignment is not None, "Department-geofence assignment should be created automatically"
        assert assignment["geofence_category"] == "office", "Assignment category should be office"
        
        print(f"Created department: {unique_name} with office geofence (id: {data['id']})")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/departments/{data['id']}")
    
    def test_create_department_with_remote_category(self):
        """Test creating department with remote geofence (unlimited radius)"""
        unique_name = f"TEST_Remote_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Remote work team",
            "geofence_category": "remote"
        }
        response = self.session.post(f"{BASE_URL}/api/departments", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["geofence_category"] == "remote", "Geofence category should be remote"
        
        # Verify auto-created geofence assignment
        geofence_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = geofence_response.json()
        assignment = next((a for a in assignments if a["department"] == unique_name), None)
        assert assignment is not None, "Auto-created geofence assignment should exist"
        assert assignment["geofence_category"] == "remote", "Assignment should be remote"
        
        print(f"Created remote department: {unique_name} (unlimited geofence)")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/departments/{data['id']}")
    
    def test_create_department_with_field_category(self):
        """Test creating department with field geofence (5000m radius)"""
        unique_name = f"TEST_Field_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Field workers team",
            "geofence_category": "field"
        }
        response = self.session.post(f"{BASE_URL}/api/departments", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["geofence_category"] == "field"
        print(f"Created field department: {unique_name}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/departments/{data['id']}")
    
    def test_create_duplicate_department_fails(self):
        """Test that creating a department with existing name fails"""
        # First get existing departments
        response = self.session.get(f"{BASE_URL}/api/departments")
        departments = response.json()
        
        if departments:
            existing_name = departments[0]["name"]
            payload = {
                "name": existing_name,
                "description": "Duplicate test",
                "geofence_category": "office"
            }
            response = self.session.post(f"{BASE_URL}/api/departments", json=payload)
            assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
            assert "already exists" in response.text.lower(), "Should indicate department exists"
            print(f"Correctly rejected duplicate department: {existing_name}")
    
    # ==================== UPDATE DEPARTMENT ====================
    
    def test_update_department_name(self):
        """Test PUT /api/departments/{id} - update department name"""
        # Create a test department first
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "description": "Original description",
            "geofence_category": "office"
        }
        create_response = self.session.post(f"{BASE_URL}/api/departments", json=create_payload)
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        
        # Update the department name
        new_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
        update_payload = {
            "name": new_name,
            "description": "Updated description"
        }
        response = self.session.put(f"{BASE_URL}/api/departments/{dept_id}", json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == new_name, "Name should be updated"
        assert data["description"] == "Updated description", "Description should be updated"
        
        # Verify geofence assignment was updated
        geofence_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = geofence_response.json()
        
        # Old assignment should not exist
        old_assignment = next((a for a in assignments if a["department"] == unique_name), None)
        assert old_assignment is None, "Old geofence assignment should be deleted"
        
        # New assignment should exist
        new_assignment = next((a for a in assignments if a["department"] == new_name), None)
        assert new_assignment is not None, "New geofence assignment should exist"
        
        print(f"Updated department from {unique_name} to {new_name}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/departments/{dept_id}")
    
    def test_update_department_geofence_category(self):
        """Test updating department's geofence category"""
        # Create a test department
        unique_name = f"TEST_GeoUpdate_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "description": "Test",
            "geofence_category": "office"
        }
        create_response = self.session.post(f"{BASE_URL}/api/departments", json=create_payload)
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        
        # Update geofence category to remote
        update_payload = {
            "geofence_category": "remote"
        }
        response = self.session.put(f"{BASE_URL}/api/departments/{dept_id}", json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["geofence_category"] == "remote", "Geofence category should be updated"
        
        # Verify geofence assignment was updated
        geofence_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = geofence_response.json()
        assignment = next((a for a in assignments if a["department"] == unique_name), None)
        assert assignment is not None, "Geofence assignment should exist"
        assert assignment["geofence_category"] == "remote", "Assignment category should be updated"
        
        print(f"Updated {unique_name} geofence from office to remote")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/departments/{dept_id}")
    
    def test_update_nonexistent_department(self):
        """Test updating a department that doesn't exist"""
        fake_id = str(uuid.uuid4())
        update_payload = {
            "name": "Doesn't exist",
            "geofence_category": "office"
        }
        response = self.session.put(f"{BASE_URL}/api/departments/{fake_id}", json=update_payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Correctly returned 404 for non-existent department")
    
    # ==================== DELETE DEPARTMENT ====================
    
    def test_delete_empty_department(self):
        """Test DELETE /api/departments/{id} - delete department with no employees"""
        # Create a test department
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "description": "To be deleted",
            "geofence_category": "office"
        }
        create_response = self.session.post(f"{BASE_URL}/api/departments", json=create_payload)
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        
        # Delete the department
        response = self.session.delete(f"{BASE_URL}/api/departments/{dept_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/departments")
        departments = get_response.json()
        deleted = next((d for d in departments if d["id"] == dept_id), None)
        assert deleted is None, "Deleted department should not exist"
        
        # Verify geofence assignment was also deleted
        geofence_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = geofence_response.json()
        assignment = next((a for a in assignments if a["department"] == unique_name), None)
        assert assignment is None, "Geofence assignment should be deleted"
        
        print(f"Successfully deleted department: {unique_name}")
    
    def test_delete_department_with_employees_fails(self):
        """Test that deleting department with employees fails"""
        # Get existing departments
        response = self.session.get(f"{BASE_URL}/api/departments")
        departments = response.json()
        
        # Get employees
        emp_response = self.session.get(f"{BASE_URL}/api/employees")
        employees = emp_response.json()
        
        # Find a department that has employees
        for dept in departments:
            dept_employees = [e for e in employees if e.get("department") == dept["name"]]
            if dept_employees:
                # Try to delete this department
                delete_response = self.session.delete(f"{BASE_URL}/api/departments/{dept['id']}")
                assert delete_response.status_code == 400, f"Expected 400, got {delete_response.status_code}"
                assert "employee" in delete_response.text.lower(), "Should mention employees"
                print(f"Correctly prevented deletion of '{dept['name']}' (has {len(dept_employees)} employees)")
                return
        
        print("No departments with employees found - skipping test")
    
    def test_delete_nonexistent_department(self):
        """Test deleting a department that doesn't exist"""
        fake_id = str(uuid.uuid4())
        response = self.session.delete(f"{BASE_URL}/api/departments/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Correctly returned 404 for non-existent department")


class TestEmployeeDepartmentDropdown:
    """Test that employee add/edit forms get departments from /api/departments"""
    
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
    
    def test_departments_api_returns_configured_departments_only(self):
        """Verify /api/departments returns only configured departments"""
        response = self.session.get(f"{BASE_URL}/api/departments")
        assert response.status_code == 200
        
        departments = response.json()
        print(f"Configured departments: {[d['name'] for d in departments]}")
        
        # All returned departments should have required fields
        for dept in departments:
            assert "id" in dept, f"Department {dept.get('name')} missing id"
            assert "name" in dept, f"Department missing name"
            assert "geofence_category" in dept, f"Department {dept.get('name')} missing geofence_category"
    
    def test_create_employee_with_configured_department(self):
        """Test creating employee with a configured department"""
        # Get configured departments
        dept_response = self.session.get(f"{BASE_URL}/api/departments")
        departments = dept_response.json()
        
        if not departments:
            pytest.skip("No departments configured")
        
        # Use the first configured department
        test_dept = departments[0]["name"]
        unique_email = f"test.emp.{uuid.uuid4().hex[:6]}@vantage.com"
        
        payload = {
            "email": unique_email,
            "full_name": "TEST Employee Dept Test",
            "password": "Welcome123!",
            "role": "employee",
            "department": test_dept,
            "position": "Tester"
        }
        response = self.session.post(f"{BASE_URL}/api/employees", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["department"] == test_dept, f"Department should be {test_dept}"
        
        print(f"Created employee in department: {test_dept}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/employees/{data['id']}")
    
    def test_update_employee_department(self):
        """Test updating employee to a different configured department"""
        # Get configured departments
        dept_response = self.session.get(f"{BASE_URL}/api/departments")
        departments = dept_response.json()
        
        if len(departments) < 2:
            pytest.skip("Need at least 2 departments for this test")
        
        dept1 = departments[0]["name"]
        dept2 = departments[1]["name"]
        
        # Create test employee
        unique_email = f"test.update.{uuid.uuid4().hex[:6]}@vantage.com"
        create_payload = {
            "email": unique_email,
            "full_name": "TEST Employee Update Dept",
            "password": "Welcome123!",
            "role": "employee",
            "department": dept1,
            "position": "Tester"
        }
        create_response = self.session.post(f"{BASE_URL}/api/employees", json=create_payload)
        assert create_response.status_code == 200
        emp_id = create_response.json()["id"]
        
        # Update to different department
        update_payload = {
            "department": dept2
        }
        update_response = self.session.put(f"{BASE_URL}/api/employees/{emp_id}", json=update_payload)
        assert update_response.status_code == 200
        
        updated_emp = update_response.json()
        assert updated_emp["department"] == dept2, f"Department should be {dept2}"
        
        print(f"Updated employee department from {dept1} to {dept2}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/employees/{emp_id}")


class TestDepartmentGeofenceSync:
    """Test that creating department auto-creates geofence assignment"""
    
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
        else:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    def test_department_auto_creates_geofence_assignment(self):
        """Test that POST /api/departments auto-creates department_geofence entry"""
        unique_name = f"TEST_AutoGeo_{uuid.uuid4().hex[:6]}"
        
        # Get initial geofence assignments
        initial_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        initial_assignments = initial_response.json()
        initial_count = len(initial_assignments)
        
        # Create new department
        create_payload = {
            "name": unique_name,
            "description": "Test auto-geofence",
            "geofence_category": "campus"
        }
        create_response = self.session.post(f"{BASE_URL}/api/departments", json=create_payload)
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        
        # Check geofence assignments now
        after_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        after_assignments = after_response.json()
        
        # Should have one more assignment
        assert len(after_assignments) == initial_count + 1, "Should have one more geofence assignment"
        
        # Find the new assignment
        new_assignment = next((a for a in after_assignments if a["department"] == unique_name), None)
        assert new_assignment is not None, "New department should have geofence assignment"
        assert new_assignment["geofence_category"] == "campus", "Assignment should be campus"
        
        print(f"Department {unique_name} auto-created geofence assignment with category: campus")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/departments/{dept_id}")
    
    def test_department_delete_removes_geofence_assignment(self):
        """Test that DELETE /api/departments also removes geofence assignment"""
        unique_name = f"TEST_DelGeo_{uuid.uuid4().hex[:6]}"
        
        # Create department
        create_payload = {
            "name": unique_name,
            "description": "Test delete geofence",
            "geofence_category": "field"
        }
        create_response = self.session.post(f"{BASE_URL}/api/departments", json=create_payload)
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        
        # Verify geofence exists
        geo_response = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments = geo_response.json()
        exists = any(a["department"] == unique_name for a in assignments)
        assert exists, "Geofence assignment should exist after department creation"
        
        # Delete department
        delete_response = self.session.delete(f"{BASE_URL}/api/departments/{dept_id}")
        assert delete_response.status_code == 200
        
        # Verify geofence is also deleted
        geo_response_after = self.session.get(f"{BASE_URL}/api/department-geofence")
        assignments_after = geo_response_after.json()
        exists_after = any(a["department"] == unique_name for a in assignments_after)
        assert not exists_after, "Geofence assignment should be deleted with department"
        
        print(f"Confirmed: deleting department {unique_name} also removed geofence assignment")


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
    
    def test_cleanup_test_departments(self):
        """Clean up TEST_ prefixed departments"""
        response = self.session.get(f"{BASE_URL}/api/departments")
        departments = response.json()
        cleaned = 0
        for dept in departments:
            if dept["name"].startswith("TEST_"):
                delete_response = self.session.delete(f"{BASE_URL}/api/departments/{dept['id']}")
                if delete_response.status_code == 200:
                    print(f"Cleaned up department: {dept['name']}")
                    cleaned += 1
        print(f"Cleaned up {cleaned} test departments")
    
    def test_cleanup_test_employees(self):
        """Clean up TEST_ prefixed employees"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        employees = response.json()
        cleaned = 0
        for emp in employees:
            if emp.get("full_name", "").startswith("TEST ") or emp.get("email", "").startswith("test."):
                delete_response = self.session.delete(f"{BASE_URL}/api/employees/{emp['id']}")
                if delete_response.status_code == 200:
                    print(f"Cleaned up employee: {emp['full_name']}")
                    cleaned += 1
        print(f"Cleaned up {cleaned} test employees")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
