import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import { Settings, Sun, Moon, Palette, Building2, Save, Lock, Upload, Trash2, Image, HardDrive, Cloud, FolderOpen, CheckCircle, XCircle, Loader2 } from 'lucide-react';

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
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const fileInputRef = useRef(null);
  
  // Remote Storage State
  const [remoteStorage, setRemoteStorage] = useState({
    storage_type: 'local',
    enabled: false,
    nextcloud_url: '',
    nextcloud_username: '',
    nextcloud_password: '',
    nextcloud_folder: '/VantageHR',
    nas_path: ''
  });
  const [savingStorage, setSavingStorage] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    fetchSettings();
    if (isAdmin) {
      fetchRemoteStorageSettings();
    }
  }, [isAdmin]);

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

  const fetchRemoteStorageSettings = async () => {
    try {
      const response = await api.getRemoteStorageSettings();
      setRemoteStorage(response.data);
    } catch (error) {
      console.error('Failed to fetch remote storage settings:', error);
    }
  };

  const handleSaveRemoteStorage = async () => {
    setSavingStorage(true);
    try {
      await api.updateRemoteStorageSettings(remoteStorage);
      toast.success('Remote storage settings saved');
      setConnectionStatus(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSavingStorage(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus(null);
    try {
      const response = await api.testRemoteStorageConnection();
      setConnectionStatus(response.data);
      if (response.data.success) {
        toast.success(response.data.message);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      setConnectionStatus({ success: false, message: error.response?.data?.detail || 'Connection test failed' });
      toast.error('Connection test failed');
    } finally {
      setTestingConnection(false);
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

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordData.new_password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setChangingPassword(true);
    try {
      await api.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      toast.success('Password changed successfully');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid file type. Please upload PNG, JPG, SVG, or WebP');
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 2MB');
      return;
    }

    setUploadingLogo(true);
    try {
      await api.uploadLogo(file);
      toast.success('Logo uploaded successfully');
      fetchSettings(); // Refresh to show new logo
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload logo');
    } finally {
      setUploadingLogo(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteLogo = async () => {
    if (!window.confirm('Are you sure you want to remove the company logo?')) return;
    
    try {
      await api.deleteLogo();
      toast.success('Logo removed');
      setSettings(prev => ({ ...prev, company_logo: null, logo_filename: null }));
    } catch (error) {
      toast.error('Failed to remove logo');
    }
  };

  const colorPresets = [
    // Blues
    { name: 'Slate', value: '#0F172A' },
    { name: 'Navy', value: '#1E3A5F' },
    { name: 'Blue', value: '#1E40AF' },
    { name: 'Sky', value: '#0284C7' },
    { name: 'Cyan', value: '#0891B2' },
    // Purples & Pinks
    { name: 'Indigo', value: '#4338CA' },
    { name: 'Violet', value: '#6D28D9' },
    { name: 'Purple', value: '#7C3AED' },
    { name: 'Fuchsia', value: '#C026D3' },
    { name: 'Pink', value: '#DB2777' },
    // Greens
    { name: 'Teal', value: '#0D9488' },
    { name: 'Emerald', value: '#059669' },
    { name: 'Green', value: '#16A34A' },
    { name: 'Lime', value: '#65A30D' },
    // Warm colors
    { name: 'Orange', value: '#EA580C' },
    { name: 'Amber', value: '#D97706' },
    { name: 'Red', value: '#DC2626' },
    { name: 'Rose', value: '#E11D48' },
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
            {/* Company Logo Upload */}
            <div className="space-y-3">
              <Label className="text-base">Company Logo</Label>
              <div className="flex items-start gap-6">
                {/* Logo Preview */}
                <div className="w-32 h-32 rounded-lg border-2 border-dashed border-muted-foreground/30 flex items-center justify-center overflow-hidden bg-muted/50">
                  {settings.company_logo ? (
                    <img 
                      src={settings.company_logo} 
                      alt="Company Logo" 
                      className="max-w-full max-h-full object-contain"
                    />
                  ) : (
                    <div className="text-center text-muted-foreground">
                      <Image className="w-8 h-8 mx-auto mb-1 opacity-50" />
                      <span className="text-xs">No logo</span>
                    </div>
                  )}
                </div>
                
                {/* Upload Controls */}
                <div className="space-y-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/svg+xml,image/webp"
                    onChange={handleLogoUpload}
                    className="hidden"
                    data-testid="logo-file-input"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadingLogo}
                    className="rounded-full"
                    data-testid="upload-logo-btn"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {uploadingLogo ? 'Uploading...' : 'Upload Logo'}
                  </Button>
                  
                  {settings.company_logo && (
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={handleDeleteLogo}
                      className="rounded-full text-destructive hover:text-destructive"
                      data-testid="delete-logo-btn"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Remove Logo
                    </Button>
                  )}
                  
                  <p className="text-xs text-muted-foreground">
                    PNG, JPG, SVG, or WebP. Max 2MB.<br/>
                    Recommended: 200x200px or larger
                  </p>
                </div>
              </div>
            </div>

            {/* Company Name */}
            <div className="space-y-2">
              <Label>Company Name</Label>
              <Input
                value={settings.company_name}
                onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
                placeholder="Your Company Name"
                data-testid="company-name-input"
              />
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

      {/* Remote Storage Settings - Admin Only */}
      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <Cloud className="w-5 h-5" />
              Remote Storage
            </CardTitle>
            <CardDescription>Configure IZHcloud or NAS for storing receipts and reports</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Enable Remote Storage */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-base">Enable Remote Storage</Label>
                <p className="text-sm text-muted-foreground">
                  Store uploaded files on external storage instead of database
                </p>
              </div>
              <Switch
                checked={remoteStorage.enabled}
                onCheckedChange={(checked) => setRemoteStorage({ ...remoteStorage, enabled: checked })}
                data-testid="remote-storage-switch"
              />
            </div>

            {remoteStorage.enabled && (
              <>
                {/* Storage Type Selection */}
                <div className="space-y-2">
                  <Label>Storage Type</Label>
                  <Select
                    value={remoteStorage.storage_type}
                    onValueChange={(value) => setRemoteStorage({ ...remoteStorage, storage_type: value })}
                  >
                    <SelectTrigger data-testid="storage-type-select">
                      <SelectValue placeholder="Select storage type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nextcloud">
                        <div className="flex items-center gap-2">
                          <Cloud className="w-4 h-4" />
                          Nextcloud
                        </div>
                      </SelectItem>
                      <SelectItem value="nas">
                        <div className="flex items-center gap-2">
                          <HardDrive className="w-4 h-4" />
                          Local NAS / Network Share
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Nextcloud Settings */}
                {remoteStorage.storage_type === 'nextcloud' && (
                  <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Cloud className="w-4 h-4" />
                      Nextcloud Configuration
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2 md:col-span-2">
                        <Label>Nextcloud URL</Label>
                        <Input
                          type="url"
                          value={remoteStorage.nextcloud_url}
                          onChange={(e) => setRemoteStorage({ ...remoteStorage, nextcloud_url: e.target.value })}
                          placeholder="https://cloud.yourcompany.com"
                          data-testid="nextcloud-url-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Username</Label>
                        <Input
                          value={remoteStorage.nextcloud_username}
                          onChange={(e) => setRemoteStorage({ ...remoteStorage, nextcloud_username: e.target.value })}
                          placeholder="your-username"
                          data-testid="nextcloud-username-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>App Password</Label>
                        <Input
                          type="password"
                          value={remoteStorage.nextcloud_password}
                          onChange={(e) => setRemoteStorage({ ...remoteStorage, nextcloud_password: e.target.value })}
                          placeholder="••••••••"
                          data-testid="nextcloud-password-input"
                        />
                        <p className="text-xs text-muted-foreground">
                          Generate from Nextcloud: Settings → Security → App Passwords
                        </p>
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label>Storage Folder</Label>
                        <div className="flex items-center gap-2">
                          <FolderOpen className="w-4 h-4 text-muted-foreground" />
                          <Input
                            value={remoteStorage.nextcloud_folder}
                            onChange={(e) => setRemoteStorage({ ...remoteStorage, nextcloud_folder: e.target.value })}
                            placeholder="/VantageHR"
                            data-testid="nextcloud-folder-input"
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Files will be stored in subfolders: /receipts, /reports
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* NAS Settings */}
                {remoteStorage.storage_type === 'nas' && (
                  <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <HardDrive className="w-4 h-4" />
                      NAS / Network Share Configuration
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Mount Path</Label>
                      <Input
                        value={remoteStorage.nas_path}
                        onChange={(e) => setRemoteStorage({ ...remoteStorage, nas_path: e.target.value })}
                        placeholder="/mnt/nas/vantage-hr or /app/storage"
                        data-testid="nas-path-input"
                      />
                      <p className="text-xs text-muted-foreground">
                        The path must be mounted and writable by the application.
                        Files will be stored in subfolders: /receipts, /reports
                      </p>
                    </div>
                  </div>
                )}

                {/* Connection Status */}
                {connectionStatus && (
                  <div className={`flex items-center gap-2 p-3 rounded-lg ${
                    connectionStatus.success 
                      ? 'bg-green-500/10 text-green-700 dark:text-green-400' 
                      : 'bg-red-500/10 text-red-700 dark:text-red-400'
                  }`}>
                    {connectionStatus.success ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <XCircle className="w-5 h-5" />
                    )}
                    <span className="text-sm">{connectionStatus.message}</span>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={testingConnection || !remoteStorage.enabled}
                    className="rounded-full"
                    data-testid="test-connection-btn"
                  >
                    {testingConnection ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <CheckCircle className="w-4 h-4 mr-2" />
                    )}
                    Test Connection
                  </Button>
                  <Button
                    onClick={handleSaveRemoteStorage}
                    disabled={savingStorage}
                    className="rounded-full"
                    data-testid="save-storage-btn"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {savingStorage ? 'Saving...' : 'Save Storage Settings'}
                  </Button>
                </div>
              </>
            )}
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

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit'] flex items-center gap-2">
            <Lock className="w-5 h-5" />
            Change Password
          </CardTitle>
          <CardDescription>Update your account password</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Current Password</Label>
                <Input
                  type="password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                  required
                  data-testid="current-password-input"
                />
              </div>
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  placeholder="Min 6 characters"
                  required
                  data-testid="new-password-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Confirm New Password</Label>
                <Input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  required
                  data-testid="confirm-password-input"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={changingPassword} className="rounded-full" data-testid="change-password-btn">
                <Lock className="w-4 h-4 mr-2" />
                {changingPassword ? 'Changing...' : 'Change Password'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
