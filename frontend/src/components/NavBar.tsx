import { useState } from 'react';
import { Menu, X } from 'lucide-react';

interface NavBarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export default function NavBar({ currentPage, onNavigate }: NavBarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { label: 'Schedule', page: 'schedule' },
    { label: 'Tasks', page: 'tasks' },
  ];

  return (
    <nav className="w-full px-6 py-4 flex items-center justify-between relative z-10">
      {/* Desktop: nav links on the left (glassmorphism container) */}
      <div className="hidden md:flex items-center gap-0 backdrop-blur-[15px] bg-white/10 rounded-full p-1">
        {navItems.map((item) => (
          <button
            key={item.page}
            onClick={() => onNavigate(item.page)}
            className={`px-5 py-2 rounded-full text-sm font-medium transition-colors ${
              currentPage === item.page
                ? 'bg-[#485C11] text-white'
                : 'bg-[#485C11] text-white hover:bg-[#3a4a0d]'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Desktop: logo centered (tablet+) */}
      <button
        onClick={() => onNavigate('home')}
        className="hidden lg:block absolute left-1/2 -translate-x-1/2 font-[Playfair_Display] text-lg font-bold text-[#485C11] tracking-wide"
      >
        The Clerk's Desk
      </button>

      {/* Desktop: Sign In on the right */}
      <div className="hidden md:block">
        <button className="px-5 py-2 rounded-full text-sm font-medium bg-[#485C11] text-white hover:bg-[#3a4a0d] transition-colors">
          Sign In
        </button>
      </div>

      {/* Mobile: "Area" brand + hamburger */}
      <div className="md:hidden flex items-center justify-between w-full">
        <button
          onClick={() => onNavigate('home')}
          className="font-[Playfair_Display] text-lg font-bold text-[#485C11]"
        >
          Area
        </button>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="text-[#485C11] p-1"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile dropdown menu */}
      {mobileMenuOpen && (
        <div className="absolute top-full left-0 right-0 bg-[#C1E1C1]/95 backdrop-blur-sm shadow-lg md:hidden z-50">
          <div className="flex flex-col p-4 gap-2">
            {navItems.map((item) => (
              <button
                key={item.page}
                onClick={() => {
                  onNavigate(item.page);
                  setMobileMenuOpen(false);
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-[#485C11] hover:bg-[#485C11] hover:text-white transition-colors text-left"
              >
                {item.label}
              </button>
            ))}
            <button className="px-4 py-2 rounded-lg text-sm font-medium text-[#485C11] hover:bg-[#485C11] hover:text-white transition-colors text-left">
              Sign In
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
