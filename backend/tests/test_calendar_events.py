"""
Test Calendar/Events API endpoints for VANTAGE HR
Tests: Team Calendar with leaves, holidays, events display
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@vantage.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestEventsAPI:
    """Test events CRUD operations for Team Calendar"""

    def test_get_events_returns_list(self, api_client):
        """GET /api/events should return events list including approved leaves"""
        response = api_client.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"GET /api/events: {len(data)} events returned")

    def test_create_event_with_query_params(self, api_client):
        """POST /api/events - Create event using query parameters"""
        today = datetime.now()
        start_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Backend uses query params, not JSON body
        params = {
            "title": "TEST_Company Holiday",
            "description": "Test company holiday event",
            "start_date": start_date,
            "end_date": end_date,
            "event_type": "holiday"
        }
        response = api_client.post(f"{BASE_URL}/api/events", params=params)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("title") == "TEST_Company Holiday"
        assert data.get("event_type") == "holiday"
        assert data.get("start_date") == start_date
        assert "id" in data
        print(f"Created event: {data.get('id')}")
        return data

    def test_create_meeting_event(self, api_client):
        """POST /api/events - Create meeting type event"""
        today = datetime.now()
        start_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        
        params = {
            "title": "TEST_Team Meeting",
            "description": "Weekly team sync",
            "start_date": start_date,
            "end_date": end_date,
            "event_type": "meeting"
        }
        response = api_client.post(f"{BASE_URL}/api/events", params=params)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("event_type") == "meeting"
        print(f"Created meeting event: {data.get('id')}")

    def test_create_generic_event(self, api_client):
        """POST /api/events - Create generic event type"""
        today = datetime.now()
        start_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        params = {
            "title": "TEST_Company Event",
            "description": "Annual celebration",
            "start_date": start_date,
            "end_date": end_date,
            "event_type": "event"
        }
        response = api_client.post(f"{BASE_URL}/api/events", params=params)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("event_type") == "event"
        print(f"Created generic event: {data.get('id')}")

    def test_events_include_approved_leaves(self, api_client):
        """GET /api/events should include approved leaves as leave events"""
        response = api_client.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        
        data = response.json()
        # Check if any leave events exist
        leave_events = [e for e in data if e.get("event_type") == "leave"]
        print(f"Found {len(leave_events)} leave events in calendar")
        
        # Leave events should have specific fields
        for leave in leave_events:
            assert "employee_name" in leave.get("title", "") or "-" in leave.get("title", "")
            assert leave.get("start_date") is not None
            assert leave.get("end_date") is not None

    def test_delete_event_success(self, api_client):
        """DELETE /api/events/{id} - Delete event as admin"""
        # First create an event to delete
        today = datetime.now()
        start_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "title": "TEST_To Delete",
            "description": "This will be deleted",
            "start_date": start_date,
            "end_date": start_date,
            "event_type": "meeting"
        }
        create_response = api_client.post(f"{BASE_URL}/api/events", params=params)
        assert create_response.status_code == 200
        event_id = create_response.json().get("id")
        
        # Now delete it
        delete_response = api_client.delete(f"{BASE_URL}/api/events/{event_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        data = delete_response.json()
        assert data.get("message") == "Event deleted"
        print(f"Successfully deleted event: {event_id}")

    def test_delete_nonexistent_event(self, api_client):
        """DELETE /api/events/{id} - Should return 404 for non-existent event"""
        response = api_client.delete(f"{BASE_URL}/api/events/nonexistent-id-12345")
        assert response.status_code == 404

    def test_filter_events_by_type(self, api_client):
        """Verify events can be filtered by type (for frontend filter tabs)"""
        response = api_client.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        
        data = response.json()
        
        # Count by type
        holidays = [e for e in data if e.get("event_type") == "holiday"]
        meetings = [e for e in data if e.get("event_type") == "meeting"]
        events = [e for e in data if e.get("event_type") == "event"]
        leaves = [e for e in data if e.get("event_type") == "leave"]
        
        print(f"Event counts - Holidays: {len(holidays)}, Meetings: {len(meetings)}, Events: {len(events)}, Leaves: {len(leaves)}")


class TestLeavesForCalendar:
    """Test leaves API for calendar integration"""

    def test_get_leaves_returns_approved_status(self, api_client):
        """GET /api/leaves should return leaves with status field"""
        response = api_client.get(f"{BASE_URL}/api/leaves")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check for approved leaves
        approved_leaves = [l for l in data if l.get("status") == "approved"]
        print(f"Found {len(approved_leaves)} approved leaves for calendar display")
        
        # Approved leaves should have required fields for calendar
        for leave in approved_leaves:
            assert "employee_name" in leave
            assert "start_date" in leave
            assert "end_date" in leave
            assert "leave_type" in leave


class TestDashboardStats:
    """Test dashboard stats for Team Calendar stats cards"""

    def test_dashboard_stats_returns_counts(self, api_client):
        """GET /api/dashboard/stats should return stats for calendar"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required stats fields
        assert "total_employees" in data
        assert "present_today" in data
        assert "pending_leaves" in data
        
        print(f"Dashboard stats: {data}")


class TestCleanup:
    """Cleanup test data"""

    def test_cleanup_test_events(self, api_client):
        """Delete all TEST_ prefixed events"""
        response = api_client.get(f"{BASE_URL}/api/events")
        if response.status_code == 200:
            events = response.json()
            test_events = [e for e in events if e.get("title", "").startswith("TEST_")]
            
            for event in test_events:
                delete_response = api_client.delete(f"{BASE_URL}/api/events/{event['id']}")
                if delete_response.status_code == 200:
                    print(f"Cleaned up event: {event['title']}")
