import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../api';
import { Save, CheckCircle } from 'lucide-react';

const DIETARY_OPTIONS = ['Vegetarian', 'Vegan', 'Low-Carb', 'Keto', 'Gluten-Free', 'Halal', 'Kosher'];
const ALLERGY_OPTIONS = ['Peanuts', 'Tree Nuts', 'Milk', 'Eggs', 'Shellfish', 'Soy', 'Wheat', 'Fish'];
const CUISINE_OPTIONS = ['Chinese', 'Japanese', 'Italian', 'Mexican', 'Indian', 'Thai', 'French', 'Korean', 'American', 'Mediterranean'];
const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced'];

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState('');
  const [dietary, setDietary] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [skillLevel, setSkillLevel] = useState('beginner');
  const [cuisines, setCuisines] = useState([]);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      const prefs = user.preferences || {};
      setDietary(prefs.dietary || []);
      setAllergies(prefs.allergies || []);
      setSkillLevel(prefs.skill_level || 'beginner');
      setCuisines(prefs.cuisines || []);
    }
  }, [user]);

  const toggleItem = (list, setList, item) => {
    setList(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  const handleSave = async () => {
    setLoading(true);
    setSaved(false);
    try {
      await api.put('/users/me', {
        name,
        preferences: { dietary, allergies, skill_level: skillLevel, cuisines },
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      alert(t('profile.saveFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="font-heading text-3xl mb-6">{t('profile.title')}</h1>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-semibold mb-1">{t('profile.name')}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className="input-field" />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">{t('profile.skillLevel')}</label>
          <div className="flex gap-2">
            {SKILL_LEVELS.map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSkillLevel(lvl)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  skillLevel === lvl ? 'bg-terracotta text-white' : 'bg-gold/20 text-charcoal hover:bg-gold/40'
                }`}
              >
                {t(`profile.${lvl}`)}
              </button>
            ))}
          </div>
        </div>

        <ChipSelector label={t('profile.dietary')} options={DIETARY_OPTIONS} selected={dietary} onToggle={(item) => toggleItem(dietary, setDietary, item)} />
        <ChipSelector label={t('profile.allergies')} options={ALLERGY_OPTIONS} selected={allergies} onToggle={(item) => toggleItem(allergies, setAllergies, item)} />
        <ChipSelector label={t('profile.cuisines')} options={CUISINE_OPTIONS} selected={cuisines} onToggle={(item) => toggleItem(cuisines, setCuisines, item)} />

        <button onClick={handleSave} disabled={loading} className="btn-primary flex items-center gap-2">
          {saved ? <><CheckCircle size={18} /> {t('profile.saved')}</> : <><Save size={18} /> {loading ? t('profile.saving') : t('profile.saveProfile')}</>}
        </button>
      </div>
    </div>
  );
}

function ChipSelector({ label, options, selected, onToggle }) {
  return (
    <div>
      <label className="block text-sm font-semibold mb-2">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onToggle(opt)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              selected.includes(opt) ? 'bg-sage text-white' : 'bg-gold/20 text-charcoal hover:bg-gold/40'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
