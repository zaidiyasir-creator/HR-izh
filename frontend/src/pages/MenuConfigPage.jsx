import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { Menu, RotateCcw, Save, Eye, EyeOff, Shield } from 'lucide-react';

const ROLES = ['admin', 'hr', 'manager', 'employee'];

const MenuConfigPage = () => {
  const { user } = useAuth();
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchMenuConfig();
  }, []);

  const fetchMenuConfig = async () => {
    try {
      const response = await api.getMenuConfig();
      setMenuItems(response.data.menu_items);
    } catch (error) {
      toast.error('Failed to fetch menu configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleGlobalToggle = (menuKey) => {
    setMenuItems(prev => prev.map(item => {
      if (item.menu_key === menuKey) {
        return { ...item, hidden_globally: !item.hidden_globally };
      }
      return item;
    }));
    setHasChanges(true);
  };

  const handleRoleToggle = (menuKey, role) => {
    setMenuItems(prev => prev.map(item => {
      if (item.menu_key === menuKey) {
        const hiddenRoles = item.hidden_for_roles || [];
        const newHiddenRoles = hiddenRoles.includes(role)
          ? hiddenRoles.filter(r => r !== role)
          : [...hiddenRoles, role];
        return { ...item, hidden_for_roles: newHiddenRoles };
      }
      return item;
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateMenuConfig({ menu_items: menuItems });
      toast.success('Menu configuration saved! Changes will apply on next page load.');
      setHasChanges(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      const response = await api.resetMenuConfig();
      setMenuItems(response.data.menu_items);
      toast.success('Menu configuration reset to defaults');
      setHasChanges(false);
    } catch (error) {
      toast.error('Failed to reset configuration');
    }
  };

  const getRoleBadgeStyle = (role) => {
    const styles = {
      admin: 'bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30',
      hr: 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30',
      manager: 'bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30',
      employee: 'bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30'
    };
    return styles[role] || styles.employee;
  };

  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Shield className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
          <p className="text-muted-foreground">Only administrators can access this page</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="menu-config-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Menu Configuration</h1>
          <p className="text-muted-foreground">Control menu visibility for different roles</p>
        </div>

        <div className="flex gap-3">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="rounded-full" data-testid="reset-menu-btn">
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Reset Menu Configuration?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will restore all menu visibility settings to their default values. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleReset}>Reset</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          <Button 
            onClick={handleSave} 
            disabled={!hasChanges || saving}
            className="rounded-full"
            data-testid="save-menu-btn"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {hasChanges && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-amber-700 dark:text-amber-400 text-sm">
          You have unsaved changes. Click "Save Changes" to apply them.
        </div>
      )}

      {/* Configuration Table */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit'] flex items-center gap-2">
            <Menu className="w-5 h-5" />
            Menu Items
          </CardTitle>
          <CardDescription>
            Configure which menu items are visible globally or per role. Hidden items will not appear in the sidebar.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[180px]">Menu Item</TableHead>
                  <TableHead className="w-[120px] text-center">
                    <div className="flex items-center justify-center gap-1">
                      <EyeOff className="w-4 h-4" />
                      Hide Globally
                    </div>
                  </TableHead>
                  {ROLES.map(role => (
                    <TableHead key={role} className="text-center min-w-[100px]">
                      <Badge variant="outline" className={getRoleBadgeStyle(role)}>
                        {role.charAt(0).toUpperCase() + role.slice(1)}
                      </Badge>
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {menuItems.map((item) => (
                  <TableRow key={item.menu_key} className={item.hidden_globally ? 'opacity-50' : ''}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {item.hidden_globally ? (
                          <EyeOff className="w-4 h-4 text-muted-foreground" />
                        ) : (
                          <Eye className="w-4 h-4 text-green-600" />
                        )}
                        {item.name}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex justify-center">
                        <Switch
                          checked={item.hidden_globally}
                          onCheckedChange={() => handleGlobalToggle(item.menu_key)}
                          data-testid={`global-toggle-${item.menu_key}`}
                        />
                      </div>
                    </TableCell>
                    {ROLES.map(role => (
                      <TableCell key={role} className="text-center">
                        <div className="flex justify-center">
                          <Switch
                            checked={(item.hidden_for_roles || []).includes(role)}
                            onCheckedChange={() => handleRoleToggle(item.menu_key, role)}
                            disabled={item.hidden_globally}
                            data-testid={`role-toggle-${item.menu_key}-${role}`}
                          />
                        </div>
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-wrap gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Switch checked={false} disabled className="scale-75" />
              <span className="text-muted-foreground">Visible</span>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={true} disabled className="scale-75" />
              <span className="text-muted-foreground">Hidden</span>
            </div>
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-green-600" />
              <span className="text-muted-foreground">Globally Visible</span>
            </div>
            <div className="flex items-center gap-2">
              <EyeOff className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground">Globally Hidden</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MenuConfigPage;
