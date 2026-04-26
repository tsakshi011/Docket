import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';

const WORK_MINUTES = 35;
const BREAK_MINUTES = 5;

type Phase = 'work' | 'break';

export default function PomodoroTimer() {
  const [phase, setPhase] = useState<Phase>('work');
  const [secondsLeft, setSecondsLeft] = useState(WORK_MINUTES * 60);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<AudioContext | null>(null);

  const playChime = useCallback(() => {
    try {
      const ctx = audioRef.current ?? new AudioContext();
      audioRef.current = ctx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      osc.type = 'sine';
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.8);
    } catch {
      // audio not available
    }
  }, []);

  useEffect(() => {
    if (!running) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }
    intervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          playChime();
          const nextPhase: Phase = phase === 'work' ? 'break' : 'work';
          setPhase(nextPhase);
          return (nextPhase === 'work' ? WORK_MINUTES : BREAK_MINUTES) * 60;
        }
        return prev - 1;
      });
    }, 1000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [running, phase, playChime]);

  const reset = () => {
    setRunning(false);
    setPhase('work');
    setSecondsLeft(WORK_MINUTES * 60);
  };

  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const totalSeconds = (phase === 'work' ? WORK_MINUTES : BREAK_MINUTES) * 60;
  const progress = ((totalSeconds - secondsLeft) / totalSeconds) * 100;

  return (
    <div className="bg-[#FFFBF1] rounded-2xl p-4 border border-[#485C11]/10 w-full max-w-sm mx-auto">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-[#485C11] uppercase tracking-wide">
          {phase === 'work' ? 'Focus Time' : 'Break Time'}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          phase === 'work'
            ? 'bg-[#485C11]/10 text-[#485C11]'
            : 'bg-green-100 text-green-700'
        }`}>
          {phase === 'work' ? `${WORK_MINUTES} min` : `${BREAK_MINUTES} min`}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-[#485C11]/10 rounded-full mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${
            phase === 'work' ? 'bg-[#485C11]' : 'bg-green-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-4xl font-bold text-[#485C11] tabular-nums font-[Inter]">
          {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setRunning(!running)}
            className={`p-2.5 rounded-full text-white transition-colors ${
              running
                ? 'bg-orange-500 hover:bg-orange-600'
                : 'bg-[#485C11] hover:bg-[#3a4a0d]'
            }`}
            title={running ? 'Pause' : 'Start'}
          >
            {running ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={reset}
            className="p-2.5 rounded-full text-[#485C11] bg-[#485C11]/10 hover:bg-[#485C11]/20 transition-colors"
            title="Reset"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
