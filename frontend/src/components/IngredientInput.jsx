import { useState, forwardRef, useImperativeHandle, useRef } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { X, Plus } from 'lucide-react';

const IngredientInput = forwardRef(({ ingredients, onChange }, ref) => {
  const { t } = useLanguage();
  const [input, setInput] = useState('');
  const inputElRef = useRef(null);

  const addIngredient = (val = null) => {
    const trimmed = (val !== null ? val : input).trim();
    if (trimmed && !ingredients.includes(trimmed)) {
      onChange([...ingredients, trimmed]);
      setInput('');
    }
  };

  useImperativeHandle(ref, () => ({
    addCurrent: () => {
      addIngredient(input);
      inputElRef.current?.blur();
    },
    getValue: () => input,
  }));

  const removeIngredient = (item) => {
    onChange(ingredients.filter((i) => i !== item));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addIngredient();
    }
  };

  return (
    <div>
      <div className="flex gap-2">
        <input
          ref={inputElRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('ingredientInput.placeholder')}
          className="input-field flex-1"
        />
        <button
          type="button"
          onClick={addIngredient}
          className="btn-primary flex items-center gap-1 px-4"
        >
          <Plus size={16} /> {t('ingredientInput.add')}
        </button>
      </div>
      {ingredients.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {ingredients.map((item) => (
            <span key={item} className="chip">
              {item}
              <button onClick={() => removeIngredient(item)} className="hover:text-terracotta">
                <X size={14} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
});

export default IngredientInput;