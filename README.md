# Digital Wardrobe-AI-Powered Outfit Builder

Welcome to **Digital Wardrobe**, an AI-enhanced clothing management app that lets you upload photos of your clothes, clean them up automatically, and store them in a personalized digital wardrobe.  
Using CLIP auto-tagging, AI outfit recommendations, and a mannequin preview mode, the app helps you organize your closet and generate fits instantly.

This project uses:

- React + TypeScript (frontend)  
- Python FastAPI (backend)  
- PostgreSQL (database)  
- CLIP (auto-labeling clothing)  
- Rembg / segmentation (background and hanger removal)

---

## Features

### Upload Clothing Items

Upload pictures of your clothes straight from your device.  
The backend automatically:

- Removes background  
- Crops and centers the item  
- Places it on a clean canvas

### AI Auto-Tagging with CLIP

Each uploaded item is passed through OpenAI’s CLIP to generate useful tags based on:

- Color  
- Style  
- Type (t-shirt, hoodie, jeans, etc.)  
- Season (summer, winter)  
- Material (cotton, denim, etc.)  
- Aesthetic keywords  

Tags are stored in PostgreSQL and used for filtering and outfit generation.

### AI Outfit Recommendations

Using your wardrobe data and CLIP tags, an LLM can generate fit ideas you can ask for in natural language, such as:

- “Give me a cozy fall fit.”  
- “Build an outfit with my red shirt and black jeans.”  
- “Recommend a summer outfit for hot weather.”  

### Mannequin Fit Preview

Includes a 2D mannequin viewer where you can:

- Select clothing items  
- Layer them visually on a male or female mannequin  
- Prototype outfits quickly  

(3D try-on coming later.)

---

## Project Structure

```text
clothingappv1/
 ├── backend/
 │    ├── app/
 │    │    ├── main.py
 │    │    ├── models.py
 │    │    ├── crud.py
 │    │    ├── database.py
 │    │    ├── segmentation.py
 │    │    ├── clip_tagger.py
 │    │    └── ...
 │    ├── uploads/
 │    └── requirements.txt
 ├── frontend/
 │    ├── src/
 │    ├── index.html
 │    └── ...
 ├── scripts/
 │    ├── setup_backend.bat
 │    ├── run_backend.bat
 │    ├── setup_frontend.bat
 │    └── run_frontend.bat
 └── README.md
```
## Requirements
Before running the app, install:
- Python 3.10+
- Node.js 18+
- PostgreSQL

Make sure PostgreSQL is running.

# Running the App
## 1. Setup Backend
From the project root:

```bash
scripts/setup_backend.bat
```
This will:
Create a virtual environment
Install dependencies
Prepare backend structure

## 2. Setup Frontend
```bash
scripts/setup_frontend.bat
```
## 3. Run Backend
```bash
scripts/run_backend.bat
```
Backend will start at:

```text
http://localhost:8000
```
## 4. Run Frontend
```bash
scripts/run_frontend.bat
```
Frontend will start at:

```text
http://localhost:5173
```
Now open your browser to use the Digital Wardrobe.

## Example Queries (for the AI Outfit Generator)
You can ask:
- “Give me five outfit ideas for cold weather.”
- “Use my white hoodie and blue jeans to make a streetwear fit.”
- “Pick a minimalistic summer outfit for vacation.”
- “Find a fall aesthetic outfit using brown or neutral tones.”

## Roadmap
- 3D mannequin try-on
- Realistic cloth simulation
- User accounts and cloud storage
- Outfit sharing
- Seasonal capsule wardrobe generator
- Mobile app (React Native)
