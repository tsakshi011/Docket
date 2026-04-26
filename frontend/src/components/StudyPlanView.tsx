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
  Plus,
  Trash2,
  Circle,
} from 'lucide-react';
import type { ParseResponse, StudyBlock } from '../types';
import { generateGcalLink } from '../api';

interface StudyPlanViewProps {
  data: ParseResponse;
  onExportIcs: () => void;
  onExportGcal: () => void;
  gcalExporting: boolean;
  gcalResult: { calendar_url: string; events_created: number } | null;
  onReset: () => void;
  savedCourses?: string[];
  onSwitchCourse?: (name: string) => void;
  onDeleteCourse?: (name: string) => void;
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

interface TaskItem {
  id: string;
  text: string;
  completed: boolean;
}

export default function StudyPlanView({ data, onExportIcs, onExportGcal, gcalExporting, gcalResult, onReset, savedCourses, onSwitchCourse, onDeleteCourse }: StudyPlanViewProps) {
  const [showStudyBlocks, setShowStudyBlocks] = useState(true);
  const [activeTab, setActiveTab] = useState<'timeline' | 'events' | 'blocks' | 'tasks'>('timeline');
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [newTask, setNewTask] = useState('');
  const [completedItems, setCompletedItems] = useState<Set<string>>(new Set());
  const [showCourseDropdown, setShowCourseDropdown] = useState(false);

  const addTask = () => {
    const text = newTask.trim();
    if (!text) return;
    setTasks([...tasks, { id: crypto.randomUUID(), text, completed: false }]);
    setNewTask('');
  };

  const toggleTask = (id: string) => {
    setTasks(tasks.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t)));
  };

  const deleteTask = (id: string) => {
    setTasks(tasks.filter((t) => t.id !== id));
  };

  const allItems = [
    ...data.syllabus_events.map((e) => ({ ...e, kind: 'event' as const })),
    ...data.study_blocks.map((b) => ({ ...b, kind: 'block' as const, event_type: b.block_type })),
  ].sort((a, b) => a.date.localeCompare(b.date));

  const allTaskCount = allItems.length + tasks.length;
  const allCompletedCount = completedItems.size + tasks.filter((t) => t.completed).length;

  const toggleTimelineItem = (key: string) => {
    setCompletedItems((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header with course dropdown */}
      <div className="text-center space-y-1 relative">
        {savedCourses && savedCourses.length > 1 ? (
          <div className="relative inline-block">
            <button
              onClick={() => setShowCourseDropdown(!showCourseDropdown)}
              className="font-[Inter] text-2xl font-bold text-[#485C11] flex items-center gap-2 mx-auto hover:opacity-80 transition-opacity"
            >
              {data.course_name}
              <ChevronDown className={`w-5 h-5 transition-transform ${showCourseDropdown ? 'rotate-180' : ''}`} />
            </button>
            {showCourseDropdown && (
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 bg-[#FFFBF1] border-2 border-[#485C11]/20 rounded-xl shadow-lg z-50 min-w-[280px] overflow-hidden">
                {savedCourses.map((name) => (
                  <div
                    key={name}
                    className={`flex items-center justify-between px-4 py-3 hover:bg-[#F5EDD6] transition-colors cursor-pointer ${
                      name === data.course_name ? 'bg-[#F5EDD6] font-medium' : ''
                    }`}
                  >
                    <button
                      onClick={() => {
                        onSwitchCourse?.(name);
                        setShowCourseDropdown(false);
                      }}
                      className="flex-1 text-left text-sm text-[#485C11]"
                    >
                      {name}
                    </button>
                    {onDeleteCourse && name !== data.course_name && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteCourse(name);
                        }}
                        className="text-[#485C11]/30 hover:text-red-500 transition-colors ml-2"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <h1 className="font-[Inter] text-2xl font-bold text-[#485C11]">{data.course_name}</h1>
        )}
        <p className="text-[#485C11]/70">{data.semester}{data.instructor ? ` — ${data.instructor}` : ''}</p>
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
        <div className="bg-[#FFFBF1] border border-[#485C11]/20 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-[#485C11]">{data.syllabus_events.length}</p>
          <p className="text-xs text-[#485C11]/60">Syllabus Events</p>
        </div>
        <div className="bg-[#FFFBF1] border border-[#485C11]/20 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-[#485C11]">{data.study_blocks.length}</p>
          <p className="text-xs text-[#485C11]/60">Study Blocks Generated</p>
        </div>
        <div className="bg-[#FFFBF1] border border-[#485C11]/20 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-[#485C11]">{data.weekly_summary.length}</p>
          <p className="text-xs text-[#485C11]/60">Weeks Planned</p>
        </div>
      </div>

      {/* Export buttons */}
      <div className="flex flex-col gap-3">
        <div className="flex gap-3">
          <button
            onClick={onExportGcal}
            disabled={gcalExporting}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-[#485C11] text-white rounded-full hover:bg-[#3a4a0d] transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Calendar className="w-4 h-4" />
            {gcalExporting ? 'Creating Calendar...' : 'Export to Google Calendar'}
          </button>
          <button
            onClick={onExportIcs}
            className="flex items-center justify-center gap-2 px-4 py-2.5 border border-[#485C11]/40 text-[#485C11] rounded-full hover:bg-[#d4ecd4] transition-colors font-medium"
          >
            <Download className="w-4 h-4" />
            .ics File
          </button>
          <button
            onClick={onReset}
            className="px-4 py-2.5 border border-[#485C11]/40 text-[#485C11] rounded-full hover:bg-[#d4ecd4] transition-colors font-medium"
          >
            New Upload
          </button>
        </div>
        {gcalResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center justify-between">
            <span className="text-sm text-green-800">
              Created {gcalResult.events_created} events in your Google Calendar!
            </span>
            <a
              href={gcalResult.calendar_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-green-700 hover:text-green-900 flex items-center gap-1"
            >
              Open Calendar <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {(['timeline', 'events', 'blocks', 'tasks'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-[#485C11] text-[#485C11]'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'timeline' ? `Timeline${completedItems.size > 0 ? ` (${completedItems.size}/${allItems.length})` : ''}` : tab === 'events' ? `Events (${data.syllabus_events.length})` : tab === 'blocks' ? `Study Plan (${data.study_blocks.length})` : `Tasks (${allCompletedCount}/${allTaskCount})`}
          </button>
        ))}
      </div>

      {/* Timeline view */}
      {activeTab === 'timeline' && (
        <div className="space-y-2">
          {allItems.map((item, i) => {
            const isEvent = item.kind === 'event';
            const block = item as StudyBlock & { kind: string };
            const itemKey = `${item.date}-${item.title}`;
            const isChecked = completedItems.has(itemKey);
            return (
              <div
                key={i}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-all duration-200 ${
                  isChecked ? 'bg-[#F5EDD6] border-[#485C11]/20' :
                  'bg-[#FFFBF1] border-[#485C11]/20'
                } ${!isEvent ? `border-l-4 ${PRIORITY_STYLES[block.priority] || ''}` : ''}`}
              >
                <button
                  onClick={() => toggleTimelineItem(itemKey)}
                  className="mt-0.5 flex-shrink-0"
                >
                  {isChecked ? (
                    <CheckCircle2 className="w-5 h-5 text-[#485C11]" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-300" />
                  )}
                </button>
                <div className="text-xs text-gray-400 w-16 shrink-0 pt-0.5">
                  {formatDate(item.date)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`font-medium ${isChecked ? 'line-through text-gray-400' : isEvent ? 'text-gray-900' : 'text-gray-700'}`}>
                      {isEvent ? '📌' : '📚'} {item.title}
                    </span>
                    <EventBadge type={item.event_type} />
                  </div>
                  {item.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                  )}
                  {!isEvent && (
                    <p className="text-xs text-[#485C11]/60 mt-0.5">
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
                    className="text-gray-400 hover:text-[#485C11]"
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
            <div key={i} className="flex items-start gap-3 p-3 bg-[#FFFBF1] border border-[#485C11]/20 rounded-lg">
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
                className="text-gray-400 hover:text-[#485C11] shrink-0"
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
              className={`flex items-start gap-3 p-3 bg-[#FFFBF1] border border-[#485C11]/20 rounded-lg border-l-4 ${
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
                <p className="text-xs text-[#485C11]/60 mt-0.5">For: {block.related_event}</p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-xs text-gray-400">{block.duration_minutes}m</span>
                <a
                  href={generateGcalLink(block.title, block.date, block.time, block.duration_minutes, block.description)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-[#485C11]"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tasks checklist */}
      {activeTab === 'tasks' && (
        <div className="space-y-4">
          {/* Progress bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-[#485C11]/60">
              <span>{allCompletedCount} of {allTaskCount} completed</span>
              <span>{Math.round((allCompletedCount / allTaskCount) * 100)}%</span>
            </div>
            <div className="w-full bg-[#485C11]/10 rounded-full h-2">
              <div
                className="bg-[#485C11] h-2 rounded-full transition-all duration-300"
                style={{ width: `${(allCompletedCount / allTaskCount) * 100}%` }}
              />
            </div>
          </div>

          {/* Add custom task input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addTask()}
              placeholder="Add a custom task..."
              className="flex-1 px-4 py-3 rounded-xl border-2 border-[#485C11]/20 bg-[#FFFBF1] text-[#485C11] placeholder-[#485C11]/40 focus:outline-none focus:border-[#485C11] transition-colors font-[Inter]"
            />
            <button
              onClick={addTask}
              className="px-4 py-3 bg-[#485C11] text-[#FFFBF1] rounded-xl hover:bg-[#3a4a0d] transition-colors"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>

          {/* Syllabus items as tasks */}
          <ul className="space-y-2">
            {allItems.map((item) => {
              const itemKey = `${item.date}-${item.title}`;
              const isChecked = completedItems.has(itemKey);
              const isEvent = item.kind === 'event';
              return (
                <li
                  key={itemKey}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all duration-200 ${
                    isChecked
                      ? 'bg-[#F5EDD6] border-[#485C11]/20'
                      : 'bg-[#FFFBF1] border-[#485C11]/20 hover:border-[#485C11]/40'
                  }`}
                >
                  <button
                    onClick={() => toggleTimelineItem(itemKey)}
                    className="text-[#485C11] flex-shrink-0"
                  >
                    {isChecked ? (
                      <CheckCircle2 className="w-6 h-6 text-[#485C11]" />
                    ) : (
                      <Circle className="w-6 h-6 text-[#485C11]/40" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <span
                      className={`font-[Inter] text-sm ${
                        isChecked ? 'line-through text-[#485C11]/40' : 'text-[#485C11]'
                      }`}
                    >
                      {isEvent ? '📌' : '📚'} {item.title}
                    </span>
                    <p className="text-xs text-[#485C11]/40 mt-0.5">
                      {formatDate(item.date)}{item.time ? ` · ${item.time}` : ''}
                    </p>
                  </div>
                  <EventBadge type={item.event_type} />
                </li>
              );
            })}

            {/* Custom tasks */}
            {tasks.map((task) => (
              <li
                key={task.id}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all duration-200 ${
                  task.completed
                    ? 'bg-[#F5EDD6] border-[#485C11]/20'
                    : 'bg-[#FFFBF1] border-[#485C11]/20 hover:border-[#485C11]/40'
                }`}
              >
                <button
                  onClick={() => toggleTask(task.id)}
                  className="text-[#485C11] flex-shrink-0"
                >
                  {task.completed ? (
                    <CheckCircle2 className="w-6 h-6 text-[#485C11]" />
                  ) : (
                    <Circle className="w-6 h-6 text-[#485C11]/40" />
                  )}
                </button>
                <span
                  className={`flex-1 font-[Inter] text-sm ${
                    task.completed
                      ? 'line-through text-[#485C11]/40'
                      : 'text-[#485C11]'
                  }`}
                >
                  {task.text}
                </span>
                <button
                  onClick={() => deleteTask(task.id)}
                  className="text-[#485C11]/30 hover:text-red-500 transition-colors flex-shrink-0"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weekly Summary */}
      <div className="bg-[#FFFBF1] border border-[#485C11]/20 rounded-lg p-4 space-y-2">
        <button
          onClick={() => setShowStudyBlocks(!showStudyBlocks)}
          className="flex items-center justify-between w-full"
        >
          <span className="font-medium text-[#485C11]">Weekly Overview</span>
          {showStudyBlocks ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showStudyBlocks && (
          <div className="space-y-1">
            {data.weekly_summary.map((s, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-[#485C11]/70">
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
