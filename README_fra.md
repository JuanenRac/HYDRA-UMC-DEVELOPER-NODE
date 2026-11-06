<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - Developer node: evidence, repro cases and checkouts, approved by a person
Copyright (C) JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

<p align="center">
  <img src="images/HYDRA_UMC_BANNER.svg" alt="HYDRA-UMC-DEVELOPER-NODE banner" width="100%">
</p>

# 🧑‍💻 HYDRA-UMC-DEVELOPER-NODE

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | 🇫🇷 <b>Français</b> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 🧑‍💻 Nœud de développement : étudie les pannes, les reproduit et n'exécute rien sans approbation

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.11%2B-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="Core">
  <img src="https://img.shields.io/badge/Parts-closed%20by%20default-367BF5.svg" alt="Parts">
  <img src="https://img.shields.io/badge/Tests-95%20passing-2ea44f.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Version-0.0.3-0f6cbd.svg" alt="Version">
  <img src="https://img.shields.io/badge/Maturity-scaffolding-FFB020.svg" alt="Maturity">
</p>

---

**Vérification d'honnêteté - ce qui fonctionne aujourd'hui :** l'ingestion des preuves (signature, nonce, somme de contrôle, contrôle des secrets), les cas de reproduction exécutables avec des approbations liées à une empreinte, le cache de checkouts avec sa limite, le document d'état, le plugin `ecosystem-ci` et les textes en huit langues sont réels et testés (95 tests automatiques, avec des dépôts git locaux et des processus locaux). Le nœud n'a pas tourné sur un vrai hôte de développement, une recette n'est pas isolée au-delà d'une liste d'autorisation et d'un environnement minimal, et rien ne prend du travail dans la file tout seul. Voir `CHANGELOG.md` pour ce qui a été livré exactement.

---

> **État de la sûreté et de la cybersécurité :** cet écosystème n'est pas un système de sécurité certifié. Il n'existe pas encore de chaîne d'E-STOP matérielle, ni de limites ou de verrouillages imposés par le firmware, ni de commande de mouvement vérifiée ; les images de firmware sont contrôlées par CRC-32 et une signature Ed25519, et une compilation de version refuse les clés de développement publiées (les têtes d'outil et les cartes d'extension derrière le relais utilisent encore les chargeurs d'URTC, qui prennent un HMAC-SHA256 à clé partagée au lieu d'une signature) ; TLS et TLS mutuel sont optionnels et désactivés par défaut ; aucune carte propre n'a encore été assemblée ni testée. Lisez la [base de sécurité](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md) et le [modèle de menaces](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md) avant de vous fier à une affirmation d'ici pour la sécurité d'une personne.

---

## 📋 En un coup d'œil

| | |
|---|---|
| Version | `0.0.3` |
| Maturité | Ébauche |
| Tests | 95 (`python -m pytest -q tests`) |
| Technologie | Python 3.11+ / JSON Schema / SQLite / git worktree |
| Cible | Un serveur de développement |
| Sur matériel réel | Sans objet : rien ici ne s'exécute sur du matériel |

**Aller à :** [Présentation](#-présentation) · [Architecture](#-architecture) · [Démarrage rapide](#-démarrage-rapide) · [Tests](#-tests) · [Structure du dépôt](#-structure-du-dépôt) · [Projets liés](#-projets-liés)

## 🚦 État du projet

Chaque ligne est une partie de ce dépôt et le feu dit où elle en est aujourd'hui. Elle est écrite d'après ce que le dépôt peut montrer (tests, compilations, exécutions), pas d'après ce qui est prévu.

🟢 Fait et vérifié · 🟡 Fonctionne, avec des limites connues · 🟠 À moitié fait ou pas encore vérifié · 🔴 Pas fait ou ne fonctionne pas

| Domaine | État | Ce que cela veut dire ici |
|---|---|---|
| Logiciel | 🟠 | Seulement la structure et les premières pièces ; l'essentiel du travail reste à faire |
| Tests | 🟡 | 95 tests automatiques, exécutés à chaque modification |
| Matériel réel | 🟡 | Sans objet : rien ici ne s'exécute sur du matériel |
| Interface et protocoles | 🟡 | Les routes ou les messages proposés sont documentés et testés avec un client ; tous les clients ne les ont pas encore utilisés |
| Intégration | 🟡 | Ses messages et ses routes sont vérifiés par rapport aux contrats partagés du SDK ; il n'a pas fonctionné avec l'équipement réel |
| Sécurité | 🟡 | Le contrôle d'accès, les limites d'entrée ou les signatures sont implémentés et testés sur un ordinateur ; personne hors du projet ne les a relus |
| Exploitation | 🟠 | Il écrit des journaux ; il n'a pas encore de point de métriques ni de santé |
| Documentation | 🟡 | README en huit langues, vérifié par rapport au manifeste à chaque modification |

## 🎯 Présentation

HYDRA-UMC-DEVELOPER-NODE est le nœud de développement de l'écosystème : l'endroit où l'on étudie une panne signalée par un nœud. Il lit le paquet de preuves de `HYDRA-UMC-LOCAL-TECHNICIAN` (en lecture seule), obtient le code exact de la révision concernée depuis un cache de worktrees git, reproduit la panne avec une recette fixe et peut lancer la CI partagée sur un espace de travail.

Quatre règles valent partout. Chaque partie est **fermée** tant que le fichier de configuration ne l'ouvre pas. Rien ne s'exécute sans **qu'une personne approuve exactement ce qui va s'exécuter**. Rien ne **quitte la machine**. Toute valeur ajustable vit dans le **fichier de configuration**, jamais dans le code.

Cette version fournit cinq éléments indépendants :

1. **Ingestion des preuves** (`evidence.py`) - vérifie un paquet ou un message signé `incident-transport/1` (signature, destinataire, âge, nonce, forme, somme de contrôle, aucun secret) et l'enregistre comme un cas qui attend une personne.
2. **Cas de reproduction exécutables** (`repro.py`, `approvals.py`) - une recette de listes d'arguments, seulement des commandes autorisées et une approbation liée à son empreinte ; chaque exécution est un `ScenarioOutcome` du SDK et le SDK donne le verdict d'une paire avant et après.
3. **Cache de checkouts par révision** (`checkouts.py`) - un miroir bare et un worktree git par commit, le commit épinglé est vérifié, une limite en Go est tenue en supprimant les worktrees les moins récemment utilisés.
4. **Document d'état** (`panel.py`) - file, journal et santé pour un tableau de bord ou un studio, en huit langues, sous forme de fichier.
5. **Plugin `ecosystem-ci`** (`plugin_ci.py`) - le validateur de CI partagé de chaque dépôt d'un espace de travail, avec un rapport consolidé. Dans le mode complet (fermé par défaut), il peut aussi lancer le test lourd que chaque dépôt déclare, comme un lot qu'une personne approuve par son empreinte, un dépôt à la fois, avec des limites de temps, de sortie et d'espace disque libre.

## 🧩 Rôle dans HYDRA-UMC

**HYDRA-UMC-DEVELOPER-NODE** est le nœud de développement de l'écosystème : il lit les paquets de preuves de `HYDRA-UMC-LOCAL-TECHNICIAN`, tient un cache de checkouts par révision, exécute des recettes de reproduction et la CI partagée, et chacune de ces parties reste fermée tant que la configuration ne l'ouvre pas et qu'une personne n'approuve pas l'exécution exacte.

## 🏛️ Architecture

<p align="center">
  <img src="images/architecture.svg" alt="HYDRA-UMC-DEVELOPER-NODE architecture" width="100%">
</p>

## 🚀 Démarrage rapide

Nécessite Python 3.11 ou plus récent.

```bash
./build.sh  # Linux, macOS (build.bat on Windows)
./run.sh
./run.sh --config configs/developer-node.json evidence verify bundle.json
```

## 🧪 Tests

95 tests automatiques s'exécutent avec `python -m pytest -q tests`. Ils n'ont besoin ni de matériel ni de rien en dehors de cette machine.

La CI exécute `HYDRA_UMC_CI=1 python tools/ci_validate.py`, qui vérifie le manifeste, les documents, les huit README et les images.

## 🏗️ Compilation et publication

```bash
chmod +x build.sh   # une seule fois
./build.sh          # crée .venv, pip install -e ".[dev]", vérifie la compilation et lance les tests
./run.sh            # vérifie la configuration fournie (tous les interrupteurs fermés)
./run.sh --config configs/developer-node.json evidence verify bundle.json
./run.sh --version
```

Sous Windows : `build.bat`, puis `run.bat`. `test.sh` / `test.bat` lancent les tests et les vérifications sans changer la version. Le verdict d'une paire avant et après demande le SDK : `pip install -e ".[dev,sdk]"`.

**Dépannage**

- `Refusé : ... is closed` : la partie est désactivée. Ouvrez-la dans le fichier de configuration (`"enabled": true`, un vrai booléen) et lisez [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- `no valid approval for this exact recipe` : approuvez de nouveau la recette avec `repro approve` ; une approbation expire et ne sert qu'une fois.
- `an approval needs a person at a terminal` : faites l'approbation dans un terminal, pas depuis un script ni un tube.

## 📂 Structure du dépôt

<p align="center">
  <img src="images/repository-structure.svg" alt="Repository structure of HYDRA-UMC-DEVELOPER-NODE" width="100%">
</p>

<details>
<summary>Version texte de l'arborescence</summary>

```text
HYDRA-UMC-DEVELOPER-NODE/
├── src/hydra_umc_developer_node/   code source
│   ├── cli.py                      ligne de commande
│   ├── settings.py                 configuration et interrupteurs
│   ├── evidence.py                 contrôle et ingestion des preuves
│   ├── repro.py                    recettes de reproduction et exécutions
│   ├── checkouts.py                cache des checkouts par révision
│   ├── panel.py                    document d'état pour les tableaux de bord
│   ├── plugin_ci.py                plugin ecosystem-ci
│   ├── plugin_full.py              mode complet du plugin ecosystem-ci
│   ├── approvals.py                approbation par une personne
│   ├── store.py                    base locale et journal
│   ├── schema.py                   vérificateur de contrats
│   ├── redaction.py                masquage des secrets
│   └── i18n.py                     textes en huit langues
├── contracts/                      contrats JSON Schema
├── tests/                          tests automatiques
├── configs/                        configuration d'exemple, tout fermé
├── docs/                           documents du projet
├── tools/                          outils du projet et vérifications de la CI
├── images/                         Médias et icônes de l'app
├── .github/                        workflow de CI et modèles de tickets
├── build.sh / build.bat            venv + installation éditable + vérification + tests
├── run.sh / run.bat                Transmet une commande CLI réelle
├── bump_version.py                 Incrément de version type compteur kilométrique (exécuté seulement par la commande `bump` explicite)
├── bump_manifest_version.py        Synchronise la version de hydra-umc.project.json avec la native (--sync)
├── CHANGELOG.md                    ce qui a changé à chaque version
├── build-test.sh                   vérification de build sans modification
├── hydra-umc.project.json          manifeste : version, maturité, famille
├── pyproject.toml                  métadonnées du paquet
└── test.sh                         lance les tests
```

</details>

## 🗺️ Feuille de route et limites connues

**Limites connues aujourd'hui**

Cette version fournit les cinq éléments ci-dessus. Ce qui manque encore :

- **L'isolation d'une exécution.** Une recette s'exécute avec les droits de l'utilisateur qui lance le nœud, avec une liste de programmes autorisés, un environnement minimal et des limites de temps et de sortie ; il n'y a pas encore de bac à sable (conteneur, espaces de noms). Une personne doit lire une recette avant de l'approuver.
- **Une approbation plus forte.** Une approbation est un enregistrement de la base locale fait dans un terminal ; elle n'est pas signée avec une clé de l'approbateur.
- **Le tableau de bord de l'autre côté.** Le document d'état est un contrat et un fichier ; `HYDRA-UMC-DASHBOARD-AI` et `HYDRA-UMC-STUDIO` ne l'affichent pas encore, et la façon dont le fichier leur parvient (un tunnel authentifié) leur appartient.
- **Une boucle de travail.** Les cas, les recettes et les checkouts s'utilisent par commandes ; rien ne prend un cas dans la file pour le traiter seul, volontairement.
- **Une exécution sur un vrai hôte de développement.** Le nœud n'a été testé que sur un ordinateur avec des dépôts git locaux.

## 🌍 Langues

Ce README et les documents du dépôt existent en huit langues : anglais, espagnol, allemand, français, italien, japonais, chinois et portugais (Portugal). Ils sont écrits ensemble et la CI vérifie que les huit fichiers ont les mêmes sections et les mêmes liens. Ce dépôt n'a ni écran ni catalogue de messages propre, il n'y a donc aucune chaîne d'interface à traduire.

## 🔗 Projets liés

Ce projet fait partie de l'écosystème robotique HYDRA-UMC du même auteur (JuanenRac / Electro Hobby 3D). Bon à savoir, car une demande pourrait en réalité concerner l'un de ceux-ci plutôt que ce dépôt.

**Directement Liés**
- **[HYDRA-UMC-LOCAL-TECHNICIAN](https://github.com/JuanenRac/HYDRA-UMC-LOCAL-TECHNICIAN)** — produit les paquets de preuves que ce nœud lit ; le nœud se contente de les vérifier et de les stocker, sans jamais les modifier ni exécuter ce qu'ils disent.
- **[HYDRA-UMC-DEV-SERVER](https://github.com/JuanenRac/HYDRA-UMC-DEV-SERVER)** — hôte de développement reproductible avec une file de tâches durable ; ce nœud est le lieu plus léger où une panne est étudiée et reproduite après l'approbation de chaque exécution par une personne.
- **[HYDRA-UMC-OPS-AGENT](https://github.com/JuanenRac/HYDRA-UMC-OPS-AGENT)** — gère le cycle de vie des incidents de maintenance (preuves, diagnostic, changement approuvé par une personne, déploiement canari, vérification) ; ce nœud fournit l'étape de reproduction et n'approuve jamais un changement.
- **[HYDRA-UMC-SDK](https://github.com/JuanenRac/HYDRA-UMC-SDK)** — les contrats partagés : le résultat de scénario de chaque exécution de reproduction suit son schéma, et le SDK calcule le verdict d'une paire avant et après.

**Fait Également Partie de l'Écosystème**

*Matériel & Plateforme de Base*
- **[HYDRA-UMC](https://github.com/JuanenRac/HYDRA-UMC)** — la conception de la carte mère du bras robotique : hôte CM5 + coprocesseur STM32H745 double cœur, destinée à coordonner jusqu'à 8 bras-outils via CAN-OTA/SPI-OTA (firmware à un stade précoce ; aucune carte assemblée pour l'instant).
- **[HYDRA-UMC-OS](https://github.com/JuanenRac/HYDRA-UMC-OS)** — couche produit reproductible sur Raspberry Pi OS pour le CM5 : agent en lecture seule, config/profils validés, provisionnement WiFi de premier contact.

*Backend Central & Clients*
- **[HYDRA-UMC-SERVER](https://github.com/JuanenRac/HYDRA-UMC-SERVER)** — le vrai backend headless (REST/WebSocket) auquel parle réellement chaque client de contrôle.
- **[HYDRA-UMC-STUDIO](https://github.com/JuanenRac/HYDRA-UMC-STUDIO)** — tableau de bord de contrôle web avec visualisation 3D multi-robot en temps réel.
- **[HYDRA-UMC-SUITE](https://github.com/JuanenRac/HYDRA-UMC-SUITE)** — centre de commande d'essaim de bureau (PySide6) pour plusieurs serveurs à la fois.
- **[HYDRA-UMC-ANDROID-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-ANDROID-CONTROL)** — application de contrôle Android native avec connexion biométrique et un compagnon Wear OS jumelé.
- **[HYDRA-UMC-IOS-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-IOS-CONTROL)** — application de contrôle iOS/iPadOS (Flutter) avec synchronisation WebSocket en temps réel.
- **[HYDRA-UMC-DSI](https://github.com/JuanenRac/HYDRA-UMC-DSI)** — interface tactile native pour l'écran tactile DSI 7" embarqué, intégrée directement sur le CM5.
- **[HYDRA-UMC-EDITOR-URDF](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-URDF)** — créateur/éditeur graphique de bureau pour URDF qui envoie les modèles terminés vers le propre catalogue de STUDIO.
- **[HYDRA-UMC-EDITOR-STL](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-STL)** — éditeur de bureau de modèles STL, transformant/remplaçant/retirant/ajoutant de vraies pièces dans le même catalogue de modèles qu'édite aussi HYDRA-UMC-EDITOR-URDF.
- **[HYDRA-UMC-BRIDGE-AMR](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-AMR)** — frontière de coordination pour les flottes AGV/AMR via un éditeur MQTT VDA 5050 (testé uniquement contre une flotte émulée).
- **[HYDRA-UMC-BRIDGE-CNC](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-CNC)** — coordinateur haut niveau pour cellules CNC avec accès au statut/octets de contrôle GRBL (testé uniquement contre un émulateur).
- **[HYDRA-UMC-BRIDGE-DROIDS](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-DROIDS)** — frontière de coordination pour droïdes à pattes/humanoïdes, avec un émetteur de commandes Boston Dynamics Spot (testé uniquement contre un émulateur).
- **[HYDRA-UMC-BRIDGE-LASER](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-LASER)** — coordinateur de cellules laser lisant 3 signaux GPIO de clé/enceinte/verrouillage (testé uniquement contre une puce simulée ; il ne peut ni armer ni tirer un laser).
- **[HYDRA-UMC-BRIDGE-OPENPNP](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-OPENPNP)** — coordinateur haut niveau sûr pour le flux de cartes du pick-and-place OpenPnP.
- **[HYDRA-UMC-BRIDGE-PRINTER3D](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-PRINTER3D)** — frontière de coordination sûre pour imprimantes 3D Moonraker/Klipper, avec de vraies commandes de tâche contrôlées.
- **[HYDRA-UMC-BRIDGE-ROS2](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-ROS2)** — coordinateur avec un transport ROS 2 rclpy à importation paresseuse (pas encore exécuté contre une installation ROS 2).
- **[HYDRA-UMC-BRIDGE-UAV](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-UAV)** — frontière de coordination pour UAV équipés de caméra, avec un émetteur de commandes MAVLink (testé uniquement contre un émulateur).

*Plateforme d'Outils URTC*
- **[URTC](https://github.com/JuanenRac/URTC)** — firmware pour la carte physique Universal Robot Tool Controller, plus de 25 profils d'outil sur bus CAN.
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — outil de bureau à interface graphique pour flasher les cartes URTC, CAN-OTA plus SWD/JTAG puce complète.
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — outil de bureau de diagnostic CAN-bus en direct pour cartes URTC, un panneau par profil d'outil.
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — alternative basée navigateur à URTC-TESTER via la Web Serial API, sans installation locale.
- **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** — passerelle devant le bus CAN d'URTC : liste d'identifiants autorisés, limite de débit et clé de session ; logiciel testé sur ordinateur, pas encore sur un bus réel.

*Nœud IA de Vision (Hailo-8)*
- **[HYDRA-UMC-VISION-NODE](https://github.com/JuanenRac/HYDRA-UMC-VISION-NODE)** — hub d'intégration pour le pipeline de vision Hailo-8, avec une vraie vérification de disponibilité matérielle par étape.
- **[HYDRA-UMC-DETECTION-HEF](https://github.com/JuanenRac/HYDRA-UMC-DETECTION-HEF)** — registre réel de modèles compilés avec vérification de chargement sécurisé par architecture Hailo/checksum.
- **[HYDRA-UMC-VISION-STREAMER](https://github.com/JuanenRac/HYDRA-UMC-VISION-STREAMER)** — générateur réel de pipeline GStreamer + config MediaMTX, avec une vraie frontière d'intégration HailoRT.
- **[HYDRA-UMC-VISUAL-SERVOING-API](https://github.com/JuanenRac/HYDRA-UMC-VISUAL-SERVOING-API)** — loi de correction Position-Based Visual Servoing avec autorisation conditionnée à l'état de zone ; pas encore d'estimation de pose par caméra.
- **[HYDRA-UMC-SAFETY-ZONES](https://github.com/JuanenRac/HYDRA-UMC-SAFETY-ZONES)** — logique v0 de violation de zone, de fraîcheur de calibration et de demande d'E-STOP qui lit les positions d'objets dans un fichier ; aucun détecteur ne l'alimente et aucun E-STOP physique n'y est encore relié.

*Nœud IA Cognitif (Hailo-10)*
- **[HYDRA-UMC-COGNITIVE-NODE](https://github.com/JuanenRac/HYDRA-UMC-COGNITIVE-NODE)** — hub d'intégration pour le pipeline cognitif Hailo-10 (orchestration LLM/VLA/voix).
- **[HYDRA-UMC-VLA-ENGINE](https://github.com/JuanenRac/HYDRA-UMC-VLA-ENGINE)** — vrai encodage/décodage de jetons d'action et génération de trajectoire pour un modèle Vision-Language-Action.
- **[HYDRA-UMC-VOICE-UI](https://github.com/JuanenRac/HYDRA-UMC-VOICE-UI)** — vrai front-end vocal (VAD + analyseur d'intention) avec un relais Watch borné et soumis à confirmation - il n'a pas de surface de notification sortante, ce projet publie donc ses événements d'incident sur le broker de l'écosystème.
- **[HYDRA-UMC-SEMANTIC-PLANNER](https://github.com/JuanenRac/HYDRA-UMC-SEMANTIC-PLANNER)** — vraie décomposition de tâches basée sur des règles et récupération sémantique d'erreurs sur les codes d'erreur MCU.
- **[HYDRA-UMC-DOCS-QA](https://github.com/JuanenRac/HYDRA-UMC-DOCS-QA)** — vraie recherche documentaire TF-IDF (bibliothèque standard uniquement) sur les propres documents Markdown de cet écosystème.

*Orchestration & Essaim*
- **[HYDRA-UMC-ORCHESTRATOR](https://github.com/JuanenRac/HYDRA-UMC-ORCHESTRATOR)** — hub d'intégration avec un vrai contrat de rapport de santé gRPC/Protobuf et une machine à états de mission.
- **[HYDRA-UMC-JOB-DISPATCHER](https://github.com/JuanenRac/HYDRA-UMC-JOB-DISPATCHER)** — vraie file de tâches basée sur la priorité avec déduplication, via une vraie API HTTP.
- **[HYDRA-UMC-PATH-PLANNER-3D](https://github.com/JuanenRac/HYDRA-UMC-PATH-PLANNER-3D)** — vrai planificateur de trajectoire 3D basé sur RRT, avec vraie validation des collisions obstacle/espace de travail.
- **[HYDRA-UMC-SWARM-SYNC](https://github.com/JuanenRac/HYDRA-UMC-SWARM-SYNC)** — vraie synchronisation d'état CRDT LWW-Element-Map, testée par propriétés pour la convergence multi-cellule.
- **[HYDRA-UMC-NODE-HEALING](https://github.com/JuanenRac/HYDRA-UMC-NODE-HEALING)** — surveillant réel de santé de flotte basé sur gRPC, avec son propre retry/backoff et détection de non-concordance d'identité.

*Jumeau Numérique & Simulation*
- **[HYDRA-UMC-TWIN](https://github.com/JuanenRac/HYDRA-UMC-TWIN)** — hub d'intégration pour le moteur de jumeau numérique, avec un vrai contrat de synchronisation par compatibilité de version.
- **[HYDRA-UMC-HIL-BRIDGE](https://github.com/JuanenRac/HYDRA-UMC-HIL-BRIDGE)** — routeur hardware-in-the-loop avec un verrouillage logiciel de collision entre simulation et matériel réel (testé sans matériel réel).
- **[HYDRA-UMC-PHYSICS-REPLICA](https://github.com/JuanenRac/HYDRA-UMC-PHYSICS-REPLICA)** — vraie cinématique directe et validation des limites articulaires sur un vrai sous-ensemble URDF.
- **[HYDRA-UMC-SYNTHETIC-DATA-GEN](https://github.com/JuanenRac/HYDRA-UMC-SYNTHETIC-DATA-GEN)** — vrai générateur procédural de scènes 2D avec export d'annotations YOLO/COCO.

*Données & Analytique*
- **[HYDRA-UMC-DATALAKE](https://github.com/JuanenRac/HYDRA-UMC-DATALAKE)** — vrai magasin de séries temporelles basé sur sqlite3, avec une vraie API HTTP d'ingestion/requête.
- **[HYDRA-UMC-ANOMALY-DETECTOR](https://github.com/JuanenRac/HYDRA-UMC-ANOMALY-DETECTOR)** — vrai détecteur d'anomalies FFT + ligne de base statistique, avec surveillance de dérive.
- **[HYDRA-UMC-PRODUCTION-REPORTS](https://github.com/JuanenRac/HYDRA-UMC-PRODUCTION-REPORTS)** — vrai calcul OEE/disponibilité sur l'historique de DATALAKE, avec export CSV reproductible.
- **[HYDRA-UMC-TELEMETRY-COLLECTOR](https://github.com/JuanenRac/HYDRA-UMC-TELEMETRY-COLLECTOR)** — vrai pipeline d'ingestion CAN/WebSocket vers DATALAKE, avec déduplication par séquence.

*Passerelle Industrielle*
- **[HYDRA-UMC-GATEWAY-INDUSTRIAL](https://github.com/JuanenRac/HYDRA-UMC-GATEWAY-INDUSTRIAL)** — hub d'intégration relayant vers les protocoles industriels, avec une vraie couche de liste blanche de commandes/contre-pression.
- **[HYDRA-UMC-OPCUA-SERVER](https://github.com/JuanenRac/HYDRA-UMC-OPCUA-SERVER)** — vrai espace d'adressage OPC-UA, vérifié avec une vraie session client du protocole binaire.
- **[HYDRA-UMC-MQTT-BROKER](https://github.com/JuanenRac/HYDRA-UMC-MQTT-BROKER)** — vrai broker MQTT avec authentification par client optionnelle et ACL de sujets.
- **[HYDRA-UMC-MTCONNECT-ADAPTER](https://github.com/JuanenRac/HYDRA-UMC-MTCONNECT-ADAPTER)** — vrais points de terminaison XML MTConnect `/probe` et `/current`, avec sortie en mode dégradé.

*Outils Complémentaires*
- **[HYDRA-UMC-DASHBOARD-AI](https://github.com/JuanenRac/HYDRA-UMC-DASHBOARD-AI)** — panneaux Smart Summaries et Anomaly Highlighting sur DATALAKE/ANOMALY-DETECTOR, avec un repli statistique honnête.
- **[HYDRA-UMC-TOOL-CLI](https://github.com/JuanenRac/HYDRA-UMC-TOOL-CLI)** — CLI de flotte avec un vrai contrat de codes de sortie stable, un vrai client en direct de la propre API de HYDRA-UMC-SERVER.
- **[HYDRA-UMC-WATCH](https://github.com/JuanenRac/HYDRA-UMC-WATCH)** — application compagnon WearOS avec des motifs d'alerte haptique et un relais vocal vers le téléphone jumelé (pas encore exécutée sur une montre physique).
- **[HYDRA-UMC-CONNECTOR-HUB](https://github.com/JuanenRac/HYDRA-UMC-CONNECTOR-HUB)** — catalogue de capacités d'adaptateurs externes, GET uniquement par conception.
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — firmware pour un rack de montage de cartes avec décodage réel d'ID d'outil et logique de préchauffage Smart Idle.
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — firmware plus un vrai compagnon de vision Python pour une tête d'outil d'inspection thermique/RGB.
- **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** — outil administratif de bureau qui découvre, clone et met à jour chaque dépôt de cet écosystème.
- **[HYDRA-UMC-OS-REBUILDER](https://github.com/JuanenRac/HYDRA-UMC-OS-REBUILDER)** — construit une image fraîche de la CM5 depuis les sources, un autre membre d'"Ecosystem Operations".

## 📚 Documentation

Où lire la suite :

* **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — les éléments, le déroulement d'un incident et où s'arrête le nœud.
* **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** — chaque interrupteur et chaque valeur ajustable du fichier de configuration.
* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — chaque commande, les codes de sortie et la forme d'une recette.
* **[docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)** — les règles que le nœud respecte et ce qui n'est pas couvert.
* **[docs/PANEL_CONTRACT.md](docs/PANEL_CONTRACT.md)** — le document d'état pour tableaux de bord et studios.
* [Base de sécurité de l'écosystème](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md)
* [Modèle de menaces de l'écosystème](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md)
* [Journal des modifications de ce dépôt](CHANGELOG.md)
* [Licence de ce dépôt](LICENSE.md)

## 🤝 Contribuer et communauté

* Avant une pull request, exécutez `HYDRA_UMC_CI=1 py -3 tools/ci_validate.py` (ou `HYDRA_UMC_CI=1 python3 tools/ci_validate.py`) : il doit afficher `CI_VALIDATION=PASS`. N'exécutez pas `build.sh` ni `build.bat` pour cette vérification ; compiler n'est pas vérifier.
* Les huit README sont écrits à partir d'une source unique dans HYDRA-UMC-DOCS ; ne les modifiez pas à la main. Changez la source et réécrivez-les avec `tools/make_readmes.py`.
* N'affirmez pas dans un README ce qui n'a pas tourné : écrivez « simulé » ou « non essayé sur matériel » quand c'est la vérité.
* Voir [CONTRIBUTING.md](CONTRIBUTING.md), le [code de conduite](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md) et [SUPPORT.md](SUPPORT.md).

## 👤 AUTEUR

**JuanenRac (Electro Hobby 3D)** · electrohobby3d@gmail.com

## 📜 LICENCE

GPL-3.0-or-later - [LICENSE](LICENSE).
