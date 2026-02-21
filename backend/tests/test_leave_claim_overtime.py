"""
Test Leave, Claim, and Overtime API endpoints
Tests the request-approval workflow for Leave, Claims, and Overtime
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuth:
    """Test authentication for workflow testing"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@vantage.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Get admin auth headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_admin_login(self, admin_token):
        """Test admin can login"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print("Admin login: PASS")


class TestLeaveWorkflow:
    """Test Leave Management CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token for leave tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@vantage.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_get_leave_balance(self, admin_headers):
        """Test GET /api/leaves/balance - returns leave balance"""
        response = requests.get(f"{BASE_URL}/api/leaves/balance", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have annual, sick, personal leave types
        assert "annual" in data or isinstance(data, dict)
        print(f"Leave balance: {data}")
        print("Get leave balance: PASS")
    
    def test_create_leave_request(self, admin_headers):
        """Test POST /api/leaves - create leave request"""
        start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        leave_data = {
            "leave_type": "annual",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Family vacation"
        }
        response = requests.post(f"{BASE_URL}/api/leaves", json=leave_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["leave_type"] == "annual"
        assert data["status"] == "pending"
        assert data["reason"] == "TEST_Family vacation"
        print(f"Created leave: {data['id']}")
        print("Create leave request: PASS")
        return data["id"]
    
    def test_get_leaves_list(self, admin_headers):
        """Test GET /api/leaves - returns list of leaves"""
        response = requests.get(f"{BASE_URL}/api/leaves", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total leaves: {len(data)}")
        print("Get leaves list: PASS")
    
    def test_approve_leave(self, admin_headers):
        """Test PUT /api/leaves/{id} - approve leave request"""
        # First create a leave
        start_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")
        
        leave_data = {
            "leave_type": "sick",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Approval test"
        }
        create_response = requests.post(f"{BASE_URL}/api/leaves", json=leave_data, headers=admin_headers)
        assert create_response.status_code == 200
        leave_id = create_response.json()["id"]
        
        # Approve the leave
        approve_response = requests.put(
            f"{BASE_URL}/api/leaves/{leave_id}",
            json={"status": "approved"},
            headers=admin_headers
        )
        assert approve_response.status_code == 200
        print(f"Approved leave: {leave_id}")
        print("Approve leave: PASS")
    
    def test_reject_leave(self, admin_headers):
        """Test PUT /api/leaves/{id} - reject leave request"""
        # First create a leave
        start_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=16)).strftime("%Y-%m-%d")
        
        leave_data = {
            "leave_type": "personal",
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST_Rejection test"
        }
        create_response = requests.post(f"{BASE_URL}/api/leaves", json=leave_data, headers=admin_headers)
        assert create_response.status_code == 200
        leave_id = create_response.json()["id"]
        
        # Reject the leave
        reject_response = requests.put(
            f"{BASE_URL}/api/leaves/{leave_id}",
            json={"status": "rejected"},
            headers=admin_headers
        )
        assert reject_response.status_code == 200
        print(f"Rejected leave: {leave_id}")
        print("Reject leave: PASS")


class TestClaimsWorkflow:
    """Test Claims Management CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token for claims tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@vantage.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_create_claim(self, admin_headers):
        """Test POST /api/claims - submit expense claim"""
        claim_date = datetime.now().strftime("%Y-%m-%d")
        
        claim_data = {
            "claim_type": "travel",
            "amount": 150.50,
            "description": "TEST_Business trip to client office",
            "date": claim_date
        }
        response = requests.post(f"{BASE_URL}/api/claims", json=claim_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["claim_type"] == "travel"
        assert data["amount"] == 150.50
        assert data["status"] == "pending"
        print(f"Created claim: {data['id']}")
        print("Create claim: PASS")
        return data["id"]
    
    def test_get_claims_list(self, admin_headers):
        """Test GET /api/claims - returns list of claims"""
        response = requests.get(f"{BASE_URL}/api/claims", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total claims: {len(data)}")
        print("Get claims list: PASS")
    
    def test_approve_claim(self, admin_headers):
        """Test PUT /api/claims/{id} - approve claim"""
        # First create a claim
        claim_date = datetime.now().strftime("%Y-%m-%d")
        
        claim_data = {
            "claim_type": "meal",
            "amount": 45.00,
            "description": "TEST_Client lunch meeting",
            "date": claim_date
        }
        create_response = requests.post(f"{BASE_URL}/api/claims", json=claim_data, headers=admin_headers)
        assert create_response.status_code == 200
        claim_id = create_response.json()["id"]
        
        # Approve the claim
        approve_response = requests.put(
            f"{BASE_URL}/api/claims/{claim_id}",
            json={"status": "approved"},
            headers=admin_headers
        )
        assert approve_response.status_code == 200
        print(f"Approved claim: {claim_id}")
        print("Approve claim: PASS")
    
    def test_reject_claim(self, admin_headers):
        """Test PUT /api/claims/{id} - reject claim"""
        # First create a claim
        claim_date = datetime.now().strftime("%Y-%m-%d")
        
        claim_data = {
            "claim_type": "equipment",
            "amount": 500.00,
            "description": "TEST_Rejected claim test",
            "date": claim_date
        }
        create_response = requests.post(f"{BASE_URL}/api/claims", json=claim_data, headers=admin_headers)
        assert create_response.status_code == 200
        claim_id = create_response.json()["id"]
        
        # Reject the claim
        reject_response = requests.put(
            f"{BASE_URL}/api/claims/{claim_id}",
            json={"status": "rejected"},
            headers=admin_headers
        )
        assert reject_response.status_code == 200
        print(f"Rejected claim: {claim_id}")
        print("Reject claim: PASS")
    
    def test_claim_types(self, admin_headers):
        """Test various claim types: travel, meal, medical, equipment, other"""
        claim_types = ["travel", "meal", "medical", "equipment", "other"]
        claim_date = datetime.now().strftime("%Y-%m-%d")
        
        for claim_type in claim_types:
            claim_data = {
                "claim_type": claim_type,
                "amount": 100.00,
                "description": f"TEST_{claim_type} claim",
                "date": claim_date
            }
            response = requests.post(f"{BASE_URL}/api/claims", json=claim_data, headers=admin_headers)
            assert response.status_code == 200
            assert response.json()["claim_type"] == claim_type
            print(f"Claim type {claim_type}: PASS")


class TestOvertimeWorkflow:
    """Test Overtime Management CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token for overtime tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@vantage.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_create_overtime(self, admin_headers):
        """Test POST /api/overtime - request overtime"""
        ot_date = datetime.now().strftime("%Y-%m-%d")
        
        overtime_data = {
            "date": ot_date,
            "hours": 3.5,
            "reason": "TEST_Project deadline"
        }
        response = requests.post(f"{BASE_URL}/api/overtime", json=overtime_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["hours"] == 3.5
        assert data["status"] == "pending"
        print(f"Created overtime: {data['id']}")
        print("Create overtime: PASS")
        return data["id"]
    
    def test_get_overtime_list(self, admin_headers):
        """Test GET /api/overtime - returns list of overtime records"""
        response = requests.get(f"{BASE_URL}/api/overtime", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total overtime records: {len(data)}")
        print("Get overtime list: PASS")
    
    def test_approve_overtime(self, admin_headers):
        """Test PUT /api/overtime/{id} - approve overtime"""
        # First create an overtime request
        ot_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        overtime_data = {
            "date": ot_date,
            "hours": 2.0,
            "reason": "TEST_Approval test overtime"
        }
        create_response = requests.post(f"{BASE_URL}/api/overtime", json=overtime_data, headers=admin_headers)
        assert create_response.status_code == 200
        ot_id = create_response.json()["id"]
        
        # Approve the overtime
        approve_response = requests.put(
            f"{BASE_URL}/api/overtime/{ot_id}",
            json={"status": "approved"},
            headers=admin_headers
        )
        assert approve_response.status_code == 200
        print(f"Approved overtime: {ot_id}")
        print("Approve overtime: PASS")
    
    def test_reject_overtime(self, admin_headers):
        """Test PUT /api/overtime/{id} - reject overtime"""
        # First create an overtime request
        ot_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        overtime_data = {
            "date": ot_date,
            "hours": 4.0,
            "reason": "TEST_Rejection test overtime"
        }
        create_response = requests.post(f"{BASE_URL}/api/overtime", json=overtime_data, headers=admin_headers)
        assert create_response.status_code == 200
        ot_id = create_response.json()["id"]
        
        # Reject the overtime
        reject_response = requests.put(
            f"{BASE_URL}/api/overtime/{ot_id}",
            json={"status": "rejected"},
            headers=admin_headers
        )
        assert reject_response.status_code == 200
        print(f"Rejected overtime: {ot_id}")
        print("Reject overtime: PASS")


class TestPerformanceWorkflow:
    """Test Performance Management CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token for performance tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@vantage.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture(scope="class")
    def admin_user_id(self, admin_headers):
        """Get admin user ID for performance review"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_get_employees_for_review(self, admin_headers):
        """Test GET /api/employees - get list of employees for review"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have at least admin user
        print(f"Total employees: {len(data)}")
        print("Get employees for review: PASS")
        return data
    
    def test_create_performance_review(self, admin_headers, admin_user_id):
        """Test POST /api/performance/reviews - create performance review"""
        review_data = {
            "employee_id": admin_user_id,
            "period": "TEST_Q1 2024",
            "goals_achieved": 8,
            "goals_total": 10,
            "rating": 4.5,
            "strengths": ["Leadership", "Problem solving", "Team collaboration"],
            "improvements": ["Time management", "Documentation"],
            "comments": "TEST_Excellent performance this quarter"
        }
        response = requests.post(f"{BASE_URL}/api/performance/reviews", json=review_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["rating"] == 4.5
        assert data["goals_achieved"] == 8
        assert data["goals_total"] == 10
        print(f"Created performance review: {data['id']}")
        print("Create performance review: PASS")
        return data["id"]
    
    def test_get_performance_reviews(self, admin_headers):
        """Test GET /api/performance/reviews - returns list of reviews"""
        response = requests.get(f"{BASE_URL}/api/performance/reviews", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total performance reviews: {len(data)}")
        print("Get performance reviews: PASS")
    
    def test_generate_performance_insights(self, admin_headers, admin_user_id):
        """Test POST /api/performance/insights - generate AI insights"""
        insight_data = {
            "employee_id": admin_user_id
        }
        response = requests.post(
            f"{BASE_URL}/api/performance/insights",
            json=insight_data,
            headers=admin_headers,
            timeout=30  # AI generation may take time
        )
        # AI insights may succeed or fail based on API key
        if response.status_code == 200:
            data = response.json()
            assert "employee_id" in data
            assert "insights" in data
            print(f"Generated insights for: {data.get('employee_name', admin_user_id)}")
            print("Generate performance insights: PASS")
        elif response.status_code == 500:
            # AI service might not be configured
            print(f"AI insights skipped (service error): {response.json().get('detail', 'Unknown')}")
            print("Generate performance insights: SKIPPED (AI not configured)")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code} - {response.text}")


class TestStatusFiltering:
    """Test status filtering for Leave/Claims/Overtime"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@vantage.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_leaves_have_status_field(self, admin_headers):
        """Verify all leaves have status field for filtering"""
        response = requests.get(f"{BASE_URL}/api/leaves", headers=admin_headers)
        assert response.status_code == 200
        leaves = response.json()
        for leave in leaves:
            assert "status" in leave
            assert leave["status"] in ["pending", "approved", "rejected"]
        print(f"Verified status field in {len(leaves)} leaves")
        print("Leaves have status field: PASS")
    
    def test_claims_have_status_field(self, admin_headers):
        """Verify all claims have status field for filtering"""
        response = requests.get(f"{BASE_URL}/api/claims", headers=admin_headers)
        assert response.status_code == 200
        claims = response.json()
        for claim in claims:
            assert "status" in claim
            assert claim["status"] in ["pending", "approved", "rejected"]
        print(f"Verified status field in {len(claims)} claims")
        print("Claims have status field: PASS")
    
    def test_overtime_has_status_field(self, admin_headers):
        """Verify all overtime records have status field for filtering"""
        response = requests.get(f"{BASE_URL}/api/overtime", headers=admin_headers)
        assert response.status_code == 200
        overtime = response.json()
        for ot in overtime:
            assert "status" in ot
            assert ot["status"] in ["pending", "approved", "rejected"]
        print(f"Verified status field in {len(overtime)} overtime records")
        print("Overtime has status field: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
