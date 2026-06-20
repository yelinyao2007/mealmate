import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { useLanguage } from '../context/LanguageContext';
import { Bell, Heart, MessageCircle, GitFork, CheckCheck, Loader2 } from 'lucide-react';

const ICON_MAP = {
  like: <Heart size={16} className="text-terracotta" />,
  comment: <MessageCircle size={16} className="text-sage" />,
  remix: <GitFork size={16} className="text-gold" />,
};

export default function Notifications() {
  const { t } = useLanguage();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/notifications').then((res) => setNotifications(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const markAllRead = async () => {
    await api.put('/notifications/read-all');
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const markRead = async (id) => {
    await api.put(`/notifications/${id}/read`);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-3xl flex items-center gap-2">
          <Bell className="text-terracotta" size={28} />
          {t('notifications.title')}
        </h1>
        {notifications.some((n) => !n.is_read) && (
          <button onClick={markAllRead} className="text-sm text-sage font-medium flex items-center gap-1 hover:underline">
            <CheckCheck size={16} /> {t('notifications.markAllRead')}
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={32} className="animate-spin text-terracotta" />
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-20 text-charcoal/40">
          <Bell size={48} className="mx-auto mb-3 opacity-30" />
          <p className="font-heading text-2xl">{t('notifications.allCaughtUp')}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => markRead(n.id)}
              className={`card flex items-start gap-3 cursor-pointer ${!n.is_read ? 'border-l-4 border-terracotta' : 'opacity-70'}`}
            >
              <div className="mt-0.5">{ICON_MAP[n.type] || <Bell size={16} />}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm">{n.message}</p>
                <p className="text-xs text-charcoal/40 mt-1">
                  {new Date(n.created_at).toLocaleDateString()}
                </p>
              </div>
              {n.recipe_id && (
                <Link
                  to={`/recipes/${n.recipe_id}`}
                  onClick={(e) => e.stopPropagation()}
                  className="text-xs text-terracotta hover:underline flex-shrink-0"
                >
                  {t('notifications.view')}
                </Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
