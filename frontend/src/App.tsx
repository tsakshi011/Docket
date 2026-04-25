import { useState } from 'react';
import NavBar from './components/NavBar';
import HeroSection from './components/HeroSection';
import FileUpload from './components/FileUpload';
import StudyPlanView from './components/StudyPlanView';
<<<<<<< HEAD
import { parseSyllabus, exportIcs, storePlan, buildGcalSubscribeUrl } from './api';
import type { ParseResponse, AppStep } from './types';
=======
import ScheduleView from './components/ScheduleView';
import { parseSyllabus, exportIcs, exportToGoogleCalendar } from './api';
import { useAuth } from './useAuth';
import type { ParseResponse, AppStep, CalendarExportResponse } from './types';
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99

type Page = 'home' | 'upload' | 'schedule';

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [step, setStep] = useState<AppStep>('upload');
  const [data, setData] = useState<ParseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [gcalExporting, setGcalExporting] = useState(false);
<<<<<<< HEAD
  const [gcalUrl, setGcalUrl] = useState<string | null>(null);
=======
  const [gcalResult, setGcalResult] = useState<CalendarExportResponse | null>(null);

  const { googleAccessToken, signInWithGoogle } = useAuth();
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99

  const handleSubmit = async (f: File) => {
    setFile(f);
    setStep('processing');
    setError(null);

    try {
      const result = await parseSyllabus(f);
      setData(result);
      setStep('review');
      setPage('schedule');
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

<<<<<<< HEAD
    setGcalExporting(true);
    setError(null);
    try {
      const { plan_id } = await storePlan({
        course_name: data.course_name,
        syllabus_events: data.syllabus_events,
        study_blocks: data.study_blocks,
      });
      const url = buildGcalSubscribeUrl(plan_id);
      setGcalUrl(url);
      window.open(url, '_blank');
    } catch (err: unknown) {
      const axiosDetail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      const message = axiosDetail || (err instanceof Error ? err.message : 'Failed to prepare Google Calendar export.');
=======
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
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99
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
<<<<<<< HEAD
    setGcalUrl(null);
=======
    setGcalResult(null);
  };

  const handleLoadDemo = () => {
    setData({
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
    });
    setStep('review');
    setPage('upload');
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99
  };

  const handleNavigate = (target: string) => {
    if (target === 'home') {
      setPage('home');
      handleReset();
    } else if (target === 'upload') {
      setPage('upload');
    } else if (target === 'schedule') {
      setPage('schedule');
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
                {error}
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
              <StudyPlanView
                data={data}
                onExportIcs={handleExportIcs}
                onExportGcal={handleExportGcal}
                gcalExporting={gcalExporting}
<<<<<<< HEAD
                gcalUrl={gcalUrl}
=======
                gcalResult={gcalResult}
>>>>>>> 5e078a0fb8605bca5ad6a1298f51f11e70d11d99
                onReset={handleReset}
              />
            )}
          </div>
        </div>
      )}

      {/* Schedule Page */}
      {page === 'schedule' && (
        <ScheduleView data={data} onNavigate={handleNavigate} onLoadDemo={handleLoadDemo} />
      )}
    </div>
  );
}
