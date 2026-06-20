import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api';
import { useLanguage } from '../context/LanguageContext';
import IngredientInput from '../components/IngredientInput';
import { BookOpen, Plus, X, Loader2 } from 'lucide-react';

export default function CreateRecipe() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const remixId = searchParams.get('remix');

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [ingredients, setIngredients] = useState([]);
  const [steps, setSteps] = useState(['']);
  const [cookTime, setCookTime] = useState(30);
  const [imageUrl, setImageUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingRemix, setLoadingRemix] = useState(false);

  useEffect(() => {
    if (remixId) {
      setLoadingRemix(true);
      api.get(`/recipes/${remixId}`).then((res) => {
        const r = res.data;
        setTitle(`${r.title} (Remix)`);
        setDescription(r.description);
        setIngredients(r.ingredients || []);
        setSteps(r.steps || ['']);
        setCookTime(r.cook_time_minutes);
      }).catch(() => {}).finally(() => setLoadingRemix(false));
    }
  }, [remixId]);

  const addStep = () => setSteps([...steps, '']);
  const removeStep = (idx) => setSteps(steps.filter((_, i) => i !== idx));
  const updateStep = (idx, val) => {
    const updated = [...steps];
    updated[idx] = val;
    setSteps(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      const res = await api.post('/recipes', {
        title,
        description,
        ingredients,
        steps: steps.filter((s) => s.trim()),
        cook_time_minutes: cookTime,
        image_url: imageUrl,
        remix_parent_id: remixId ? parseInt(remixId) : null,
      });
      navigate(`/recipes/${res.data.id}`);
    } catch {
      alert(t('create.failed'));
    } finally {
      setLoading(false);
    }
  };

  if (loadingRemix) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 size={32} className="animate-spin text-terracotta" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="font-heading text-3xl flex items-center gap-2 mb-6">
        <BookOpen className="text-terracotta" size={28} />
        {remixId ? t('create.remixTitle') : t('create.title')}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-semibold mb-1">{t('create.labelTitle')}</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required className="input-field" placeholder={t('create.titlePlaceholder')} />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1">{t('create.labelDesc')}</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="input-field min-h-[80px]" placeholder={t('create.descPlaceholder')} />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1">{t('create.labelImage')}</label>
          <input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} className="input-field" placeholder={t('create.imagePlaceholder')} />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1">{t('create.labelCookTime')}</label>
          <input type="number" value={cookTime} onChange={(e) => setCookTime(parseInt(e.target.value) || 0)} min={0} className="input-field w-32" />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1">{t('create.labelIngredients')}</label>
          <IngredientInput ingredients={ingredients} onChange={setIngredients} />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">{t('create.labelSteps')}</label>
          <div className="space-y-2">
            {steps.map((step, idx) => (
              <div key={idx} className="flex gap-2 items-start">
                <span className="w-7 h-7 rounded-full bg-sage/20 text-sage flex items-center justify-center flex-shrink-0 text-xs font-bold mt-2">
                  {idx + 1}
                </span>
                <textarea
                  value={step}
                  onChange={(e) => updateStep(idx, e.target.value)}
                  className="input-field flex-1 min-h-[60px]"
                  placeholder={t('create.stepPlaceholder', { n: idx + 1 })}
                />
                {steps.length > 1 && (
                  <button type="button" onClick={() => removeStep(idx)} className="mt-2 text-charcoal/30 hover:text-terracotta">
                    <X size={18} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button type="button" onClick={addStep} className="mt-2 text-sm text-sage font-medium flex items-center gap-1 hover:underline">
            <Plus size={14} /> {t('create.addStep')}
          </button>
        </div>

        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
          {loading ? <><Loader2 size={18} className="animate-spin" /> {t('create.publishing')}</> : t('create.publish')}
        </button>
      </form>
    </div>
  );
}
