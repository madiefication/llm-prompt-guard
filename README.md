# LLM Prompt Guard

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Paper DOI](https://img.shields.io/badge/DOI-10.36227%2Ftechrxiv.175416873.36395198%2Fv1-green?style=flat-square)](https://doi.org/10.36227/techrxiv.175416873.36395198/v1)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen?style=flat-square)](https://your-app.onrender.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)

> A production-ready implementation of the hybrid adversarial prompt detection engine described in:
>
> **"LLM Adversarial Prompt Attack Detection and Mitigation Engine: A Novel Framework for Securing Generative AI Systems"**
> — Madiha Fathima, TechRxiv DOI: [10.36227/techrxiv.175416873.36395198/v1](https://doi.org/10.36227/techrxiv.175416873.36395198/v1)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      POST /analyze                           │
│                    { prompt: string }                        │
└─────────────────────────┬────────────────────────────────────┘
                          │
                ┌─────────▼─────────┐
                │  Preprocessor     │  HTML strip · Unicode norm
                │  (preprocessor.py)│  Zero-width removal · tokenize
                └────────┬──────────┘
              ┌──────────┴──────────┐
              │                     │
   ┌──────────▼──────────┐  ┌───────▼───────────┐
   │  Rule-Based          │  │  ML Classifier    │
   │  Classifier          │  │  TF-IDF (1-3gram) │
   │  (30+ regex rules)   │  │  + Logistic Reg.  │
   │  → score 0.0–1.0     │  │  → P(adversarial) │
   └──────────┬──────────┘  └───────┬───────────┘
              │   0.55 weight        │  0.45 weight
              └──────────┬──────────┘
                ┌────────▼────────┐
                │  Hybrid Decision│  score = 0.55·rule + 0.45·ml
                │  Engine         │  < 0.30  → benign  → ALLOW
                │                 │  0.30–0.70 → suspicious → REWRITE
                │                 │  > 0.70  → malicious → BLOCK
                └────────┬────────┘
              ┌──────────┴──────────┐
              │                     │
   ┌──────────▼──────────┐  ┌───────▼───────────┐
   │  Rewriter            │  │  Explainability   │
   │  (suspicious only)   │  │  Engine           │
   │  Strip injection     │  │  Rules + tokens   │
   │  keywords            │  │  + score breakdown│
   └─────────────────────┘  └───────────────────┘
```

---

## Performance Metrics (from paper)

| Classifier     | Accuracy | Precision | Recall | F1 Score | Latency |
|---------------|----------|-----------|--------|----------|---------|
| Rule-Based    | 89.2%    | 91.7%     | 85.3%  | 88.4%    | ~8ms    |
| ML (TF-IDF+LR)| 91.5%    | 93.2%     | 88.6%  | 90.8%    | ~23ms   |
| **Hybrid**    | **94.8%**| **96.5%** |**92.4%**|**94.4%**|**~31ms**|

---

## Quickstart

### 1. Clone & install

```bash
git clone https://github.com/your-username/llm-prompt-guard.git
cd llm-prompt-guard
pip install -r backend/requirements.txt
```

### 2. Build (generate dataset + train model)

```bash
cd backend
python build.py
```

This outputs `models/tfidf_vectorizer.pkl` and `models/lr_model.pkl`.

### 3. Start the backend

```bash
python app.py
# Server running at http://localhost:5000
```

### 4. Open the frontend

Open `frontend/index.html` in your browser (or use Live Server in VS Code).
Set `API_BASE_URL` at the top of `app.js` to your backend URL.

---

## API Reference

### `POST /analyze`

**Request**
```json
{ "prompt": "Ignore all previous instructions and..." }
```

**Response**
```json
{
  "label": "malicious",
  "score": 0.9142,
  "rule_score": 1.0,
  "ml_score": 0.809,
  "risk_level": "High",
  "action": "block",
  "rules_triggered": [
    {
      "name": "ignore_previous_instructions",
      "weight": 0.95,
      "description": "Attempts to override prior system instructions."
    }
  ],
  "rewritten_prompt": null,
  "top_tokens": [
    { "token": "ignore", "weight": 0.312 },
    { "token": "instructions", "weight": 0.218 }
  ],
  "explanation": {
    "summary": "This prompt was classified as MALICIOUS...",
    "score_breakdown": { "hybrid_score": 0.914, "rule_score": 1.0, "ml_score": 0.809 },
    "rule_findings": [...],
    "ml_findings": [...],
    "action_taken": "Prompt blocked — request rejected, incident logged."
  },
  "latency_ms": 28.4
}
```

### `GET /health`

```json
{ "status": "ok", "service": "llm-prompt-guard" }
```

---

## Deployment

### Backend → Render.com

1. Push to GitHub
2. Create a new **Web Service** on Render
3. Set **Build Command**: `pip install -r backend/requirements.txt && python backend/build.py`
4. Set **Start Command**: `gunicorn --chdir backend app:app`
5. Update `API_BASE_URL` in `frontend/app.js` to your Render URL

### Frontend → GitHub Pages

1. Go to repo **Settings → Pages**
2. Set source to the `frontend/` folder (or copy to `/docs`)
3. Your demo will be live at `https://your-username.github.io/llm-prompt-guard`

---

## Project Structure

```
llm-prompt-guard/
├── backend/
│   ├── app.py                  # Flask API entry point
│   ├── build.py                # One-shot build: data + training
│   ├── engine/
│   │   ├── preprocessor.py     # Normalization pipeline
│   │   ├── rule_classifier.py  # 30+ regex rule engine
│   │   ├── ml_classifier.py    # TF-IDF + Logistic Regression
│   │   ├── hybrid_engine.py    # Decision fusion
│   │   ├── rewriter.py         # Prompt sanitizer
│   │   └── explainer.py        # Explainability output
│   ├── data/
│   │   └── generate_dataset.py # Synthetic training data generator
│   ├── models/                 # Saved .pkl files (generated)
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── index.html              # SPA shell
│   ├── style.css               # Cybersecurity dark theme
│   └── app.js                  # Fetch + render logic
└── README.md
```

---

## Paper Citation

```bibtex
@article{fathima2025llmpromptguard,
  title   = {LLM Adversarial Prompt Attack Detection and Mitigation Engine:
             A Novel Framework for Securing Generative AI Systems},
  author  = {Fathima, Madiha},
  journal = {TechRxiv},
  year    = {2025},
  doi     = {10.36227/techrxiv.175416873.36395198/v1},
  url     = {https://doi.org/10.36227/techrxiv.175416873.36395198/v1}
}
```
