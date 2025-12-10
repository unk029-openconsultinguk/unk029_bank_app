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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';

interface AccountsDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  userName: string;
}

const AccountsDialog = ({ isOpen, onOpenChange, userName }: AccountsDialogProps) => {
  // Read-only fields
  const [fullName, setFullName] = useState(userName);
  const [accountNumber, setAccountNumber] = useState('');
  const [sortCode, setSortCode] = useState('');
  const [accountType, setAccountType] = useState('');
  
  // Editable fields
  const [email, setEmail] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  
  // Password change
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setFetching(true);
      const accountNo = localStorage.getItem('account_number');
      if (accountNo) {
        fetch(`/account/${accountNo}`)
          .then(res => res.json())
          .then(data => {
            setFullName(data.name || userName);
            setAccountNumber(accountNo);
            setSortCode(data.sortcode || data.sort_code || '');
            setAccountType(data.account_type || '');
            setEmail(data.email || '');
            setMobileNumber(data.mobile || '');
            setNewPassword('');
            setConfirmPassword('');
            setShowChangePassword(false);
          })
          .catch(err => {
            console.error('Error fetching account details:', err);
            toast({
              title: 'Error',
              description: 'Failed to load account details',
              variant: 'destructive',
            });
          })
          .finally(() => setFetching(false));
      }
    }
  }, [isOpen, userName]);

  const handleSave = async () => {
    if (!email.trim()) {
      toast({
        title: 'Error',
        description: 'Email is required',
        variant: 'destructive',
      });
      return;
    }

    if (!mobileNumber.trim()) {
      toast({
        title: 'Error',
        description: 'Mobile number is required',
        variant: 'destructive',
      });
      return;
    }

    if (showChangePassword) {
      if (!newPassword.trim()) {
        toast({
          title: 'Error',
          description: 'New password is required',
          variant: 'destructive',
        });
        return;
      }
      if (newPassword !== confirmPassword) {
        toast({
          title: 'Error',
          description: 'Passwords do not match',
          variant: 'destructive',
        });
        return;
      }
    }

    setLoading(true);
    try {
      const accountNo = localStorage.getItem('account_number');
      const payload: any = {
        email,
        mobile: mobileNumber,
      };

      if (showChangePassword && newPassword.trim()) {
        payload.password = newPassword;
      }

      const response = await fetch(`/account/${accountNo}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Account details updated successfully',
        });
        setShowChangePassword(false);
        onOpenChange(false);
      } else {
        const error = await response.json();
        toast({
          title: 'Error',
          description: error.detail || 'Failed to update account details',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error updating account:', error);
      toast({
        title: 'Error',
        description: 'Failed to update account details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Manage Account</DialogTitle>
          <DialogDescription>
            View your account information and update your details
          </DialogDescription>
        </DialogHeader>
        {fetching ? (
          <div className="flex justify-center items-center py-8">
            <p className="text-sm text-muted-foreground">Loading account details...</p>
          </div>
        ) : (
          <div className="grid gap-6 py-4">
            {/* Read-Only Account Information Section */}
            <div className="border rounded-lg p-4 bg-muted/50">
              <h3 className="font-semibold mb-4 text-sm">Account Information (Read Only)</h3>
              <div className="grid gap-3">
                <div className="grid gap-1">
                  <Label className="text-xs text-muted-foreground">Full Name</Label>
                  <div className="px-3 py-2 bg-background border rounded text-sm">
                    {fullName}
                  </div>
                </div>
                <div className="grid gap-1">
                  <Label className="text-xs text-muted-foreground">Account Number</Label>
                  <div className="px-3 py-2 bg-background border rounded text-sm font-mono">
                    {accountNumber}
                  </div>
                </div>
                {sortCode && (
                  <div className="grid gap-1">
                    <Label className="text-xs text-muted-foreground">Sort Code</Label>
                    <div className="px-3 py-2 bg-background border rounded text-sm font-mono">
                      {sortCode}
                    </div>
                  </div>
                )}
                {accountType && (
                  <div className="grid gap-1">
                    <Label className="text-xs text-muted-foreground">Account Type</Label>
                    <div className="px-3 py-2 bg-background border rounded text-sm">
                      {accountType}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Editable Fields Section */}
            <div className="space-y-4">
              <h3 className="font-semibold text-sm">Edit Account Details</h3>
              <div className="grid gap-3">
                <div className="grid gap-1">
                  <Label htmlFor="email">Email Address *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                  />
                </div>
                <div className="grid gap-1">
                  <Label htmlFor="mobileNumber">Mobile Number *</Label>
                  <Input
                    id="mobileNumber"
                    value={mobileNumber}
                    onChange={(e) => setMobileNumber(e.target.value)}
                    placeholder="Enter your mobile number"
                  />
                </div>
              </div>
            </div>

            {/* Change Password Section */}
            <div className="space-y-4">
              {!showChangePassword ? (
                <Button
                  variant="outline"
                  onClick={() => setShowChangePassword(true)}
                  className="w-full"
                >
                  Change Password
                </Button>
              ) : (
                <div className="border rounded-lg p-4 bg-muted/50">
                  <h3 className="font-semibold mb-4 text-sm">Change Password</h3>
                  <div className="grid gap-3">
                    <div className="grid gap-1">
                      <Label htmlFor="newPassword">New Password *</Label>
                      <Input
                        id="newPassword"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="Enter new password"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label htmlFor="confirmPassword">Confirm Password *</Label>
                      <Input
                        id="confirmPassword"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Confirm new password"
                      />
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setShowChangePassword(false);
                        setNewPassword('');
                        setConfirmPassword('');
                      }}
                    >
                      Cancel Password Change
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || fetching}>
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AccountsDialog;
