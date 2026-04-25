import { Calendar, Clock, BookOpen, GraduationCap, PenLine, FileText, FlaskConical } from 'lucide-react';
import type { ParseResponse } from '../types';

interface ScheduleViewProps {
  data: ParseResponse | null;
  onNavigate: (page: string) => void;
  onLoadDemo?: () => void;
}

const EVENT_ICONS: Record<string, typeof BookOpen> = {
  exam: GraduationCap,
  assignment: PenLine,
  quiz: FileText,
  project: FlaskConical,
  reading: BookOpen,
  lecture: BookOpen,
  lab: FlaskConical,
  other: Calendar,
};

const EVENT_COLORS: Record<string, string> = {
  exam: 'bg-red-100 text-red-700 border-red-200',
  assignment: 'bg-blue-100 text-blue-700 border-blue-200',
  quiz: 'bg-orange-100 text-orange-700 border-orange-200',
  project: 'bg-purple-100 text-purple-700 border-purple-200',
  reading: 'bg-green-100 text-green-700 border-green-200',
  lecture: 'bg-gray-100 text-gray-700 border-gray-200',
  lab: 'bg-teal-100 text-teal-700 border-teal-200',
  other: 'bg-gray-100 text-gray-600 border-gray-200',
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export default function ScheduleView({ data, onNavigate, onLoadDemo }: ScheduleViewProps) {
  if (!data) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="font-[Inter] text-3xl font-bold text-[#485C11]">Schedule</h2>
          <p className="text-[#485C11]/70 max-w-md">
            Your schedule will appear here once you upload a syllabus and generate a study plan.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => onNavigate('upload')}
              className="px-6 py-2.5 bg-[#485C11] text-white rounded-full font-medium hover:bg-[#3a4a0d] transition-colors"
            >
              Upload Syllabus
            </button>
            {onLoadDemo && (
              <button
                onClick={onLoadDemo}
                className="px-6 py-2.5 border-2 border-[#485C11] text-[#485C11] rounded-full font-medium hover:bg-[#485C11]/10 transition-colors"
              >
                Load Demo
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  const allEvents = [
    ...data.syllabus_events.map((e) => ({ ...e, kind: 'event' as const })),
    ...data.study_blocks.map((b) => ({
      title: b.title,
      date: b.date,
      time: b.time,
      duration_minutes: b.duration_minutes,
      event_type: b.block_type,
      description: b.description,
      weight: null,
      kind: 'block' as const,
    })),
  ].sort((a, b) => a.date.localeCompare(b.date));

  // Group by date
  const grouped: Record<string, typeof allEvents> = {};
  for (const event of allEvents) {
    if (!grouped[event.date]) grouped[event.date] = [];
    grouped[event.date].push(event);
  }

  return (
    <div className="max-w-2xl mx-auto w-full px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-[Inter] text-3xl font-bold text-[#485C11]">Schedule</h2>
          <p className="text-[#485C11]/60 text-sm mt-1">
            {data.course_name} — {data.semester}
          </p>
        </div>
        <span className="text-sm text-[#485C11]/50">
          {allEvents.length} events
        </span>
      </div>

      {Object.entries(grouped).map(([date, events]) => (
        <div key={date} className="space-y-2">
          <h3 className="font-[Inter] text-sm font-semibold text-[#485C11]/70 uppercase tracking-wide">
            {formatDate(date)}
          </h3>
          <div className="space-y-2">
            {events.map((event, i) => {
              const Icon = EVENT_ICONS[event.event_type] || Calendar;
              const colors = EVENT_COLORS[event.event_type] || EVENT_COLORS.other;
              return (
                <div
                  key={`${date}-${i}`}
                  className={`flex items-start gap-3 px-4 py-3 rounded-xl border-2 bg-white/80 border-[#485C11]/10 transition-colors`}
                >
                  <div className={`p-2 rounded-lg ${colors} flex-shrink-0`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-[Inter] text-sm font-medium text-[#485C11]">
                        {event.title}
                      </span>
                      {event.kind === 'block' && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#485C11]/10 text-[#485C11]/60">
                          study
                        </span>
                      )}
                    </div>
                    {event.description && (
                      <p className="text-xs text-[#485C11]/50 mt-0.5 truncate">{event.description}</p>
                    )}
                    {(event.time || event.duration_minutes) && (
                      <div className="flex items-center gap-2 mt-1 text-xs text-[#485C11]/40">
                        {event.time && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {event.time}
                          </span>
                        )}
                        {event.duration_minutes && (
                          <span>{event.duration_minutes}min</span>
                        )}
                      </div>
                    )}
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${colors}`}>
                    {event.event_type}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
