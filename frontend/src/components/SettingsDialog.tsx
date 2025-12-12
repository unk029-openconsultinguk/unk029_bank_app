import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from '@/hooks/use-toast';

interface SettingsDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

interface UserSettings {
  notifications_enabled: boolean;
  two_factor_auth: boolean;
  biometric_login: boolean;
}

const SettingsDialog = ({ isOpen, onOpenChange }: SettingsDialogProps) => {
  const [settings, setSettings] = useState<UserSettings>({
    notifications_enabled: true,
    two_factor_auth: false,
    biometric_login: false,
  });
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Fetch user settings from localStorage or API
      setFetching(true);
      try {
        const savedSettings = localStorage.getItem('user_settings');
        if (savedSettings) {
          setSettings(JSON.parse(savedSettings));
        }
      } catch (error) {
        console.error('Error loading settings:', error);
      } finally {
        setFetching(false);
      }
    }
  }, [isOpen]);

  const handleSettingChange = (setting: keyof UserSettings) => {
    setSettings(prev => ({
      ...prev,
      [setting]: !prev[setting],
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Save settings to localStorage
      localStorage.setItem('user_settings', JSON.stringify(settings));

      // Optional: Send to backend API
      const accountNo = localStorage.getItem('account_number');
      if (accountNo) {
        await fetch(`/account/${accountNo}/settings`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(settings),
        }).catch(err => console.warn('Settings API not available:', err));
      }

      toast({
        title: 'Success',
        description: 'Settings saved successfully',
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Error saving settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to save settings',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Manage your account preferences and security settings
          </DialogDescription>
        </DialogHeader>
        {fetching ? (
          <div className="flex justify-center items-center py-8">
            <p className="text-sm text-muted-foreground">Loading settings...</p>
          </div>
        ) : (
          <div className="grid gap-6 py-4">
            <div className="flex items-center justify-between space-x-4">
              <div className="space-y-1">
                <Label htmlFor="notifications" className="font-semibold">
                  Enable Notifications
                </Label>
                <p className="text-xs text-muted-foreground">
                  Receive notifications about your transactions
                </p>
              </div>
              <Switch
                id="notifications"
                checked={settings.notifications_enabled}
                onCheckedChange={() => handleSettingChange('notifications_enabled')}
              />
            </div>

            <div className="border-t pt-4" />

            <div className="flex items-center justify-between space-x-4">
              <div className="space-y-1">
                <Label htmlFor="twofa" className="font-semibold">
                  Two-Factor Authentication
                </Label>
                <p className="text-xs text-muted-foreground">
                  Require an additional code for login
                </p>
              </div>
              <Switch
                id="twofa"
                checked={settings.two_factor_auth}
                onCheckedChange={() => handleSettingChange('two_factor_auth')}
              />
            </div>

            <div className="border-t pt-4" />

            <div className="flex items-center justify-between space-x-4">
              <div className="space-y-1">
                <Label htmlFor="biometric" className="font-semibold">
                  Biometric Login
                </Label>
                <p className="text-xs text-muted-foreground">
                  Use fingerprint or face recognition
                </p>
              </div>
              <Switch
                id="biometric"
                checked={settings.biometric_login}
                onCheckedChange={() => handleSettingChange('biometric_login')}
              />
            </div>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || fetching}>
            {loading ? 'Saving...' : 'Save Settings'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsDialog;
