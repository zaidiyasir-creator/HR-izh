import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
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
import { MapPin, Plus, Trash2, Building2, Users, Pencil, FolderTree } from 'lucide-react';

const GeofenceSettingsPage = () => {
  const { user } = useAuth();
  const [officeLocations, setOfficeLocations] = useState([]);
  const [categories, setCategories] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [isAddOfficeOpen, setIsAddOfficeOpen] = useState(false);
  const [isAddDeptOpen, setIsAddDeptOpen] = useState(false);
  const [isEditCategoryOpen, setIsEditCategoryOpen] = useState(false);
  const [isEditDeptOpen, setIsEditDeptOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingDept, setEditingDept] = useState(null);
  
  const [officeForm, setOfficeForm] = useState({
    name: '',
    address: '',
    latitude: '',
    longitude: '',
    default_radius: 500
  });
  
  const [deptForm, setDeptForm] = useState({
    name: '',
    description: '',
    geofence_category: 'office'
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [locRes, catRes, deptRes, empRes] = await Promise.all([
        api.getOfficeLocations(),
        api.getGeofenceCategories(),
        api.getDepartmentGeofence().catch(() => ({ data: [] })),
        api.getEmployees()
      ]);
      setOfficeLocations(locRes.data);
      setCategories(catRes.data);
      setDepartmentAssignments(deptRes.data);
      setEmployees(empRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddOffice = async (e) => {
    e.preventDefault();
    try {
      await api.createOfficeLocation({
        ...officeForm,
        latitude: parseFloat(officeForm.latitude),
        longitude: parseFloat(officeForm.longitude),
        default_radius: parseInt(officeForm.default_radius)
      });
      toast.success('Office location added');
      setIsAddOfficeOpen(false);
      setOfficeForm({ name: '', address: '', latitude: '', longitude: '', default_radius: 500 });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add location');
    }
  };

  const handleDeleteOffice = async (id) => {
    if (!window.confirm('Delete this office location?')) return;
    try {
      await api.deleteOfficeLocation(id);
      toast.success('Office location deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleAddDeptAssignment = async (e) => {
    e.preventDefault();
    try {
      await api.setDepartmentGeofence(deptForm);
      toast.success('Department geofence assigned');
      setIsAddDeptOpen(false);
      setDeptForm({ department: '', geofence_category: 'office' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign');
    }
  };

  const handleDeleteDeptAssignment = async (department) => {
    try {
      await api.deleteDepartmentGeofence(department);
      toast.success('Assignment removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleEditCategory = (cat) => {
    setEditingCategory({ ...cat });
    setIsEditCategoryOpen(true);
  };

  const handleSaveCategory = async () => {
    try {
      await api.updateGeofenceCategory(editingCategory.name, {
        display_name: editingCategory.display_name,
        radius: parseInt(editingCategory.radius),
        description: editingCategory.description
      });
      toast.success('Category updated');
      setIsEditCategoryOpen(false);
      setEditingCategory(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const formatRadius = (radius) => {
    if (radius === -1 || radius > 50000) return 'Unlimited';
    if (radius >= 1000) return `${(radius / 1000).toFixed(1)} km`;
    return `${radius} m`;
  };

  // Get unique departments
  const departments = [...new Set(employees.map(e => e.department).filter(Boolean))];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="geofence-settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Geofence Settings</h1>
        <p className="text-muted-foreground">Configure location-based attendance restrictions</p>
      </div>

      {/* Office Locations */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Office Locations
            </CardTitle>
            <CardDescription>Define office coordinates for geofencing</CardDescription>
          </div>
          {isAdmin && (
            <Dialog open={isAddOfficeOpen} onOpenChange={setIsAddOfficeOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full" data-testid="add-office-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Office
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-['Outfit']">Add Office Location</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleAddOffice} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Office Name</Label>
                    <Input
                      value={officeForm.name}
                      onChange={(e) => setOfficeForm({ ...officeForm, name: e.target.value })}
                      placeholder="Main Office"
                      required
                      data-testid="office-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Address</Label>
                    <Input
                      value={officeForm.address}
                      onChange={(e) => setOfficeForm({ ...officeForm, address: e.target.value })}
                      placeholder="123 Business Street, City"
                      required
                      data-testid="office-address"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Latitude</Label>
                      <Input
                        type="number"
                        step="any"
                        value={officeForm.latitude}
                        onChange={(e) => setOfficeForm({ ...officeForm, latitude: e.target.value })}
                        placeholder="3.1390"
                        required
                        data-testid="office-lat"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Longitude</Label>
                      <Input
                        type="number"
                        step="any"
                        value={officeForm.longitude}
                        onChange={(e) => setOfficeForm({ ...officeForm, longitude: e.target.value })}
                        placeholder="101.6869"
                        required
                        data-testid="office-lng"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Default Radius (meters)</Label>
                    <Input
                      type="number"
                      value={officeForm.default_radius}
                      onChange={(e) => setOfficeForm({ ...officeForm, default_radius: e.target.value })}
                      data-testid="office-radius"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Tip: Get coordinates from Google Maps by right-clicking on a location
                  </p>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsAddOfficeOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="office-submit">
                      Add Office
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </CardHeader>
        <CardContent>
          {officeLocations.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Address</TableHead>
                  <TableHead>Coordinates</TableHead>
                  <TableHead>Default Radius</TableHead>
                  {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {officeLocations.map((loc) => (
                  <TableRow key={loc.id}>
                    <TableCell className="font-medium">{loc.name}</TableCell>
                    <TableCell>{loc.address}</TableCell>
                    <TableCell className="font-mono text-sm">{loc.latitude}, {loc.longitude}</TableCell>
                    <TableCell>{formatRadius(loc.default_radius)}</TableCell>
                    {isAdmin && (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteOffice(loc.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <MapPin className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No office locations configured</p>
              <p className="text-sm">Add an office location to enable geofencing</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Geofence Categories */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit'] flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            Geofence Categories
          </CardTitle>
          <CardDescription>Define radius limits for different employee types</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead>Display Name</TableHead>
                <TableHead>Radius</TableHead>
                <TableHead>Description</TableHead>
                {isAdmin && <TableHead className="text-right">Actions</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {categories.map((cat) => (
                <TableRow key={cat.name}>
                  <TableCell className="font-medium capitalize">{cat.name}</TableCell>
                  <TableCell>{cat.display_name}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      cat.radius === -1 ? 'bg-green-500/15 text-green-700' : 'bg-blue-500/15 text-blue-700'
                    }`}>
                      {formatRadius(cat.radius)}
                    </span>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{cat.description}</TableCell>
                  {isAdmin && (
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEditCategory(cat)}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Department Assignments */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <Users className="w-5 h-5" />
              Department Geofence Assignments
            </CardTitle>
            <CardDescription>Assign geofence categories to departments</CardDescription>
          </div>
          {isAdmin && (
            <Dialog open={isAddDeptOpen} onOpenChange={setIsAddDeptOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full" data-testid="add-dept-geofence-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Assign Department
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-['Outfit']">Assign Department Geofence</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleAddDeptAssignment} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Department</Label>
                    <Select
                      value={deptForm.department}
                      onValueChange={(v) => setDeptForm({ ...deptForm, department: v })}
                    >
                      <SelectTrigger data-testid="dept-select">
                        <SelectValue placeholder="Select department" />
                      </SelectTrigger>
                      <SelectContent>
                        {departments.map(dept => (
                          <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Geofence Category</Label>
                    <Select
                      value={deptForm.geofence_category}
                      onValueChange={(v) => setDeptForm({ ...deptForm, geofence_category: v })}
                    >
                      <SelectTrigger data-testid="category-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map(cat => (
                          <SelectItem key={cat.name} value={cat.name}>
                            {cat.display_name} ({formatRadius(cat.radius)})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsAddDeptOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="dept-submit">
                      Assign
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </CardHeader>
        <CardContent>
          {departmentAssignments.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Department</TableHead>
                  <TableHead>Geofence Category</TableHead>
                  <TableHead>Radius</TableHead>
                  {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {departmentAssignments.map((assignment) => {
                  const cat = categories.find(c => c.name === assignment.geofence_category);
                  return (
                    <TableRow key={assignment.department}>
                      <TableCell className="font-medium">{assignment.department}</TableCell>
                      <TableCell>{cat?.display_name || assignment.geofence_category}</TableCell>
                      <TableCell>{formatRadius(cat?.radius || 500)}</TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteDeptAssignment(assignment.department)}
                            className="text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No department assignments</p>
              <p className="text-sm">All departments use default "Office" category (500m)</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Category Dialog */}
      <Dialog open={isEditCategoryOpen} onOpenChange={setIsEditCategoryOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-['Outfit']">Edit Geofence Category</DialogTitle>
          </DialogHeader>
          {editingCategory && (
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Display Name</Label>
                <Input
                  value={editingCategory.display_name}
                  onChange={(e) => setEditingCategory({ ...editingCategory, display_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Radius (meters, -1 for unlimited)</Label>
                <Input
                  type="number"
                  value={editingCategory.radius}
                  onChange={(e) => setEditingCategory({ ...editingCategory, radius: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Common values: 500 (office), 1000 (campus), 5000 (field), -1 (remote/unlimited)
                </p>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={editingCategory.description || ''}
                  onChange={(e) => setEditingCategory({ ...editingCategory, description: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => setIsEditCategoryOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveCategory}>
                  Save Changes
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GeofenceSettingsPage;
