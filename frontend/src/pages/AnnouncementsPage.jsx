import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
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
import { toast } from 'sonner';
import { Plus, Megaphone, Sparkles, Send, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

const AnnouncementsPage = () => {
  const { user } = useAuth();
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isAIOpen, setIsAIOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    priority: 'normal',
    is_ai_generated: false
  });
  
  const [aiForm, setAiForm] = useState({
    topic: '',
    tone: 'professional',
    target_audience: ''
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr';

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const fetchAnnouncements = async () => {
    try {
      const response = await api.getAnnouncements();
      setAnnouncements(response.data);
    } catch (error) {
      toast.error('Failed to fetch announcements');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createAnnouncement(formData);
      toast.success('Announcement published');
      setIsAddOpen(false);
      setFormData({ title: '', content: '', priority: 'normal', is_ai_generated: false });
      fetchAnnouncements();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to publish');
    }
  };

  const handleGenerateAI = async (e) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const response = await api.generateAnnouncement(aiForm);
      setAiResult(response.data);
      toast.success('Announcement generated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'AI generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleUseGenerated = () => {
    if (aiResult) {
      setFormData({
        title: aiResult.title,
        content: aiResult.content,
        priority: 'normal',
        is_ai_generated: true
      });
      setIsAIOpen(false);
      setIsAddOpen(true);
      setAiResult(null);
    }
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      low: 'bg-gray-500/15 text-gray-700 dark:text-gray-400',
      normal: 'bg-blue-500/15 text-blue-700 dark:text-blue-400',
      high: 'bg-orange-500/15 text-orange-700 dark:text-orange-400',
      urgent: 'bg-red-500/15 text-red-700 dark:text-red-400'
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[priority]}`}>
        {priority}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="announcements-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Announcements</h1>
          <p className="text-muted-foreground">Company-wide communications</p>
        </div>

        {isAdmin && (
          <div className="flex gap-3">
            {/* AI Generate Button */}
            <Dialog open={isAIOpen} onOpenChange={setIsAIOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="rounded-full btn-ai" data-testid="ai-generate-btn">
                  <Sparkles className="w-4 h-4 mr-2" />
                  AI Generate
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-['Outfit'] flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-500" />
                    AI Announcement Generator
                  </DialogTitle>
                </DialogHeader>
                
                {!aiResult ? (
                  <form onSubmit={handleGenerateAI} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>What's the announcement about?</Label>
                      <Input
                        value={aiForm.topic}
                        onChange={(e) => setAiForm({ ...aiForm, topic: e.target.value })}
                        placeholder="e.g., New office opening, Holiday schedule, Team achievement..."
                        required
                        data-testid="ai-topic-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tone</Label>
                      <Select
                        value={aiForm.tone}
                        onValueChange={(v) => setAiForm({ ...aiForm, tone: v })}
                      >
                        <SelectTrigger data-testid="ai-tone-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="professional">Professional</SelectItem>
                          <SelectItem value="friendly">Friendly</SelectItem>
                          <SelectItem value="urgent">Urgent</SelectItem>
                          <SelectItem value="celebratory">Celebratory</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Target Audience (optional)</Label>
                      <Input
                        value={aiForm.target_audience}
                        onChange={(e) => setAiForm({ ...aiForm, target_audience: e.target.value })}
                        placeholder="e.g., All employees, Engineering team, New hires..."
                        data-testid="ai-audience-input"
                      />
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => setIsAIOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={generating} className="btn-ai" data-testid="ai-submit-btn">
                        {generating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 mr-2" />
                            Generate
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-4 mt-4">
                    <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
                      <h3 className="font-semibold text-lg mb-2">{aiResult.title}</h3>
                      <p className="text-muted-foreground whitespace-pre-wrap">{aiResult.content}</p>
                    </div>
                    <div className="flex justify-end gap-3">
                      <Button variant="outline" onClick={() => setAiResult(null)}>
                        Regenerate
                      </Button>
                      <Button onClick={handleUseGenerated} data-testid="use-generated-btn">
                        <Send className="w-4 h-4 mr-2" />
                        Use This
                      </Button>
                    </div>
                  </div>
                )}
              </DialogContent>
            </Dialog>

            {/* Manual Add Button */}
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full" data-testid="add-announcement-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  New Announcement
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-['Outfit']">Create Announcement</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      required
                      data-testid="announcement-title"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select
                      value={formData.priority}
                      onValueChange={(v) => setFormData({ ...formData, priority: v })}
                    >
                      <SelectTrigger data-testid="announcement-priority">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="normal">Normal</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Content</Label>
                    <Textarea
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                      rows={6}
                      required
                      data-testid="announcement-content"
                    />
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="announcement-submit">
                      Publish
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      {/* Announcements List */}
      <div className="space-y-4">
        {announcements.length > 0 ? (
          announcements.map((ann) => (
            <Card 
              key={ann.id} 
              className={`card-hover ${ann.is_ai_generated ? 'animate-pulse-glow' : ''}`}
            >
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold">{ann.title}</h3>
                      {ann.is_ai_generated && (
                        <Badge variant="outline" className="text-indigo-500 border-indigo-500/50">
                          <Sparkles className="w-3 h-3 mr-1" />
                          AI
                        </Badge>
                      )}
                    </div>
                    <p className="text-muted-foreground whitespace-pre-wrap">{ann.content}</p>
                    <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
                      <span>By {ann.author_name}</span>
                      <span>•</span>
                      <span>{format(new Date(ann.created_at), 'MMM d, yyyy h:mm a')}</span>
                    </div>
                  </div>
                  <div>
                    {getPriorityBadge(ann.priority)}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <Megaphone className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">No announcements yet</p>
              {isAdmin && (
                <p className="text-sm text-muted-foreground mt-1">
                  Create your first announcement to keep everyone informed
                </p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AnnouncementsPage;
