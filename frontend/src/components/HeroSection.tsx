import typewriterImg from '../assets/typewriter.png';
import starImg from '../assets/star.png';

interface HeroSectionProps {
  onNavigate: (page: string) => void;
}

export default function HeroSection({ onNavigate }: HeroSectionProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 pb-12 text-center relative overflow-hidden">
      {/* 3D star decorations */}
      <img
        src={starImg}
        alt=""
        className="absolute bottom-16 left-[10%] w-24 h-24 md:w-36 md:h-36 opacity-90 pointer-events-none animate-float-slow object-contain"
      />
      <img
        src={starImg}
        alt=""
        className="absolute bottom-28 right-[12%] w-20 h-20 md:w-28 md:h-28 opacity-80 pointer-events-none animate-float-delayed object-contain"
      />

      {/* Heading */}
      <div className="mb-8 md:mb-12 relative z-10">
        <p className="text-[#485C11] text-base md:text-lg font-medium font-[Inter] mb-2">
          What's next on the
        </p>
        <h1 className="font-[Playfair_Display] text-6xl md:text-8xl lg:text-[120px] font-bold text-[#485C11] leading-none tracking-tight">
          Docket?
        </h1>
      </div>

      {/* Typewriter image */}
      <div className="relative z-10 w-full max-w-md md:max-w-lg lg:max-w-xl">
        <img
          src={typewriterImg}
          alt="Vintage typewriter"
          className="w-full h-auto object-contain drop-shadow-2xl"
        />
      </div>

      {/* CTA button */}
      <div className="mt-8 relative z-10">
        <button
          onClick={() => onNavigate('upload')}
          className="px-8 py-3 bg-[#485C11] text-white rounded-full font-medium text-base hover:bg-[#3a4a0d] transition-colors shadow-lg"
        >
          Upload Syllabus
        </button>
      </div>
    </div>
  );
}
