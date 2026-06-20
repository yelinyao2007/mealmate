import { Link } from 'react-router-dom';
import { Heart, MessageCircle, Clock, ChefHat } from 'lucide-react';

export default function RecipeCard({ recipe }) {
  return (
    <Link to={`/recipes/${recipe.id}`} className="card block group">
      {recipe.image_url ? (
        <img
          src={recipe.image_url}
          alt={recipe.title}
          className="w-full h-44 object-cover rounded-xl mb-3"
        />
      ) : (
        <div className="w-full h-44 bg-gradient-to-br from-gold/20 to-sage/20 rounded-xl mb-3 flex items-center justify-center">
          <ChefHat size={48} className="text-terracotta/30" />
        </div>
      )}
      <h3 className="font-heading text-xl text-charcoal group-hover:text-terracotta transition-colors line-clamp-2">
        {recipe.title}
      </h3>
      {recipe.description && (
        <p className="text-sm text-charcoal/60 mt-1 line-clamp-2">{recipe.description}</p>
      )}
      <div className="flex items-center justify-between mt-3 text-sm text-charcoal/50">
        <span className="font-medium text-sage">{recipe.author_name || 'Anonymous'}</span>
        <div className="flex items-center gap-3">
          {recipe.cook_time_minutes > 0 && (
            <span className="flex items-center gap-1">
              <Clock size={14} /> {recipe.cook_time_minutes}m
            </span>
          )}
          <span className="flex items-center gap-1">
            <Heart size={14} className={recipe.is_liked ? 'fill-terracotta text-terracotta' : ''} />
            {recipe.likes_count}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle size={14} /> {recipe.comment_count}
          </span>
        </div>
      </div>
    </Link>
  );
}
