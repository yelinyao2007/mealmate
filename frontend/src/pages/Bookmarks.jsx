import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { useLanguage } from '../context/LanguageContext';
import { Bookmark, Loader2, ChefHat, Clock, Heart } from 'lucide-react';

export default function Bookmarks() {
  const { t } = useLanguage();
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/bookmarks').then((res) => setBookmarks(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="font-heading text-3xl flex items-center gap-2 mb-6">
        <Bookmark className="text-terracotta" size={28} />
        {t('bookmarks.title')}
      </h1>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={32} className="animate-spin text-terracotta" />
        </div>
      ) : bookmarks.length === 0 ? (
        <div className="text-center py-20 text-charcoal/40">
          <Bookmark size={48} className="mx-auto mb-3 opacity-30" />
          <p className="font-heading text-2xl mb-2">{t('bookmarks.empty')}</p>
          <p>
            {t('bookmarks.emptyHint', { link: '' })}
            <Link to="/feed" className="text-terracotta hover:underline">{t('bookmarks.feedLink')}</Link>
          </p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {bookmarks.map((r) => (
            <Link key={r.id} to={`/recipes/${r.id}`} className="card block group">
              {r.image_url ? (
                <img src={r.image_url} alt={r.title} className="w-full h-44 object-cover rounded-xl mb-3" />
              ) : (
                <div className="w-full h-44 bg-gradient-to-br from-gold/20 to-sage/20 rounded-xl mb-3 flex items-center justify-center">
                  <ChefHat size={48} className="text-terracotta/30" />
                </div>
              )}
              <h3 className="font-heading text-xl text-charcoal group-hover:text-terracotta transition-colors line-clamp-2">
                {r.title}
              </h3>
              <div className="flex items-center justify-between mt-2 text-sm text-charcoal/50">
                <span className="text-sage font-medium">{r.author_name}</span>
                <div className="flex items-center gap-3">
                  {r.cook_time_minutes > 0 && <span className="flex items-center gap-1"><Clock size={14} /> {r.cook_time_minutes}m</span>}
                  <span className="flex items-center gap-1"><Heart size={14} /> {r.likes_count}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
