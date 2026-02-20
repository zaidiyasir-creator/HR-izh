import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const api = {
  // Dashboard
  getDashboardStats: () => axios.get(`${API}/dashboard/stats`),

  // Auth
  changePassword: (data) => axios.post(`${API}/auth/change-password`, data),

  // Employees
  getEmployees: () => axios.get(`${API}/employees`),
  getEmployee: (id) => axios.get(`${API}/employees/${id}`),
  createEmployee: (data) => axios.post(`${API}/employees`, data),
  updateEmployee: (id, data) => axios.put(`${API}/employees/${id}`, data),
  deleteEmployee: (id) => axios.delete(`${API}/employees/${id}`),

  // Leaves
  getLeaves: () => axios.get(`${API}/leaves`),
  createLeave: (data) => axios.post(`${API}/leaves`, data),
  updateLeave: (id, data) => axios.put(`${API}/leaves/${id}`, data),
  getLeaveBalance: () => axios.get(`${API}/leaves/balance`),

  // Attendance
  getAttendance: (params) => axios.get(`${API}/attendance`, { params }),
  getTodayAttendance: () => axios.get(`${API}/attendance/today`),
  checkIn: (data) => axios.post(`${API}/attendance/check-in`, data),
  checkOut: (data) => axios.post(`${API}/attendance/check-out`, data),

  // Claims
  getClaims: () => axios.get(`${API}/claims`),
  createClaim: (data) => axios.post(`${API}/claims`, data),
  updateClaim: (id, data) => axios.put(`${API}/claims/${id}`, data),

  // Overtime
  getOvertime: () => axios.get(`${API}/overtime`),
  createOvertime: (data) => axios.post(`${API}/overtime`, data),
  updateOvertime: (id, data) => axios.put(`${API}/overtime/${id}`, data),

  // Announcements
  getAnnouncements: () => axios.get(`${API}/announcements`),
  createAnnouncement: (data) => axios.post(`${API}/announcements`, data),
  generateAnnouncement: (data) => axios.post(`${API}/announcements/generate`, data),

  // Performance
  getPerformanceReviews: () => axios.get(`${API}/performance/reviews`),
  createPerformanceReview: (data) => axios.post(`${API}/performance/reviews`, data),
  generatePerformanceInsights: (data) => axios.post(`${API}/performance/insights`, data),

  // Payroll
  getPayroll: () => axios.get(`${API}/payroll`),
  createPayroll: (data) => axios.post(`${API}/payroll`, data),
  processPayment: (id) => axios.post(`${API}/payroll/${id}/pay`),
  getPaymentStatus: (sessionId) => axios.get(`${API}/payroll/payment-status/${sessionId}`),

  // Advance Salary
  getAdvanceSalary: () => axios.get(`${API}/advance-salary`),
  createAdvanceSalary: (data) => axios.post(`${API}/advance-salary`, data),
  updateAdvanceSalary: (id, status) => axios.put(`${API}/advance-salary/${id}?status=${status}`),

  // Events
  getEvents: () => axios.get(`${API}/events`),
  createEvent: (data) => axios.post(`${API}/events`, null, { params: data }),

  // Settings
  getSettings: () => axios.get(`${API}/settings`),
  updateSettings: (data) => axios.put(`${API}/settings`, data),
};

export default api;
