
# Décodeur local IZAR RC IoT LRW wMB – LRZ102

## Objectif

Cette application locale permet de **coller un payload applicatif en hexadécimal** et d'afficher les **valeurs métier décodées**.

## Ce que fait cette V1

- Décode les trames **DS40_OQ**, **DS40_I**, **DS40_2S**, **DS40_E** *(payload applicatif en clair)*
- Décode la trame **DS40_O_OMS4** *(payload installation en clair, port 20)*
- Affiche :
  - type de trame
  - meter key
  - version firmware
  - timestamp
  - valeurs métier
  - alarmes actives

## Limite importante

D'après la documentation fournie, **tout le payload est chiffré** et les **clés de déchiffrement** sont fournies via un autre document / transfert de clés.

👉 Donc :
- si vous collez un **payload déjà déchiffré**, l'application fonctionne,
- si vous collez une **trame LoRaWAN chiffrée brute**, il faudra ajouter dans une V2 :
  - les vraies clés,
  - la règle complète de déchiffrement LRZ102,
  - la gestion du MAC applicatif.

## Installation

Ouvrez un terminal dans ce dossier, puis lancez :

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

### Lancer le site local

```bash
python -m streamlit run app.py
```

Ensuite, ouvrez dans votre navigateur l'adresse indiquée dans le terminal (souvent `http://localhost:8501`).

## Fichiers

- `app.py` : interface Streamlit
- `decoder.py` : logique de décodage
- `requirements.txt` : dépendances Python

## Prochaine étape possible

Si vous me fournissez ensuite le **fichier de clés** / la règle exacte de déchiffrement LRZ102, je pourrai vous préparer une **V2** qui accepte directement une **trame chiffrée** collée depuis le réseau et l'affiche en clair.
