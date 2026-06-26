import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import api from '../api';
import { ChefHat, Send, Clock, Flame, Apple, Brain, Heart, User, Sparkles, Loader2 } from 'lucide-react';

const GOAL_ICONS = {
  lose_fat: Flame,
  gain_muscle: Apple,
  sugar_control: Brain,
  general: Heart,
};

export default function SmartCook() {
  const { t } = useLanguage();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [result]);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await api.post('/smart-chef/generate', { user_input: text });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const StepBadge = ({ step }) => (
    <div className="flex items-center gap-1.5 text-xs text-sage/80">
      <div className="w-2 h-2 rounded-full bg-sage animate-pulse" />
      {step.action}
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-terracotta/10 text-terracotta text-xs font-medium mb-4">
          <Sparkles size={14} /> Multi-Agent Smart Cooking
        </div>
        <h1 className="font-heading text-3xl text-charcoal mb-2">Tell me your story</h1>
        <p className="text-sm text-charcoal/50">
          Describe your situation, mood, and what's in your fridge — the AI will craft a personalized recipe just for you.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. I'm on a sugar-control diet, worked late and feeling exhausted. I only have tomatoes and eggs in the fridge. Can you make me something warm and comforting?"
            className="input-field w-full min-h-[100px] pr-12 resize-none"
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute bottom-3 right-3 w-10 h-10 rounded-full bg-terracotta text-white flex items-center justify-center disabled:opacity-40 hover:bg-terracotta/90 transition-colors"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
        <div className="flex gap-2 mt-3">
          {[
            'I want to lose weight, my fridge has chicken and broccoli',
            'Working late, need something quick, I have eggs and noodles',
            'Sugar control, I have tomatoes and tofu, want something warm',
          ].map((hint, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setInput(hint)}
              disabled={loading}
              className="text-xs px-2 py-1 rounded-full bg-cream border border-gold/30 text-charcoal/50 hover:border-gold/50 hover:text-charcoal transition-colors text-left line-clamp-2"
            >
              {hint}
            </button>
          ))}
        </div>
      </form>

      {error && (
        <div className="bg-terracotta/10 border border-terracotta/30 rounded-xl p-4 text-sm text-terracotta mb-6">{error}</div>
      )}

      {loading && (
        <div className="text-center py-12">
          <Loader2 size={32} className="animate-spin text-terracotta mx-auto mb-3" />
          <p className="text-sm text-charcoal/60">Agents collaborating...</p>
          <div className="flex justify-center gap-4 mt-4">
            {['ProfileAgent', 'NutritionAnalyzer', 'SmartChefAgent'].map((name, i) => (
              <div key={name} className="flex items-center gap-1.5 text-xs text-charcoal/40">
                <div className="w-1.5 h-1.5 rounded-full bg-sage" style={{ animationDelay: `${i * 0.3}s` }} />
                {name}
              </div>
            ))}
          </div>
        </div>
      )}

      {result && result.success && result.data && (
        <div className="space-y-6">
          {/* Steps visualization */}
          {result.steps && result.steps.length > 0 && (
            <div className="flex items-center gap-4 text-xs text-charcoal/40 border-b border-gold/20 pb-4">
              {result.steps.map((s, i) => (
                <StepBadge key={i} step={s} />
              ))}
            </div>
          )}

          {/* Chef Chat */}
          {result.data.chef_chat && (
            <div className="bg-white/60 rounded-xl p-4 flex gap-3">
              <div className="w-10 h-10 rounded-full bg-terracotta/10 flex items-center justify-center flex-shrink-0">
                <ChefHat size={20} className="text-terracotta" />
              </div>
              <div>
                <p className="text-xs text-charcoal/40 mb-1">AI Chef</p>
                <p className="text-sm text-charcoal leading-relaxed">{result.data.chef_chat}</p>
              </div>
            </div>
          )}

          {/* User Intent */}
          {result.data.user_intent && (
            <div className="flex flex-wrap gap-2">
              {result.data.user_intent.goal && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-medium">
                  <Brain size={12} /> {result.data.user_intent.goal}
                </span>
              )}
              {result.data.user_intent.mood && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                  {result.data.user_intent.mood}
                </span>
              )}
              {result.data.user_intent.ingredients && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                  {result.data.user_intent.ingredients.join(', ')}
                </span>
              )}
            </div>
          )}

          {/* Profile Check */}
          {result.data.profile_check && (
            <div className="bg-sage/5 border border-sage/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <User size={16} className="text-sage" />
                <span className="text-sm font-semibold text-sage">Profile Check</span>
              </div>
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-charcoal/40">BMI</span>
                  <p className="font-semibold text-charcoal">{result.data.profile_check.bmi || '—'}</p>
                </div>
                <div>
                  <span className="text-charcoal/40">Goal</span>
                  <p className="font-semibold text-charcoal">{result.data.profile_check.goal || '—'}</p>
                </div>
                <div>
                  <span className="text-charcoal/40">Cal/Meal</span>
                  <p className="font-semibold text-charcoal">{result.data.profile_check.calorie_budget_per_meal || '—'} kcal</p>
                </div>
              </div>
              {result.data.profile_check.health_alerts && result.data.profile_check.health_alerts.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {result.data.profile_check.health_alerts.map((a, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-terracotta/10 text-terracotta text-xs">{a}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Recipe Card */}
          {result.data.recipe && (
            <div className="bg-white rounded-2xl shadow-sm border border-gold/20 overflow-hidden">
              <div className="bg-terracotta/5 px-5 py-4 flex items-center justify-between">
                <div>
                  <h3 className="font-heading text-lg text-charcoal">{result.data.recipe.title}</h3>
                  <p className="text-xs text-charcoal/40 mt-0.5">{result.data.recipe.description}</p>
                </div>
                {result.data.recipe.vibe && (
                  <span className="text-xs px-2 py-1 rounded-full bg-terracotta/10 text-terracotta">{result.data.recipe.vibe}</span>
                )}
              </div>
              <div className="px-5 py-4 space-y-4">
                <div className="flex gap-4 text-xs text-charcoal/50">
                  {result.data.recipe.time_minutes && (
                    <span className="flex items-center gap-1"><Clock size={14} /> {result.data.recipe.time_minutes}min</span>
                  )}
                  {result.data.recipe.difficulty && (
                    <span className="flex items-center gap-1"><Flame size={14} /> {result.data.recipe.difficulty}</span>
                  )}
                  {result.data.recipe.calories_estimate && (
                    <span className="flex items-center gap-1"><Apple size={14} /> {result.data.recipe.calories_estimate}kcal</span>
                  )}
                  {result.data.recipe.gi_level && (
                    <span className="flex items-center gap-1"><Brain size={14} /> {result.data.recipe.gi_level}</span>
                  )}
                </div>

                {result.data.recipe.nutrition && (
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(result.data.recipe.nutrition).map(([k, v]) => (
                      <div key={k} className="bg-cream rounded-lg px-2 py-1.5 text-center">
                        <p className="text-lg font-bold text-charcoal">{v}</p>
                        <p className="text-[10px] text-charcoal/40">{k.replace('_g', '')}</p>
                      </div>
                    ))}
                  </div>
                )}

                {result.data.recipe.ingredients && (
                  <div>
                    <p className="text-xs font-semibold text-charcoal/60 mb-2">Ingredients</p>
                    <ul className="text-xs text-charcoal/70 space-y-1">
                      {result.data.recipe.ingredients.map((ing, i) => <li key={i}>• {ing}</li>)}
                    </ul>
                  </div>
                )}

                {result.data.recipe.steps && (
                  <div>
                    <p className="text-xs font-semibold text-charcoal/60 mb-2">Steps</p>
                    <ol className="text-xs text-charcoal/70 space-y-1.5">
                      {result.data.recipe.steps.map((step, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-terracotta font-bold min-w-[1.2em]">{i + 1}.</span>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {result.data.recipe.tips && (
                  <div className="bg-gold/5 border border-gold/20 rounded-lg px-3 py-2 text-xs text-charcoal/70 flex items-start gap-2">
                    <ChefHat size={14} className="text-gold mt-0.5 flex-shrink-0" />
                    {result.data.recipe.tips}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Health Notes */}
          {result.data.health_notes && (
            <div className="bg-sage/5 rounded-xl p-4 text-xs text-charcoal/60 flex items-start gap-2">
              <Heart size={14} className="text-sage mt-0.5 flex-shrink-0" />
              {result.data.health_notes}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
