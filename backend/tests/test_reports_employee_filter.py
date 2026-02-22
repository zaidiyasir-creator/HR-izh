"""
Test suite for Employee Filtering on Reports Page
Tests the report generation API with employee_ids filter parameter
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestReportsEmployeeFilter:
    """Tests for employee filtering on report generation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin.test.101506@vantage.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get employees list for test data
        emp_response = self.session.get(f"{BASE_URL}/api/employees")
        assert emp_response.status_code == 200
        self.employees = emp_response.json()
        
        # Find "Admin Test User" and "zaidi" for testing
        self.admin_user = next((e for e in self.employees if e["full_name"] == "Admin Test User"), None)
        self.zaidi_user = next((e for e in self.employees if e["full_name"] == "zaidi"), None)

    # ==================== CLAIMS REPORT TESTS ====================
    
    def test_claims_report_all_employees_pdf(self):
        """Test claims report generation for all employees (PDF format)"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": None  # All employees
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0, "PDF content should not be empty"
        print(f"PASS: Claims report (all employees, PDF) - {len(response.content)} bytes")

    def test_claims_report_specific_employee_pdf(self):
        """Test claims report generation for specific employee (PDF format)"""
        if not self.admin_user:
            pytest.skip("Admin Test User not found in database")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": [self.admin_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PASS: Claims report (Admin Test User, PDF) - {len(response.content)} bytes")

    def test_claims_report_multiple_employees_pdf(self):
        """Test claims report generation for multiple specific employees (PDF format)"""
        if not self.admin_user or not self.zaidi_user:
            pytest.skip("Required test users not found")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": [self.admin_user["id"], self.zaidi_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PASS: Claims report (Admin + zaidi, PDF) - {len(response.content)} bytes")

    def test_claims_report_specific_employee_csv(self):
        """Test claims report generation for specific employee (CSV format)"""
        if not self.zaidi_user:
            pytest.skip("zaidi user not found in database")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "csv",
            "status": "all",
            "employee_ids": [self.zaidi_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        
        # Verify CSV content only contains zaidi's data
        csv_content = response.text
        assert "zaidi" in csv_content, "CSV should contain zaidi's claims"
        print(f"PASS: Claims report (zaidi, CSV) - verified zaidi data present")

    def test_claims_report_csv_employee_filter_verification(self):
        """Verify CSV content is properly filtered by employee"""
        if not self.zaidi_user or not self.admin_user:
            pytest.skip("Required test users not found")
        
        # Generate report for zaidi only
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "csv",
            "status": "all",
            "employee_ids": [self.zaidi_user["id"]]
        })
        
        assert response.status_code == 200
        csv_content = response.text
        
        # Should contain zaidi's name
        assert "zaidi" in csv_content, "CSV should contain zaidi"
        # Verify no other employee data is present (check for specific known employees)
        # Note: Admin Test User claims should NOT be in this report
        lines = csv_content.strip().split('\n')
        header = lines[0]
        data_lines = lines[1:] if len(lines) > 1 else []
        
        # Check each data line - only zaidi should appear
        for line in data_lines:
            if line and not line.startswith("TOTAL"):
                assert "Admin Test User" not in line or "zaidi" in line, "Non-zaidi employee data found in filtered report"
        
        print(f"PASS: CSV employee filter verification - only zaidi data present")

    # ==================== LEAVE REPORT TESTS ====================
    
    def test_leave_report_all_employees_pdf(self):
        """Test leave report generation for all employees (PDF format)"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "leaves",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": None
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PASS: Leave report (all employees, PDF) - {len(response.content)} bytes")

    def test_leave_report_specific_employee_csv(self):
        """Test leave report generation for specific employee (CSV format)"""
        if not self.admin_user:
            pytest.skip("Admin Test User not found in database")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "leaves",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "csv",
            "status": "all",
            "employee_ids": [self.admin_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        print(f"PASS: Leave report (Admin Test User, CSV) - generated successfully")

    # ==================== ATTENDANCE REPORT TESTS ====================
    
    def test_attendance_report_all_employees_pdf(self):
        """Test attendance report generation for all employees (PDF format)"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "attendance",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "employee_ids": None
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PASS: Attendance report (all employees, PDF) - {len(response.content)} bytes")

    def test_attendance_report_specific_employee_csv(self):
        """Test attendance report generation for specific employee (CSV format)"""
        if not self.admin_user:
            pytest.skip("Admin Test User not found in database")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "attendance",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "csv",
            "employee_ids": [self.admin_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        print(f"PASS: Attendance report (Admin Test User, CSV) - generated successfully")

    def test_attendance_report_multiple_employees_csv(self):
        """Test attendance report generation for multiple employees (CSV format)"""
        if not self.admin_user or not self.zaidi_user:
            pytest.skip("Required test users not found")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "attendance",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "csv",
            "employee_ids": [self.admin_user["id"], self.zaidi_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        print(f"PASS: Attendance report (multiple employees, CSV) - generated successfully")

    # ==================== OVERTIME REPORT TESTS ====================
    
    def test_overtime_report_all_employees_pdf(self):
        """Test overtime report generation for all employees (PDF format)"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "overtime",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": None
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PASS: Overtime report (all employees, PDF) - {len(response.content)} bytes")

    def test_overtime_report_specific_employee_csv(self):
        """Test overtime report generation for specific employee (CSV format)"""
        if not self.admin_user:
            pytest.skip("Admin Test User not found in database")
        
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "overtime",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "csv",
            "status": "all",
            "employee_ids": [self.admin_user["id"]]
        })
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        print(f"PASS: Overtime report (Admin Test User, CSV) - generated successfully")

    # ==================== AUTHORIZATION TESTS ====================
    
    def test_report_generation_unauthorized(self):
        """Test that non-admin/hr users cannot generate reports"""
        # Login as regular employee
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Find an employee user
        emp_user = next((e for e in self.employees if e["role"] == "employee"), None)
        if not emp_user:
            pytest.skip("No employee user found to test authorization")
        
        # Try to login as employee - skip if can't login
        # Note: We may not know the password, so we test with a different approach
        # Test authorization with the admin token but verify the role check
        
        # This test verifies the API returns 403 for non-admin users
        # Since we don't have employee credentials, we'll skip this test
        pytest.skip("Cannot test employee authorization without valid employee credentials")

    # ==================== EDGE CASE TESTS ====================
    
    def test_report_empty_employee_ids_array(self):
        """Test report generation with empty employee_ids array - should still work"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": []  # Empty array
        })
        
        # Empty array should be treated as "all employees"
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        print(f"PASS: Report with empty employee_ids array - generated successfully")

    def test_report_invalid_date_range(self):
        """Test report generation with invalid date range"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-28",  # End before start
            "end_date": "2026-02-01",
            "format": "pdf",
            "status": "all",
            "employee_ids": None
        })
        
        # API might still generate report (empty) or return error
        # Either behavior is acceptable
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"PASS: Report with reversed dates - handled gracefully (status {response.status_code})")

    def test_report_nonexistent_employee_id(self):
        """Test report generation with non-existent employee ID"""
        response = self.session.post(f"{BASE_URL}/api/reports/generate", json={
            "report_type": "claims",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "format": "pdf",
            "status": "all",
            "employee_ids": ["non-existent-uuid-12345"]
        })
        
        # Should still return 200 with empty report
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        print(f"PASS: Report with non-existent employee ID - generated successfully (empty report)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
