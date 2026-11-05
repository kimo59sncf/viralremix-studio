# ViralRemix Studio

Application web locale permettant d'importer une vidéo (MP4, MOV, WebM), de lui
appliquer des transformations (miroir, zoom, rotation, format, vitesse, couleurs,
audio) et d'exporter le résultat en MP4 (H.264 + AAC, 1080p).

## Stack

- **Frontend** : React + TypeScript + Vite + Tailwind CSS (+ composants Radix UI)
- **Backend** : Python + FastAPI
- **Traitement vidéo** : FFmpeg (binaire fourni par `imageio-ffmpeg`, repli sur le PATH)

## Lancer le backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API disponible sur http://localhost:8000 (docs : http://localhost:8000/docs).

## Lancer le frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Interface disponible sur http://localhost:5173 (le proxy Vite redirige `/api` vers le backend).

> Le fichier source n'est jamais écrasé : chaque export produit un nouveau MP4.

## Fonctionnalités (MVP)

- Importation vidéo (MP4, MOV, WebM) avec durée/résolution + lecteur.
- Transformations : miroir horizontal, rotation, zoom, format (16:9, 9:16, 1:1, 4:5), arrière-plan flouté.
- Vitesse : x0.5 → x2 (audio synchronisée).
- Couleurs : noir et blanc, saturation, contraste, luminosité, teinte, chaud/froid.
- Audio : volume, suppression de l'audio.
- Aperçu instantané (image) + aperçu vidéo (extrait).
- Export MP4 1080p (H.264 + AAC) avec barre de progression et téléchargement.

## Note : proxy d'entreprise (SNCF)

Le réseau bloque les connexions directes vers PyPI / npm. Un relais local est fourni
dans `backend/local_proxy.py` : il traverse le proxy `web-pa-*.access.sncf.fr:8080`
avec l'authentification Windows (SSPI / Kerberos).

```powershell
# démarrer le relais (une fois, dans un terminal dédié)
cd backend
py local_proxy.py
```

Puis utiliser `http://127.0.0.1:8899` comme proxy pour pip / npm :

```powershell
py -m pip install --proxy http://127.0.0.1:8899 <paquet>
npm.cmd install --proxy http://127.0.0.1:8899 --https-proxy http://127.0.0.1:8899
```

Prérequis du relais : `py -m pip install pywin32` (déjà installé sur ce poste).

