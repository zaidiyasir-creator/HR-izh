import requests
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

class VantageHRTester:
    def __init__(self):
        # Get base URL from frontend .env
        env_path = Path("/app/frontend/.env")
        self.base_url = None
        
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        self.base_url = line.split("=", 1)[1].strip()
                        break
        
        if not self.base_url:
            self.base_url = "https://attendance-geo-test.preview.emergentagent.com"
        
        self.token = None
        self.admin_user_id = None
        self.employee_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_result(self, test_name, success, details=""):
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            self.failed_tests.append({"test": test_name, "details": details})
            print(f"❌ {test_name}: FAILED {details}")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            success = response.status_code == expected_status
            result_data = {}
            
            try:
                result_data = response.json() if response.content else {}
            except:
                result_data = {"text": response.text}
            
            return success, result_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_health_check(self):
        success, data, status = self.make_request('GET', '/', expected_status=200)
        self.log_result("Health Check", success, f"Status: {status}")
        return success

    def test_register_admin(self):
        test_data = {
            "email": f"admin.test.{datetime.now().strftime('%H%M%S')}@vantage.com",
            "password": "AdminPass123!",
            "full_name": "Admin Test User",
            "role": "admin"
        }
        
        success, data, status = self.make_request('POST', 'auth/register', test_data, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.admin_user_id = data['user']['id']
            self.log_result("Admin Registration", True, f"Token received, User ID: {self.admin_user_id}")
            return True
        else:
            self.log_result("Admin Registration", False, f"Status: {status}, Response: {data}")
            return False

    def test_login(self):
        # Try login with demo credentials
        test_data = {
            "email": "admin@vantage.com", 
            "password": "admin123"
        }
        
        success, data, status = self.make_request('POST', 'auth/login', test_data, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.admin_user_id = data['user']['id']
            self.log_result("Login Test", True, f"Logged in as {data['user']['full_name']}")
            return True
        else:
            self.log_result("Login Test", False, f"Status: {status}, Response: {data}")
            return False

    def test_auth_me(self):
        success, data, status = self.make_request('GET', 'auth/me', expected_status=200)
        self.log_result("Auth Me", success, f"User: {data.get('full_name', 'N/A')}")
        return success

    def test_dashboard_stats(self):
        success, data, status = self.make_request('GET', 'dashboard/stats', expected_status=200)
        if success:
            required_fields = ['total_employees', 'present_today', 'pending_leaves', 'pending_claims']
            has_fields = all(field in data for field in required_fields)
            self.log_result("Dashboard Stats", has_fields, f"Fields: {list(data.keys())}")
            return has_fields
        else:
            self.log_result("Dashboard Stats", False, f"Status: {status}")
            return False

    def test_create_employee(self):
        test_data = {
            "email": f"emp.test.{datetime.now().strftime('%H%M%S')}@vantage.com",
            "full_name": "Test Employee",
            "role": "employee", 
            "department": "Engineering",
            "position": "Software Developer",
            "phone": "+1234567890",
            "salary": 75000.0
        }
        
        success, data, status = self.make_request('POST', 'employees', test_data, 200)
        
        if success and 'id' in data:
            self.employee_id = data['id']
            self.log_result("Create Employee", True, f"Employee ID: {self.employee_id}")
            return True
        else:
            self.log_result("Create Employee", False, f"Status: {status}, Response: {data}")
            return False

    def test_get_employees(self):
        success, data, status = self.make_request('GET', 'employees', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_result("Get Employees", True, f"Found {len(data)} employees")
            return True
        else:
            self.log_result("Get Employees", False, f"Status: {status}")
            return False

    def test_leave_request(self):
        if not self.employee_id:
            self.log_result("Leave Request", False, "No employee ID available")
            return False
            
        test_data = {
            "leave_type": "annual",
            "start_date": (datetime.now() + timedelta(days=7)).date().isoformat(),
            "end_date": (datetime.now() + timedelta(days=10)).date().isoformat(),
            "reason": "Vacation test"
        }
        
        success, data, status = self.make_request('POST', 'leaves', test_data, 200)
        self.log_result("Leave Request", success, f"Status: {status}")
        return success

    def test_get_leave_balance(self):
        success, data, status = self.make_request('GET', 'leaves/balance', expected_status=200)
        
        if success and isinstance(data, dict):
            self.log_result("Leave Balance", True, f"Balance: {data}")
            return True
        else:
            self.log_result("Leave Balance", False, f"Status: {status}")
            return False

    def test_attendance_checkin(self):
        test_data = {"location": "Office", "notes": "Test check-in"}
        success, data, status = self.make_request('POST', 'attendance/check-in', test_data, 200)
        self.log_result("Attendance Check-in", success, f"Status: {status}")
        return success

    def test_attendance_today(self):
        success, data, status = self.make_request('GET', 'attendance/today', expected_status=200)
        self.log_result("Today's Attendance", success, f"Status: {status}")
        return success

    def test_create_claim(self):
        test_data = {
            "claim_type": "travel",
            "amount": 150.50,
            "description": "Business trip expenses",
            "date": datetime.now().date().isoformat()
        }
        
        success, data, status = self.make_request('POST', 'claims', test_data, 200)
        self.log_result("Create Claim", success, f"Status: {status}")
        return success

    def test_overtime_request(self):
        test_data = {
            "date": datetime.now().date().isoformat(),
            "hours": 3.5,
            "reason": "Project deadline"
        }
        
        success, data, status = self.make_request('POST', 'overtime', test_data, 200)
        self.log_result("Overtime Request", success, f"Status: {status}")
        return success

    def test_create_announcement(self):
        test_data = {
            "title": "Test Announcement",
            "content": "This is a test announcement for system validation.",
            "priority": "normal"
        }
        
        success, data, status = self.make_request('POST', 'announcements', test_data, 200)
        self.log_result("Create Announcement", success, f"Status: {status}")
        return success

    def test_ai_announcement_generation(self):
        test_data = {
            "topic": "New office opening",
            "tone": "professional",
            "target_audience": "All employees"
        }
        
        success, data, status = self.make_request('POST', 'announcements/generate', test_data, 200)
        
        if success and 'title' in data and 'content' in data:
            self.log_result("AI Announcement Generation", True, f"Generated: {data.get('title', '')[:50]}...")
            return True
        else:
            self.log_result("AI Announcement Generation", False, f"Status: {status}, Response: {str(data)[:100]}")
            return False

    def test_get_announcements(self):
        success, data, status = self.make_request('GET', 'announcements', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_result("Get Announcements", True, f"Found {len(data)} announcements")
            return True
        else:
            self.log_result("Get Announcements", False, f"Status: {status}")
            return False

    def test_create_payroll(self):
        if not self.employee_id:
            self.log_result("Create Payroll", False, "No employee ID available")
            return False
            
        test_data = {
            "employee_id": self.employee_id,
            "period": "January 2025",
            "basic_salary": 5000.0,
            "allowances": 500.0,
            "deductions": 300.0,
            "overtime_pay": 200.0,
            "bonus": 100.0
        }
        
        success, data, status = self.make_request('POST', 'payroll', test_data, 200)
        self.log_result("Create Payroll", success, f"Status: {status}")
        return success

    def test_settings(self):
        # Get settings
        success, data, status = self.make_request('GET', 'settings', expected_status=200)
        
        if success and isinstance(data, dict):
            self.log_result("Get Settings", True, f"Company: {data.get('company_name', 'N/A')}")
            
            # Try to update settings
            update_data = {"theme": "dark", "primary_color": "#1F2937"}
            success2, data2, status2 = self.make_request('PUT', 'settings', update_data, 200)
            self.log_result("Update Settings", success2, f"Status: {status2}")
            return success and success2
        else:
            self.log_result("Get Settings", False, f"Status: {status}")
            return False

    def test_calendar_events(self):
        # Create event
        test_data = {
            "title": "Team Meeting",
            "description": "Weekly sync meeting",
            "start_date": (datetime.now() + timedelta(days=1)).date().isoformat(),
            "end_date": (datetime.now() + timedelta(days=1)).date().isoformat(),
            "event_type": "meeting"
        }
        
        success, data, status = self.make_request('POST', f'events?title={test_data["title"]}&description={test_data["description"]}&start_date={test_data["start_date"]}&end_date={test_data["end_date"]}&event_type={test_data["event_type"]}', expected_status=200)
        
        if success:
            # Get events
            success2, data2, status2 = self.make_request('GET', 'events', expected_status=200)
            if success2 and isinstance(data2, list):
                self.log_result("Calendar Events", True, f"Created and retrieved {len(data2)} events")
                return True
            else:
                self.log_result("Calendar Events", False, f"Get events failed: {status2}")
                return False
        else:
            self.log_result("Calendar Events", False, f"Create event failed: {status}")
            return False

    def run_all_tests(self):
        print(f"🚀 Starting VANTAGE HR API Tests")
        print(f"Base URL: {self.base_url}")
        print("="*60)
        
        # Health check first
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Try admin registration, if failed try login
        auth_success = self.test_register_admin()
        if not auth_success:
            print("📝 Admin registration failed, trying login...")
            auth_success = self.test_login()
        
        if not auth_success:
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Test protected endpoints
        self.test_auth_me()
        self.test_dashboard_stats()
        
        # Employee management
        self.test_create_employee()
        self.test_get_employees()
        
        # Leave management 
        self.test_leave_request()
        self.test_get_leave_balance()
        
        # Attendance
        self.test_attendance_checkin()
        self.test_attendance_today()
        
        # Claims and Overtime
        self.test_create_claim()
        self.test_overtime_request()
        
        # Announcements and AI
        self.test_create_announcement()
        self.test_ai_announcement_generation()
        self.test_get_announcements()
        
        # Payroll
        self.test_create_payroll()
        
        # Settings
        self.test_settings()
        
        # Calendar
        self.test_calendar_events()
        
        print("\n" + "="*60)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"  - {failure['test']}: {failure['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        return success_rate >= 80

def main():
    tester = VantageHRTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())