import { useState } from 'react';
import FileUpload from './components/FileUpload';
import StudyPlanView from './components/StudyPlanView';
import { parseSyllabus, exportIcs } from './api';
import type { ParseResponse, AppStep } from './types';

export default function App() {
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto px-4 py-10">
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
            <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto" />
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-gray-900">AI Agent Working...</h2>
              <div className="space-y-1 text-sm text-gray-500">
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
  );
}
