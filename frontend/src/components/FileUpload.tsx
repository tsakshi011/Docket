import { useState, useCallback } from 'react';
import { Upload, FileText, Key } from 'lucide-react';

interface FileUploadProps {
  onSubmit: (file: File, apiKey: string) => void;
  isLoading: boolean;
}

export default function FileUpload({ onSubmit, isLoading }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('openai_key') || '');
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.type === 'application/pdf') {
      setFile(dropped);
    }
  }, []);

  const handleSubmit = () => {
    if (!file || !apiKey) return;
    localStorage.setItem('openai_key', apiKey);
    onSubmit(file, apiKey);
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">
          Syllabus<span className="text-indigo-600">Sync</span>
        </h1>
        <p className="text-gray-500">
          Upload your syllabus. Our AI agent breaks down every assignment, schedules study sessions, and builds your personalized academic plan.
        </p>
      </div>

      {/* File Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-indigo-500 bg-indigo-50'
            : file
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
        }`}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText className="w-8 h-8 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-10 h-10 text-gray-400 mx-auto" />
            <p className="text-gray-600 font-medium">Drop your syllabus PDF here</p>
            <p className="text-sm text-gray-400">or click to browse</p>
          </div>
        )}
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) setFile(f);
          }}
        />
      </div>

      {/* API Key */}
      <div className="space-y-1">
        <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
          <Key className="w-4 h-4" />
          OpenAI API Key
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
        />
        <p className="text-xs text-gray-400">Stored locally in your browser. Never sent anywhere except OpenAI.</p>
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!file || !apiKey || isLoading}
        className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Analyzing syllabus...
          </>
        ) : (
          <>
            <Upload className="w-5 h-5" />
            Generate Study Plan
          </>
        )}
      </button>
    </div>
  );
}
