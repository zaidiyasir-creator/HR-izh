import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  Users, CalendarDays, Clock, FileText, TrendingUp, 
  Megaphone, ArrowRight, CheckCircle2, XCircle, Timer
} from 'lucide-react';
import { format } from 'date-fns';

const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [todayAttendance, setTodayAttendance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, attendanceRes] = await Promise.all([
        api.getDashboardStats(),
        api.getTodayAttendance()
      ]);
      setStats(statsRes.data);
      setTodayAttendance(attendanceRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async () => {
    try {
      await api.checkIn({ location: 'Office' });
      toast.success('Checked in successfully!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Check-in failed');
    }
  };

  const handleCheckOut = async () => {
    try {
      await api.checkOut({});
      toast.success('Checked out successfully!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Check-out failed');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400',
      approved: 'bg-green-500/15 text-green-700 dark:text-green-400',
      rejected: 'bg-red-500/15 text-red-700 dark:text-red-400'
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${styles[status] || 'bg-blue-500/15 text-blue-700'}`}>
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading dashboard...</div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Employees',
      value: stats?.total_employees || 0,
      icon: Users,
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-500/10'
    },
    {
      title: 'Present Today',
      value: stats?.present_today || 0,
      icon: CheckCircle2,
      color: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-500/10'
    },
    {
      title: 'Pending Leaves',
      value: stats?.pending_leaves || 0,
      icon: CalendarDays,
      color: 'text-yellow-600 dark:text-yellow-400',
      bg: 'bg-yellow-500/10'
    },
    {
      title: 'Pending Claims',
      value: stats?.pending_claims || 0,
      icon: FileText,
      color: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-500/10'
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard-page">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold font-['Outfit'] tracking-tight">
            Welcome back, {user?.full_name?.split(' ')[0]}!
          </h1>
          <p className="text-muted-foreground mt-1">
            {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </p>
        </div>

        {/* Quick Check-in/out */}
        <Card className="w-full md:w-auto">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="flex-1 md:flex-none">
              <p className="text-sm text-muted-foreground mb-1">Today's Status</p>
              {todayAttendance ? (
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                  <span className="font-medium">
                    {todayAttendance.check_out ? 'Checked Out' : 'Checked In'}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-muted-foreground" />
                  <span className="text-muted-foreground">Not checked in</span>
                </div>
              )}
            </div>
            {!todayAttendance ? (
              <Button 
                onClick={handleCheckIn} 
                className="rounded-full"
                data-testid="checkin-btn"
              >
                <Clock className="w-4 h-4 mr-2" />
                Check In
              </Button>
            ) : !todayAttendance.check_out ? (
              <Button 
                onClick={handleCheckOut} 
                variant="outline" 
                className="rounded-full"
                data-testid="checkout-btn"
              >
                <Clock className="w-4 h-4 mr-2" />
                Check Out
              </Button>
            ) : (
              <div className="text-sm text-muted-foreground">
                <p>Hours: {todayAttendance.total_hours?.toFixed(1)}h</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, idx) => (
          <Card key={idx} className="card-hover">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                  <p className="text-3xl font-bold mt-2 font-['Outfit']">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-xl ${stat.bg}`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Announcements - Wide */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <Megaphone className="w-5 h-5" />
              Recent Announcements
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <a href="/announcements" className="flex items-center gap-1">
                View All <ArrowRight className="w-4 h-4" />
              </a>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {stats?.recent_announcements?.length > 0 ? (
              stats.recent_announcements.map((ann, idx) => (
                <div 
                  key={idx} 
                  className="p-4 rounded-lg bg-accent/50 border border-border"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="font-semibold">{ann.title}</h4>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {ann.content}
                      </p>
                    </div>
                    <Badge variant={ann.priority === 'high' ? 'destructive' : 'secondary'}>
                      {ann.priority}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    By {ann.author_name} • {format(new Date(ann.created_at), 'MMM d, yyyy')}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Megaphone className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No announcements yet</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Overtime */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <Timer className="w-5 h-5" />
              Pending Overtime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <p className="text-4xl font-bold font-['Outfit']">{stats?.pending_overtime || 0}</p>
              <p className="text-muted-foreground mt-1">requests awaiting approval</p>
              <Button variant="outline" className="mt-4 rounded-full" asChild>
                <a href="/overtime">
                  Review <ArrowRight className="w-4 h-4 ml-2" />
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Recent Leave Requests */}
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <CalendarDays className="w-5 h-5" />
              Recent Leave Requests
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <a href="/leaves" className="flex items-center gap-1">
                View All <ArrowRight className="w-4 h-4" />
              </a>
            </Button>
          </CardHeader>
          <CardContent>
            {stats?.recent_leaves?.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Employee</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Type</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Duration</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_leaves.map((leave, idx) => (
                      <tr key={idx} className="border-b border-border last:border-0">
                        <td className="py-3 px-4">
                          <p className="font-medium">{leave.employee_name}</p>
                          <p className="text-sm text-muted-foreground">{leave.department}</p>
                        </td>
                        <td className="py-3 px-4 capitalize">{leave.leave_type}</td>
                        <td className="py-3 px-4">
                          {format(new Date(leave.start_date), 'MMM d')} - {format(new Date(leave.end_date), 'MMM d')}
                        </td>
                        <td className="py-3 px-4">{getStatusBadge(leave.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <CalendarDays className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No recent leave requests</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
