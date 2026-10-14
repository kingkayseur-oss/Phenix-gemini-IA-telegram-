logo.png

# 🤖 Bot Telegram — IA Dev Web

Bot Telegram IA qui **génère du code de site web** (HTML/CSS/JS, React, Vue, PHP…) à partir d'une simple description.

## ✨ Fonctionnalités

- 💻 IA spécialisée « dev web » : décrivez un site, recevez le code complet
- 🆓 **10 questions gratuites par 24h**
- ⭐ **Premium** payé en Telegram Stars (50 → 1000 étoiles)
- 🔒 **Abonnement obligatoire** à une chaîne + un groupe avant utilisation
- 🛠 Commandes admin pour gérer le premium

## 📦 Stack

- **Python 3.11**
- **aiogram** (interaction Telegram)
- **Ollama** (modèle IA local, sans clé API)
- **Docker** (déploiement)

## 🚀 Déploiement (Dokploy)

1. Fork / clone ce dépôt
2. Crée une nouvelle **Application** dans Dokploy, connecte le dépôt GitHub
3. Dokploy détecte le `Dockerfile` et build l'image
4. Ajoute les **variables d'environnement** (onglet *Environment*) :

| Variable | Description | Exemple |
|---|---|---|
| `BOT_TOKEN` | Token du bot (via @BotFather) | `123456:ABC...` |
| `ADMIN_ID` | Ton ID Telegram (admin) | `987654321` |
| `CHANNEL_ID` | @username de la chaîne | `@ma_chaine` |
| `GROUP_ID` | @username du groupe | `@mon_groupe` |
| `CHANNEL_URL` | Lien de la chaîne | `https://t.me/ma_chaine` |
| `GROUP_URL` | Lien du groupe | `https://t.me/mon_groupe` |
| `AI_API_URL` | Endpoint du modèle IA | `http://ollama:11434/api/generate` |
| `AI_MODEL` | Nom du modèle | `llama3` |

5. Clique sur **Deploy** ✅

> ⚠️ Le modèle IA doit tourner quelque part (Ollama). Déploie-le séparément (RunPod GPU, autre container) et pointe `AI_API_URL` dessus.

## 🎮 Commandes

| Commande | Qui | Rôle |
|---|---|---|
| `/start` | Tous | Démarre le bot |
| `/premium` | Tous | Affiche l'offre premium |
| `/givepremium <id> <jours>` | Admin | Active le premium |
| `/delpremium <id>` | Admin | Retire le premium |

## 💰 Offre Premium

| Étoiles | Durée |
|---|---|
| 50 ⭐ | 14 jours |
| 100 ⭐ | 28 jours |
| 200 ⭐ | 63 jours |
| 500 ⭐ | 180 jours |
| 1000 ⭐ | 420 jours |

## 📁 Structure

```
.
├── bot.py            # Code principal
├── requirements.txt  # Dépendances Python
├── Dockerfile        # Image Docker
├── .gitignore
└── README.md
```

## 🔧 Lancer en local

```bash
pip install -r requirements.txt
export BOT_TOKEN="ton_token"
python bot.py
```

## ⚖️ Licence

Usage personnel. Respectez les règles de Telegram.
