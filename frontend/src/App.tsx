import { useState } from 'react';
import NavBar from './components/NavBar';
import HeroSection from './components/HeroSection';
import FileUpload from './components/FileUpload';
import StudyPlanView from './components/StudyPlanView';
import { parseSyllabus, exportIcs } from './api';
import type { ParseResponse, AppStep } from './types';

type Page = 'home' | 'upload' | 'tasks' | 'schedule';

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [step, setStep] = useState<AppStep>('upload');
  const [data, setData] = useState<ParseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (f: File) => {
    setFile(f);
    setStep('processing');
    setError(null);

    try {
      const result = await parseSyllabus(f);
      setData(result);
      setStep('review');
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

  const handleReset = () => {
    setStep('upload');
    setData(null);
    setFile(null);
    setError(null);
  };

  const handleNavigate = (target: string) => {
    if (target === 'home') {
      setPage('home');
      handleReset();
    } else if (target === 'upload') {
      setPage('upload');
    } else if (target === 'tasks' || target === 'schedule') {
      setPage(target as Page);
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
                onReset={handleReset}
              />
            )}
          </div>
        </div>
      )}

      {/* Tasks Page (placeholder) */}
      {page === 'tasks' && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <h2 className="font-[Inter] text-3xl font-bold text-[#485C11]">
              Tasks
            </h2>
            <p className="text-[#485C11]/70 max-w-md">
              Your tasks will appear here once you upload a syllabus and generate a study plan.
            </p>
            <button
              onClick={() => handleNavigate('upload')}
              className="px-6 py-2.5 bg-[#485C11] text-white rounded-full font-medium hover:bg-[#3a4a0d] transition-colors"
            >
              Upload Syllabus
            </button>
          </div>
        </div>
      )}

      {/* Schedule Page (placeholder) */}
      {page === 'schedule' && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <h2 className="font-[Inter] text-3xl font-bold text-[#485C11]">
              Schedule
            </h2>
            <p className="text-[#485C11]/70 max-w-md">
              Your schedule will appear here once you upload a syllabus and generate a study plan.
            </p>
            <button
              onClick={() => handleNavigate('upload')}
              className="px-6 py-2.5 bg-[#485C11] text-white rounded-full font-medium hover:bg-[#3a4a0d] transition-colors"
            >
              Upload Syllabus
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
