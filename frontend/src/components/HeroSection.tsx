import typewriterImg from '../assets/typewriter.png';
import starImg from '../assets/star.png';
import logoD from '../assets/docket-logo-d.png';
import logoOcket from '../assets/docket-logo-ocket.png';

interface HeroSectionProps {
  onNavigate: (page: string) => void;
}

export default function HeroSection({ onNavigate }: HeroSectionProps) {
  return (
    <div className="flex-1 flex flex-col items-start justify-center px-6 md:px-16 lg:px-24 py-4 text-left relative overflow-hidden">
      {/* Outer scattered stars */}
      <img src={starImg} alt="" className="absolute top-6 left-[4%] w-16 h-16 md:w-24 md:h-24 opacity-100 pointer-events-none animate-float-delayed object-contain rotate-12" />
      <img src={starImg} alt="" className="absolute top-10 right-[7%] w-20 h-20 md:w-28 md:h-28 opacity-100 pointer-events-none animate-float-slow object-contain -rotate-6" />
      <img src={starImg} alt="" className="absolute top-[28%] left-[2%] w-14 h-14 md:w-20 md:h-20 opacity-100 pointer-events-none animate-float-slow object-contain rotate-45" />
      <img src={starImg} alt="" className="absolute top-[22%] right-[3%] w-20 h-20 md:w-32 md:h-32 opacity-100 pointer-events-none animate-float-delayed object-contain -rotate-12" />
      <img src={starImg} alt="" className="absolute bottom-14 left-[8%] w-32 h-32 md:w-44 md:h-44 opacity-100 pointer-events-none animate-float-slow object-contain" />
      <img src={starImg} alt="" className="absolute bottom-24 right-[10%] w-28 h-28 md:w-40 md:h-40 opacity-100 pointer-events-none animate-float-delayed object-contain" />
      <img src={starImg} alt="" className="absolute bottom-[48%] left-[14%] w-16 h-16 md:w-24 md:h-24 opacity-100 pointer-events-none animate-float-slow object-contain rotate-[30deg]" />
      <img src={starImg} alt="" className="absolute bottom-[42%] right-[5%] w-14 h-14 md:w-20 md:h-20 opacity-100 pointer-events-none animate-float-delayed object-contain -rotate-[20deg]" />
      <img src={starImg} alt="" className="absolute bottom-6 left-[38%] w-10 h-10 md:w-14 md:h-14 opacity-100 pointer-events-none animate-float-slow object-contain rotate-[15deg]" />
      <img src={starImg} alt="" className="absolute top-[42%] left-[22%] w-6 h-6 md:w-8 md:h-8 opacity-100 pointer-events-none animate-float-delayed object-contain rotate-[60deg]" />
      <img src={starImg} alt="" className="absolute top-12 left-[20%] w-14 h-14 md:w-20 md:h-20 opacity-100 pointer-events-none animate-float-slow object-contain -rotate-[25deg]" />
      <img src={starImg} alt="" className="absolute top-[15%] right-[18%] w-16 h-16 md:w-22 md:h-22 opacity-100 pointer-events-none animate-float-delayed object-contain rotate-[40deg]" />
      <img src={starImg} alt="" className="absolute bottom-10 right-[35%] w-14 h-14 md:w-20 md:h-20 opacity-100 pointer-events-none animate-float-slow object-contain -rotate-[10deg]" />
      <img src={starImg} alt="" className="absolute top-[55%] right-[20%] w-7 h-7 md:w-9 md:h-9 opacity-100 pointer-events-none animate-float-delayed object-contain rotate-[50deg]" />
      <img src={starImg} alt="" className="absolute bottom-[55%] left-[30%] w-6 h-6 md:w-8 md:h-8 opacity-100 pointer-events-none animate-float-slow object-contain rotate-[70deg]" />

      {/* Heading */}
      <div className="mb-0 relative z-10">
        <p className="text-[#FFFBF1] text-xl md:text-2xl lg:text-3xl font-medium font-[Inter] mb-2">
          What's next on the
        </p>
        <h1 className="font-[Inter] text-8xl md:text-[11rem] lg:text-[14rem] font-bold text-[#FFFBF1] leading-none tracking-tight flex items-end -mt-14 md:-mt-22">
          <img src={logoD} alt="D" className="inline-block h-[2em] w-auto -mr-[0.68em] -mt-[0.3em] -mb-[0.45em] -ml-[0.75em] object-contain" />
          <img src={logoOcket} alt="ocket" className="inline-block h-[2.3em] w-auto -ml-[0.05em] -mb-[0.7em] object-contain" />
          <span>?</span>
        </h1>
      </div>

      {/* Typewriter image with nearby stars */}
      <div className="relative z-10 w-full max-w-xs md:max-w-lg lg:max-w-xl self-center -mt-12 md:-mt-20">
        <img
          src={typewriterImg}
          alt="Vintage typewriter"
          className="w-full h-auto object-contain drop-shadow-2xl"
        />
        {/* Stars hugging the typewriter */}
        <img src={starImg} alt="" className="absolute -top-4 -left-8 md:-left-14 w-18 h-18 md:w-28 md:h-28 opacity-100 pointer-events-none animate-float-delayed object-contain rotate-[20deg]" />
        <img src={starImg} alt="" className="absolute -top-6 -right-6 md:-right-12 w-16 h-16 md:w-24 md:h-24 opacity-100 pointer-events-none animate-float-slow object-contain -rotate-[15deg]" />
        <img src={starImg} alt="" className="absolute top-[20%] -left-10 md:-left-16 w-8 h-8 md:w-12 md:h-12 opacity-100 pointer-events-none animate-float-slow object-contain rotate-[45deg]" />
        <img src={starImg} alt="" className="absolute top-[30%] -right-8 md:-right-14 w-16 h-16 md:w-24 md:h-24 opacity-100 pointer-events-none animate-float-delayed object-contain -rotate-[30deg]" />
        <img src={starImg} alt="" className="absolute bottom-[15%] -left-6 md:-left-10 w-16 h-16 md:w-24 md:h-24 opacity-100 pointer-events-none animate-float-delayed object-contain rotate-[10deg]" />
        <img src={starImg} alt="" className="absolute bottom-[10%] -right-5 md:-right-10 w-8 h-8 md:w-12 md:h-12 opacity-100 pointer-events-none animate-float-slow object-contain -rotate-[40deg]" />
        <img src={starImg} alt="" className="absolute -bottom-4 left-[20%] w-7 h-7 md:w-10 md:h-10 opacity-100 pointer-events-none animate-float-slow object-contain rotate-[55deg]" />
        <img src={starImg} alt="" className="absolute -bottom-6 right-[15%] w-9 h-9 md:w-12 md:h-12 opacity-100 pointer-events-none animate-float-delayed object-contain -rotate-[25deg]" />
      </div>

      {/* CTA button */}
      <div className="-mt-28 relative z-20 self-center">
        <button
          onClick={() => onNavigate('upload')}
          className="px-12 py-4 bg-[#485C11] text-white rounded-full font-semibold text-lg md:text-xl hover:bg-[#3a4a0d] transition-colors shadow-lg"
        >
          Upload Syllabus
        </button>
      </div>
    </div>
  );
}
