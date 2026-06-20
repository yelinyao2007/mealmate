import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import AffiliateLinks from '../components/AffiliateLinks';
import RecipeCard from '../components/RecipeCard';
import {
  Heart, Bookmark, MessageCircle, Clock, GitFork, Send, Loader2, ChefHat, ArrowLeft,
} from 'lucide-react';

export default function RecipeDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { t } = useLanguage();
  const [recipe, setRecipe] = useState(null);
  const [comments, setComments] = useState([]);
  const [remixes, setRemixes] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [commenting, setCommenting] = useState(false);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [rRes, cRes, rmRes] = await Promise.all([
        api.get(`/recipes/${id}`),
        api.get(`/recipes/${id}/comments`),
        api.get(`/recipes/${id}/remixes`),
      ]);
      setRecipe(rRes.data);
      setComments(cRes.data);
      setRemixes(rmRes.data);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, [id]);

  const handleLike = async () => {
    if (!user) return;
    try {
      const res = await api.post(`/recipes/${id}/like`);
      setRecipe((prev) => ({
        ...prev,
        likes_count: res.data.likes_count,
        is_liked: res.data.status === 'liked',
      }));
    } catch {}
  };

  const handleBookmark = async () => {
    if (!user) return;
    try {
      const res = await api.post(`/bookmarks/${id}`);
      setRecipe((prev) => ({
        ...prev,
        is_saved: res.data.status === 'saved',
      }));
    } catch {}
  };

  const handleComment = async () => {
    if (!newComment.trim()) return;
    setCommenting(true);
    try {
      const res = await api.post(`/recipes/${id}/comments`, { text: newComment });
      setComments((prev) => [res.data, ...prev]);
      setNewComment('');
    } catch {}
    setCommenting(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 size={32} className="animate-spin text-terracotta" />
      </div>
    );
  }

  if (!recipe) {
    return <div className="text-center py-20 text-charcoal/40 font-heading text-2xl">{t('detail.notFound')}</div>;
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link to="/feed" className="inline-flex items-center gap-1 text-sm text-charcoal/50 hover:text-terracotta mb-4">
        <ArrowLeft size={16} /> {t('detail.backToFeed')}
      </Link>

      {/* Header */}
      <div className="card mb-6">
        {recipe.image_url ? (
          <img src={recipe.image_url} alt={recipe.title} className="w-full h-64 object-cover rounded-xl mb-4" />
        ) : (
          <div className="w-full h-48 bg-gradient-to-br from-gold/20 to-sage/20 rounded-xl mb-4 flex items-center justify-center">
            <ChefHat size={64} className="text-terracotta/20" />
          </div>
        )}

        <h1 className="font-heading text-3xl mb-2">{recipe.title}</h1>
        {recipe.description && <p className="text-charcoal/60 mb-4">{recipe.description}</p>}

        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-4 text-sm text-charcoal/50">
            <span className="font-medium text-sage">{recipe.author_name || t('detail.anonymous')}</span>
            {recipe.cook_time_minutes > 0 && (
              <span className="flex items-center gap-1"><Clock size={14} /> {recipe.cook_time_minutes} {t('detail.min')}</span>
            )}
            {recipe.remix_parent_id && (
              <Link to={`/recipes/${recipe.remix_parent_id}`} className="flex items-center gap-1 text-terracotta hover:underline">
                <GitFork size={14} /> {t('detail.remixed')}
              </Link>
            )}
          </div>
          {user && (
            <div className="flex items-center gap-2">
              <button onClick={handleLike} className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${recipe.is_liked ? 'bg-terracotta/10 text-terracotta' : 'bg-gold/20 text-charcoal hover:bg-gold/40'}`}>
                <Heart size={16} className={recipe.is_liked ? 'fill-terracotta' : ''} /> {recipe.likes_count}
              </button>
              <button onClick={handleBookmark} className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${recipe.is_saved ? 'bg-sage/10 text-sage' : 'bg-gold/20 text-charcoal hover:bg-gold/40'}`}>
                <Bookmark size={16} className={recipe.is_saved ? 'fill-sage' : ''} /> {recipe.is_saved ? t('detail.saved') : t('detail.save')}
              </button>
              <Link to={`/recipes/new?remix=${recipe.id}`} className="flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium bg-gold/20 text-charcoal hover:bg-gold/40 transition-colors">
                <GitFork size={16} /> {t('detail.remix')}
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Ingredients & Steps */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h2 className="font-heading text-xl mb-3">{t('detail.ingredients')}</h2>
          <ul className="space-y-2">
            {(recipe.ingredients || []).map((ing, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-terracotta mt-1.5 flex-shrink-0" />
                {ing}
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="font-heading text-xl mb-3">{t('detail.steps')}</h2>
          <ol className="space-y-3">
            {(recipe.steps || []).map((step, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="w-6 h-6 rounded-full bg-sage/20 text-sage flex items-center justify-center flex-shrink-0 text-xs font-bold">
                  {i + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      {/* Affiliate */}
{(recipe.ingredients && recipe.ingredients.length > 0) && (
          <div className="mt-4">
            <AffiliateLinks ingredients={recipe.ingredients} userIngredients={[]} />
        </div>
      )}

      {/* Remixes */}
      {remixes.length > 0 && (
        <div className="mb-6">
          <h2 className="font-heading text-2xl mb-4">{t('detail.remixes')} ({remixes.length})</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {remixes.map((r) => <RecipeCard key={r.id} recipe={r} />)}
          </div>
        </div>
      )}

      {/* Comments */}
      <div className="card">
        <h2 className="font-heading text-xl mb-4 flex items-center gap-2">
          <MessageCircle size={20} /> {t('detail.comments')} ({comments.length})
        </h2>

        {user && (
          <div className="flex gap-2 mb-4">
            <input
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleComment()}
              placeholder={t('detail.addComment')}
              className="input-field flex-1"
            />
            <button onClick={handleComment} disabled={commenting} className="btn-primary px-4">
              {commenting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
        )}

        {comments.length === 0 ? (
          <p className="text-charcoal/40 text-sm">{t('detail.noComments')}</p>
        ) : (
          <div className="space-y-3">
            {comments.map((c) => (
              <div key={c.id} className="bg-cream/50 rounded-xl px-4 py-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-sage">{c.author_name || t('detail.anonymous')}</span>
                  <span className="text-xs text-charcoal/40">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-sm text-charcoal/80">{c.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
