import { Check, Clock, Loader2, Sparkles } from 'lucide-react';

export default function ImageRecognitionResult({
  result,
  onConfirm,
  onRegenerate,
  onEdit,
  loading = false,
}) {
  if (!result) return null;

  const ingredients = result.ingredients || [];
  const recipe = result.recipe;

  return (
    <div className="card">
      <h3 className="font-heading text-lg mb-3 flex items-center gap-2">
        <Sparkles size={18} className="text-terracotta" />
        {'\u8bc6\u522b\u7ed3\u679c'}
      </h3>

      {result.message && (
        <p className="mb-3 text-sm text-charcoal/60">{result.message}</p>
      )}

      {recipe && (
        <div className="mb-5 rounded-xl bg-cream p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h4 className="font-heading text-xl">{recipe.title}</h4>
              {recipe.description && (
                <p className="mt-1 text-sm text-charcoal/60">{recipe.description}</p>
              )}
            </div>
            <div className="flex items-center gap-1 text-sm text-charcoal/50">
              <Clock size={14} />
              {recipe.cook_time_minutes || 30} {'\u5206\u949f'}
            </div>
          </div>

          {recipe.steps?.length > 0 && (
            <ol className="mt-4 space-y-2">
              {recipe.steps.map((step, idx) => (
                <li key={idx} className="flex gap-3 text-sm">
                  <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-sage/20 text-xs font-bold text-sage">
                    {idx + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {ingredients.length > 0 ? (
        <>
          <div className="flex flex-wrap gap-2 mb-4">
            {ingredients.map((ing, idx) => (
              <span key={idx} className="chip">
                {ing}
              </span>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={onConfirm}
              disabled={loading}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Check size={16} />
              )}
              {'\u751f\u6210\u83dc\u8c31'}
            </button>
            <button
              onClick={onEdit}
              className="btn-secondary"
            >
              {'\u7f16\u8f91'}
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-4 text-charcoal/50">
          {result.message || '\u672a\u80fd\u8bc6\u522b\u51fa\u98df\u6750\uff0c\u8bf7\u91cd\u8bd5\u6216\u624b\u52a8\u8f93\u5165'}
        </div>
      )}
    </div>
  );
}
