import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../api';
import { Save, CheckCircle, Brain } from 'lucide-react';

const DIETARY_OPTIONS = ['Vegetarian', 'Vegan', 'Low-Carb', 'Keto', 'Gluten-Free', 'Halal', 'Kosher'];
const ALLERGY_OPTIONS = ['Peanuts', 'Tree Nuts', 'Milk', 'Eggs', 'Shellfish', 'Soy', 'Wheat', 'Fish'];
const CUISINE_OPTIONS = ['Chinese', 'Japanese', 'Italian', 'Mexican', 'Indian', 'Thai', 'French', 'Korean', 'American', 'Mediterranean'];
const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced'];
const GOALS = [
  { value: 'lose_fat', labelKey: 'profile.goal.loseFat' },
  { value: 'gain_muscle', labelKey: 'profile.goal.gainMuscle' },
  { value: 'sugar_control', labelKey: 'profile.goal.sugarControl' },
  { value: 'general', labelKey: 'profile.goal.general' },
];
const HEALTH_CONDITIONS = [
  { value: 'diabetes', labelKey: 'profile.healthConditions.diabetes' },
  { value: 'hypertension', labelKey: 'profile.healthConditions.hypertension' },
];

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState('');
  const [dietary, setDietary] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [skillLevel, setSkillLevel] = useState('beginner');
  const [cuisines, setCuisines] = useState([]);
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [age, setAge] = useState('');
  const [goal, setGoal] = useState('');
  const [targetCalories, setTargetCalories] = useState('');
  const [healthConditions, setHealthConditions] = useState([]);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      const prefs = user.preferences || {};
      setDietary(prefs.dietary || []);
      setAllergies(prefs.allergies || []);
      setSkillLevel(prefs.skill_level || 'beginner');
      setCuisines(prefs.cuisines || []);
      setHeight(user.height ? String(user.height) : '');
      setWeight(user.weight ? String(user.weight) : '');
      setAge(user.age ? String(user.age) : '');
      setGoal(user.goal || '');
      setTargetCalories(user.target_calories ? String(user.target_calories) : '');
      setHealthConditions(user.health_conditions || []);
    }
  }, [user]);

  const toggleItem = (list, setList, item) => {
    setList(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  const handleSave = async () => {
    setLoading(true);
    setSaved(false);
    try {
      const payload = {
        name,
        preferences: { dietary, allergies, skill_level: skillLevel, cuisines },
        profile: {
          height: height ? parseFloat(height) : null,
          weight: weight ? parseFloat(weight) : null,
          age: age ? parseInt(age, 10) : null,
          goal: goal || null,
          target_calories: targetCalories ? parseInt(targetCalories, 10) : null,
          health_conditions: healthConditions,
        },
      };
      await api.put('/users/me', payload);
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      alert(t('profile.saveFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setAnalysisResult(null);
    try {
      const res = await api.post('/users/me/analyze-profile');
      setAnalysisResult(res.data);
    } catch {
      alert(t('profile.saveFailed'));
    } finally {
      setAnalyzing(false);
    }
  };

  const goalLabel = (val) => {
    const g = GOALS.find((x) => x.value === val);
    return g ? t(g.labelKey) : val;
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

        <hr className="border-gold/30" />
        <h2 className="font-heading text-xl">{t('profile.healthTitle')}</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-1">{t('profile.height')}</label>
            <input type="number" value={height} onChange={(e) => setHeight(e.target.value)} className="input-field" placeholder="170" />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">{t('profile.weight')}</label>
            <input type="number" value={weight} onChange={(e) => setWeight(e.target.value)} className="input-field" placeholder="65" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-1">{t('profile.age')}</label>
            <input type="number" value={age} onChange={(e) => setAge(e.target.value)} className="input-field" placeholder="25" />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">{t('profile.targetCalories')}</label>
            <input type="number" value={targetCalories} onChange={(e) => setTargetCalories(e.target.value)} className="input-field" placeholder="2000" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-semibold mb-2">{t('profile.goal')}</label>
          <div className="flex flex-wrap gap-2">
            {GOALS.map((g) => (
              <button
                key={g.value}
                onClick={() => setGoal(goal === g.value ? '' : g.value)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  goal === g.value ? 'bg-terracotta text-white' : 'bg-gold/20 text-charcoal hover:bg-gold/40'
                }`}
              >
                {t(g.labelKey)}
              </button>
            ))}
          </div>
        </div>
        <ChipSelector label={t('profile.healthConditions')} options={HEALTH_CONDITIONS.map((c) => c.value)} selected={healthConditions} onToggle={(item) => toggleItem(healthConditions, setHealthConditions, item)} optionLabels={Object.fromEntries(HEALTH_CONDITIONS.map((c) => [c.value, t(c.labelKey)]))} />

        <div className="flex gap-3">
          <button onClick={handleSave} disabled={loading} className="btn-primary flex items-center gap-2">
            {saved ? <><CheckCircle size={18} /> {t('profile.saved')}</> : <><Save size={18} /> {loading ? t('profile.saving') : t('profile.saveProfile')}</>}
          </button>
          <button onClick={handleAnalyze} disabled={analyzing} className="btn-primary flex items-center gap-2" style={{ background: '#7c3aed' }}>
            <Brain size={18} /> {analyzing ? t('profile.analyzing') : t('profile.analyzeProfile')}
          </button>
        </div>

        {analysisResult && analysisResult.success && (
          <div className="bg-gold/10 border border-gold/30 rounded-xl p-4 space-y-3">
            <h3 className="font-heading text-lg">{t('profile.analysisResult')}</h3>
            {analysisResult.data.bmi != null && (
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="font-semibold">BMI:</span> {analysisResult.data.bmi} ({analysisResult.data.bmi_category || '-'})</div>
                <div><span className="font-semibold">{t('profile.targetCalories')}:</span> {analysisResult.data.recommended_calories} kcal</div>
              </div>
            )}
            {analysisResult.data.goal_analysis && (
              <div className="text-sm space-y-1">
                <div><span className="font-semibold">{t('profile.goal')}:</span> {goalLabel(analysisResult.data.goal_analysis.goal)}</div>
                {analysisResult.data.goal_analysis.key_principles && (
                  <ul className="list-disc list-inside text-xs text-charcoal/70">
                    {analysisResult.data.goal_analysis.key_principles.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                )}
              </div>
            )}
            {analysisResult.data.health_warnings && analysisResult.data.health_warnings.length > 0 && (
              <div className="text-sm">
                <span className="font-semibold text-terracotta">{t('profile.healthConditions')}:</span>
                <ul className="list-disc list-inside text-xs text-terracotta/70">
                  {analysisResult.data.health_warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}
            {analysisResult.data.weekly_core_principles && (
              <div className="text-sm">
                <span className="font-semibold">Core Principles:</span>
                <ul className="list-disc list-inside text-xs text-charcoal/70">
                  {analysisResult.data.weekly_core_principles.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>
            )}
            {analysisResult.data.summary && (
              <p className="text-xs text-charcoal/60 italic">{analysisResult.data.summary}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ChipSelector({ label, options, selected, onToggle, optionLabels }) {
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
            {optionLabels ? optionLabels[opt] || opt : opt}
          </button>
        ))}
      </div>
    </div>
  );
}
