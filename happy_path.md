# MealMate – Happy Path Testing Guide

## Prerequisites

```powershell
# From the project root, start the server:
python run.py
# → Server runs at http://127.0.0.1:8000
```

> **Note:** You need a valid `OPENAI_API_KEY` in a `.env` file (copy from `.env.example`)
> for the AI Chef feature. All other features work without it.

---

## Flow 1: Registration & Profile Setup

1. Open **http://127.0.0.1:8000** in your browser
2. Click **"Get Started Free"** on the landing page
3. Fill in:
   - Name: `Alice`
   - Email: `alice@example.com`
   - Password: `password123`
4. Click **"Create Account"** → redirected to **Profile** page
5. On Profile page:
   - Set skill level to **intermediate**
   - Select dietary: **Vegetarian**
   - Select allergies: **Peanuts**
   - Select cuisines: **Italian**, **Japanese**
6. Click **"Save Profile"** → see "Profile saved!" alert

**Expected:** User is created, preferences are stored, navbar shows authenticated links.

---

## Flow 2: AI Recipe Generation & Chat

1. Click **"AI Chef"** in the navbar
2. Add ingredients one by one:
   - Type `tomatoes` → press Enter
   - Type `pasta` → press Enter
   - Type `garlic` → press Enter
   - Type `olive oil` → press Enter
   - Type `basil` → press Enter
3. Click **"✨ Generate Recipes"**
4. Wait for AI to return 2–3 recipe suggestions
5. Click on a recipe card to see full ingredients & steps
6. In the **"Chat with AI Chef"** section, type:
   - `Make it spicier and add some cheese`
   - Press **Send**
7. AI responds with a modified version
8. Click the **💾** icon on any recipe to save it to your collection

**Expected:** Recipes generated matching ingredients + user preferences, chat modifies recipes in real-time, saved recipe appears in feed.

---

## Flow 3: Create & Publish a Recipe Manually

1. Click **"Create"** in the navbar
2. Fill in:
   - Title: `My Simple Bruschetta`
   - Description: `Classic Italian appetizer with fresh tomatoes`
   - Cook Time: `15`
3. Add ingredients: `bread`, `tomatoes`, `garlic`, `basil`, `olive oil`
4. Add steps:
   - Step 1: `Dice tomatoes and mix with chopped garlic and basil`
   - Step 2: `Drizzle with olive oil, add salt and pepper`
   - Step 3: `Toast bread slices until golden`
   - Step 4: `Top bread with tomato mixture and serve`
5. Click **"Publish Recipe"**

**Expected:** Redirected to the recipe detail page showing the full recipe.

---

## Flow 4: Browse Feed, Like, Comment, Bookmark

1. Click **"Feed"** in the navbar
2. See the recipe(s) you created/saved
3. Click on a recipe card → opens recipe detail
4. Click **🤍** to **like** the recipe → icon changes to ❤️, count increases
5. Click **📑 Save** to **bookmark** it → changes to 🔖 Saved
6. Scroll to comments section:
   - Type: `Looks delicious! Will try tonight`
   - Click **Send**
7. Comment appears at the top of the list

**Expected:** Like count updates, bookmark toggles, comment is posted with your name.

---

## Flow 5: Remix a Recipe

1. On any recipe detail page, click **"🔀 Remix"**
2. The Create Recipe form opens pre-filled with the original recipe data
3. Modify:
   - Change title to `Bruschetta with Mozzarella (Remix)`
   - Add ingredient: `mozzarella`
   - Add step: `Add fresh mozzarella slices on top`
4. Click **"Publish Recipe"**
5. Go to the **original** recipe page → see the remix listed under "Remixes"

**Expected:** Remix is linked to the original; original shows remix count.

---

## Flow 6: Bookmarks Page

1. Click **"Saved"** in the navbar
2. See all bookmarked recipes
3. Click on any to view the detail

**Expected:** All previously bookmarked recipes appear in a grid.

---

## Flow 7: Notifications

1. (Requires a second user) Register a second account in an incognito window:
   - Email: `bob@example.com`, Name: `Bob`
2. As Bob, go to Feed → click on Alice's recipe → like it and add a comment
3. Switch back to Alice's browser → click **"Alerts"**
4. See notifications:
   - "Bob liked your recipe 'My Simple Bruschetta'"
   - "Bob commented on your recipe 'My Simple Bruschetta'"
5. Click **"✓ Mark all read"** to clear

**Expected:** Notifications generated for likes, comments, and remixes on your recipes.

---

## Flow 8: Affiliate / Buy Ingredients

1. Open any recipe detail page
2. Scroll to **"🛒 Buy Missing Ingredients"**
  3. Click **"千问 ↗"** → opens Qianwen search with recipe ingredients
  4. Click **"元宝 ↗"** → opens Yuanbao search

**Expected:** External links open correctly with ingredient search query.

---

## Flow 9: Feed Sorting

1. Go to **Feed** page
2. Use the dropdown to switch between **Newest** and **Popular**
3. Verify recipes reorder based on selection

**Expected:** "Newest" sorts by date descending, "Popular" sorts by likes descending.

---

## Quick API Smoke Test (PowerShell)

```powershell
# Register
$reg = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/auth/register -Method POST -ContentType "application/json" -Body '{"email":"test@test.com","password":"test123","name":"Tester"}'
$token = $reg.access_token

# Get profile
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/auth/me -Headers $headers

# Create recipe
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/recipes -Method POST -ContentType "application/json" -Headers $headers -Body '{"title":"Test Recipe","ingredients":["egg","cheese"],"steps":["Scramble eggs","Add cheese"],"cook_time_minutes":10}'

# Get feed
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/recipes/feed
```

---

## Summary Checklist

| #  | Flow                     | Status |
|----|--------------------------|--------|
| 1  | Register & Profile       | ☐      |
| 2  | AI Recipe Generation     | ☐      |
| 3  | Create Recipe Manually   | ☐      |
| 4  | Like, Comment, Bookmark  | ☐      |
| 5  | Remix Recipe             | ☐      |
| 6  | Bookmarks Page           | ☐      |
| 7  | Notifications            | ☐      |
| 8  | Affiliate Links          | ☐      |
| 9  | Feed Sorting             | ☐      |
