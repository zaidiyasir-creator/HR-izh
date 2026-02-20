import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
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
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { toast } from 'sonner';
import { Plus, Search, Mail, Phone, Building2, Briefcase, Trash2, Pencil } from 'lucide-react';
import { format } from 'date-fns';

const EmployeesPage = () => {
  const { user } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'employee',
    department: '',
    position: '',
    phone: '',
    salary: ''
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr';

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    const filtered = employees.filter(emp =>
      emp.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.department?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredEmployees(filtered);
  }, [searchQuery, employees]);

  const fetchEmployees = async () => {
    try {
      const response = await api.getEmployees();
      setEmployees(response.data);
      setFilteredEmployees(response.data);
    } catch (error) {
      toast.error('Failed to fetch employees');
    } finally {
      setLoading(false);
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    try {
      await api.createEmployee({
        ...formData,
        salary: parseFloat(formData.salary) || 0
      });
      toast.success('Employee added successfully');
      setIsAddOpen(false);
      setFormData({
        email: '',
        full_name: '',
        password: '',
        role: 'employee',
        department: '',
        position: '',
        phone: '',
        salary: ''
      });
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add employee');
    }
  };

  const handleDeleteEmployee = async (id) => {
    if (!window.confirm('Are you sure you want to delete this employee?')) return;
    
    try {
      await api.deleteEmployee(id);
      toast.success('Employee deleted');
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete employee');
    }
  };

  const handleEditClick = (emp) => {
    setEditingEmployee(emp);
    setNewPassword('');
    setIsEditOpen(true);
  };

  const handleEditEmployee = async (e) => {
    e.preventDefault();
    try {
      await api.updateEmployee(editingEmployee.id, {
        full_name: editingEmployee.full_name,
        department: editingEmployee.department,
        position: editingEmployee.position,
        phone: editingEmployee.phone,
        salary: parseFloat(editingEmployee.salary) || 0,
        role: editingEmployee.role,
        status: editingEmployee.status
      });
      toast.success('Employee updated successfully');
      setIsEditOpen(false);
      setEditingEmployee(null);
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update employee');
    }
  };

  const handleResetPassword = async () => {
    if (!newPassword) {
      toast.error('Please enter a new password');
      return;
    }
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    try {
      await api.resetPassword({
        employee_id: editingEmployee.id,
        new_password: newPassword
      });
      toast.success('Password reset successfully');
      setNewPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  const getInitials = (name) => {
    return name?.split(' ').map(n => n[0]).join('').toUpperCase() || '?';
  };

  const getRoleBadge = (role) => {
    const styles = {
      admin: 'bg-purple-500/15 text-purple-700 dark:text-purple-400',
      hr: 'bg-blue-500/15 text-blue-700 dark:text-blue-400',
      manager: 'bg-green-500/15 text-green-700 dark:text-green-400',
      employee: 'bg-gray-500/15 text-gray-700 dark:text-gray-400'
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[role] || styles.employee}`}>
        {role}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading employees...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="employees-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Employees</h1>
          <p className="text-muted-foreground">Manage your team members</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search employees..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-full sm:w-64"
              data-testid="employee-search"
            />
          </div>

          {/* Add Employee Button */}
          {isAdmin && (
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full" data-testid="add-employee-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Employee
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle className="font-['Outfit']">Add New Employee</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleAddEmployee} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2 space-y-2">
                      <Label>Full Name</Label>
                      <Input
                        value={formData.full_name}
                        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                        required
                        data-testid="emp-name-input"
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        required
                        data-testid="emp-email-input"
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Password</Label>
                      <Input
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="Set initial password"
                        required
                        data-testid="emp-password-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Role</Label>
                      <Select
                        value={formData.role}
                        onValueChange={(v) => setFormData({ ...formData, role: v })}
                      >
                        <SelectTrigger data-testid="emp-role-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="employee">Employee</SelectItem>
                          <SelectItem value="manager">Manager</SelectItem>
                          <SelectItem value="hr">HR</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Department</Label>
                      <Input
                        value={formData.department}
                        onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                        required
                        data-testid="emp-dept-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Position</Label>
                      <Input
                        value={formData.position}
                        onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                        required
                        data-testid="emp-position-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        data-testid="emp-phone-input"
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Monthly Salary ($)</Label>
                      <Input
                        type="number"
                        value={formData.salary}
                        onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
                        data-testid="emp-salary-input"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="emp-submit-btn">
                      Add Employee
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Employee Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total</p>
            <p className="text-2xl font-bold font-['Outfit']">{employees.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Active</p>
            <p className="text-2xl font-bold font-['Outfit'] text-green-600">
              {employees.filter(e => e.status === 'active').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Departments</p>
            <p className="text-2xl font-bold font-['Outfit']">
              {new Set(employees.map(e => e.department).filter(Boolean)).size}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Managers</p>
            <p className="text-2xl font-bold font-['Outfit']">
              {employees.filter(e => e.role === 'manager').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Employees Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Position</TableHead>
                  <TableHead>Contact</TableHead>
                  {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEmployees.length > 0 ? (
                  filteredEmployees.map((emp) => (
                    <TableRow key={emp.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar>
                            <AvatarFallback className="bg-primary text-primary-foreground">
                              {getInitials(emp.full_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{emp.full_name}</p>
                            <p className="text-sm text-muted-foreground">{emp.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{getRoleBadge(emp.role)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-muted-foreground" />
                          {emp.department || 'N/A'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Briefcase className="w-4 h-4 text-muted-foreground" />
                          {emp.position || 'N/A'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {emp.phone && (
                            <div className="flex items-center gap-2 text-sm">
                              <Phone className="w-3 h-3" />
                              {emp.phone}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleEditClick(emp)}
                              className="text-muted-foreground hover:text-foreground"
                              data-testid={`edit-emp-${emp.id}`}
                            >
                              <Pencil className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteEmployee(emp.id)}
                              className="text-destructive hover:text-destructive"
                              data-testid={`delete-emp-${emp.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12">
                      <p className="text-muted-foreground">No employees found</p>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Edit Employee Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Outfit']">Edit Employee</DialogTitle>
          </DialogHeader>
          {editingEmployee && (
            <form onSubmit={handleEditEmployee} className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    value={editingEmployee.full_name || ''}
                    onChange={(e) => setEditingEmployee({ ...editingEmployee, full_name: e.target.value })}
                    required
                    data-testid="edit-emp-name"
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={editingEmployee.email || ''}
                    disabled
                    className="bg-muted"
                  />
                  <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select
                    value={editingEmployee.role}
                    onValueChange={(v) => setEditingEmployee({ ...editingEmployee, role: v })}
                  >
                    <SelectTrigger data-testid="edit-emp-role">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="employee">Employee</SelectItem>
                      <SelectItem value="manager">Manager</SelectItem>
                      <SelectItem value="hr">HR</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={editingEmployee.status || 'active'}
                    onValueChange={(v) => setEditingEmployee({ ...editingEmployee, status: v })}
                  >
                    <SelectTrigger data-testid="edit-emp-status">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Department</Label>
                  <Input
                    value={editingEmployee.department || ''}
                    onChange={(e) => setEditingEmployee({ ...editingEmployee, department: e.target.value })}
                    data-testid="edit-emp-dept"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Position</Label>
                  <Input
                    value={editingEmployee.position || ''}
                    onChange={(e) => setEditingEmployee({ ...editingEmployee, position: e.target.value })}
                    data-testid="edit-emp-position"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input
                    value={editingEmployee.phone || ''}
                    onChange={(e) => setEditingEmployee({ ...editingEmployee, phone: e.target.value })}
                    data-testid="edit-emp-phone"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Salary ($)</Label>
                  <Input
                    type="number"
                    value={editingEmployee.salary || ''}
                    onChange={(e) => setEditingEmployee({ ...editingEmployee, salary: e.target.value })}
                    data-testid="edit-emp-salary"
                  />
                </div>
              </div>

              {/* Reset Password Section */}
              <div className="pt-4 border-t border-border">
                <Label className="text-sm font-medium">Reset Password</Label>
                <p className="text-xs text-muted-foreground mb-2">Set a new password for this employee</p>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    placeholder="New password (min 6 chars)"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="flex-1"
                    data-testid="reset-password-input"
                  />
                  <Button 
                    type="button" 
                    variant="secondary"
                    onClick={handleResetPassword}
                    data-testid="reset-password-btn"
                  >
                    Reset
                  </Button>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="edit-emp-submit">
                  Save Changes
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EmployeesPage;
