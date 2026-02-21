import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Calendar } from '../components/ui/calendar';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import { toast } from 'sonner';
import { CalendarDays, Plus, Users, Palmtree, Calendar as CalendarIcon, Trash2, UserCircle } from 'lucide-react';
import { format, isSameDay, parseISO, isWithinInterval, startOfDay, endOfDay } from 'date-fns';

const CalendarPage = () => {
  const { user } = useAuth();
  const [events, setEvents] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [isAddEventOpen, setIsAddEventOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    event_type: 'event',
    start_date: '',
    end_date: ''
  });

  const isAdmin = user?.role === 'admin' || user?.role === 'hr';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [eventsRes, leavesRes] = await Promise.all([
        api.getEvents(),
        api.getLeaves()
      ]);
      setEvents(eventsRes.data);
      // Only show approved leaves on calendar
      setLeaves(leavesRes.data.filter(l => l.status === 'approved'));
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEvent = async (e) => {
    e.preventDefault();
    try {
      await api.createEvent(eventForm);
      toast.success('Event added to calendar');
      setIsAddEventOpen(false);
      setEventForm({ title: '', description: '', event_type: 'event', start_date: '', end_date: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to add event');
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Delete this event?')) return;
    try {
      await api.deleteEvent(eventId);
      toast.success('Event deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete event');
    }
  };

  // Combine events and leaves for calendar display
  const getAllCalendarItems = () => {
    const calendarItems = [
      ...events.map(e => ({ ...e, itemType: 'event' })),
      ...leaves.map(l => ({
        id: l.id,
        title: `${l.employee_name} - ${l.leave_type} Leave`,
        description: l.reason,
        event_type: 'leave',
        start_date: l.start_date,
        end_date: l.end_date,
        employee_name: l.employee_name,
        itemType: 'leave'
      }))
    ];
    return calendarItems;
  };

  const getItemsForDate = (date) => {
    const items = getAllCalendarItems();
    return items.filter(item => {
      try {
        const start = startOfDay(parseISO(item.start_date));
        const end = endOfDay(parseISO(item.end_date));
        return isWithinInterval(date, { start, end });
      } catch {
        return false;
      }
    });
  };

  const getFilteredItems = (date) => {
    const items = getItemsForDate(date);
    if (activeTab === 'all') return items;
    if (activeTab === 'leaves') return items.filter(i => i.event_type === 'leave');
    if (activeTab === 'holidays') return items.filter(i => i.event_type === 'holiday');
    if (activeTab === 'events') return items.filter(i => !['leave', 'holiday'].includes(i.event_type));
    return items;
  };

  const selectedDateItems = getFilteredItems(selectedDate);

  const getEventTypeBadge = (type) => {
    const styles = {
      leave: 'bg-orange-500/15 text-orange-700 dark:text-orange-400',
      meeting: 'bg-blue-500/15 text-blue-700 dark:text-blue-400',
      holiday: 'bg-green-500/15 text-green-700 dark:text-green-400',
      event: 'bg-purple-500/15 text-purple-700 dark:text-purple-400'
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${styles[type] || styles.event}`}>
        {type}
      </span>
    );
  };

  const getEventIcon = (type) => {
    switch(type) {
      case 'leave': return <UserCircle className="w-4 h-4 text-orange-500" />;
      case 'holiday': return <Palmtree className="w-4 h-4 text-green-500" />;
      default: return <CalendarIcon className="w-4 h-4 text-purple-500" />;
    }
  };

  // Stats for the sidebar
  const upcomingLeaves = leaves.filter(l => new Date(l.start_date) >= new Date()).length;
  const upcomingHolidays = events.filter(e => e.event_type === 'holiday' && new Date(e.start_date) >= new Date()).length;
  const upcomingEvents = events.filter(e => e.event_type !== 'holiday' && new Date(e.start_date) >= new Date()).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6 animate-fade-in" data-testid="calendar-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl lg:text-3xl font-bold font-['Outfit']">Team Calendar</h1>
          <p className="text-sm text-muted-foreground">View team leaves, holidays, and events</p>
        </div>
        
        {isAdmin && (
          <Dialog open={isAddEventOpen} onOpenChange={setIsAddEventOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-full w-full sm:w-auto" data-testid="add-event-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Event
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle className="font-['Outfit']">Add Calendar Event</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddEvent} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Event Title</Label>
                  <Input
                    value={eventForm.title}
                    onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                    placeholder="e.g., Company Holiday, Team Meeting"
                    required
                    data-testid="event-title-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Event Type</Label>
                  <Select
                    value={eventForm.event_type}
                    onValueChange={(v) => setEventForm({ ...eventForm, event_type: v })}
                  >
                    <SelectTrigger data-testid="event-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="holiday">Holiday</SelectItem>
                      <SelectItem value="meeting">Meeting</SelectItem>
                      <SelectItem value="event">Event</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Date</Label>
                    <Input
                      type="date"
                      value={eventForm.start_date}
                      onChange={(e) => setEventForm({ ...eventForm, start_date: e.target.value })}
                      required
                      data-testid="event-start-date"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>End Date</Label>
                    <Input
                      type="date"
                      value={eventForm.end_date}
                      onChange={(e) => setEventForm({ ...eventForm, end_date: e.target.value })}
                      required
                      data-testid="event-end-date"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description (Optional)</Label>
                  <Textarea
                    value={eventForm.description}
                    onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
                    placeholder="Add details about this event..."
                    rows={2}
                    data-testid="event-desc-input"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsAddEventOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" data-testid="event-submit-btn">
                    Add Event
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats Cards - Mobile Responsive */}
      <div className="grid grid-cols-3 gap-2 md:gap-4">
        <Card className="p-3 md:p-4">
          <div className="flex items-center gap-2 md:gap-3">
            <div className="p-1.5 md:p-2 rounded-lg bg-orange-500/10">
              <Users className="w-4 h-4 md:w-5 md:h-5 text-orange-500" />
            </div>
            <div>
              <p className="text-xs md:text-sm text-muted-foreground">Team Leaves</p>
              <p className="text-lg md:text-2xl font-bold">{upcomingLeaves}</p>
            </div>
          </div>
        </Card>
        <Card className="p-3 md:p-4">
          <div className="flex items-center gap-2 md:gap-3">
            <div className="p-1.5 md:p-2 rounded-lg bg-green-500/10">
              <Palmtree className="w-4 h-4 md:w-5 md:h-5 text-green-500" />
            </div>
            <div>
              <p className="text-xs md:text-sm text-muted-foreground">Holidays</p>
              <p className="text-lg md:text-2xl font-bold">{upcomingHolidays}</p>
            </div>
          </div>
        </Card>
        <Card className="p-3 md:p-4">
          <div className="flex items-center gap-2 md:gap-3">
            <div className="p-1.5 md:p-2 rounded-lg bg-purple-500/10">
              <CalendarIcon className="w-4 h-4 md:w-5 md:h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-xs md:text-sm text-muted-foreground">Events</p>
              <p className="text-lg md:text-2xl font-bold">{upcomingEvents}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content - Responsive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
        {/* Calendar */}
        <Card className="lg:col-span-2">
          <CardContent className="p-2 md:p-4">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              className="rounded-md w-full"
              modifiers={{
                hasEvent: (date) => getItemsForDate(date).length > 0,
                hasLeave: (date) => getItemsForDate(date).some(i => i.event_type === 'leave'),
                hasHoliday: (date) => getItemsForDate(date).some(i => i.event_type === 'holiday')
              }}
              modifiersStyles={{
                hasEvent: {
                  fontWeight: 'bold',
                  backgroundColor: 'hsl(var(--primary) / 0.1)',
                  borderRadius: '50%'
                },
                hasLeave: {
                  backgroundColor: 'hsl(25 95% 53% / 0.15)',
                  borderRadius: '50%'
                },
                hasHoliday: {
                  backgroundColor: 'hsl(142 71% 45% / 0.15)',
                  borderRadius: '50%'
                }
              }}
              data-testid="team-calendar"
            />
          </CardContent>
        </Card>

        {/* Selected Date Events */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="font-['Outfit'] flex items-center gap-2 text-base md:text-lg">
              <CalendarDays className="w-4 h-4 md:w-5 md:h-5" />
              {format(selectedDate, 'MMM d, yyyy')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* Filter Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4 h-8">
                <TabsTrigger value="all" className="text-xs px-1">All</TabsTrigger>
                <TabsTrigger value="leaves" className="text-xs px-1">Leaves</TabsTrigger>
                <TabsTrigger value="holidays" className="text-xs px-1">Holidays</TabsTrigger>
                <TabsTrigger value="events" className="text-xs px-1">Events</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="space-y-2 mt-3 max-h-[300px] overflow-y-auto">
              {selectedDateItems.length > 0 ? (
                selectedDateItems.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-2 md:p-3 rounded-lg border border-border bg-accent/30"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 min-w-0 flex-1">
                        {getEventIcon(item.event_type)}
                        <div className="min-w-0 flex-1">
                          <h4 className="font-medium text-xs md:text-sm truncate">{item.title}</h4>
                          {item.description && (
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{item.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {getEventTypeBadge(item.event_type)}
                        {isAdmin && item.itemType === 'event' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => handleDeleteEvent(item.id)}
                          >
                            <Trash2 className="w-3 h-3 text-destructive" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6">
                  <CalendarDays className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                  <p className="text-xs text-muted-foreground">No {activeTab === 'all' ? 'items' : activeTab} on this day</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Section - Responsive Grid */}
      <Card>
        <CardHeader className="pb-2 md:pb-4">
          <CardTitle className="font-['Outfit'] text-base md:text-lg">Upcoming</CardTitle>
          <CardDescription className="text-xs md:text-sm">Next 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
            {getAllCalendarItems()
              .filter(e => new Date(e.start_date) >= new Date())
              .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
              .slice(0, 6)
              .map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 md:p-4 rounded-xl border border-border hover:border-primary/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      {getEventIcon(item.event_type)}
                      <h4 className="font-medium text-sm truncate">{item.title}</h4>
                    </div>
                    {getEventTypeBadge(item.event_type)}
                  </div>
                  {item.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{item.description}</p>
                  )}
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <CalendarDays className="w-3 h-3" />
                    {format(parseISO(item.start_date), 'MMM d')} - {format(parseISO(item.end_date), 'MMM d')}
                  </div>
                </div>
              ))}
            {getAllCalendarItems().filter(e => new Date(e.start_date) >= new Date()).length === 0 && (
              <div className="col-span-full text-center py-8">
                <p className="text-muted-foreground text-sm">No upcoming events or leaves</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CalendarPage;
