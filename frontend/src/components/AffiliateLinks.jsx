import { useLanguage } from '../context/LanguageContext';
import { ShoppingCart, ExternalLink, Copy, Check } from 'lucide-react';
import { useState } from 'react';

const COMMON_INGREDIENTS = [
  '盐', 'salt', '少许盐', '适量盐', '盐少许',
  '油', 'oil', '食用油', '油适量', '食用油适量',
  '清水', '水', 'water', '白开水',
  '鸡蛋', 'egg', '鸡蛋个',
  '葱', '葱段', 'shallot',
  '姜', '生姜', '姜片', 'ginger',
  '蒜', '大蒜', 'garlic',
  '味精', '鸡精', 'MSG',
];

function extractBaseIngredient(ing) {
  // Extract base ingredient name by removing quantities/units: "意大利面200克" -> "意大利面"
  return ing.toLowerCase().replace(/\d+[a-zA-Z克个勺杯毫升ml市斤两]/gi, '').trim();
}

export default function AffiliateLinks({ ingredients, userIngredients = [] }) {
  const { t, language } = useLanguage();
  const [copied, setCopied] = useState(false);
  const [userInput, setUserInput] = useState(userIngredients.join(', '));

  // Parse user input into base ingredients (去除数量后的基础食材名)
  const userItems = userInput.split(',')
    .map(i => extractBaseIngredient(i))
    .filter(Boolean);
  
  // Filter out recipe ingredients that user already has
  const missingIngredients = ingredients.filter(recipeIng => {
    const baseIng = extractBaseIngredient(recipeIng);
    // Check if any user ingredient is contained in recipe ingredient
    return !userItems.some(ui => baseIng.includes(ui) || ui.includes(baseIng));
  });

  const query = encodeURIComponent(missingIngredients.join(', '));
  const ingredientText = missingIngredients.join(', ');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(ingredientText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="card bg-gold/10 border border-gold/20">
      <h4 className="font-heading text-lg flex items-center gap-2 mb-3">
        <ShoppingCart size={20} className="text-terracotta" />
        {t('affiliate.title')}
      </h4>
      <div className="mb-3">
        <label className="text-sm text-charcoal/60 mb-1 block">
          {language === 'zh' ? '我有的食材（用逗号分隔）' : 'My ingredients (comma separated)'}
        </label>
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder={language === 'zh' ? '例如：鸡蛋，牛奶，面粉...' : 'e.g. eggs, milk, flour...'}
          className="w-full px-3 py-2 text-sm border border-gold/30 rounded-lg bg-white"
        />
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        <a
          href={`https://qianwen.example.com/search/${query}`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-outline text-sm py-2 px-4 flex items-center gap-1"
        >
          千问 <ExternalLink size={14} />
        </a>
        <a
          href={`https://yuanbao.example.com/search?k=${query}&i=yuanbao`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-outline text-sm py-2 px-4 flex items-center gap-1"
        >
          元宝 <ExternalLink size={14} />
        </a>
      </div>
      <div className="mt-3">
        <label className="text-sm text-charcoal/60 mb-1 block">
          {t('affiliate.copyLabel') || (language === 'zh' ? '缺少的食材（点击复制）' : 'Missing ingredients (click to copy)')}
        </label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            readOnly
            value={ingredientText}
            className="flex-1 px-3 py-2 text-sm border border-gold/30 rounded-lg bg-white"
            onClick={handleCopy}
          />
          <button
            onClick={handleCopy}
            className="p-2 text-terracotta hover:bg-terracotta/10 rounded-lg transition-colors"
            title={language === 'zh' ? '点击复制' : 'Click to copy'}
          >
            {copied ? <Check size={18} /> : <Copy size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
