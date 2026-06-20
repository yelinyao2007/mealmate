import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { translations } from '../i18n';
import api from '../api';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem('language') || 'en');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.get('/users/me/language')
        .then(res => {
          const lang = res.data.language || 'en';
          setLanguage(lang);
          localStorage.setItem('language', lang);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const switchLanguage = useCallback(async (lang) => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        await api.put('/users/me/language', null, { params: { lang } });
      } catch (e) {
        console.error('Failed to save language preference:', e);
      }
    }
    localStorage.setItem('language', lang);
    setLanguage(lang);
  }, []);

  const t = useCallback((key, params) => {
    const dict = translations[language] || translations.en;
    let text = dict[key] || translations.en[key] || key;
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        text = text.replace(`{${k}}`, v);
      });
    }
    return text;
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, switchLanguage, t, loading }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext);