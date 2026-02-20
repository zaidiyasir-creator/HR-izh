import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import { Settings, Sun, Moon, Palette, Building2, Save, Lock } from 'lucide-react';

const SettingsPage = () => {
  const { user } = useAuth();
  const { theme, toggleTheme, primaryColor, setPrimaryColor } = useTheme();
  const [settings, setSettings] = useState({
    company_name: 'VANTAGE HR',
    company_logo: '',
    leave_policies: { annual: 14, sick: 14, personal: 5 }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [changingPassword, setChangingPassword] = useState(false);

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.getSettings();
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isAdmin) {
      toast.error('Only admins can change settings');
      return;
    }
    
    setSaving(true);
    try {
      await api.updateSettings(settings);
      toast.success('Settings saved');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const colorPresets = [
    { name: 'Slate', value: '#0F172A' },
    { name: 'Blue', value: '#1E40AF' },
    { name: 'Indigo', value: '#4338CA' },
    { name: 'Purple', value: '#7C3AED' },
    { name: 'Teal', value: '#0D9488' },
    { name: 'Emerald', value: '#059669' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Settings</h1>
        <p className="text-muted-foreground">Customize your VANTAGE HR experience</p>
      </div>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit'] flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Appearance
          </CardTitle>
          <CardDescription>Customize the look and feel</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Theme Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base">Dark Mode</Label>
              <p className="text-sm text-muted-foreground">
                Switch between light and dark themes
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Sun className="w-4 h-4 text-muted-foreground" />
              <Switch
                checked={theme === 'dark'}
                onCheckedChange={toggleTheme}
                data-testid="theme-switch"
              />
              <Moon className="w-4 h-4 text-muted-foreground" />
            </div>
          </div>

          {/* Color Presets */}
          <div className="space-y-3">
            <Label className="text-base">Accent Color</Label>
            <div className="flex flex-wrap gap-3">
              {colorPresets.map((color) => (
                <button
                  key={color.value}
                  onClick={() => setPrimaryColor(color.value)}
                  className={`w-10 h-10 rounded-full transition-all hover:scale-110 ${
                    primaryColor === color.value ? 'ring-2 ring-offset-2 ring-primary' : ''
                  }`}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                  data-testid={`color-${color.name.toLowerCase()}`}
                />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Company Settings - Admin Only */}
      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              Company Settings
            </CardTitle>
            <CardDescription>Configure organization details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>Company Name</Label>
                <Input
                  value={settings.company_name}
                  onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
                  placeholder="Your Company Name"
                  data-testid="company-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Logo URL</Label>
                <Input
                  value={settings.company_logo || ''}
                  onChange={(e) => setSettings({ ...settings, company_logo: e.target.value })}
                  placeholder="https://..."
                  data-testid="company-logo-input"
                />
              </div>
            </div>

            {/* Leave Policies */}
            <div className="space-y-3">
              <Label className="text-base">Default Leave Policies (days per year)</Label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Annual Leave</Label>
                  <Input
                    type="number"
                    min="0"
                    value={settings.leave_policies?.annual || 14}
                    onChange={(e) => setSettings({
                      ...settings,
                      leave_policies: { ...settings.leave_policies, annual: parseInt(e.target.value) }
                    })}
                    data-testid="annual-leave-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Sick Leave</Label>
                  <Input
                    type="number"
                    min="0"
                    value={settings.leave_policies?.sick || 14}
                    onChange={(e) => setSettings({
                      ...settings,
                      leave_policies: { ...settings.leave_policies, sick: parseInt(e.target.value) }
                    })}
                    data-testid="sick-leave-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Personal Leave</Label>
                  <Input
                    type="number"
                    min="0"
                    value={settings.leave_policies?.personal || 5}
                    onChange={(e) => setSettings({
                      ...settings,
                      leave_policies: { ...settings.leave_policies, personal: parseInt(e.target.value) }
                    })}
                    data-testid="personal-leave-input"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={saving} className="rounded-full" data-testid="save-settings-btn">
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* User Info */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit'] flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Account Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm text-muted-foreground">Name</Label>
              <p className="font-medium">{user?.full_name}</p>
            </div>
            <div>
              <Label className="text-sm text-muted-foreground">Email</Label>
              <p className="font-medium">{user?.email}</p>
            </div>
            <div>
              <Label className="text-sm text-muted-foreground">Role</Label>
              <p className="font-medium capitalize">{user?.role}</p>
            </div>
            <div>
              <Label className="text-sm text-muted-foreground">Department</Label>
              <p className="font-medium">{user?.department || 'Not assigned'}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
