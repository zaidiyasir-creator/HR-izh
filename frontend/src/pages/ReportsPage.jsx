import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import { FileText, Download, Calendar, Filter, FileSpreadsheet, Loader2, Receipt, Clock, UserCheck, CalendarDays } from 'lucide-react';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';

const ReportsPage = () => {
  const { user } = useAuth();
  const [generating, setGenerating] = useState(false);
  const [reportConfig, setReportConfig] = useState({
    report_type: 'claims',
    start_date: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
    end_date: format(endOfMonth(new Date()), 'yyyy-MM-dd'),
    format: 'pdf',
    status: 'all'
  });

  const reportTypes = [
    { 
      id: 'claims', 
      name: 'Claims Report', 
      description: 'Expense claims summary with amounts and status',
      icon: Receipt,
      color: 'text-green-500'
    },
    { 
      id: 'leaves', 
      name: 'Leave Report', 
      description: 'Leave requests, approvals, and balances',
      icon: CalendarDays,
      color: 'text-blue-500'
    },
    { 
      id: 'attendance', 
      name: 'Attendance Report', 
      description: 'Check-in/out records and working hours',
      icon: UserCheck,
      color: 'text-purple-500'
    },
    { 
      id: 'overtime', 
      name: 'Overtime Report', 
      description: 'Overtime hours summary and approvals',
      icon: Clock,
      color: 'text-orange-500'
    }
  ];

  const quickDateRanges = [
    { label: 'This Month', getValue: () => ({
      start_date: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
      end_date: format(endOfMonth(new Date()), 'yyyy-MM-dd')
    })},
    { label: 'Last 7 Days', getValue: () => ({
      start_date: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      end_date: format(new Date(), 'yyyy-MM-dd')
    })},
    { label: 'Last 30 Days', getValue: () => ({
      start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end_date: format(new Date(), 'yyyy-MM-dd')
    })},
    { label: 'Last 90 Days', getValue: () => ({
      start_date: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
      end_date: format(new Date(), 'yyyy-MM-dd')
    })}
  ];

  const handleQuickDate = (range) => {
    const dates = range.getValue();
    setReportConfig(prev => ({ ...prev, ...dates }));
  };

  const handleGenerateReport = async () => {
    if (!reportConfig.start_date || !reportConfig.end_date) {
      toast.error('Please select date range');
      return;
    }

    setGenerating(true);
    try {
      const response = await api.generateReport(reportConfig);
      
      // Check if response is an error (blob might contain JSON error)
      if (response.data instanceof Blob && response.data.type === 'application/json') {
        const text = await response.data.text();
        const error = JSON.parse(text);
        throw new Error(error.detail || 'Failed to generate report');
      }
      
      // Create blob and download
      const blob = new Blob([response.data], { 
        type: reportConfig.format === 'pdf' ? 'application/pdf' : 'text/csv' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${reportConfig.report_type}_report_${reportConfig.start_date}_to_${reportConfig.end_date}.${reportConfig.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Report generated successfully');
    } catch (error) {
      console.error('Report generation error:', error);
      // Handle blob error response
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text();
          const errorData = JSON.parse(text);
          toast.error(errorData.detail || 'Failed to generate report');
        } catch {
          toast.error('Failed to generate report');
        }
      } else {
        toast.error(error.message || error.response?.data?.detail || 'Failed to generate report');
      }
    } finally {
      setGenerating(false);
    }
  };

  const selectedReport = reportTypes.find(r => r.id === reportConfig.report_type);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Reports</h1>
          <p className="text-muted-foreground mt-1">Generate and download HR reports</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Type Selection */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Select Report Type
            </CardTitle>
            <CardDescription>Choose the type of report you want to generate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {reportTypes.map((report) => {
                const Icon = report.icon;
                const isSelected = reportConfig.report_type === report.id;
                return (
                  <div
                    key={report.id}
                    onClick={() => setReportConfig(prev => ({ ...prev, report_type: report.id }))}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50 hover:bg-muted/50'
                    }`}
                    data-testid={`report-type-${report.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg bg-muted ${report.color}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium">{report.name}</h3>
                        <p className="text-sm text-muted-foreground mt-1">{report.description}</p>
                      </div>
                      {isSelected && (
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Report Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Quick Date Selection */}
            <div className="space-y-2">
              <Label className="text-sm text-muted-foreground">Quick Select</Label>
              <div className="flex flex-wrap gap-2">
                {quickDateRanges.map((range) => (
                  <Button
                    key={range.label}
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickDate(range)}
                    className="text-xs"
                  >
                    {range.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Start Date</Label>
                <Input
                  type="date"
                  value={reportConfig.start_date}
                  onChange={(e) => setReportConfig(prev => ({ ...prev, start_date: e.target.value }))}
                  data-testid="report-start-date"
                />
              </div>
              <div className="space-y-2">
                <Label>End Date</Label>
                <Input
                  type="date"
                  value={reportConfig.end_date}
                  onChange={(e) => setReportConfig(prev => ({ ...prev, end_date: e.target.value }))}
                  data-testid="report-end-date"
                />
              </div>
            </div>

            {/* Status Filter (for claims, leaves, overtime) */}
            {['claims', 'leaves', 'overtime'].includes(reportConfig.report_type) && (
              <div className="space-y-2">
                <Label>Status Filter</Label>
                <Select
                  value={reportConfig.status}
                  onValueChange={(value) => setReportConfig(prev => ({ ...prev, status: value }))}
                >
                  <SelectTrigger data-testid="report-status-filter">
                    <SelectValue placeholder="All Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                    <SelectItem value="rejected">Rejected</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Output Format */}
            <div className="space-y-2">
              <Label>Output Format</Label>
              <Select
                value={reportConfig.format}
                onValueChange={(value) => setReportConfig(prev => ({ ...prev, format: value }))}
              >
                <SelectTrigger data-testid="report-format-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-red-500" />
                      PDF Document
                    </div>
                  </SelectItem>
                  <SelectItem value="csv">
                    <div className="flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-green-500" />
                      CSV Spreadsheet
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Generate Button */}
      <Card>
        <CardContent className="py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {selectedReport && (
                <>
                  <div className={`p-3 rounded-lg bg-muted ${selectedReport.color}`}>
                    <selectedReport.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-medium">{selectedReport.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {reportConfig.start_date} to {reportConfig.end_date} • {reportConfig.format.toUpperCase()}
                      {reportConfig.status !== 'all' && ` • ${reportConfig.status}`}
                    </p>
                  </div>
                </>
              )}
            </div>
            <Button 
              onClick={handleGenerateReport} 
              disabled={generating}
              size="lg"
              className="rounded-full w-full sm:w-auto"
              data-testid="generate-report-btn"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Generate & Download
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-muted/30">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-muted-foreground mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground">Report Information</p>
              <ul className="mt-2 space-y-1">
                <li>• Reports are generated based on the selected date range</li>
                <li>• PDF reports include company branding and summary totals</li>
                <li>• CSV reports can be opened in Excel or Google Sheets</li>
                <li>• If remote storage is enabled, reports are also saved there</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReportsPage;
