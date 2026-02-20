import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { Plus, CreditCard, DollarSign, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

const PayrollPage = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [payroll, setPayroll] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [processing, setProcessing] = useState(null);
  const [formData, setFormData] = useState({
    employee_id: '',
    period: '',
    basic_salary: '',
    allowances: '0',
    deductions: '0',
    overtime_pay: '0',
    bonus: '0'
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr';

  useEffect(() => {
    fetchData();
    checkPaymentStatus();
  }, []);

  const fetchData = async () => {
    try {
      const [payrollRes, empRes] = await Promise.all([
        api.getPayroll(),
        api.getEmployees()
      ]);
      setPayroll(payrollRes.data);
      setEmployees(empRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async () => {
    const params = new URLSearchParams(location.search);
    const sessionId = params.get('session_id');
    const status = params.get('status');
    
    if (sessionId && status === 'success') {
      try {
        const response = await api.getPaymentStatus(sessionId);
        if (response.data.payment_status === 'paid') {
          toast.success('Payment processed successfully!');
          fetchData();
        }
      } catch (error) {
        console.error('Failed to check payment status:', error);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createPayroll({
        ...formData,
        basic_salary: parseFloat(formData.basic_salary),
        allowances: parseFloat(formData.allowances) || 0,
        deductions: parseFloat(formData.deductions) || 0,
        overtime_pay: parseFloat(formData.overtime_pay) || 0,
        bonus: parseFloat(formData.bonus) || 0
      });
      toast.success('Payroll record created');
      setIsAddOpen(false);
      setFormData({
        employee_id: '',
        period: '',
        basic_salary: '',
        allowances: '0',
        deductions: '0',
        overtime_pay: '0',
        bonus: '0'
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create payroll');
    }
  };

  const handleProcessPayment = async (payrollId) => {
    setProcessing(payrollId);
    try {
      const response = await api.processPayment(payrollId);
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Payment processing failed');
      setProcessing(null);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'badge-warning',
      completed: 'badge-success',
      processing: 'badge-info'
    };
    return <span className={styles[status] || 'badge-warning'}>{status}</span>;
  };

  const getPaymentBadge = (status) => {
    const styles = {
      unpaid: 'badge-warning',
      paid: 'badge-success',
      pending: 'badge-info'
    };
    return <span className={styles[status] || 'badge-warning'}>{status}</span>;
  };

  const totalPayroll = payroll.reduce((a, p) => a + p.net_salary, 0);
  const paidPayroll = payroll.filter(p => p.payment_status === 'paid').reduce((a, p) => a + p.net_salary, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Secured Payroll</h1>
          <p className="text-muted-foreground">Manage salary payments with Stripe</p>
        </div>

        {isAdmin && (
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-full" data-testid="create-payroll-btn">
                <Plus className="w-4 h-4 mr-2" />
                Create Payroll
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-['Outfit']">Create Payroll Record</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 space-y-2">
                    <Label>Employee</Label>
                    <Select
                      value={formData.employee_id}
                      onValueChange={(v) => {
                        const emp = employees.find(e => e.id === v);
                        setFormData({
                          ...formData,
                          employee_id: v,
                          basic_salary: emp?.salary?.toString() || ''
                        });
                      }}
                    >
                      <SelectTrigger data-testid="payroll-employee">
                        <SelectValue placeholder="Select employee" />
                      </SelectTrigger>
                      <SelectContent>
                        {employees.map(emp => (
                          <SelectItem key={emp.id} value={emp.id}>
                            {emp.full_name} ({emp.department})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Period</Label>
                    <Input
                      value={formData.period}
                      onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                      placeholder="e.g., January 2024"
                      required
                      data-testid="payroll-period"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Basic Salary ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.basic_salary}
                      onChange={(e) => setFormData({ ...formData, basic_salary: e.target.value })}
                      required
                      data-testid="payroll-basic"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Allowances ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.allowances}
                      onChange={(e) => setFormData({ ...formData, allowances: e.target.value })}
                      data-testid="payroll-allowances"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Deductions ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.deductions}
                      onChange={(e) => setFormData({ ...formData, deductions: e.target.value })}
                      data-testid="payroll-deductions"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Overtime Pay ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.overtime_pay}
                      onChange={(e) => setFormData({ ...formData, overtime_pay: e.target.value })}
                      data-testid="payroll-overtime"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Bonus ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.bonus}
                      onChange={(e) => setFormData({ ...formData, bonus: e.target.value })}
                      data-testid="payroll-bonus"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" data-testid="payroll-submit-btn">
                    Create Payroll
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-blue-500/10">
                <DollarSign className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Payroll</p>
                <p className="text-2xl font-bold font-['Outfit']">${totalPayroll.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-green-500/10">
                <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Paid</p>
                <p className="text-2xl font-bold font-['Outfit']">${paidPayroll.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-yellow-500/10">
                <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold font-['Outfit']">${(totalPayroll - paidPayroll).toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Payroll Table */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit']">Payroll Records</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Basic</TableHead>
                  <TableHead>Allowances</TableHead>
                  <TableHead>Deductions</TableHead>
                  <TableHead>Net Salary</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Payment</TableHead>
                  {isAdmin && <TableHead className="text-right">Action</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {payroll.length > 0 ? (
                  payroll.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">{record.employee_name}</TableCell>
                      <TableCell>{record.period}</TableCell>
                      <TableCell>${record.basic_salary.toFixed(2)}</TableCell>
                      <TableCell className="text-green-600">+${record.allowances.toFixed(2)}</TableCell>
                      <TableCell className="text-red-600">-${record.deductions.toFixed(2)}</TableCell>
                      <TableCell className="font-semibold">${record.net_salary.toFixed(2)}</TableCell>
                      <TableCell>{getStatusBadge(record.status)}</TableCell>
                      <TableCell>{getPaymentBadge(record.payment_status)}</TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          {record.payment_status !== 'paid' && (
                            <Button
                              size="sm"
                              onClick={() => handleProcessPayment(record.id)}
                              disabled={processing === record.id}
                              className="rounded-full"
                              data-testid={`pay-btn-${record.id}`}
                            >
                              {processing === record.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <>
                                  <CreditCard className="w-4 h-4 mr-1" />
                                  Pay
                                </>
                              )}
                            </Button>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-12">
                      <CreditCard className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                      <p className="text-muted-foreground">No payroll records</p>
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

export default PayrollPage;
