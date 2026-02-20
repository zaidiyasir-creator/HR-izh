import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Calendar } from '../components/ui/calendar';
import { toast } from 'sonner';
import { CalendarDays, Plus, Users } from 'lucide-react';
import { format, isSameDay, parseISO } from 'date-fns';

const CalendarPage = () => {
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await api.getEvents();
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventsForDate = (date) => {
    return events.filter(event => {
      const start = parseISO(event.start_date);
      const end = parseISO(event.end_date);
      return date >= start && date <= end;
    });
  };

  const selectedDateEvents = getEventsForDate(selectedDate);

  const getEventTypeBadge = (type) => {
    const styles = {
      leave: 'bg-orange-500/15 text-orange-700 dark:text-orange-400',
      meeting: 'bg-blue-500/15 text-blue-700 dark:text-blue-400',
      holiday: 'bg-green-500/15 text-green-700 dark:text-green-400',
      event: 'bg-purple-500/15 text-purple-700 dark:text-purple-400'
    };
    return (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[type] || styles.event}`}>
        {type}
      </span>
    );
  };

  // Highlight dates with events
  const eventDates = events.map(e => ({
    from: parseISO(e.start_date),
    to: parseISO(e.end_date)
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="calendar-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-['Outfit']">Team Calendar</h1>
          <p className="text-muted-foreground">View events, leaves, and schedules</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <Card className="lg:col-span-2">
          <CardContent className="p-4">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              className="rounded-md w-full"
              modifiers={{
                hasEvent: (date) => getEventsForDate(date).length > 0
              }}
              modifiersStyles={{
                hasEvent: {
                  fontWeight: 'bold',
                  backgroundColor: 'hsl(var(--primary) / 0.1)',
                  borderRadius: '50%'
                }
              }}
              data-testid="team-calendar"
            />
          </CardContent>
        </Card>

        {/* Selected Date Events */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Outfit'] flex items-center gap-2">
              <CalendarDays className="w-5 h-5" />
              {format(selectedDate, 'MMMM d, yyyy')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {selectedDateEvents.length > 0 ? (
              selectedDateEvents.map((event, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg border border-border bg-accent/30"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-medium text-sm">{event.title}</h4>
                    {getEventTypeBadge(event.event_type)}
                  </div>
                  {event.description && (
                    <p className="text-xs text-muted-foreground mt-1">{event.description}</p>
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    {format(parseISO(event.start_date), 'MMM d')} - {format(parseISO(event.end_date), 'MMM d')}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <CalendarDays className="w-10 h-10 mx-auto mb-2 text-muted-foreground opacity-50" />
                <p className="text-sm text-muted-foreground">No events on this day</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Events */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Outfit']">Upcoming Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {events.filter(e => new Date(e.start_date) >= new Date()).slice(0, 6).map((event, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-border hover:border-primary/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h4 className="font-medium">{event.title}</h4>
                  {getEventTypeBadge(event.event_type)}
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">{event.description}</p>
                <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
                  <CalendarDays className="w-3 h-3" />
                  {format(parseISO(event.start_date), 'MMM d')} - {format(parseISO(event.end_date), 'MMM d, yyyy')}
                </div>
              </div>
            ))}
            {events.filter(e => new Date(e.start_date) >= new Date()).length === 0 && (
              <div className="col-span-full text-center py-8">
                <p className="text-muted-foreground">No upcoming events</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CalendarPage;
