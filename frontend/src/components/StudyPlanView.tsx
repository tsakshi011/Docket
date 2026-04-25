import { useState } from 'react';
import {
  Calendar,
  BookOpen,
  AlertTriangle,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Clock,
  GraduationCap,
  FileText,
  FlaskConical,
  PenLine,
  CheckCircle2,
} from 'lucide-react';
import type { ParseResponse, StudyBlock } from '../types';
import { generateGcalLink } from '../api';

interface StudyPlanViewProps {
  data: ParseResponse;
  onExportIcs: () => void;
  onReset: () => void;
}

const EVENT_TYPE_STYLES: Record<string, { bg: string; text: string; icon: typeof BookOpen }> = {
  exam: { bg: 'bg-red-100', text: 'text-red-700', icon: GraduationCap },
  assignment: { bg: 'bg-blue-100', text: 'text-blue-700', icon: PenLine },
  quiz: { bg: 'bg-orange-100', text: 'text-orange-700', icon: FileText },
  project: { bg: 'bg-purple-100', text: 'text-purple-700', icon: FlaskConical },
  reading: { bg: 'bg-green-100', text: 'text-green-700', icon: BookOpen },
  lecture: { bg: 'bg-gray-100', text: 'text-gray-700', icon: BookOpen },
  lab: { bg: 'bg-teal-100', text: 'text-teal-700', icon: FlaskConical },
  other: { bg: 'bg-gray-100', text: 'text-gray-600', icon: Calendar },
};

const PRIORITY_STYLES: Record<string, string> = {
  critical: 'border-l-red-500',
  high: 'border-l-orange-500',
  medium: 'border-l-blue-500',
  low: 'border-l-gray-400',
};

function EventBadge({ type }: { type: string }) {
  const style = EVENT_TYPE_STYLES[type] || EVENT_TYPE_STYLES.other;
  const Icon = style.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
      <Icon className="w-3 h-3" />
      {type}
    </span>
  );
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export default function StudyPlanView({ data, onExportIcs, onReset }: StudyPlanViewProps) {
  const [showStudyBlocks, setShowStudyBlocks] = useState(true);
  const [activeTab, setActiveTab] = useState<'timeline' | 'events' | 'blocks'>('timeline');

  const allItems = [
    ...data.syllabus_events.map((e) => ({ ...e, kind: 'event' as const })),
    ...data.study_blocks.map((b) => ({ ...b, kind: 'block' as const, event_type: b.block_type })),
  ].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-bold text-gray-900">{data.course_name}</h1>
        <p className="text-gray-500">{data.semester}{data.instructor ? ` — ${data.instructor}` : ''}</p>
      </div>

      {/* Warnings */}
      {data.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-1">
          <div className="flex items-center gap-2 font-medium text-amber-800">
            <AlertTriangle className="w-5 h-5" />
            Heads Up
          </div>
          {data.warnings.map((w, i) => (
            <p key={i} className="text-sm text-amber-700 ml-7">• {w}</p>
          ))}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-indigo-600">{data.syllabus_events.length}</p>
          <p className="text-xs text-gray-500">Syllabus Events</p>
        </div>
        <div className="bg-white border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-green-600">{data.study_blocks.length}</p>
          <p className="text-xs text-gray-500">Study Blocks Generated</p>
        </div>
        <div className="bg-white border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-purple-600">{data.weekly_summary.length}</p>
          <p className="text-xs text-gray-500">Weeks Planned</p>
        </div>
      </div>

      {/* Export buttons */}
      <div className="flex gap-3">
        <button
          onClick={onExportIcs}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
        >
          <Download className="w-4 h-4" />
          Download .ics File
        </button>
        <button
          onClick={onReset}
          className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
        >
          New Upload
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {(['timeline', 'events', 'blocks'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'timeline' ? 'Timeline' : tab === 'events' ? `Events (${data.syllabus_events.length})` : `Study Plan (${data.study_blocks.length})`}
          </button>
        ))}
      </div>

      {/* Timeline view */}
      {activeTab === 'timeline' && (
        <div className="space-y-2">
          {allItems.map((item, i) => {
            const isEvent = item.kind === 'event';
            const block = item as StudyBlock & { kind: string };
            return (
              <div
                key={i}
                className={`flex items-start gap-3 p-3 rounded-lg border ${
                  isEvent ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-100'
                } ${!isEvent ? `border-l-4 ${PRIORITY_STYLES[block.priority] || ''}` : ''}`}
              >
                <div className="text-xs text-gray-400 w-16 shrink-0 pt-0.5">
                  {formatDate(item.date)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`font-medium ${isEvent ? 'text-gray-900' : 'text-gray-700'}`}>
                      {isEvent ? '📌' : '📚'} {item.title}
                    </span>
                    <EventBadge type={item.event_type} />
                  </div>
                  {item.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                  )}
                  {!isEvent && (
                    <p className="text-xs text-indigo-500 mt-0.5">
                      For: {block.related_event}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {item.time && (
                    <span className="text-xs text-gray-400 flex items-center gap-0.5">
                      <Clock className="w-3 h-3" />
                      {item.time}
                    </span>
                  )}
                  <a
                    href={generateGcalLink(
                      item.title,
                      item.date,
                      item.time,
                      item.duration_minutes,
                      item.description || '',
                    )}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-indigo-600"
                    title="Add to Google Calendar"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Events only */}
      {activeTab === 'events' && (
        <div className="space-y-2">
          {data.syllabus_events.map((ev, i) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-white border rounded-lg">
              <div className="text-xs text-gray-400 w-16 shrink-0 pt-0.5">
                {formatDate(ev.date)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-900">{ev.title}</span>
                  <EventBadge type={ev.event_type} />
                  {ev.weight && (
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">
                      {ev.weight}
                    </span>
                  )}
                </div>
                {ev.description && <p className="text-xs text-gray-500 mt-0.5">{ev.description}</p>}
              </div>
              <a
                href={generateGcalLink(ev.title, ev.date, ev.time, ev.duration_minutes, ev.description)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-indigo-600 shrink-0"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>
      )}

      {/* Study blocks only */}
      {activeTab === 'blocks' && (
        <div className="space-y-2">
          {data.study_blocks.map((block, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 p-3 bg-gray-50 border rounded-lg border-l-4 ${
                PRIORITY_STYLES[block.priority] || ''
              }`}
            >
              <div className="text-xs text-gray-400 w-16 shrink-0 pt-0.5">
                {formatDate(block.date)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-700">📚 {block.title}</span>
                  <EventBadge type={block.block_type} />
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    block.priority === 'critical' ? 'bg-red-100 text-red-700' :
                    block.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {block.priority}
                  </span>
                </div>
                {block.description && <p className="text-xs text-gray-500 mt-0.5">{block.description}</p>}
                <p className="text-xs text-indigo-500 mt-0.5">For: {block.related_event}</p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-xs text-gray-400">{block.duration_minutes}m</span>
                <a
                  href={generateGcalLink(block.title, block.date, block.time, block.duration_minutes, block.description)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-indigo-600"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Weekly Summary */}
      <div className="bg-white border rounded-lg p-4 space-y-2">
        <button
          onClick={() => setShowStudyBlocks(!showStudyBlocks)}
          className="flex items-center justify-between w-full"
        >
          <span className="font-medium text-gray-900">Weekly Overview</span>
          {showStudyBlocks ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showStudyBlocks && (
          <div className="space-y-1">
            {data.weekly_summary.map((s, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                {s}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
