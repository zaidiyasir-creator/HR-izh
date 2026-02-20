import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Progress } from '../components/ui/progress';
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
import { toast } from 'sonner';
import { Plus, TrendingUp, Star, Sparkles, Loader2, Brain } from 'lucide-react';
import { format } from 'date-fns';

const PerformancePage = () => {
  const { user } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isInsightOpen, setIsInsightOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [insights, setInsights] = useState(null);
  const [generatingInsight, setGeneratingInsight] = useState(false);
  
  const [formData, setFormData] = useState({
    employee_id: '',
    period: '',
    goals_achieved: '',
    goals_total: '',
    rating: '',
    strengths: '',
    improvements: '',
    comments: ''
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr' || user?.role === 'manager';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [reviewsRes, empRes] = await Promise.all([
        api.getPerformanceReviews(),
        api.getEmployees()
      ]);
      setReviews(reviewsRes.data);
      setEmployees(empRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createPerformanceReview({
        ...formData,
        goals_achieved: parseInt(formData.goals_achieved),
        goals_total: parseInt(formData.goals_total),
        rating: parseFloat(formData.rating),
        strengths: formData.strengths.split('\n').filter(s => s.trim()),
        improvements: formData.improvements.split('\n').filter(s => s.trim())
      });
      toast.success('Performance review created');
      setIsAddOpen(false);
      setFormData({
        employee_id: '',
        period: '',
        goals_achieved: '',
        goals_total: '',
        rating: '',
        strengths: '',
        improvements: '',
        comments: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create review');
    }
  };

  const handleGenerateInsights = async () => {
    if (!selectedEmployee) {
      toast.error('Please select an employee');
      return;
    }
    
    setGeneratingInsight(true);
    try {
      const response = await api.generatePerformanceInsights({ employee_id: selectedEmployee });
      setInsights(response.data);
      toast.success('AI insights generated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate insights');
    } finally {
      setGeneratingInsight(false);
    }
  };

  const getRatingStars = (rating) => {
    return Array(5).fill(0).map((_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`}
      />
    ));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="performance-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Performance Management</h1>
          <p className="text-muted-foreground">Track and analyze employee performance</p>
        </div>

        {isAdmin && (
          <div className="flex gap-3">
            {/* AI Insights */}
            <Dialog open={isInsightOpen} onOpenChange={setIsInsightOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="rounded-full btn-ai" data-testid="ai-insights-btn">
                  <Sparkles className="w-4 h-4 mr-2" />
                  AI Insights
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="font-['Outfit'] flex items-center gap-2">
                    <Brain className="w-5 h-5 text-indigo-500" />
                    AI Performance Insights
                  </DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4 mt-4">
                  <div className="flex gap-4">
                    <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                      <SelectTrigger className="flex-1" data-testid="insight-employee-select">
                        <SelectValue placeholder="Select employee" />
                      </SelectTrigger>
                      <SelectContent>
                        {employees.map(emp => (
                          <SelectItem key={emp.id} value={emp.id}>
                            {emp.full_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      onClick={handleGenerateInsights}
                      disabled={generatingInsight || !selectedEmployee}
                      className="btn-ai"
                      data-testid="generate-insights-btn"
                    >
                      {generatingInsight ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 mr-2" />
                          Generate
                        </>
                      )}
                    </Button>
                  </div>

                  {insights && (
                    <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">Employee: {insights.employee_name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Generated at: {format(new Date(insights.generated_at), 'MMM d, yyyy h:mm a')}
                        </p>
                      </div>
                      
                      {insights.insights?.summary && (
                        <div>
                          <h5 className="font-medium text-sm mb-1">Summary</h5>
                          <p className="text-sm text-muted-foreground">{insights.insights.summary}</p>
                        </div>
                      )}
                      
                      {insights.insights?.strengths && (
                        <div>
                          <h5 className="font-medium text-sm mb-1">Strengths</h5>
                          <ul className="list-disc list-inside text-sm text-muted-foreground">
                            {(Array.isArray(insights.insights.strengths) 
                              ? insights.insights.strengths 
                              : [insights.insights.strengths]
                            ).map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {insights.insights?.improvements && (
                        <div>
                          <h5 className="font-medium text-sm mb-1">Areas for Improvement</h5>
                          <ul className="list-disc list-inside text-sm text-muted-foreground">
                            {(Array.isArray(insights.insights.improvements) 
                              ? insights.insights.improvements 
                              : [insights.insights.improvements]
                            ).map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {insights.insights?.actions && (
                        <div>
                          <h5 className="font-medium text-sm mb-1">Recommended Actions</h5>
                          <ul className="list-disc list-inside text-sm text-muted-foreground">
                            {(Array.isArray(insights.insights.actions) 
                              ? insights.insights.actions 
                              : [insights.insights.actions]
                            ).map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {insights.insights?.trajectory && (
                        <div>
                          <h5 className="font-medium text-sm mb-1">Growth Trajectory</h5>
                          <p className="text-sm text-muted-foreground">{insights.insights.trajectory}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>

            {/* Add Review */}
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full" data-testid="add-review-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Review
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle className="font-['Outfit']">Create Performance Review</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2 space-y-2">
                      <Label>Employee</Label>
                      <Select
                        value={formData.employee_id}
                        onValueChange={(v) => setFormData({ ...formData, employee_id: v })}
                      >
                        <SelectTrigger data-testid="review-employee">
                          <SelectValue placeholder="Select employee" />
                        </SelectTrigger>
                        <SelectContent>
                          {employees.map(emp => (
                            <SelectItem key={emp.id} value={emp.id}>
                              {emp.full_name}
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
                        placeholder="e.g., Q1 2024"
                        required
                        data-testid="review-period"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Rating (1-5)</Label>
                      <Input
                        type="number"
                        min="1"
                        max="5"
                        step="0.5"
                        value={formData.rating}
                        onChange={(e) => setFormData({ ...formData, rating: e.target.value })}
                        required
                        data-testid="review-rating"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Goals Achieved</Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.goals_achieved}
                        onChange={(e) => setFormData({ ...formData, goals_achieved: e.target.value })}
                        required
                        data-testid="review-goals-achieved"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Total Goals</Label>
                      <Input
                        type="number"
                        min="1"
                        value={formData.goals_total}
                        onChange={(e) => setFormData({ ...formData, goals_total: e.target.value })}
                        required
                        data-testid="review-goals-total"
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Strengths (one per line)</Label>
                      <Textarea
                        value={formData.strengths}
                        onChange={(e) => setFormData({ ...formData, strengths: e.target.value })}
                        placeholder="Leadership skills&#10;Problem solving&#10;Team collaboration"
                        rows={3}
                        data-testid="review-strengths"
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Areas for Improvement (one per line)</Label>
                      <Textarea
                        value={formData.improvements}
                        onChange={(e) => setFormData({ ...formData, improvements: e.target.value })}
                        placeholder="Time management&#10;Documentation&#10;Public speaking"
                        rows={3}
                        data-testid="review-improvements"
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Comments</Label>
                      <Textarea
                        value={formData.comments}
                        onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
                        data-testid="review-comments"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="review-submit-btn">
                      Create Review
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      {/* Performance Reviews */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reviews.length > 0 ? (
          reviews.map((review) => (
            <Card key={review.id} className="card-hover">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg font-['Outfit']">{review.employee_name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{review.period}</p>
                  </div>
                  <div className="flex">{getRatingStars(review.rating)}</div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Goals Progress</span>
                    <span>{review.goals_achieved}/{review.goals_total}</span>
                  </div>
                  <Progress value={(review.goals_achieved / review.goals_total) * 100} />
                </div>
                
                {review.strengths?.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-1">Strengths</p>
                    <div className="flex flex-wrap gap-1">
                      {review.strengths.slice(0, 3).map((s, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 bg-green-500/10 text-green-700 dark:text-green-400 rounded-full">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                <p className="text-xs text-muted-foreground">
                  Reviewed by {review.reviewer_name} • {format(new Date(review.created_at), 'MMM d, yyyy')}
                </p>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">No performance reviews yet</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default PerformancePage;
