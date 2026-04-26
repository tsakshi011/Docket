import { useState, useEffect, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import NavBar from './components/NavBar';
import HeroSection from './components/HeroSection';
import FileUpload from './components/FileUpload';
import StudyPlanView from './components/StudyPlanView';
import ScheduleView from './components/ScheduleView';
import PomodoroTimer from './components/PomodoroTimer';
import { parseSyllabus, exportIcs, exportToGoogleCalendar, fetchUserCourses, saveUserCourse, deleteUserCourse, saveUserTaskProgress, recordColdCall } from './api';
import type { UserDataResponse } from './api';
import { useAuth } from './useAuth';
import type { ParseResponse, AppStep, CalendarExportResponse } from './types';

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('StudyPlanView crashed:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 text-center">
          <h2 className="text-xl font-bold text-red-600 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })} className="px-4 py-2 bg-[#485C11] text-white rounded-lg">Try Again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

type Page = 'home' | 'upload' | 'schedule' | 'pomodoro';

interface SavedCourse {
  name: string;
  data: ParseResponse;
}

function loadSavedCourses(): SavedCourse[] {
  try {
    const raw = localStorage.getItem('docket_courses');
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [step, setStep] = useState<AppStep>('upload');
  const [data, setData] = useState<ParseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [savedCourses, setSavedCourses] = useState<SavedCourse[]>(loadSavedCourses);
  const [gcalExporting, setGcalExporting] = useState(false);
  const [gcalResult, setGcalResult] = useState<CalendarExportResponse | null>(null);

  const [taskProgress, setTaskProgress] = useState<UserDataResponse['task_progress']>({});
  const [coldCalls, setColdCalls] = useState<Record<string, string>>({});

  const { user, googleAccessToken, signInWithGoogle } = useAuth();

  useEffect(() => {
    localStorage.setItem('docket_courses', JSON.stringify(savedCourses));
  }, [savedCourses]);

  // Load courses from MongoDB when user signs in
  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    fetchUserCourses(user.uid)
      .then((res) => {
        if (cancelled) return;
        if (res.courses.length > 0) {
          setSavedCourses(res.courses);
          localStorage.setItem('docket_courses', JSON.stringify(res.courses));
        }
        if (res.task_progress) {
          setTaskProgress(res.task_progress);
        }
        if (res.cold_calls) {
          setColdCalls(res.cold_calls);
        }
      })
      .catch(() => { /* backend may not be running */ });
    return () => { cancelled = true; };
  }, [user?.uid]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveCourse = (courseData: ParseResponse) => {
    setSavedCourses((prev) => {
      const filtered = prev.filter((c) => c.name !== courseData.course_name);
      return [...filtered, { name: courseData.course_name, data: courseData }];
    });
    if (user) {
      saveUserCourse(user.uid, courseData.course_name, courseData).catch(() => {});
    }
  };

  const switchCourse = (courseName: string) => {
    const course = savedCourses.find((c) => c.name === courseName);
    if (course) {
      setData(course.data);
      setStep('review');
      setPage('upload');
    }
  };

  const deleteCourse = (courseName: string) => {
    setSavedCourses((prev) => prev.filter((c) => c.name !== courseName));
    if (data?.course_name === courseName) {
      setData(null);
      setStep('upload');
    }
    if (user) {
      deleteUserCourse(user.uid, courseName).catch(() => {});
    }
  };

  const handleTaskProgressChange = (courseName: string, completedItems: string[], customTasks: { id: string; text: string; completed: boolean }[]) => {
    const safeKey = courseName.replace(/\./g, '_').replace(/\$/g, '_');
    setTaskProgress((prev) => ({
      ...prev,
      [safeKey]: { completed_items: completedItems, custom_tasks: customTasks },
    }));
    if (user) {
      saveUserTaskProgress(user.uid, courseName, completedItems, customTasks).catch(() => {});
    }
  };

  const getCurrentTaskProgress = () => {
    if (!data) return undefined;
    const safeKey = data.course_name.replace(/\./g, '_').replace(/\$/g, '_');
    return taskProgress[safeKey];
  };

  const handleColdCall = (courseName: string) => {
    const safeKey = courseName.replace(/\./g, '_').replace(/\$/g, '_');
    const now = new Date().toISOString();
    setColdCalls((prev) => ({ ...prev, [safeKey]: now }));
    if (user) {
      recordColdCall(user.uid, courseName).catch(() => {});
    }
  };

  const handleSubmit = async (f: File) => {
    setFile(f);
    setStep('processing');
    setError(null);

    try {
      const result = await parseSyllabus(f);
      setData(result);
      saveCourse(result);
      setStep('review');
      setPage('upload');
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'Something went wrong. Please try again.';
      const axiosDetail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(axiosDetail || message);
      setStep('upload');
    }
  };

  const handleExportIcs = async () => {
    if (!file) return;
    try {
      const blob = await exportIcs(file);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${data?.course_name || 'study_plan'}.ics`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Failed to export .ics file. Please try again.');
    }
  };

  const handleExportGcal = async () => {
    if (!data) return;

    if (!googleAccessToken) {
      try {
        await signInWithGoogle();
      } catch {
        alert('Google sign-in is required to export to Google Calendar.');
      }
      return;
    }

    setGcalExporting(true);
    setError(null);
    try {
      const result = await exportToGoogleCalendar({
        course_name: data.course_name,
        access_token: googleAccessToken,
        syllabus_events: data.syllabus_events,
        study_blocks: data.study_blocks,
      });
      setGcalResult(result);
    } catch (err: unknown) {
      const axiosDetail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      const message = axiosDetail || (err instanceof Error ? err.message : 'Failed to export to Google Calendar.');
      setError(message);
    } finally {
      setGcalExporting(false);
    }
  };

  const handleReset = () => {
    setStep('upload');
    setData(null);
    setFile(null);
    setError(null);
    setGcalResult(null);
  };

  const handleLoadDemo = () => {
    const demoData: ParseResponse = {
      course_name: 'CS 131 - Programming Languages',
      semester: 'Fall 2026',
      instructor: 'Prof. Sarah Chen',
      syllabus_events: [
        { title: 'HW1 Due: Functional Programming', date: '2026-09-15', time: '23:59', duration_minutes: 30, event_type: 'assignment', description: 'Implement map, filter, reduce in OCaml', weight: '5%' },
        { title: 'Quiz 1: Lambda Calculus', date: '2026-09-22', time: '10:00', duration_minutes: 30, event_type: 'quiz', description: 'Covers weeks 1-3 material', weight: '5%' },
        { title: 'HW2 Due: Type Systems', date: '2026-10-01', time: '23:59', duration_minutes: 30, event_type: 'assignment', description: 'Type inference exercises', weight: '5%' },
        { title: 'Midterm Exam', date: '2026-10-20', time: '10:00', duration_minutes: 120, event_type: 'exam', description: 'Closed book. Covers all material through Week 7.', weight: '25%' },
        { title: 'Project Proposal Due', date: '2026-11-03', time: '23:59', duration_minutes: 30, event_type: 'project', description: '1-page proposal for final project', weight: null },
        { title: 'HW3 Due: Concurrency', date: '2026-11-10', time: '23:59', duration_minutes: 30, event_type: 'assignment', description: 'Thread safety and synchronization', weight: '5%' },
        { title: 'Final Project Due', date: '2026-12-08', time: '23:59', duration_minutes: 60, event_type: 'project', description: 'Implement a small programming language', weight: '25%' },
        { title: 'Final Exam', date: '2026-12-15', time: '14:00', duration_minutes: 180, event_type: 'exam', description: 'Comprehensive. Open notes, no electronics.', weight: '25%' },
      ],
      study_blocks: [
        { title: 'Review: FP Basics', date: '2026-09-13', time: '14:00', duration_minutes: 60, block_type: 'study_session', related_event: 'HW1 Due: Functional Programming', description: 'Review OCaml syntax and FP concepts', priority: 'medium' },
        { title: 'Practice: Lambda Calculus', date: '2026-09-20', time: '16:00', duration_minutes: 90, block_type: 'practice', related_event: 'Quiz 1: Lambda Calculus', description: 'Work through practice problems', priority: 'high' },
        { title: 'Midterm Review 1', date: '2026-10-16', time: '10:00', duration_minutes: 90, block_type: 'review', related_event: 'Midterm Exam', description: 'Review Weeks 1-4', priority: 'critical' },
        { title: 'Midterm Review 2', date: '2026-10-18', time: '14:00', duration_minutes: 90, block_type: 'review', related_event: 'Midterm Exam', description: 'Review Weeks 5-7', priority: 'critical' },
        { title: 'Draft: Project Outline', date: '2026-10-30', time: '15:00', duration_minutes: 60, block_type: 'outline', related_event: 'Project Proposal Due', description: 'Outline language features', priority: 'high' },
        { title: 'Final Review 1', date: '2026-12-10', time: '10:00', duration_minutes: 120, block_type: 'review', related_event: 'Final Exam', description: 'Comprehensive review', priority: 'critical' },
        { title: 'Final Review 2', date: '2026-12-13', time: '14:00', duration_minutes: 120, block_type: 'review', related_event: 'Final Exam', description: 'Practice problems and past exams', priority: 'critical' },
      ],
      weekly_summary: ['Week 3: HW1 due', 'Week 4: Quiz 1', 'Week 7: MIDTERM', 'Week 14: Final project due', 'Week 15: FINAL EXAM'],
      warnings: ['Heavy week: Midterm Oct 20 — start reviewing by Oct 14', 'Final project Dec 8 and Final Exam Dec 15 — only 1 week gap'],
      raw_text_preview: 'CS 131 - Programming Languages, Fall 2026...',
    };
    setData(demoData);
    saveCourse(demoData);
    setStep('review');
    setPage('upload');
  };

  const handleNavigate = (target: string) => {
    if (target === 'home') {
      setPage('home');
      handleReset();
    } else if (target === 'upload') {
      setPage('upload');
    } else if (target === 'schedule') {
      setPage('schedule');
    } else if (target === 'pomodoro') {
      setPage('pomodoro');
    }
  };

  return (
    <div className="min-h-screen bg-[#C1E1C1] flex flex-col font-[Inter]">
      <NavBar currentPage={page} onNavigate={handleNavigate} />

      {/* Home / Landing Page */}
      {page === 'home' && <HeroSection onNavigate={handleNavigate} />}

      {/* Upload / Processing / Review flow */}
      {page === 'upload' && (
        <div className="flex-1 flex flex-col">
          <div className="max-w-4xl mx-auto px-4 py-10 w-full">
            {error && (
              <div className="max-w-xl mx-auto mb-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                {error.split(/(https?:\/\/[^\s]+)/g).map((part, i) =>
                  part.match(/^https?:\/\//) ? (
                    <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="underline font-medium text-red-800 hover:text-red-900">
                      {part}
                    </a>
                  ) : (
                    <span key={i}>{part}</span>
                  ),
                )}
              </div>
            )}

            {step === 'upload' && (
              <FileUpload onSubmit={handleSubmit} isLoading={false} />
            )}

            {step === 'processing' && (
              <div className="max-w-xl mx-auto text-center space-y-6 py-20">
                <div className="w-16 h-16 border-4 border-[#C1E1C1] border-t-[#485C11] rounded-full animate-spin mx-auto" />
                <div className="space-y-2">
                  <h2 className="text-xl font-semibold text-[#485C11]">AI Agent Working...</h2>
                  <div className="space-y-1 text-sm text-[#485C11]/70">
                    <p>Step 1: Extracting text from your syllabus</p>
                    <p>Step 2: Identifying assignments, exams & deadlines</p>
                    <p>Step 3: Reasoning about optimal study schedule</p>
                    <p>Step 4: Generating your personalized study plan</p>
                  </div>
                </div>
              </div>
            )}

            {step === 'review' && data && (
              <ErrorBoundary>
              <StudyPlanView
                data={data}
                onExportIcs={handleExportIcs}
                onExportGcal={handleExportGcal}
                gcalExporting={gcalExporting}
                gcalResult={gcalResult}
                onReset={handleReset}
                savedCourses={savedCourses.map((c) => c.name)}
                onSwitchCourse={switchCourse}
                onDeleteCourse={deleteCourse}
                initialTaskProgress={getCurrentTaskProgress()}
                onTaskProgressChange={handleTaskProgressChange}
                coldCallDate={(() => { const safeKey = data.course_name.replace(/\./g, '_').replace(/\$/g, '_'); return coldCalls[safeKey]; })()}
                onColdCall={handleColdCall}
              />
              </ErrorBoundary>
            )}
          </div>
        </div>
      )}

      {/* Schedule Page */}
      {page === 'schedule' && (
        <ScheduleView data={data} onNavigate={handleNavigate} onLoadDemo={handleLoadDemo} savedCourses={savedCourses.map((c) => c.name)} onSwitchCourse={switchCourse} />
      )}

      {/* Pomodoro Page */}
      {page === 'pomodoro' && (
        <div className="flex flex-col items-center pt-16 gap-6 px-4">
          <h2 className="flex items-end text-5xl font-bold text-[#485C11]" style={{ fontFamily: '"Nimbus Roman No9 L", "Times New Roman", Georgia, serif' }}>
            <span>Pomo</span>
            <img src="/src/assets/docket-logo-d.png" alt="d" className="h-[4.5rem] -mr-6" style={{ marginBottom: '-6px', marginLeft: '-1rem' }} />
            <span>oro</span>
          </h2>
          <PomodoroTimer />
          <img src="/src/assets/star.png" alt="star" className="w-10 h-10 mt-2" />
        </div>
      )}
    </div>
  );
}
