import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../api';
import { useLanguage } from '../context/LanguageContext';
import IngredientInput from '../components/IngredientInput';
import ChatBubble from '../components/ChatBubble';
import AffiliateLinks from '../components/AffiliateLinks';
import { Sparkles, Send, ChefHat, Clock, Save, Loader2, Camera } from 'lucide-react';

function stripRecipeBlocks(text) {
  if (!text) return '';

  const cleaned = text
    .replace(/```(?:recipe|json)\s*[\r\n]+[\s\S]*?```/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  return cleaned;
}

export default function AIChef() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, language } = useLanguage();
  const [ingredients, setIngredients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [generating, setGenerating] = useState(false);
  const [chatting, setChatting] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const chatEndRef = useRef(null);
  const ingredientInputRef = useRef(null);

  useEffect(() => {
    if (location.state?.ingredients) {
      setIngredients(location.state.ingredients);
    }
  }, [location.state]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleGenerate = async () => {
    console.log('handleGenerate called');
    const currentInput = ingredientInputRef.current?.getValue() || '';
    console.log('currentInput:', currentInput);
    const toAdd = currentInput.trim() ? [currentInput.trim()] : [];    
    const allIngredients = [...ingredients, ...toAdd.filter(i => !ingredients.includes(i))];
    
    console.log('allIngredients:', allIngredients);
    
    if (allIngredients.length === 0) {
      console.log('No ingredients, returning');
      return;
    }
    
    if (currentInput.trim()) {
      ingredientInputRef.current?.addCurrent();
    }
    
    setGenerating(true);
    setRecipes([]);
    setChatMessages([]);
    setSelectedRecipe(null);
    try {
      console.log('Calling /ai/generate with ingredients:', allIngredients);
      const res = await api.post('/ai/generate', { ingredients: allIngredients, language });
      console.log('Response:', res.data);
      setRecipes(res.data.recipes);
      setSessionId(res.data.session_id);
      if (res.data.recipes.length > 0) {
        setSelectedRecipe(res.data.recipes[0]);
      }
    } catch (err) {
      console.error('Generate error:', err);
      alert(err.response?.data?.detail || t('ai.generateFailed'));
    } finally {
      setGenerating(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || !sessionId) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setChatting(true);
    try {
      const res = await api.post(`/ai/chat/${sessionId}`, { message: msg });
      const prettyReply = stripRecipeBlocks(res.data.reply) || t('ai.recipeUpdated');
      setChatMessages((prev) => [...prev, { role: 'assistant', content: prettyReply }]);
      if (res.data.updated_recipe) {
        setSelectedRecipe(res.data.updated_recipe);
      }
    } catch {
      setChatMessages((prev) => [...prev, { role: 'assistant', content: t('ai.chatError') }]);
    } finally {
      setChatting(false);
    }
  };

  const handleSaveRecipe = async (recipe) => {
    try {
      await api.post('/recipes', {
        title: recipe.title,
        description: recipe.description,
        ingredients: recipe.ingredients,
        steps: recipe.steps,
        cook_time_minutes: recipe.cook_time_minutes,
        image_url: recipe.image_url || '',
      });
      alert(t('ai.recipeSaved'));
    } catch {
      alert(t('ai.saveFailed'));
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="font-heading text-4xl flex items-center justify-center gap-2">
          <Sparkles className="text-terracotta" size={32} />
          {t('ai.title')}
        </h1>
        <p className="text-charcoal/60 mt-1">{t('ai.subtitle')}</p>
      </div>

      {/* Ingredient Input */}
      <div className="card mb-6">
        <h2 className="font-heading text-xl mb-3">{t('ai.yourIngredients')}</h2>
        <IngredientInput ref={ingredientInputRef} ingredients={ingredients} onChange={setIngredients} />
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="btn-primary mt-4 flex items-center gap-2"
        >
          {generating ? (
            <><Loader2 size={18} className="animate-spin" /> {t('ai.generating')}</>
          ) : (
            <><Sparkles size={18} /> {t('ai.generateRecipes')}</>
          )}
        </button>
        
        <button
          onClick={() => navigate('/image')}
          disabled={generating}
          className="btn-secondary mt-2 flex items-center justify-center gap-2 w-full"
        >
          <Camera size={16} />
          通过图片识别食材
        </button>
      </div>

      {/* Generated Recipes */}
      {recipes.length > 0 && (
        <div className="space-y-4 mb-6">
          <h2 className="font-heading text-2xl">{t('ai.suggestedRecipes')}</h2>
          <div className="grid gap-4">
            {recipes.map((recipe, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedRecipe(recipe)}
                className={`card cursor-pointer border-2 transition-colors ${
                  selectedRecipe === recipe ? 'border-terracotta' : 'border-transparent'
                }`}
              >
                {recipe.image_url ? (
                  <img
                    src={recipe.image_url}
                    alt={recipe.title}
                    className="w-full h-44 object-cover rounded-xl mb-3"
                  />
                ) : null}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-heading text-xl">{recipe.title}</h3>
                    <p className="text-sm text-charcoal/60 mt-1">{recipe.description}</p>
                    <div className="flex items-center gap-2 mt-2 text-sm text-charcoal/50">
                      <Clock size={14} />
                      {recipe.cook_time_minutes} {t('ai.min')}
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleSaveRecipe(recipe); }}
                    className="p-2 rounded-lg hover:bg-sage/10 text-sage transition-colors"
                    title={t('ai.saveRecipe')}
                  >
                    <Save size={20} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Recipe Detail */}
      {selectedRecipe && (
        <div className="card mb-6">
          {selectedRecipe.image_url ? (
            <img
              src={selectedRecipe.image_url}
              alt={selectedRecipe.title}
              className="w-full h-56 object-cover rounded-xl mb-4"
            />
          ) : null}
          <h2 className="font-heading text-2xl mb-4">{selectedRecipe.title}</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-sm uppercase text-charcoal/50 mb-2">{t('ai.ingredients')}</h3>
              <ul className="space-y-1">
                {selectedRecipe.ingredients.map((ing, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-terracotta mt-1.5 flex-shrink-0" />
                    {ing}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-sm uppercase text-charcoal/50 mb-2">{t('ai.steps')}</h3>
              <ol className="space-y-2">
                {selectedRecipe.steps.map((step, i) => (
                  <li key={i} className="flex gap-3 text-sm">
                    <span className="w-6 h-6 rounded-full bg-sage/20 text-sage flex items-center justify-center flex-shrink-0 text-xs font-bold">
                      {i + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div className="mt-6">
            <AffiliateLinks ingredients={selectedRecipe.ingredients} userIngredients={ingredients} />
          </div>
        </div>
      )}

      {/* Chat with AI */}
      {sessionId && (
        <div className="card">
          <h2 className="font-heading text-xl mb-4 flex items-center gap-2">
            <ChefHat size={20} className="text-terracotta" />
            {t('ai.chatTitle')}
          </h2>
          <p className="text-sm text-charcoal/50 mb-4">
            {t('ai.chatHint')}
          </p>

          {chatMessages.length > 0 && (
            <div className="space-y-3 max-h-80 overflow-y-auto mb-4 p-2">
              {chatMessages.map((msg, i) => (
                <ChatBubble key={i} role={msg.role} content={msg.content} />
              ))}
              <div ref={chatEndRef} />
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              placeholder={t('ai.chatPlaceholder')}
              className="input-field flex-1"
            />
            <button
              onClick={handleChat}
              disabled={chatting || !chatInput.trim()}
              className="btn-primary px-4"
            >
              {chatting ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
