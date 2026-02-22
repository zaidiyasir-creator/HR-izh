import React, { useState, useEffect, useRef } from 'react';
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
import { Plus, FileText, DollarSign, Check, X, Filter, Upload, Camera, Image, File, Eye, ZoomIn, ZoomOut, RotateCw, Download, Maximize2, Minimize2 } from 'lucide-react';
import { format } from 'date-fns';

const ClaimsPage = () => {
  const { user } = useAuth();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [formData, setFormData] = useState({
    claim_type: 'travel',
    amount: '',
    description: '',
    date: '',
    receipt_url: ''
  });
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptPreview, setReceiptPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [viewingReceipt, setViewingReceipt] = useState(null);
  const [viewerZoom, setViewerZoom] = useState(1);
  const [viewerRotation, setViewerRotation] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const isAdmin = user?.role === 'admin' || user?.role === 'hr' || user?.role === 'manager';

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      const response = await api.getClaims();
      setClaims(response.data);
    } catch (error) {
      toast.error('Failed to fetch claims');
    } finally {
      setLoading(false);
    }
  };

  const filteredClaims = claims.filter(claim => 
    statusFilter === 'all' || claim.status === statusFilter
  );

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'application/pdf'];
      if (!allowedTypes.includes(file.type)) {
        toast.error('Invalid file type. Allowed: PNG, JPG, WebP, PDF');
        return;
      }
      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File too large. Max 5MB allowed');
        return;
      }
      setReceiptFile(file);
      
      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setReceiptPreview(e.target.result);
        reader.readAsDataURL(file);
      } else {
        setReceiptPreview(null);
      }
    }
  };

  const uploadReceipt = async () => {
    if (!receiptFile) return null;
    
    setUploading(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', receiptFile);
      
      const response = await api.uploadReceipt(formDataUpload);
      return response.data.receipt_id;
    } catch (error) {
      toast.error('Failed to upload receipt');
      return null;
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    let receiptId = null;
    if (receiptFile) {
      receiptId = await uploadReceipt();
      if (!receiptId) return; // Upload failed
    }
    
    try {
      await api.createClaim({
        ...formData,
        amount: parseFloat(formData.amount),
        receipt_url: receiptId || formData.receipt_url
      });
      toast.success('Claim submitted');
      setIsAddOpen(false);
      setFormData({ claim_type: 'travel', amount: '', description: '', date: '', receipt_url: '' });
      setReceiptFile(null);
      setReceiptPreview(null);
      fetchClaims();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit claim');
    }
  };

  const handleViewReceipt = async (receiptId) => {
    try {
      const response = await api.getReceipt(receiptId);
      setViewingReceipt(response.data);
      setViewerZoom(1);
      setViewerRotation(0);
      setIsFullscreen(false);
    } catch (error) {
      toast.error('Failed to load receipt');
    }
  };

  const handleCloseViewer = () => {
    setViewingReceipt(null);
    setViewerZoom(1);
    setViewerRotation(0);
    setIsFullscreen(false);
  };

  const handleZoomIn = () => setViewerZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setViewerZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleRotate = () => setViewerRotation(prev => (prev + 90) % 360);
  const handleResetView = () => { setViewerZoom(1); setViewerRotation(0); };

  const handleDownload = () => {
    if (!viewingReceipt) return;
    const link = document.createElement('a');
    link.href = viewingReceipt.data;
    link.download = viewingReceipt.original_filename || 'receipt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleApprove = async (id) => {
    try {
      await api.updateClaim(id, { status: 'approved' });
      toast.success('Claim approved');
      fetchClaims();
    } catch (error) {
      toast.error('Failed to approve');
    }
  };

  const handleReject = async (id) => {
    try {
      await api.updateClaim(id, { status: 'rejected' });
      toast.success('Claim rejected');
      fetchClaims();
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

  const totalPending = claims.filter(c => c.status === 'pending').reduce((a, c) => a + c.amount, 0);
  const totalApproved = claims.filter(c => c.status === 'approved').reduce((a, c) => a + c.amount, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="claims-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Claim Management</h1>
          <p className="text-muted-foreground">Submit and manage expense claims</p>
        </div>

        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="rounded-full" data-testid="submit-claim-btn">
              <Plus className="w-4 h-4 mr-2" />
              Submit Claim
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-['Outfit']">Submit Expense Claim</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Claim Type</Label>
                <Select
                  value={formData.claim_type}
                  onValueChange={(v) => setFormData({ ...formData, claim_type: v })}
                >
                  <SelectTrigger data-testid="claim-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="travel">Travel</SelectItem>
                    <SelectItem value="meal">Meal</SelectItem>
                    <SelectItem value="medical">Medical</SelectItem>
                    <SelectItem value="equipment">Equipment</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Amount ($)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    required
                    data-testid="claim-amount"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                    data-testid="claim-date"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  data-testid="claim-description"
                />
              </div>
              
              {/* Receipt Upload Section */}
              <div className="space-y-2">
                <Label>Receipt (Optional)</Label>
                <div className="flex flex-col gap-3">
                  <div className="flex gap-2">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileSelect}
                      accept="image/png,image/jpeg,image/jpg,image/webp,application/pdf"
                      className="hidden"
                    />
                    <input
                      type="file"
                      ref={cameraInputRef}
                      onChange={handleFileSelect}
                      accept="image/*"
                      capture="environment"
                      className="hidden"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      className="flex-1"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Upload File
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => cameraInputRef.current?.click()}
                      className="flex-1"
                    >
                      <Camera className="w-4 h-4 mr-2" />
                      Take Photo
                    </Button>
                  </div>
                  
                  {receiptFile && (
                    <div className="flex items-center gap-2 p-2 bg-muted rounded-lg">
                      {receiptFile.type.startsWith('image/') ? (
                        <Image className="w-4 h-4 text-blue-500" />
                      ) : (
                        <File className="w-4 h-4 text-red-500" />
                      )}
                      <span className="text-sm truncate flex-1">{receiptFile.name}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setReceiptFile(null);
                          setReceiptPreview(null);
                        }}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                  
                  {receiptPreview && (
                    <div className="relative">
                      <img
                        src={receiptPreview}
                        alt="Receipt preview"
                        className="max-h-32 rounded-lg object-contain mx-auto border"
                      />
                    </div>
                  )}
                  
                  <p className="text-xs text-muted-foreground">
                    Accepted: PNG, JPG, WebP, PDF (Max 5MB)
                  </p>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={uploading} data-testid="claim-submit-btn">
                  {uploading ? 'Uploading...' : 'Submit Claim'}
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
                <DollarSign className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold font-['Outfit']">${totalPending.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-green-500/10">
                <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Approved</p>
                <p className="text-2xl font-bold font-['Outfit']">${totalApproved.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-blue-500/10">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Claims</p>
                <p className="text-2xl font-bold font-['Outfit']">{claims.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Claims Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-['Outfit']">Claims History</CardTitle>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]" data-testid="claim-status-filter">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Receipt</TableHead>
                  <TableHead>Status</TableHead>
                  {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredClaims.length > 0 ? (
                  filteredClaims.map((claim) => (
                    <TableRow key={claim.id}>
                      <TableCell className="font-medium">{claim.employee_name}</TableCell>
                      <TableCell className="capitalize">{claim.claim_type}</TableCell>
                      <TableCell>${claim.amount.toFixed(2)}</TableCell>
                      <TableCell>{format(new Date(claim.date), 'MMM d, yyyy')}</TableCell>
                      <TableCell className="max-w-xs truncate">{claim.description}</TableCell>
                      <TableCell>
                        {claim.receipt_url ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleViewReceipt(claim.receipt_url)}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                      <TableCell>{getStatusBadge(claim.status)}</TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          {claim.status === 'pending' && (
                            <div className="flex justify-end gap-2">
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => handleApprove(claim.id)}
                                className="text-green-600 hover:text-green-700 hover:bg-green-500/10"
                                data-testid={`approve-claim-${claim.id}`}
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => handleReject(claim.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-500/10"
                                data-testid={`reject-claim-${claim.id}`}
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
                    <TableCell colSpan={8} className="text-center py-12">
                      <FileText className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                      <p className="text-muted-foreground">
                        {statusFilter === 'all' ? 'No claims submitted' : `No ${statusFilter} claims`}
                      </p>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Receipt Viewer Dialog */}
      <Dialog open={!!viewingReceipt} onOpenChange={handleCloseViewer}>
        <DialogContent className={`${isFullscreen ? 'max-w-[95vw] h-[95vh]' : 'max-w-4xl'} flex flex-col`}>
          <DialogHeader className="flex-shrink-0">
            <div className="flex items-center justify-between">
              <DialogTitle className="font-['Outfit']">Receipt Viewer</DialogTitle>
              {viewingReceipt && (
                <div className="flex items-center gap-1">
                  {viewingReceipt.content_type?.startsWith('image/') && (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleZoomOut}
                        disabled={viewerZoom <= 0.5}
                        title="Zoom Out"
                      >
                        <ZoomOut className="w-4 h-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground min-w-[50px] text-center">
                        {Math.round(viewerZoom * 100)}%
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleZoomIn}
                        disabled={viewerZoom >= 3}
                        title="Zoom In"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleRotate}
                        title="Rotate"
                      >
                        <RotateCw className="w-4 h-4" />
                      </Button>
                    </>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                  >
                    {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleDownload}
                    title="Download"
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
          </DialogHeader>
          
          {viewingReceipt && (
            <div className="flex-1 overflow-auto mt-2">
              <p className="text-sm text-muted-foreground mb-3 flex-shrink-0">
                File: {viewingReceipt.original_filename}
                {viewingReceipt.storage_type && (
                  <span className="ml-2 text-xs px-2 py-0.5 bg-muted rounded">
                    {viewingReceipt.storage_type === 'remote' ? 'Remote Storage' : 'Local Storage'}
                  </span>
                )}
              </p>
              
              {/* Image Viewer */}
              {viewingReceipt.content_type?.startsWith('image/') && (
                <div 
                  className={`${isFullscreen ? 'h-[calc(95vh-150px)]' : 'max-h-[60vh]'} overflow-auto bg-muted/30 rounded-lg border flex items-center justify-center p-4`}
                >
                  <img
                    src={viewingReceipt.data}
                    alt="Receipt"
                    className="transition-transform duration-200"
                    style={{
                      transform: `scale(${viewerZoom}) rotate(${viewerRotation}deg)`,
                      transformOrigin: 'center center',
                      maxWidth: viewerZoom > 1 ? 'none' : '100%',
                      maxHeight: viewerZoom > 1 ? 'none' : '100%',
                    }}
                    onDoubleClick={handleResetView}
                    draggable={false}
                  />
                </div>
              )}
              
              {/* PDF Viewer */}
              {viewingReceipt.content_type === 'application/pdf' && (
                <div className={`${isFullscreen ? 'h-[calc(95vh-150px)]' : 'h-[60vh]'} w-full rounded-lg border overflow-hidden`}>
                  <iframe
                    src={viewingReceipt.data}
                    title="PDF Receipt"
                    className="w-full h-full"
                    style={{ border: 'none' }}
                  />
                </div>
              )}
              
              {/* Unsupported Type */}
              {!viewingReceipt.content_type?.startsWith('image/') && 
               viewingReceipt.content_type !== 'application/pdf' && (
                <div className="flex flex-col items-center justify-center gap-4 py-12">
                  <File className="w-16 h-16 text-muted-foreground" />
                  <p className="text-muted-foreground">Unable to preview this file type</p>
                  <Button onClick={handleDownload}>
                    <Download className="w-4 h-4 mr-2" />
                    Download File
                  </Button>
                </div>
              )}
              
              {/* Image viewer instructions */}
              {viewingReceipt.content_type?.startsWith('image/') && (
                <p className="text-xs text-muted-foreground text-center mt-2">
                  Double-click image to reset view • Use buttons to zoom and rotate
                </p>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClaimsPage;
