import { useState, useCallback } from 'react';
import { Upload, FileText } from 'lucide-react';

interface FileUploadProps {
  onSubmit: (file: File) => void;
  isLoading: boolean;
}

export default function FileUpload({ onSubmit, isLoading }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
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
    if (!file) return;
    onSubmit(file);
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h1 className="font-[Inter] text-3xl font-bold text-[#485C11]">
          Upload Your <span className="text-[#485C11]/80">Syllabus</span>
        </h1>
        <p className="text-[#485C11]/70">
          Upload your syllabus. Our AI agent breaks down every assignment, schedules study sessions, and builds your personalized academic plan.
        </p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-[#485C11] bg-[#d4ecd4]'
            : file
            ? 'border-[#485C11] bg-[#dff0df]'
            : 'border-[#485C11]/40 hover:border-[#485C11] hover:bg-[#d4ecd4]'
        }`}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText className="w-8 h-8 text-[#485C11]" />
            <div className="text-left">
              <p className="font-medium text-[#485C11]">{file.name}</p>
              <p className="text-sm text-[#485C11]/60">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-10 h-10 text-[#485C11]/50 mx-auto" />
            <p className="text-[#485C11] font-medium">Drop your syllabus PDF here</p>
            <p className="text-sm text-[#485C11]/50">or click to browse</p>
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

      <button
        onClick={handleSubmit}
        disabled={!file || isLoading}
        className="w-full py-3 px-4 bg-[#485C11] text-white font-medium rounded-full hover:bg-[#3a4a0d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
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
