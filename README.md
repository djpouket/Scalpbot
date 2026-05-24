# ScalpBot Pro — Institutional SMC

## Features
- WebSocket Alpaca IEX temps réel
- Score SMC 0-10 : EMA trend M5, VWAP, OB, FVG, BOS/CHoCH
- Graphiques Plotly M5 + M1 + Volume
- Auto-Trade avec seuil configurable
- Supabase logging (optionnel)

## Corrections intégrées
- Structure projet remise au propre : `app.py`, `requirements.txt`, `.env.example`, `.gitignore`
- Démarrage des threads après la définition de toutes les fonctions
- Lecture des clés depuis `.env` ou Streamlit Secrets
- Garde-fous sur la taille d'ordre : risque, notional et quantité maximum
- Etat partagé protégé par lock réentrant
- Correction de la variable `prix` inexistante dans le calcul ATR fallback
- Style graphique inspiré de Q-terminal : fond sombre quadrillé, panneaux fins, accents vert/cyan/ambre
- VWAP reset quotidien par session NY
- Lookback swing réduit (n=2 vs n=3)
- BOS confirmation 2 bougies
- OB invalidation automatique
- FVG/OB filtrés par direction du biais
- Score directionnel (pas de score contradictoire)
- Equity dynamique via API

## Setup local
```bash
cp .env.example .env
pip install -r requirements.txt
streamlit run app.py
```

## Variables optionnelles
```env
MAX_RISK_FRACTION=0.01
MAX_ORDER_NOTIONAL=10000
MAX_SYMBOL_ORDER_QTY=1000
SUPABASE_URL=
SUPABASE_KEY=
```

## Streamlit Cloud — Secrets
```toml
ALPACA_API_KEY = "..."
ALPACA_SECRET_KEY = "..."
SUPABASE_URL = "..."   # optionnel
SUPABASE_KEY = "..."   # optionnel
MAX_RISK_FRACTION = "0.01"
MAX_ORDER_NOTIONAL = "10000"
MAX_SYMBOL_ORDER_QTY = "1000"
```
