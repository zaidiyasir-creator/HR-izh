"""
Test Dashboard Role-Based Filtering
Tests that dashboard stats (pending leaves, pending claims) are filtered by user role:
- Admin/HR: See ALL pending items
- Manager: See only their DEPARTMENT's pending items  
- Employee: See only their OWN pending items
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDashboardRoleFiltering:
    """Test dashboard stats are filtered correctly by user role"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Admin credentials
        self.admin_email = "admin@vantage.com"
        self.admin_password = "admin123"
        
        # Employee credentials
        self.employee_email = "testemployee@vantage.com"
        self.employee_password = "test123"
        
        # Get admin token
        self.admin_token = self._login(self.admin_email, self.admin_password)
        self.employee_token = self._login(self.employee_email, self.employee_password)
        
        yield
        
    def _login(self, email, password):
        """Helper to login and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def _get_headers(self, token):
        """Get headers with auth token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    # ==================== ADMIN DASHBOARD TESTS ====================
    
    def test_admin_login_success(self):
        """Test admin can login successfully"""
        assert self.admin_token is not None, "Admin login failed"
        print("PASS: Admin login successful")
    
    def test_admin_dashboard_stats_endpoint(self):
        """Test admin can access dashboard stats"""
        response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.admin_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify all expected fields are present
        assert "total_employees" in data, "Missing total_employees"
        assert "present_today" in data, "Missing present_today"
        assert "pending_leaves" in data, "Missing pending_leaves"
        assert "pending_claims" in data, "Missing pending_claims"
        assert "pending_overtime" in data, "Missing pending_overtime"
        assert "recent_leaves" in data, "Missing recent_leaves"
        assert "recent_claims" in data, "Missing recent_claims"
        assert "recent_announcements" in data, "Missing recent_announcements"
        
        print(f"PASS: Admin dashboard stats - pending_leaves={data['pending_leaves']}, pending_claims={data['pending_claims']}")
        return data
    
    def test_admin_sees_all_pending_leaves(self):
        """Test admin sees all pending leaves in the system"""
        # Get all leaves via leaves endpoint
        leaves_response = self.session.get(
            f"{BASE_URL}/api/leaves",
            headers=self._get_headers(self.admin_token)
        )
        assert leaves_response.status_code == 200
        all_leaves = leaves_response.json()
        total_pending_leaves = sum(1 for l in all_leaves if l.get("status") == "pending")
        
        # Get dashboard stats
        stats_response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.admin_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Admin should see ALL pending leaves
        assert stats["pending_leaves"] == total_pending_leaves, \
            f"Admin should see all {total_pending_leaves} pending leaves, but sees {stats['pending_leaves']}"
        print(f"PASS: Admin sees all {total_pending_leaves} pending leaves")
    
    def test_admin_sees_all_pending_claims(self):
        """Test admin sees all pending claims in the system"""
        # Get all claims via claims endpoint
        claims_response = self.session.get(
            f"{BASE_URL}/api/claims",
            headers=self._get_headers(self.admin_token)
        )
        assert claims_response.status_code == 200
        all_claims = claims_response.json()
        total_pending_claims = sum(1 for c in all_claims if c.get("status") == "pending")
        
        # Get dashboard stats
        stats_response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.admin_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Admin should see ALL pending claims
        assert stats["pending_claims"] == total_pending_claims, \
            f"Admin should see all {total_pending_claims} pending claims, but sees {stats['pending_claims']}"
        print(f"PASS: Admin sees all {total_pending_claims} pending claims")
    
    # ==================== EMPLOYEE DASHBOARD TESTS ====================
    
    def test_employee_login_success(self):
        """Test employee can login successfully"""
        assert self.employee_token is not None, "Employee login failed"
        print("PASS: Employee login successful")
    
    def test_employee_dashboard_stats_endpoint(self):
        """Test employee can access dashboard stats"""
        response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify all expected fields are present
        assert "pending_leaves" in data, "Missing pending_leaves"
        assert "pending_claims" in data, "Missing pending_claims"
        assert "recent_leaves" in data, "Missing recent_leaves"
        assert "recent_claims" in data, "Missing recent_claims"
        
        print(f"PASS: Employee dashboard stats - pending_leaves={data['pending_leaves']}, pending_claims={data['pending_claims']}")
        return data
    
    def test_employee_sees_only_own_pending_leaves(self):
        """Test employee sees only their own pending leaves"""
        # Get employee's own leaves
        leaves_response = self.session.get(
            f"{BASE_URL}/api/leaves",
            headers=self._get_headers(self.employee_token)
        )
        assert leaves_response.status_code == 200
        employee_leaves = leaves_response.json()
        employee_pending_leaves = sum(1 for l in employee_leaves if l.get("status") == "pending")
        
        # Get dashboard stats
        stats_response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Employee should see ONLY their own pending leaves (could be 0)
        assert stats["pending_leaves"] == employee_pending_leaves, \
            f"Employee should see {employee_pending_leaves} pending leaves, but sees {stats['pending_leaves']}"
        print(f"PASS: Employee sees only their own {employee_pending_leaves} pending leaves")
    
    def test_employee_sees_only_own_pending_claims(self):
        """Test employee sees only their own pending claims"""
        # Get employee's own claims
        claims_response = self.session.get(
            f"{BASE_URL}/api/claims",
            headers=self._get_headers(self.employee_token)
        )
        assert claims_response.status_code == 200
        employee_claims = claims_response.json()
        employee_pending_claims = sum(1 for c in employee_claims if c.get("status") == "pending")
        
        # Get dashboard stats
        stats_response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Employee should see ONLY their own pending claims (could be 0)
        assert stats["pending_claims"] == employee_pending_claims, \
            f"Employee should see {employee_pending_claims} pending claims, but sees {stats['pending_claims']}"
        print(f"PASS: Employee sees only their own {employee_pending_claims} pending claims")
    
    def test_employee_recent_leaves_only_own(self):
        """Test employee's recent_leaves list contains only their own leaves"""
        # Get employee info first
        me_response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers=self._get_headers(self.employee_token)
        )
        assert me_response.status_code == 200
        employee_info = me_response.json()
        employee_id = employee_info.get("id")
        
        # Get dashboard stats
        stats_response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # All recent_leaves should belong to this employee
        for leave in stats.get("recent_leaves", []):
            assert leave.get("employee_id") == employee_id, \
                f"Employee sees leave from another employee: {leave.get('employee_name')}"
        
        print(f"PASS: Employee's recent_leaves contains only their own leaves ({len(stats.get('recent_leaves', []))} items)")
    
    def test_employee_recent_claims_only_own(self):
        """Test employee's recent_claims list contains only their own claims"""
        # Get employee info first
        me_response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers=self._get_headers(self.employee_token)
        )
        assert me_response.status_code == 200
        employee_info = me_response.json()
        employee_id = employee_info.get("id")
        
        # Get dashboard stats
        stats_response = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # All recent_claims should belong to this employee
        for claim in stats.get("recent_claims", []):
            assert claim.get("employee_id") == employee_id, \
                f"Employee sees claim from another employee: {claim.get('employee_name')}"
        
        print(f"PASS: Employee's recent_claims contains only their own claims ({len(stats.get('recent_claims', []))} items)")
    
    # ==================== ROLE COMPARISON TESTS ====================
    
    def test_admin_vs_employee_pending_leaves_comparison(self):
        """Compare admin vs employee pending leaves - admin should see >= employee"""
        # Get admin stats
        admin_stats = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.admin_token)
        ).json()
        
        # Get employee stats
        employee_stats = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        ).json()
        
        # Admin should see >= employee leaves (admin sees all, employee sees own)
        assert admin_stats["pending_leaves"] >= employee_stats["pending_leaves"], \
            f"Admin ({admin_stats['pending_leaves']}) should see >= employee ({employee_stats['pending_leaves']}) pending leaves"
        
        print(f"PASS: Admin sees {admin_stats['pending_leaves']} pending leaves, Employee sees {employee_stats['pending_leaves']} (their own)")
    
    def test_admin_vs_employee_pending_claims_comparison(self):
        """Compare admin vs employee pending claims - admin should see >= employee"""
        # Get admin stats
        admin_stats = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.admin_token)
        ).json()
        
        # Get employee stats
        employee_stats = self.session.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self._get_headers(self.employee_token)
        ).json()
        
        # Admin should see >= employee claims
        assert admin_stats["pending_claims"] >= employee_stats["pending_claims"], \
            f"Admin ({admin_stats['pending_claims']}) should see >= employee ({employee_stats['pending_claims']}) pending claims"
        
        print(f"PASS: Admin sees {admin_stats['pending_claims']} pending claims, Employee sees {employee_stats['pending_claims']} (their own)")
    
    # ==================== DATA CREATION FOR TESTING ====================
    
    def test_create_leave_and_verify_role_filtering(self):
        """Create a leave as employee and verify it shows in both admin and employee dashboards"""
        # Create a leave request as employee
        start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        leave_data = {
            "leave_type": "annual",
            "start_date": start_date,
            "end_date": end_date,
            "reason": f"TEST_ROLE_FILTER_{uuid.uuid4().hex[:8]}"
        }
        
        # Create leave as employee
        create_response = self.session.post(
            f"{BASE_URL}/api/leaves",
            headers=self._get_headers(self.employee_token),
            json=leave_data
        )
        assert create_response.status_code == 200, f"Failed to create leave: {create_response.text}"
        created_leave = create_response.json()
        leave_id = created_leave.get("id")
        
        try:
            # Verify it appears in employee's dashboard
            employee_stats = self.session.get(
                f"{BASE_URL}/api/dashboard/stats",
                headers=self._get_headers(self.employee_token)
            ).json()
            
            # Verify it appears in admin's dashboard
            admin_stats = self.session.get(
                f"{BASE_URL}/api/dashboard/stats",
                headers=self._get_headers(self.admin_token)
            ).json()
            
            # Both should now have at least 1 pending leave
            assert employee_stats["pending_leaves"] >= 1, "Employee should see at least 1 pending leave after creation"
            assert admin_stats["pending_leaves"] >= 1, "Admin should see at least 1 pending leave after creation"
            
            # Admin should see >= employee
            assert admin_stats["pending_leaves"] >= employee_stats["pending_leaves"]
            
            print(f"PASS: Created leave appears in both dashboards - Admin: {admin_stats['pending_leaves']}, Employee: {employee_stats['pending_leaves']}")
            
        finally:
            # Cleanup: Approve the leave to remove from pending
            self.session.put(
                f"{BASE_URL}/api/leaves/{leave_id}",
                headers=self._get_headers(self.admin_token),
                json={"status": "approved"}
            )
    
    def test_create_claim_and_verify_role_filtering(self):
        """Create a claim as employee and verify it shows in both admin and employee dashboards"""
        claim_data = {
            "claim_type": "travel",
            "amount": 50.00,
            "description": f"TEST_ROLE_FILTER_CLAIM_{uuid.uuid4().hex[:8]}",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Create claim as employee
        create_response = self.session.post(
            f"{BASE_URL}/api/claims",
            headers=self._get_headers(self.employee_token),
            json=claim_data
        )
        assert create_response.status_code == 200, f"Failed to create claim: {create_response.text}"
        created_claim = create_response.json()
        claim_id = created_claim.get("id")
        
        try:
            # Verify it appears in employee's dashboard
            employee_stats = self.session.get(
                f"{BASE_URL}/api/dashboard/stats",
                headers=self._get_headers(self.employee_token)
            ).json()
            
            # Verify it appears in admin's dashboard
            admin_stats = self.session.get(
                f"{BASE_URL}/api/dashboard/stats",
                headers=self._get_headers(self.admin_token)
            ).json()
            
            # Both should now have at least 1 pending claim
            assert employee_stats["pending_claims"] >= 1, "Employee should see at least 1 pending claim after creation"
            assert admin_stats["pending_claims"] >= 1, "Admin should see at least 1 pending claim after creation"
            
            # Admin should see >= employee
            assert admin_stats["pending_claims"] >= employee_stats["pending_claims"]
            
            print(f"PASS: Created claim appears in both dashboards - Admin: {admin_stats['pending_claims']}, Employee: {employee_stats['pending_claims']}")
            
        finally:
            # Cleanup: Approve the claim to remove from pending
            self.session.put(
                f"{BASE_URL}/api/claims/{claim_id}",
                headers=self._get_headers(self.admin_token),
                json={"status": "approved"}
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
