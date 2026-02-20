import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { Clock, MapPin, CheckCircle2, XCircle, Timer, CalendarDays } from 'lucide-react';
import { format } from 'date-fns';

const AttendancePage = () => {
  const { user } = useAuth();
  const [attendance, setAttendance] = useState([]);
  const [todayRecord, setTodayRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [attRes, todayRes] = await Promise.all([
        api.getAttendance({ start_date: startDate, end_date: endDate }),
        api.getTodayAttendance()
      ]);
      setAttendance(attRes.data);
      setTodayRecord(todayRes.data);
    } catch (error) {
      console.error('Failed to fetch attendance:', error);
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

  const handleFilter = () => {
    setLoading(true);
    fetchData();
  };

  const getStatusBadge = (record) => {
    if (!record.check_in) {
      return <span className="badge-error">Absent</span>;
    }
    if (!record.check_out) {
      return <span className="badge-warning">In Progress</span>;
    }
    return <span className="badge-success">Complete</span>;
  };

  // Calculate stats
  const totalPresent = attendance.filter(a => a.check_in).length;
  const totalHours = attendance.reduce((acc, a) => acc + (a.total_hours || 0), 0);
  const avgHours = totalPresent > 0 ? (totalHours / totalPresent).toFixed(1) : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="attendance-page">
      {/* Header with Check-in/out */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Attendance</h1>
          <p className="text-muted-foreground">Track your work hours</p>
        </div>

        {/* Today's Status Card */}
        <Card className="w-full lg:w-auto">
          <CardContent className="p-4 flex flex-col sm:flex-row items-center gap-4">
            <div className="flex-1 text-center sm:text-left">
              <p className="text-sm text-muted-foreground">Today's Status</p>
              <div className="flex items-center justify-center sm:justify-start gap-2 mt-1">
                {todayRecord ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                    <span className="font-medium">
                      {todayRecord.check_out ? 'Checked Out' : 'Checked In'}
                    </span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-5 h-5 text-muted-foreground" />
                    <span className="text-muted-foreground">Not checked in</span>
                  </>
                )}
              </div>
              {todayRecord?.check_in && (
                <p className="text-xs text-muted-foreground mt-1">
                  In: {format(new Date(todayRecord.check_in), 'HH:mm')}
                  {todayRecord.check_out && ` | Out: ${format(new Date(todayRecord.check_out), 'HH:mm')}`}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              {!todayRecord ? (
                <Button onClick={handleCheckIn} className="rounded-full" data-testid="checkin-btn">
                  <Clock className="w-4 h-4 mr-2" />
                  Check In
                </Button>
              ) : !todayRecord.check_out ? (
                <Button onClick={handleCheckOut} variant="outline" className="rounded-full" data-testid="checkout-btn">
                  <Clock className="w-4 h-4 mr-2" />
                  Check Out
                </Button>
              ) : (
                <div className="text-center">
                  <p className="text-2xl font-bold font-['Outfit']">{todayRecord.total_hours?.toFixed(1)}h</p>
                  <p className="text-xs text-muted-foreground">Total Hours</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-green-500/10">
                <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Present Days</p>
                <p className="text-2xl font-bold font-['Outfit']">{totalPresent}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-blue-500/10">
                <Timer className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Hours</p>
                <p className="text-2xl font-bold font-['Outfit']">{totalHours.toFixed(1)}h</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-purple-500/10">
                <CalendarDays className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Average Hours</p>
                <p className="text-2xl font-bold font-['Outfit']">{avgHours}h</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                data-testid="filter-start-date"
              />
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                data-testid="filter-end-date"
              />
            </div>
            <Button onClick={handleFilter} className="rounded-full" data-testid="filter-btn">
              Apply Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Attendance Table */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit']">Attendance History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Employee</TableHead>
                  <TableHead>Check In</TableHead>
                  <TableHead>Check Out</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attendance.length > 0 ? (
                  attendance.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">
                        {format(new Date(record.date), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell>{record.employee_name}</TableCell>
                      <TableCell>
                        {record.check_in ? format(new Date(record.check_in), 'HH:mm') : '-'}
                      </TableCell>
                      <TableCell>
                        {record.check_out ? format(new Date(record.check_out), 'HH:mm') : '-'}
                      </TableCell>
                      <TableCell>
                        {record.total_hours ? `${record.total_hours.toFixed(1)}h` : '-'}
                      </TableCell>
                      <TableCell>
                        {record.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {record.location}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getStatusBadge(record)}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12">
                      <Clock className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                      <p className="text-muted-foreground">No attendance records</p>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AttendancePage;
