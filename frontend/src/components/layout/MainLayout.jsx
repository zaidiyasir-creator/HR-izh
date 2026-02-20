import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { 
  LayoutDashboard, Users, CalendarDays, Clock, Megaphone, 
  FileText, Timer, CreditCard, TrendingUp, Settings, LogOut,
  Menu, X, Sun, Moon, ChevronLeft, ChevronRight, MapPin
} from 'lucide-react';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback } from '../ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Employees', href: '/employees', icon: Users, roles: ['admin', 'hr', 'manager'] },
  { name: 'Leaves', href: '/leaves', icon: CalendarDays, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Attendance', href: '/attendance', icon: Clock, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Announcements', href: '/announcements', icon: Megaphone, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Calendar', href: '/calendar', icon: CalendarDays, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Claims', href: '/claims', icon: FileText, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Overtime', href: '/overtime', icon: Timer, roles: ['admin', 'hr', 'manager', 'employee'] },
  { name: 'Payroll', href: '/payroll', icon: CreditCard, roles: ['admin', 'hr'] },
  { name: 'Performance', href: '/performance', icon: TrendingUp, roles: ['admin', 'hr', 'manager'] },
  { name: 'Geofence', href: '/geofence-settings', icon: MapPin, roles: ['admin', 'hr'] },
  { name: 'Settings', href: '/settings', icon: Settings, roles: ['admin', 'hr', 'manager', 'employee'] },
];

const MainLayout = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const getInitials = (name) => {
    return name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U';
  };

  // Filter navigation based on user role
  const filteredNavigation = navigation.filter(item => 
    item.roles.includes(user?.role || 'employee')
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed left-0 top-0 h-full border-r border-border bg-card/95 backdrop-blur-xl z-50 transition-all duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${sidebarCollapsed ? 'w-20' : 'w-64'}
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-border">
          {!sidebarCollapsed && (
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">V</span>
              </div>
              <span className="font-bold text-lg tracking-tight font-['Outfit']">VANTAGE</span>
            </Link>
          )}
          {sidebarCollapsed && (
            <div className="w-full flex justify-center">
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold">V</span>
              </div>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="hidden lg:flex"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            data-testid="sidebar-collapse-btn"
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1 overflow-y-auto h-[calc(100vh-4rem)]">
          {filteredNavigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                data-testid={`nav-${item.name.toLowerCase()}`}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                  ${isActive 
                    ? 'bg-primary text-primary-foreground' 
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  }
                  ${sidebarCollapsed ? 'justify-center px-2' : ''}
                `}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span className="font-medium">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main content */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'}`}>
        {/* Header */}
        <header className="sticky top-0 z-30 h-16 border-b border-border bg-background/95 backdrop-blur-md">
          <div className="h-full flex items-center justify-between px-4 lg:px-8">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
                data-testid="mobile-menu-btn"
              >
                <Menu className="w-5 h-5" />
              </Button>
              <h1 className="text-lg font-semibold font-['Outfit'] hidden sm:block">
                {filteredNavigation.find(n => n.href === location.pathname)?.name || 'Dashboard'}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              {/* Theme toggle */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                data-testid="theme-toggle-btn"
              >
                {theme === 'dark' ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </Button>

              {/* User menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 px-2" data-testid="user-menu-btn">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                        {getInitials(user?.full_name)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="hidden sm:block font-medium">{user?.full_name}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium">{user?.full_name}</p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                    <p className="text-xs text-muted-foreground capitalize mt-1">Role: {user?.role}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/settings" className="cursor-pointer">
                      <Settings className="w-4 h-4 mr-2" />
                      Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={logout}
                    className="text-destructive cursor-pointer"
                    data-testid="logout-btn"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8 min-h-[calc(100vh-4rem)]">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
