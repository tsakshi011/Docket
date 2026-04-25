import typewriterImg from '../assets/typewriter.png';
import starImg from '../assets/star.png';

interface HeroSectionProps {
  onNavigate: (page: string) => void;
}

export default function HeroSection({ onNavigate }: HeroSectionProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 pb-12 text-center relative overflow-hidden">
      {/* Outer scattered stars */}
      <img src={starImg} alt="" className="absolute top-6 left-[4%] w-10 h-10 md:w-14 md:h-14 opacity-60 pointer-events-none animate-float-delayed object-contain rotate-12" />
      <img src={starImg} alt="" className="absolute top-10 right-[7%] w-12 h-12 md:w-16 md:h-16 opacity-70 pointer-events-none animate-float-slow object-contain -rotate-6" />
      <img src={starImg} alt="" className="absolute top-[28%] left-[2%] w-8 h-8 md:w-12 md:h-12 opacity-50 pointer-events-none animate-float-slow object-contain rotate-45" />
      <img src={starImg} alt="" className="absolute top-[22%] right-[3%] w-14 h-14 md:w-20 md:h-20 opacity-65 pointer-events-none animate-float-delayed object-contain -rotate-12" />
      <img src={starImg} alt="" className="absolute bottom-14 left-[8%] w-24 h-24 md:w-36 md:h-36 opacity-90 pointer-events-none animate-float-slow object-contain" />
      <img src={starImg} alt="" className="absolute bottom-24 right-[10%] w-20 h-20 md:w-28 md:h-28 opacity-80 pointer-events-none animate-float-delayed object-contain" />
      <img src={starImg} alt="" className="absolute bottom-[48%] left-[14%] w-10 h-10 md:w-14 md:h-14 opacity-55 pointer-events-none animate-float-slow object-contain rotate-[30deg]" />
      <img src={starImg} alt="" className="absolute bottom-[42%] right-[5%] w-8 h-8 md:w-10 md:h-10 opacity-45 pointer-events-none animate-float-delayed object-contain -rotate-[20deg]" />
      <img src={starImg} alt="" className="absolute bottom-6 left-[38%] w-10 h-10 md:w-14 md:h-14 opacity-50 pointer-events-none animate-float-slow object-contain rotate-[15deg]" />
      <img src={starImg} alt="" className="absolute top-[42%] left-[22%] w-6 h-6 md:w-8 md:h-8 opacity-40 pointer-events-none animate-float-delayed object-contain rotate-[60deg]" />
      <img src={starImg} alt="" className="absolute top-12 left-[20%] w-7 h-7 md:w-10 md:h-10 opacity-55 pointer-events-none animate-float-slow object-contain -rotate-[25deg]" />
      <img src={starImg} alt="" className="absolute top-[15%] right-[18%] w-8 h-8 md:w-11 md:h-11 opacity-50 pointer-events-none animate-float-delayed object-contain rotate-[40deg]" />
      <img src={starImg} alt="" className="absolute bottom-10 right-[35%] w-9 h-9 md:w-12 md:h-12 opacity-55 pointer-events-none animate-float-slow object-contain -rotate-[10deg]" />
      <img src={starImg} alt="" className="absolute top-[55%] right-[20%] w-7 h-7 md:w-9 md:h-9 opacity-45 pointer-events-none animate-float-delayed object-contain rotate-[50deg]" />
      <img src={starImg} alt="" className="absolute bottom-[55%] left-[30%] w-6 h-6 md:w-8 md:h-8 opacity-35 pointer-events-none animate-float-slow object-contain rotate-[70deg]" />

      {/* Heading */}
      <div className="mb-8 md:mb-12 relative z-10">
        <p className="text-[#485C11] text-base md:text-lg font-medium font-[Inter] mb-2">
          What's next on the
        </p>
        <h1 className="font-[Playfair_Display] text-6xl md:text-8xl lg:text-[120px] font-bold text-[#485C11] leading-none tracking-tight">
          Docket?
        </h1>
      </div>

      {/* Typewriter image with nearby stars */}
      <div className="relative z-10 w-full max-w-md md:max-w-lg lg:max-w-xl">
        <img
          src={typewriterImg}
          alt="Vintage typewriter"
          className="w-full h-auto object-contain drop-shadow-2xl"
        />
        {/* Stars hugging the typewriter */}
        <img src={starImg} alt="" className="absolute -top-4 -left-8 md:-left-14 w-12 h-12 md:w-18 md:h-18 opacity-85 pointer-events-none animate-float-delayed object-contain rotate-[20deg]" />
        <img src={starImg} alt="" className="absolute -top-6 -right-6 md:-right-12 w-10 h-10 md:w-16 md:h-16 opacity-75 pointer-events-none animate-float-slow object-contain -rotate-[15deg]" />
        <img src={starImg} alt="" className="absolute top-[20%] -left-10 md:-left-16 w-8 h-8 md:w-12 md:h-12 opacity-60 pointer-events-none animate-float-slow object-contain rotate-[45deg]" />
        <img src={starImg} alt="" className="absolute top-[30%] -right-8 md:-right-14 w-9 h-9 md:w-14 md:h-14 opacity-70 pointer-events-none animate-float-delayed object-contain -rotate-[30deg]" />
        <img src={starImg} alt="" className="absolute bottom-[15%] -left-6 md:-left-10 w-10 h-10 md:w-14 md:h-14 opacity-65 pointer-events-none animate-float-delayed object-contain rotate-[10deg]" />
        <img src={starImg} alt="" className="absolute bottom-[10%] -right-5 md:-right-10 w-8 h-8 md:w-12 md:h-12 opacity-55 pointer-events-none animate-float-slow object-contain -rotate-[40deg]" />
        <img src={starImg} alt="" className="absolute -bottom-4 left-[20%] w-7 h-7 md:w-10 md:h-10 opacity-60 pointer-events-none animate-float-slow object-contain rotate-[55deg]" />
        <img src={starImg} alt="" className="absolute -bottom-6 right-[15%] w-9 h-9 md:w-12 md:h-12 opacity-70 pointer-events-none animate-float-delayed object-contain -rotate-[25deg]" />
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
