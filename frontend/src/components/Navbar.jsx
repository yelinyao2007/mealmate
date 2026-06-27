import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { languages } from '../i18n';
import { ChefHat, Home, Sparkles, BookOpen, Bookmark, Bell, User, LogOut, Menu, X, Globe, Users, Camera } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import api from '../api';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { t, language, switchLanguage } = useLanguage();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const desktopLangRef = useRef(null);
  const mobileLangRef = useRef(null);

  useEffect(() => {
    if (user) {
      api.get('/notifications/unread-count').then(r => setUnread(r.data.count)).catch(() => {});
    }
  }, [user]);

  useEffect(() => {
    const handleClick = (e) => {
      if (desktopLangRef.current && !desktopLangRef.current.contains(e.target) && 
          mobileLangRef.current && !mobileLangRef.current.contains(e.target)) {
        setLangOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
    setMenuOpen(false);
  };

  const currentLang = languages.find((l) => l.code === language) || languages[0];

  return (
    <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gold/20 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="flex items-center gap-2 text-terracotta font-heading text-2xl">
          <ChefHat size={28} />
          MealMate
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          <NavLink to="/feed" icon={<Home size={18} />} label={t('nav.feed')} />
          {user && <NavLink to="/workflow" icon={<Users size={18} />} label={t('nav.workflow')} />}
          {user && <NavLink to="/smart-cook" icon={<Sparkles size={18} />} label="SmartCook" />}
          {user && <NavLink to="/ai" icon={<ChefHat size={18} />} label={t('nav.aiChef')} />}
          {user && <NavLink to="/image" icon={<Camera size={18} />} label={t('nav.imageRecog')} />}
          {user && <NavLink to="/recipes/new" icon={<BookOpen size={18} />} label={t('nav.create')} />}
          {user && <NavLink to="/bookmarks" icon={<Bookmark size={18} />} label={t('nav.saved')} />}
          {user && (
            <NavLink to="/notifications" icon={<Bell size={18} />} label={t('nav.alerts')} badge={unread} />
          )}
          {user ? (
            <>
              <NavLink to="/profile" icon={<User size={18} />} label={t('nav.profile')} />
              <button onClick={handleLogout} className="ml-2 p-2 rounded-lg text-charcoal/60 hover:text-terracotta hover:bg-terracotta/5 transition-colors">
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <Link to="/login" className="btn-primary ml-2 text-sm py-2 px-4">{t('nav.signIn')}</Link>
          )}

          {/* Language switcher */}
          <div className="relative ml-2" ref={desktopLangRef}>
            <button
              onClick={() => setLangOpen(!langOpen)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-charcoal/70 hover:text-terracotta hover:bg-terracotta/5 transition-colors"
            >
              <Globe size={16} />
              {currentLang.flag}
            </button>
            {langOpen && (
              <div className="absolute right-0 mt-1 w-36 bg-white rounded-xl shadow-lg border border-gold/20 py-1 z-50">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => { switchLanguage(lang.code); setLangOpen(false); }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-cream transition-colors flex items-center gap-2 ${
                      language === lang.code ? 'text-terracotta font-semibold' : 'text-charcoal/70'
                    }`}
                  >
                    <span>{lang.flag}</span> {lang.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Mobile menu toggle */}
        <div className="flex items-center gap-1 md:hidden">
          {/* Mobile language switcher */}
          <div className="relative" ref={mobileLangRef}>
            <button
              onClick={() => setLangOpen(!langOpen)}
              className="p-2 text-charcoal/70"
            >
              <Globe size={20} />
            </button>
            {langOpen && (
              <div className="absolute right-0 mt-1 w-36 bg-white rounded-xl shadow-lg border border-gold/20 py-1 z-50">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => { switchLanguage(lang.code); setLangOpen(false); }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-cream transition-colors flex items-center gap-2 ${
                      language === lang.code ? 'text-terracotta font-semibold' : 'text-charcoal/70'
                    }`}
                  >
                    <span>{lang.flag}</span> {lang.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button className="p-2" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t border-gold/20 px-4 py-3 space-y-1">
          <MobileLink to="/feed" label={t('nav.feed')} onClick={() => setMenuOpen(false)} />
          {user && <MobileLink to="/workflow" label={t('nav.workflow')} onClick={() => setMenuOpen(false)} />}
          {user && <MobileLink to="/smart-cook" label="SmartCook" onClick={() => setMenuOpen(false)} />}
          {user && <MobileLink to="/ai" label={t('nav.aiChef')} onClick={() => setMenuOpen(false)} />}
          {user && <MobileLink to="/recipes/new" label={t('nav.createRecipe')} onClick={() => setMenuOpen(false)} />}
          {user && <MobileLink to="/bookmarks" label={t('nav.saved')} onClick={() => setMenuOpen(false)} />}
          {user && <MobileLink to="/notifications" label={`${t('nav.notifications')}${unread ? ` (${unread})` : ''}`} onClick={() => setMenuOpen(false)} />}
          {user ? (
            <>
              <MobileLink to="/profile" label={t('nav.profile')} onClick={() => setMenuOpen(false)} />
              <button onClick={handleLogout} className="w-full text-left px-3 py-2 rounded-lg text-terracotta font-medium">
                {t('nav.logOut')}
              </button>
            </>
          ) : (
            <MobileLink to="/login" label={t('nav.signIn')} onClick={() => setMenuOpen(false)} />
          )}
        </div>
      )}
    </nav>
  );
}

function NavLink({ to, icon, label, badge }) {
  return (
    <Link
      to={to}
      className="relative flex items-center gap-1.5 px-2 py-2 rounded-lg text-sm font-medium text-charcoal/70 hover:text-terracotta hover:bg-terracotta/5 transition-colors whitespace-nowrap"
    >
{icon}
      <span>{label}</span>
      {badge > 0 && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-terracotta text-white text-xs rounded-full flex items-center justify-center">
          {badge}
        </span>
      )}
    </Link>
  );
}

function MobileLink({ to, label, onClick }) {
  return (
    <Link to={to} onClick={onClick} className="block px-3 py-2 rounded-lg text-charcoal/80 hover:bg-cream font-medium">
      {label}
    </Link>
  );
}
