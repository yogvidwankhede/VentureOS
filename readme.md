# VentureOS

> AI startup analysis, premium website generation, and investor-ready slide decks in one workflow.

VentureOS is an AI startup workspace that turns a single idea prompt into a structured go-to-market foundation, a premium landing page, and a polished presentation system. The app combines streamed startup analysis, premium website generation, investor-style slide creation, editable PPT export, and report sharing in one interface.

Instead of stopping at a basic summary, VentureOS is designed to take an idea from "rough concept" to "something you can review, present, and iterate on." It produces market research, competitor analysis, product strategy, a pitch outline, financial context, pivots, follow-up chat, a production-style website draft, and a premium presentation deck with controllable visual systems.

Live app: [https://ventureos-yogvid.vercel.app](https://ventureos-yogvid.vercel.app)

## What VentureOS does

VentureOS currently covers five connected workflows:

1. Startup analysis
   Streams a structured startup review across market research, competitor analysis, product strategy, pitch structure, and fundability scoring.
2. Premium website generation
   Builds a polished startup website from the analysis context using a premium landing-page prompt and multiple visual directions.
3. Premium presentation generation
   Converts the pitch and analysis into a themed slide deck with premium layouts, slide-level objectives, design notes, animation intent, and visual direction.
4. Editable PPT export
   Exports the generated deck as an editable PowerPoint instead of a flat image-only slideshow.
5. Share and iterate loop
   Saves reports, supports copy/share flows, allows follow-up chat, and lets users refresh deck visuals without rerunning the whole analysis from scratch.

## Current capability set

| Area | Capability |
|---|---|
| Analysis | Market sizing, target customer, pain points, market trends, opportunity summary |
| Competitive | Competitor landscape, whitespace analysis, strategic differentiation |
| Product | MVP scope, MoSCoW prioritization, stack suggestions, build timeline, monetization ideas |
| Pitch | 10-slide pitch outline, investor emails, domain ideas |
| Scoring | Fundability scorecard with verdict, strength, risk, and dimension breakdown |
| Website | Premium website generation with reusable sections and multiple visual themes |
| Slides | Premium themed slide deck generation with regeneration, present mode, and slide inspector |
| Visuals | Image style controls, image coverage controls, model selection, visual refresh |
| Export | Editable PPTX export, CSV export, copyable text report |
| Sharing | Shareable saved report links and reloadable analysis state |
| Iteration | Co-founder chat and pivot suggestions grounded in generated analysis |

## Product highlights

### 1. Streamed startup analysis

The main analysis flow is streamed with Server-Sent Events so users see output appear as each agent finishes instead of waiting for one large response. The core sequence is:

1. Market research
2. Competitor analysis
3. Product strategy
4. Pitch generation
5. Scorecard

The frontend renders result cards progressively as the stream arrives.

### 2. Premium website generator

The website generator is no longer documented as a generic prototype builder. It now functions as a premium startup website generator that uses the analysis context to produce:

- A clearer landing-page narrative
- Stronger section hierarchy
- Premium theme variation
- A more production-ready single-file HTML result

The generator is driven by `agents/prototype_agent.py`, but the generated output is positioned as a startup website, not a rough prototype.

### 3. Premium slide deck system

The slide workflow has been expanded well beyond the original pitch outline. VentureOS now supports:

- Premium slide themes and deck systems
- Regeneration with different visual styles
- Slide inspector with objective, layout direction, and deck palette
- Present mode
- Image style selection
- Image coverage selection
- Visual refresh without regenerating the full analysis
- Editable PPT export from the deck modal

The UI exposes slide generation directly from the results area and through persistent slide actions in the deck modal.

### 4. Image-backed decks

Decks support image-backed slides in both live and local modes.

- Production deployment uses a hosted image path for the lead deck image and then derives additional slide-specific visuals for selected slides.
- Local development can optionally use Hugging Face Diffusers models for richer image generation via `requirements-imagegen.txt`.
- Coverage modes include `Hero Only (Fast)`, `Key Slides`, `Image Heavy`, and `Every Slide`.
- Key Slides is the default balanced mode and targets roughly 4-5 image-backed slides in a deck.
- Image style options include presentation illustration, animated scene, editorial illustration, cartoon, product illustration, 3D illustration, and abstract scenic directions depending on the active generator path.

### 5. Editable PPT export

The exported deck is intended to remain editable in PowerPoint. The app uses a browser-side editable PPT builder for the main user flow, while the backend also exposes a `/download_pptx` route that can be used where `python-pptx` is available.

## Architecture overview

```text
Browser
  -> POST /analyze
  -> Flask app
  -> agents/orchestrator.py
      -> market agent
      -> competitor agent
      -> product agent
      -> pitch agent
      -> scorecard agent
  -> streamed SSE events back to the browser

Browser
  -> POST /prototype
  -> premium website HTML response

Browser
  -> POST /slides
  -> premium deck structure + themed slide data + image metadata

Browser
  -> editable PPT export flow
```

## Repository structure

```text
VentureOS/
├── app.py
├── agents/
│   ├── orchestrator.py
│   ├── market_agent.py
│   ├── competitor_agent.py
│   ├── product_agent.py
│   ├── pitch_agent.py
│   ├── scorecard_agent.py
│   ├── prototype_agent.py
│   └── pivot_agent.py
├── templates/
│   └── index.html
├── tools/
│   ├── image_generation.py
│   └── download_image_models.py
├── static/
├── requirements.txt
├── requirements-imagegen.txt
├── vercel.json
└── readme.md
```

## Backend details

### `app.py`

`app.py` is the main Flask application and currently handles:

- Main UI route
- SSE analysis streaming
- Website generation
- Co-founder chat
- Pivot generation
- Slide deck generation
- PPT download route
- Report save and report load routes
- Hosted image fallback behavior for live deck visuals
- Local image generation integration when optional dependencies are available

### `agents/orchestrator.py`

The orchestrator now uses a Gemini-first provider strategy with Groq fallback. It detects quota and rate-limit style failures, then switches providers during the same request instead of leaving the frontend hanging.

Default provider behavior:

- Preferred provider: Google Gemini (`gemini-2.5-flash-lite` by default)
- Fallback provider: Groq (`llama-3.1-8b-instant` by default)
- Retry and rate-limit handling: built in

### `agents/prototype_agent.py`

This module powers the website generator. It produces a premium landing-page style output rather than a bare prototype. The prompt and theme system are tuned for high-conversion startup website structure and stronger visual hierarchy.

### `tools/image_generation.py`

This optional local image pipeline supports multiple free/open Hugging Face image models, including:

- `SimianLuo/LCM_Dreamshaper_v7`
- `Lykon/dreamshaper-8-lcm`
- `Lykon/dreamshaper-8`
- `stable-diffusion-v1-5/stable-diffusion-v1-5`
- `segmind/tiny-sd`

It also exposes:

- style presets
- coverage options
- supported model listing
- cached slide image output under `static/generated/slide_images`

### `tools/download_image_models.py`

This helper pre-downloads the default local image models used by the slide generator for faster subsequent runs.

## Frontend details

The entire frontend lives in `templates/index.html` and includes:

- streamed analysis rendering
- results cards
- website preview modal
- slide deck modal
- present mode
- share/save actions
- PPT generation trigger
- image style and coverage controls
- visual refresh flow
- financial model UI
- co-founder chat
- history and reload behavior

Recent UI updates reflected in the current codebase include:

- visible `Generate Slides` entry points near the analysis results
- floating slide CTA button
- `Generate Website` / `Regenerate Website` website flow
- deck themes and theme switching
- image style pills
- image coverage pills
- image model selection
- `Refresh Visuals`
- `Generate PPT`

## API surface

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Main application UI |
| `POST` | `/analyze` | Streams startup analysis results over SSE |
| `POST` | `/prototype` | Generates the premium website HTML |
| `POST` | `/chat` | Co-founder follow-up chat with full context |
| `POST` | `/pivot` | Generates strategic pivots |
| `POST` | `/slides` | Generates the premium presentation deck payload |
| `POST` | `/download_pptx` | Backend PPT export route |
| `POST` | `/report/save` | Persists a report snapshot for sharing |
| `GET` | `/report/<report_id>` | Loads a saved report |

## Deployment model

VentureOS is deployed on Vercel and includes a Vercel config in `vercel.json`.

Important deployment behavior:

- The live app stays lean enough to deploy without the full local Diffusers stack.
- The production deck image path relies on a hosted lead image strategy plus derived slide visuals.
- Local environments can enable the richer optional image generator with `requirements-imagegen.txt`.
- The project also includes `render.yaml` for Render-compatible deployment setup.

Live URL:

- [https://ventureos-yogvid.vercel.app](https://ventureos-yogvid.vercel.app)

## Local setup

### Prerequisites

- Python 3.9+
- At least one LLM provider key
- Optional GPU support if you want local deck image generation

### Install

```bash
git clone https://github.com/yogvidwankhede/VentureOS.git
cd VentureOS

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Optional: local image generation models and dependencies
pip install -r requirements-imagegen.txt
```

### Environment variables

Create a `.env` file and configure the providers you want to use.

Common variables:

```bash
GOOGLE_API_KEY=...
GROQ_API_KEY=...

VENTUREOS_LLM_PROVIDER=auto
VENTUREOS_GOOGLE_MODEL=gemini-2.5-flash-lite
VENTUREOS_GROQ_MODEL=llama-3.1-8b-instant

# Optional image settings
VENTUREOS_DISABLE_IMAGEGEN=false
VENTUREOS_IMAGE_MODEL=lcm-dreamshaper-v7
VENTUREOS_IMAGE_STYLE=deck-illustration
VENTUREOS_IMAGE_COVERAGE=key-slides
```

### Run locally

```bash
python app.py
```

Open:

- [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Dependency split

### `requirements.txt`

Core runtime dependencies for the live app:

- Flask
- Gunicorn
- python-dotenv
- LangChain core packages
- Google and Groq LangChain integrations
- ChromaDB
- python-pptx

### `requirements-imagegen.txt`

Optional local slide image generation stack:

- torch
- torchvision
- torchaudio
- transformers
- accelerate
- diffusers
- huggingface-hub
- safetensors

## Notes on image generation

There are two main operating modes:

### Live deployment mode

- optimized for hosted deployment
- uses hosted lead-image generation where available
- derives additional slide visuals for selected slides
- keeps the deck generator responsive enough for the public app

### Local enhanced mode

- enabled with `requirements-imagegen.txt`
- uses free/open local Hugging Face models
- supports richer image experimentation and model switching
- trades speed for higher control

## Notes on PPT generation

The deck workflow now supports:

- premium slide structure
- themed layouts
- on-screen presentation mode
- editable PowerPoint export
- image-backed slide export

Because the app prioritizes editable export, the PowerPoint output is built to stay manipulable rather than being a pure screenshot capture of the browser UI.

## Suggested development workflow

1. Run the main analysis with a startup idea.
2. Review market, competitor, product, pitch, and scorecard output.
3. Generate the website draft.
4. Generate the premium slide deck.
5. Adjust theme, image style, coverage, or model.
6. Refresh visuals if needed.
7. Export the PPT.
8. Save/share the report.

## Roadmap direction

The codebase already points toward several obvious next expansions:

- stronger report persistence
- richer comparison workflows
- deeper RAG-backed research
- more robust hosted image generation for live decks
- additional export formats
- more advanced team and investor matching

## Author

Yogvid Wankhede  
M.S. Data Analytics and Statistics  
Washington University in St. Louis

- Portfolio: [https://yogvidwankhede.com](https://yogvidwankhede.com)
- GitHub: [https://github.com/yogvidwankhede](https://github.com/yogvidwankhede)

## License

MIT License
