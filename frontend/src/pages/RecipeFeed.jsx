import { useState, useEffect } from 'react';
import api from '../api';
import RecipeCard from '../components/RecipeCard';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Loader2, TrendingUp, Clock as ClockIcon, Users } from 'lucide-react';

export default function RecipeFeed() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState('newest');
  const [followingOnly, setFollowingOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchFeed = async () => {
    setLoading(true);
    try {
      const res = await api.get('/recipes/feed', {
        params: { page, page_size: 12, sort, following_only: followingOnly },
      });
      setRecipes(res.data.items);
      setTotal(res.data.total);
    } catch {
      // silent fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeed();
  }, [sort, followingOnly, page]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="font-heading text-3xl">{t('feed.title')}</h1>
        <div className="flex items-center gap-2 flex-wrap">
          <SortButton active={sort === 'newest'} onClick={() => { setSort('newest'); setPage(1); }} icon={<ClockIcon size={14} />} label={t('feed.newest')} />
          <SortButton active={sort === 'popular'} onClick={() => { setSort('popular'); setPage(1); }} icon={<TrendingUp size={14} />} label={t('feed.popular')} />
          {user && (
            <SortButton
              active={followingOnly}
              onClick={() => { setFollowingOnly(!followingOnly); setPage(1); }}
              icon={<Users size={14} />}
              label={t('feed.following')}
            />
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={32} className="animate-spin text-terracotta" />
        </div>
      ) : recipes.length === 0 ? (
        <div className="text-center py-20 text-charcoal/40">
          <p className="font-heading text-2xl mb-2">{t('feed.noRecipes')}</p>
          <p>{t('feed.beFirst')}</p>
        </div>
      ) : (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {recipes.map((r) => (
              <RecipeCard key={r.id} recipe={r} />
            ))}
          </div>
          {total > 12 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="btn-outline px-4 py-2 text-sm disabled:opacity-30"
              >
                {t('feed.previous')}
              </button>
              <span className="flex items-center px-4 text-sm text-charcoal/60">
                {t('feed.pageOf', { page, total: Math.ceil(total / 12) })}
              </span>
              <button
                disabled={page * 12 >= total}
                onClick={() => setPage(page + 1)}
                className="btn-outline px-4 py-2 text-sm disabled:opacity-30"
              >
                {t('feed.next')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SortButton({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
        active ? 'bg-terracotta text-white' : 'bg-gold/20 text-charcoal hover:bg-gold/40'
      }`}
    >
      {icon} {label}
    </button>
  );
}
