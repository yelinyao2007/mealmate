import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { ChefHat, AlertCircle } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/ai');
    } catch (err) {
      setError(err.response?.data?.detail || t('login.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <ChefHat size={48} className="text-terracotta mx-auto mb-3" />
          <h1 className="font-heading text-3xl">{t('login.welcome')}</h1>
          <p className="text-charcoal/60 text-sm mt-1">{t('login.subtitle')}</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 text-red-500 text-sm bg-red-50 px-4 py-3 rounded-xl">
              <AlertCircle size={16} /> {error}
            </div>
          )}
          <input
            type="email"
            placeholder={t('login.emailPlaceholder')}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="input-field"
          />
          <input
            type="password"
            placeholder={t('login.passwordPlaceholder')}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="input-field"
          />
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? t('login.signingIn') : t('login.signIn')}
          </button>
        </form>
        <p className="text-center text-sm text-charcoal/60 mt-6">
          {t('login.noAccount')}{' '}
          <Link to="/register" className="text-terracotta font-semibold hover:underline">
            {t('login.signUp')}
          </Link>
        </p>
      </div>
    </div>
  );
}
