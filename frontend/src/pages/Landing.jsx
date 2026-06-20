import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { ChefHat, Sparkles, Users, ShoppingCart, Leaf } from 'lucide-react';

export default function Landing() {
  const { user } = useAuth();
  const { t } = useLanguage();

  return (
    <div className="min-h-[calc(100vh-3.5rem)]">
      {/* Hero */}
      <section className="max-w-5xl mx-auto px-4 py-16 md:py-24 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage/10 text-sage text-sm font-medium mb-6">
          <Leaf size={16} /> {t('landing.badge')}
        </div>
        <h1 className="font-heading text-5xl md:text-7xl text-charcoal mb-4 leading-tight">
          {t('landing.heroTitle1')}<br />
          <span className="text-terracotta">{t('landing.heroTitle2')}</span>
        </h1>
        <p className="text-lg text-charcoal/60 max-w-xl mx-auto mb-8">
          {t('landing.heroDesc')}
        </p>
        <div className="flex items-center justify-center gap-4">
          {user ? (
            <Link to="/ai" className="btn-primary text-lg px-8 py-3">
              {t('landing.startCooking')}
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn-primary text-lg px-8 py-3">
                {t('landing.getStarted')}
              </Link>
              <Link to="/feed" className="btn-outline text-lg px-8 py-3">
                {t('landing.browseRecipes')}
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 pb-20">
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            icon={<Sparkles className="text-terracotta" size={32} />}
            title={t('landing.feature1Title')}
            desc={t('landing.feature1Desc')}
          />
          <FeatureCard
            icon={<Users className="text-sage" size={32} />}
            title={t('landing.feature2Title')}
            desc={t('landing.feature2Desc')}
          />
          <FeatureCard
            icon={<ShoppingCart className="text-gold" size={32} />}
            title={t('landing.feature3Title')}
            desc={t('landing.feature3Desc')}
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="card text-center">
      <div className="w-16 h-16 rounded-2xl bg-cream flex items-center justify-center mx-auto mb-4">
        {icon}
      </div>
      <h3 className="font-heading text-xl mb-2">{title}</h3>
      <p className="text-sm text-charcoal/60">{desc}</p>
    </div>
  );
}
