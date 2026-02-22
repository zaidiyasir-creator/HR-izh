# VANTAGE HR - Product Requirements Document

## Overview
VANTAGE HR is a high-performance HR operating system that transforms mundane HR tasks into a command-center experience. Built with a modern tech stack featuring React, FastAPI, and MongoDB.

## Original Problem Statement
Build an HR system with Employee Management, Leave Management, Smart Announcement, Team Calendar, Smart Attendance, Claim Management, Overtime Management, Secured Payroll, Payment Voucher, Performance Management, and Advance Salary.

## User Personas
1. **Admin/HR Manager** - Full access to all features, can manage employees, approve requests, process payroll
2. **Manager** - Can approve leaves, claims, overtime for their team, view performance
3. **Employee** - Can submit requests, check-in/out, view personal data, submit claims

## Core Requirements (Static)
- JWT-based authentication with role-based access control
- Employee CRUD operations with department/position management
- Leave management with balance tracking
- Attendance system with check-in/check-out
- Claims and expense management
- Overtime tracking and approval
- Payroll processing with Stripe integration
- AI-powered announcements using GPT-5.2
- AI-powered performance insights
- Team calendar with events and leave overlays
- Theme customization (light/dark mode, accent colors)
- Logo and company settings customization

## What's Been Implemented (Feb 22, 2026)

### Backend (FastAPI)
- ✅ Auth: Register, Login, JWT token validation
- ✅ Employees: CRUD operations with role update fix
- ✅ Leaves: Request, approve/reject, balance tracking, date validation
- ✅ Attendance: Check-in, check-out, history (with geolocation validation)
- ✅ Claims: Submit, approve/reject, receipt upload
- ✅ Overtime: Request, approve/reject
- ✅ Announcements: Create, AI generate with Gemini 3 Flash
- ✅ Performance: Reviews CRUD, AI insights
- ✅ Payroll: Create records, Stripe checkout integration
- ✅ Events/Calendar: CRUD with leave overlay
- ✅ Settings: Company config, leave policies, remote storage
- ✅ Dashboard: Stats aggregation
- ✅ **Geofence Settings**: Office locations, categories, department assignments
- ✅ **Reports Generation**: PDF & CSV exports for Claims, Leaves, Attendance, Overtime
- ✅ **Reports Employee Filtering**: Admin/HR can filter reports by specific employees
- ✅ **Receipt Upload**: Store in MongoDB or Remote Storage (Nextcloud/NAS)
- ✅ **Remote Storage**: Nextcloud WebDAV and Local NAS integration

### Frontend (React + Shadcn UI)
- ✅ Login/Register with split-screen design
- ✅ Dashboard with stats, quick actions, recent data
- ✅ Employee management with table and add dialog
- ✅ Leave management with balance display, date validation
- ✅ Attendance with check-in/out and history
- ✅ Claims submission with **receipt upload** (PNG, JPG, PDF, Camera)
- ✅ **Receipt Viewer** with zoom, rotate, fullscreen, download (images & PDF)
- ✅ Overtime management
- ✅ Announcements with AI generation (sparkle button)
- ✅ Performance reviews with AI insights
- ✅ Payroll with Stripe payment processing
- ✅ Calendar with event display
- ✅ **Team Calendar** with leaves, holidays, events integration and filtering
- ✅ **Malaysia 2026 Public Holidays** - 18 holidays (corrected Hari Raya dates)
- ✅ **Malaysia 2026 School Holidays** - 4 term breaks
- ✅ Settings with theme toggle, colors, company config
- ✅ **Company Logo Upload** - file upload instead of URL
- ✅ **Remote Storage Settings** - Nextcloud & NAS configuration
- ✅ **Reports Page** - Generate Claims, Leaves, Attendance, Overtime reports
- ✅ **Reports Employee Filter** - Admin/HR can select specific employees for reports
- ✅ Responsive sidebar navigation
- ✅ **Mobile Responsiveness** - optimized for mobile devices
- ✅ Dark/Light mode toggle
- ✅ **Accent Colors** - 18 customizable accent colors
- ✅ Toast notifications
- ✅ **Geofence Settings Page**: Full CRUD for office locations, category editing, department assignments

### Integrations
- ✅ Gemini 3 Flash via emergentintegrations (Announcements, Performance)
- ✅ Stripe Checkout for payroll payments
- ✅ MongoDB for data persistence
- ✅ **Geolocation-based Attendance**: Haversine distance calculation for geofencing
- ✅ **Nextcloud WebDAV**: Remote storage for receipts and reports
- ✅ **Local NAS/Filesystem**: Alternative remote storage option
- ✅ **ReportLab**: PDF report generation

## Prioritized Backlog

### P0 (Critical - Done)
- [x] Authentication system
- [x] Employee management (with role update fix)
- [x] Leave management (with date validation)
- [x] Attendance tracking
- [x] Dashboard overview
- [x] **Geofence Settings** - Office locations CRUD, category-based radius, department assignments
- [x] **Departments Management** - Full CRUD with geofence category sync, employee assignment validation
- [x] **Menu Configuration** - Admin can hide/show menu items globally or per role
- [x] **Malaysia 2026 Holidays** - 18 public holidays + 4 school term breaks
- [x] **Reports Generation** - PDF & CSV exports for all HR data
- [x] **Reports Employee Filtering** - Admin/HR can filter reports by specific employees

### P1 (High Priority - Done)
- [x] AI announcements (Gemini 3 Flash via Emergent LLM Key)
- [x] Performance management with AI insights
- [x] Payroll with Stripe
- [x] Claims management with receipt upload
- [x] Overtime management with approval workflow
- [x] Leave management with balance tracking and approval workflow
- [x] Status filtering for Leave/Claims/Overtime pages
- [x] **Receipt Upload & Viewer** - PNG, JPG, PDF with zoom/rotate/fullscreen
- [x] **Remote Storage** - Nextcloud and NAS integration for files

### P2 (Medium Priority - Partially Done)
- [x] Team Calendar
- [x] Theme customization
- [x] Report exports (PDF/CSV)
- [ ] Advance Salary requests (backend ready, needs UI polish)
- [ ] Payment voucher generation

### P3 (Nice to Have)
- [ ] Mobile-optimized PWA
- [ ] Email notifications (on hold per user request)
- [ ] Bulk employee import
- [ ] Department hierarchy management
- [ ] Shift scheduling
- [ ] Document management

## Next Tasks
1. Advance Salary requests (UI polish)
2. Payment voucher/slip generation (PDF)
3. Secured Payroll with Stripe (P1 - playbook available, needs API key)
4. Email notifications (on hold - user requested)
5. Mobile App (PWA) considerations

## Technical Architecture
- **Frontend**: React 19, Tailwind CSS, Shadcn UI, React Router
- **Backend**: FastAPI, Motor (async MongoDB), Pydantic, ReportLab
- **Database**: MongoDB
- **AI**: emergentintegrations with Gemini 3 Flash
- **Payments**: Stripe Checkout via emergentintegrations
- **Storage**: MongoDB (base64) + Nextcloud WebDAV + Local NAS
- **Auth**: JWT with bcrypt password hashing
