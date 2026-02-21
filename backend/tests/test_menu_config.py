"""
Menu Configuration API Tests
Tests menu hide/unhide functionality for admin users
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@vantage.com"
ADMIN_PASSWORD = "admin123"

# Employee test credentials
EMPLOYEE_EMAIL = "test_employee_menu@vantage.com"
EMPLOYEE_PASSWORD = "employee123"


class TestMenuConfigBackend:
    """Test Menu Configuration API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.employee_token = None
        self.employee_id = None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        self.admin_token = data["access_token"]
        return self.admin_token
    
    def get_admin_headers(self):
        """Get headers with admin auth token"""
        return {"Authorization": f"Bearer {self.get_admin_token()}"}
    
    def create_test_employee(self):
        """Create an employee user for testing role-based menu hiding"""
        # First check if employee exists
        response = self.session.get(
            f"{BASE_URL}/api/employees",
            headers=self.get_admin_headers()
        )
        employees = response.json()
        
        for emp in employees:
            if emp.get("email") == EMPLOYEE_EMAIL:
                self.employee_id = emp["id"]
                # Login to get token
                login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
                    "email": EMPLOYEE_EMAIL,
                    "password": EMPLOYEE_PASSWORD
                })
                if login_resp.status_code == 200:
                    self.employee_token = login_resp.json()["access_token"]
                    return self.employee_id
        
        # Create new employee
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            json={
                "email": EMPLOYEE_EMAIL,
                "full_name": "Test Menu Employee",
                "password": EMPLOYEE_PASSWORD,
                "role": "employee",
                "department": "Test Department",
                "position": "Tester"
            },
            headers=self.get_admin_headers()
        )
        
        if response.status_code in [200, 201]:
            self.employee_id = response.json()["id"]
            # Login to get token
            login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": EMPLOYEE_EMAIL,
                "password": EMPLOYEE_PASSWORD
            })
            if login_resp.status_code == 200:
                self.employee_token = login_resp.json()["access_token"]
        
        return self.employee_id
    
    def get_employee_headers(self):
        """Get headers with employee auth token"""
        if not self.employee_token:
            self.create_test_employee()
        if self.employee_token:
            return {"Authorization": f"Bearer {self.employee_token}"}
        return {}
    
    # =============== GET /api/menu-config Tests ===============
    
    def test_get_menu_config_admin(self):
        """Test admin can get menu config"""
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        
        assert response.status_code == 200, f"Failed to get menu config: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "menu_items" in data
        assert isinstance(data["menu_items"], list)
        assert len(data["menu_items"]) > 0
        
        # Verify menu item structure
        first_item = data["menu_items"][0]
        assert "menu_key" in first_item
        assert "hidden_globally" in first_item
        assert "hidden_for_roles" in first_item
        
        print(f"PASS: Admin can get menu config with {len(data['menu_items'])} items")
    
    def test_get_menu_config_employee(self):
        """Test employee can get menu config (for sidebar filtering)"""
        self.create_test_employee()
        if not self.employee_token:
            pytest.skip("Could not create test employee")
        
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_employee_headers()
        )
        
        assert response.status_code == 200, f"Employee failed to get menu config: {response.text}"
        data = response.json()
        
        assert "menu_items" in data
        print(f"PASS: Employee can get menu config")
    
    def test_get_menu_config_without_auth(self):
        """Test menu config requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/menu-config")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Menu config requires authentication")
    
    def test_menu_config_has_all_default_items(self):
        """Test default menu config contains all expected items"""
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_keys = [
            "dashboard", "employees", "leaves", "attendance",
            "announcements", "calendar", "claims", "overtime",
            "payroll", "performance", "geofence", "settings", "menu-config"
        ]
        
        actual_keys = [item["menu_key"] for item in data["menu_items"]]
        
        for key in expected_keys:
            assert key in actual_keys, f"Missing menu key: {key}"
        
        print(f"PASS: All {len(expected_keys)} expected menu items present")
    
    # =============== PUT /api/menu-config Tests ===============
    
    def test_update_menu_config_admin(self):
        """Test admin can update menu config"""
        # Get current config
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        assert response.status_code == 200
        current_config = response.json()["menu_items"]
        
        # Modify one item - hide calendar globally
        modified_items = []
        for item in current_config:
            if item["menu_key"] == "calendar":
                modified_items.append({
                    "menu_key": "calendar",
                    "hidden_globally": True,
                    "hidden_for_roles": []
                })
            else:
                modified_items.append({
                    "menu_key": item["menu_key"],
                    "hidden_globally": item.get("hidden_globally", False),
                    "hidden_for_roles": item.get("hidden_for_roles", [])
                })
        
        # Update
        update_response = self.session.put(
            f"{BASE_URL}/api/menu-config",
            json={"menu_items": modified_items},
            headers=self.get_admin_headers()
        )
        
        assert update_response.status_code == 200, f"Failed to update: {update_response.text}"
        
        # Verify change persisted
        verify_response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        verify_data = verify_response.json()
        
        calendar_item = next(
            (item for item in verify_data["menu_items"] if item["menu_key"] == "calendar"), 
            None
        )
        assert calendar_item is not None
        assert calendar_item["hidden_globally"] == True
        
        print("PASS: Admin can update menu config - calendar hidden globally")
    
    def test_update_menu_config_hide_per_role(self):
        """Test hiding menu item for specific roles"""
        # Get current config
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        assert response.status_code == 200
        current_config = response.json()["menu_items"]
        
        # Hide claims for employee and manager roles
        modified_items = []
        for item in current_config:
            if item["menu_key"] == "claims":
                modified_items.append({
                    "menu_key": "claims",
                    "hidden_globally": False,
                    "hidden_for_roles": ["employee", "manager"]
                })
            else:
                modified_items.append({
                    "menu_key": item["menu_key"],
                    "hidden_globally": item.get("hidden_globally", False),
                    "hidden_for_roles": item.get("hidden_for_roles", [])
                })
        
        # Update
        update_response = self.session.put(
            f"{BASE_URL}/api/menu-config",
            json={"menu_items": modified_items},
            headers=self.get_admin_headers()
        )
        
        assert update_response.status_code == 200, f"Failed to update: {update_response.text}"
        
        # Verify change
        verify_response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        verify_data = verify_response.json()
        
        claims_item = next(
            (item for item in verify_data["menu_items"] if item["menu_key"] == "claims"), 
            None
        )
        assert claims_item is not None
        assert "employee" in claims_item["hidden_for_roles"]
        assert "manager" in claims_item["hidden_for_roles"]
        
        print("PASS: Admin can hide menu item per role - claims hidden for employee/manager")
    
    def test_update_menu_config_employee_denied(self):
        """Test employee cannot update menu config"""
        self.create_test_employee()
        if not self.employee_token:
            pytest.skip("Could not create test employee")
        
        response = self.session.put(
            f"{BASE_URL}/api/menu-config",
            json={"menu_items": [{"menu_key": "dashboard", "hidden_globally": True, "hidden_for_roles": []}]},
            headers=self.get_employee_headers()
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Employee cannot update menu config (403 Forbidden)")
    
    def test_update_menu_config_without_auth(self):
        """Test menu config update requires authentication"""
        response = self.session.put(
            f"{BASE_URL}/api/menu-config",
            json={"menu_items": [{"menu_key": "dashboard", "hidden_globally": True, "hidden_for_roles": []}]}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Menu config update requires authentication")
    
    # =============== POST /api/menu-config/reset Tests ===============
    
    def test_reset_menu_config_admin(self):
        """Test admin can reset menu config to defaults"""
        response = self.session.post(
            f"{BASE_URL}/api/menu-config/reset",
            headers=self.get_admin_headers()
        )
        
        assert response.status_code == 200, f"Failed to reset: {response.text}"
        data = response.json()
        
        assert "menu_items" in data
        assert data.get("message") == "Menu configuration reset to defaults"
        
        # Verify defaults restored
        verify_response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        verify_data = verify_response.json()
        
        # Dashboard should NOT be hidden globally by default
        dashboard_item = next(
            (item for item in verify_data["menu_items"] if item["menu_key"] == "dashboard"), 
            None
        )
        assert dashboard_item is not None
        assert dashboard_item["hidden_globally"] == False
        
        print("PASS: Admin can reset menu config to defaults")
    
    def test_reset_menu_config_employee_denied(self):
        """Test employee cannot reset menu config"""
        self.create_test_employee()
        if not self.employee_token:
            pytest.skip("Could not create test employee")
        
        response = self.session.post(
            f"{BASE_URL}/api/menu-config/reset",
            headers=self.get_employee_headers()
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Employee cannot reset menu config (403 Forbidden)")
    
    def test_reset_menu_config_without_auth(self):
        """Test menu config reset requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/menu-config/reset")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Menu config reset requires authentication")
    
    # =============== Default Configuration Tests ===============
    
    def test_default_menu_config_hides_items_per_role(self):
        """Test default config hides certain items from employee/manager roles"""
        # Reset first to get defaults
        self.session.post(
            f"{BASE_URL}/api/menu-config/reset",
            headers=self.get_admin_headers()
        )
        
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check expected default hidden items
        expected_hidden = {
            "employees": ["employee"],
            "payroll": ["employee", "manager"],
            "performance": ["employee"],
            "geofence": ["employee", "manager"],
            "menu-config": ["employee", "manager", "hr"]
        }
        
        for menu_key, expected_roles in expected_hidden.items():
            item = next(
                (i for i in data["menu_items"] if i["menu_key"] == menu_key), 
                None
            )
            assert item is not None, f"Menu item {menu_key} not found"
            for role in expected_roles:
                assert role in item.get("hidden_for_roles", []), \
                    f"{menu_key} should be hidden for {role}, but hidden_for_roles = {item.get('hidden_for_roles')}"
        
        print("PASS: Default menu config has correct per-role hiding")
    
    def test_menu_config_link_hidden_for_non_admin(self):
        """Test menu-config is hidden for employee, manager, hr by default"""
        # Reset to defaults
        self.session.post(
            f"{BASE_URL}/api/menu-config/reset",
            headers=self.get_admin_headers()
        )
        
        response = self.session.get(
            f"{BASE_URL}/api/menu-config",
            headers=self.get_admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        menu_config_item = next(
            (i for i in data["menu_items"] if i["menu_key"] == "menu-config"), 
            None
        )
        
        assert menu_config_item is not None
        assert "employee" in menu_config_item.get("hidden_for_roles", [])
        assert "manager" in menu_config_item.get("hidden_for_roles", [])
        assert "hr" in menu_config_item.get("hidden_for_roles", [])
        assert "admin" not in menu_config_item.get("hidden_for_roles", [])
        
        print("PASS: Menu Config is hidden for employee, manager, hr but visible to admin")
    
    # =============== Cleanup ===============
    
    def test_cleanup(self):
        """Reset config after tests"""
        response = self.session.post(
            f"{BASE_URL}/api/menu-config/reset",
            headers=self.get_admin_headers()
        )
        assert response.status_code == 200
        print("PASS: Cleanup - menu config reset to defaults")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
