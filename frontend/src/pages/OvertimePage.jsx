import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { Plus, Timer, Clock, Check, X, Filter } from 'lucide-react';
import { format } from 'date-fns';

const OvertimePage = () => {
  const { user } = useAuth();
  const [overtime, setOvertime] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [formData, setFormData] = useState({
    date: '',
    hours: '',
    reason: ''
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr' || user?.role === 'manager';

  useEffect(() => {
    fetchOvertime();
  }, []);

  const fetchOvertime = async () => {
    try {
      const response = await api.getOvertime();
      setOvertime(response.data);
    } catch (error) {
      toast.error('Failed to fetch overtime records');
    } finally {
      setLoading(false);
    }
  };

  const filteredOvertime = overtime.filter(ot => 
    statusFilter === 'all' || ot.status === statusFilter
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createOvertime({
        ...formData,
        hours: parseFloat(formData.hours)
      });
      toast.success('Overtime request submitted');
      setIsAddOpen(false);
      setFormData({ date: '', hours: '', reason: '' });
      fetchOvertime();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit');
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.updateOvertime(id, { status: 'approved' });
      toast.success('Overtime approved');
      fetchOvertime();
    } catch (error) {
      toast.error('Failed to approve');
    }
  };

  const handleReject = async (id) => {
    try {
      await api.updateOvertime(id, { status: 'rejected' });
      toast.success('Overtime rejected');
      fetchOvertime();
    } catch (error) {
      toast.error('Failed to reject');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400',
      approved: 'bg-green-500/15 text-green-700 dark:text-green-400',
      rejected: 'bg-red-500/15 text-red-700 dark:text-red-400'
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const totalPendingHours = overtime.filter(o => o.status === 'pending').reduce((a, o) => a + o.hours, 0);
  const totalApprovedHours = overtime.filter(o => o.status === 'approved').reduce((a, o) => a + o.hours, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="overtime-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Overtime Management</h1>
          <p className="text-muted-foreground">Track and manage overtime hours</p>
        </div>

        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-full" data-testid="request-overtime-btn">
              <Plus className="w-4 h-4 mr-2" />
              Request Overtime
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-['Outfit']">Request Overtime</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                    data-testid="overtime-date"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Hours</Label>
                  <Input
                    type="number"
                    step="0.5"
                    min="0.5"
                    value={formData.hours}
                    onChange={(e) => setFormData({ ...formData, hours: e.target.value })}
                    required
                    data-testid="overtime-hours"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Reason</Label>
                <Textarea
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  placeholder="Briefly describe the reason for overtime..."
                  required
                  data-testid="overtime-reason"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="overtime-submit-btn">
                  Submit Request
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-yellow-500/10">
                <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending Hours</p>
                <p className="text-2xl font-bold font-['Outfit']">{totalPendingHours}h</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-green-500/10">
                <Clock className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Approved Hours</p>
                <p className="text-2xl font-bold font-['Outfit']">{totalApprovedHours}h</p>
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
                <p className="text-sm text-muted-foreground">Total Requests</p>
                <p className="text-2xl font-bold font-['Outfit']">{overtime.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Overtime Table */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit']">Overtime Records</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {overtime.length > 0 ? (
                  overtime.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">{record.employee_name}</TableCell>
                      <TableCell>{format(new Date(record.date), 'MMM d, yyyy')}</TableCell>
                      <TableCell>{record.hours}h</TableCell>
                      <TableCell className="max-w-xs truncate">{record.reason}</TableCell>
                      <TableCell>{getStatusBadge(record.status)}</TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          {record.status === 'pending' && (
                            <div className="flex justify-end gap-2">
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => handleApprove(record.id)}
                                className="text-green-600 hover:text-green-700 hover:bg-green-500/10"
                                data-testid={`approve-ot-${record.id}`}
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => handleReject(record.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-500/10"
                                data-testid={`reject-ot-${record.id}`}
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12">
                      <Timer className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                      <p className="text-muted-foreground">No overtime records</p>
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

export default OvertimePage;
