import { useState } from 'react';
import { Menu, X, LogOut } from 'lucide-react';
import { useAuth } from '../useAuth';

interface NavBarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export default function NavBar({ currentPage, onNavigate }: NavBarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, signInWithGoogle, logout } = useAuth();

  const navItems = [
    { label: 'Schedule', page: 'schedule' },
    { label: 'Tasks', page: 'tasks' },
  ];

  return (
    <nav className="w-full px-6 py-4 flex items-center justify-between relative z-10">
      {/* Desktop: Schedule | Tasks unified bar on the left */}
      <div className="hidden md:flex items-center rounded-full overflow-hidden bg-[#485C11]">
        {navItems.map((item, i) => (
          <button
            key={item.page}
            onClick={() => onNavigate(item.page)}
            className={`px-6 py-2 text-sm font-medium text-[#FFFBF1] transition-colors hover:bg-[#3a4a0d] ${
              currentPage === item.page ? 'bg-[#3a4a0d]' : ''
            } ${i > 0 ? 'border-l border-[#FFFBF1]/30' : ''}`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Desktop: logo centered (tablet+) */}
      <button
        onClick={() => onNavigate('home')}
        className="hidden lg:block absolute left-1/2 -translate-x-1/2 font-[Inter] text-lg font-bold text-[#485C11] tracking-wide"
      >
        The Clerk's Desk
      </button>

      {/* Desktop: Sign In / User on the right */}
      <div className="hidden md:flex items-center gap-3">
        {user ? (
          <>
            <img
              src={user.photoURL || ''}
              alt={user.displayName || 'User'}
              className="w-8 h-8 rounded-full border-2 border-[#485C11]"
              referrerPolicy="no-referrer"
            />
            <span className="text-sm font-medium text-[#485C11] max-w-[120px] truncate">
              {user.displayName?.split(' ')[0]}
            </span>
            <button
              onClick={logout}
              className="p-2 rounded-full text-[#485C11] hover:bg-[#485C11]/10 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </>
        ) : (
          <button
            onClick={signInWithGoogle}
            className="px-5 py-2 rounded-full text-sm font-medium bg-[#485C11] text-white hover:bg-[#3a4a0d] transition-colors"
          >
            Sign In
          </button>
        )}
      </div>

      {/* Mobile: brand + hamburger */}
      <div className="md:hidden flex items-center justify-between w-full">
        <button
          onClick={() => onNavigate('home')}
          className="font-[Inter] text-lg font-bold text-[#485C11]"
        >
          Docket
        </button>
        <div className="flex items-center gap-2">
          {user && (
            <img
              src={user.photoURL || ''}
              alt={user.displayName || 'User'}
              className="w-7 h-7 rounded-full border-2 border-[#485C11]"
              referrerPolicy="no-referrer"
            />
          )}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="text-[#485C11] p-1"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
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
            {user ? (
              <button
                onClick={() => { logout(); setMobileMenuOpen(false); }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-[#485C11] hover:bg-[#485C11] hover:text-white transition-colors text-left"
              >
                Sign Out
              </button>
            ) : (
              <button
                onClick={() => { signInWithGoogle(); setMobileMenuOpen(false); }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-[#485C11] hover:bg-[#485C11] hover:text-white transition-colors text-left"
              >
                Sign In with Google
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
