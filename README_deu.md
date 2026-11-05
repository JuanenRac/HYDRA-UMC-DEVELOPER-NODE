<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - Developer node: evidence, repro cases and checkouts, approved by a person
Copyright (C) JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

<p align="center">
  <img src="images/HYDRA_UMC_BANNER.svg" alt="HYDRA-UMC-DEVELOPER-NODE banner" width="100%">
</p>

# 🧑‍💻 HYDRA-UMC-DEVELOPER-NODE

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | 🇩🇪 <b>Deutsch</b> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 🧑‍💻 Entwicklungsknoten: untersucht Fehler, reproduziert sie und führt nichts ohne Freigabe aus

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.11%2B-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="Core">
  <img src="https://img.shields.io/badge/Parts-closed%20by%20default-367BF5.svg" alt="Parts">
  <img src="https://img.shields.io/badge/Tests-94%20passing-2ea44f.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Version-0.0.2-0f6cbd.svg" alt="Version">
  <img src="https://img.shields.io/badge/Maturity-scaffolding-FFB020.svg" alt="Maturity">
</p>

---

**Ehrlichkeitsprüfung - was heute wirklich läuft:** die Beleg-Aufnahme (Signatur, Nonce, Prüfsumme, Geheimnisprüfung), die ausführbaren Reproduktionsfälle mit an einen Digest gebundenen Freigaben, der Checkout-Cache mit seinem Limit, das Statusdokument, das Plugin `ecosystem-ci` und die Texte in acht Sprachen sind echt und getestet (94 automatische Tests, mit lokalen Git-Repositories und lokalen Prozessen). Der Knoten lief nicht auf einem echten Entwicklungshost, ein Rezept ist nur durch eine Erlaubnisliste und eine minimale Umgebung isoliert, und nichts nimmt von selbst Arbeit aus der Warteschlange. Was genau ausgeliefert wurde, steht in `CHANGELOG.md`.

---

> **Stand von Sicherheit (Safety) und Security:** Dieses Ökosystem ist kein zertifiziertes Sicherheitssystem. Es gibt noch keinen Hardware-E-STOP-Pfad, keine von der Firmware durchgesetzten Grenzen oder Verriegelungen und keinen verifizierten Bewegungsbefehl; Firmware-Images werden mit CRC-32 und einer Ed25519-Signatur geprüft, und ein Release-Build verweigert die veröffentlichten Entwicklungsschlüssel (die Werkzeugköpfe und Erweiterungsplatinen hinter dem Relais laufen noch mit URTC-Bootloadern, die statt einer Signatur ein HMAC-SHA256 mit gemeinsamem Schlüssel verwenden); TLS und gegenseitiges TLS sind optional und standardmäßig aus; noch keine eigene Platine wurde bestückt oder getestet. Lesen Sie die [Sicherheitsbasis](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md) und das [Bedrohungsmodell](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md), bevor Sie sich für die Sicherheit einer Person auf eine Aussage hier verlassen.

---

## 📋 Auf einen Blick

| | |
|---|---|
| Version | `0.0.2` |
| Reifegrad | Gerüst |
| Tests | 94 (`python -m pytest -q tests`) |
| Technik | Python 3.11+ / JSON Schema / SQLite / git worktree |
| Ziel | Ein Entwicklungsserver |
| Auf echter Hardware | Nicht zutreffend: nichts hiervon läuft auf Hardware |

**Springe zu:** [Überblick](#-überblick) · [Architektur](#-architektur) · [Schnellstart](#-schnellstart) · [Tests](#-tests) · [Struktur des Repositorys](#-struktur-des-repositorys) · [Verwandte Projekte](#-verwandte-projekte)

## 🚦 Projektstatus

Jede Zeile ist ein Teil dieses Repositorys, und die Ampel sagt, wie weit er heute ist. Sie beruht auf dem, was das Repository zeigen kann (Tests, Builds, Läufe), nicht auf dem, was geplant ist.

🟢 Fertig und überprüft · 🟡 Funktioniert, mit bekannten Grenzen · 🟠 Teilweise fertig oder noch nicht überprüft · 🔴 Nicht gemacht oder funktioniert nicht

| Bereich | Stand | Was das hier bedeutet |
|---|---|---|
| Software | 🟠 | Nur Struktur und erste Teile; der größte Teil der Arbeit steht noch aus |
| Tests | 🟡 | 94 automatische Tests, bei jeder Änderung ausgeführt |
| Echte Hardware | 🟡 | Nicht zutreffend: nichts hiervon läuft auf Hardware |
| Schnittstelle und Protokolle | 🟡 | Die angebotenen Routen oder Nachrichten sind dokumentiert und mit einem Client getestet; noch nicht jeder Client hat sie benutzt |
| Integration | 🟡 | Seine Nachrichten und Routen werden gegen die gemeinsamen Verträge des SDK geprüft; es lief noch nicht zusammen mit der echten Ausrüstung |
| Sicherheit | 🟡 | Zugriffskontrolle, Eingabegrenzen oder Signaturen sind umgesetzt und auf einem Rechner getestet; niemand außerhalb des Projekts hat sie geprüft |
| Betrieb | 🟠 | Es schreibt Logs; einen Metrik- oder Gesundheits-Endpunkt hat es noch nicht |
| Dokumentation | 🟡 | README in acht Sprachen, bei jeder Änderung gegen das Manifest geprüft |

## 🎯 Überblick

HYDRA-UMC-DEVELOPER-NODE ist der Entwicklungsknoten des Ökosystems: der Ort, an dem ein von einem Knoten gemeldeter Fehler untersucht wird. Er liest das Belegpaket von `HYDRA-UMC-LOCAL-TECHNICIAN` (nur lesend), holt den genauen Quelltext der betroffenen Revision aus einem Cache von Git-Worktrees, reproduziert den Fehler mit einem festen Rezept und kann die gemeinsame CI über einen Arbeitsbereich laufen lassen.

Vier Regeln gelten überall. Jeder Teil ist **geschlossen**, bis die Konfigurationsdatei ihn öffnet. Nichts läuft, ohne dass **ein Mensch genau das freigibt, was ausgeführt wird**. Nichts **verlässt den Rechner**. Jeder einstellbare Wert steht in der **Konfigurationsdatei**, nie im Code.

Diese Version liefert fünf unabhängige Teile:

1. **Beleg-Aufnahme** (`evidence.py`) - prüft ein Paket oder eine signierte `incident-transport/1`-Nachricht (Signatur, Empfänger, Alter, Nonce, Form, Prüfsumme, keine Geheimnisse) und speichert sie als Fall, der auf einen Menschen wartet.
2. **Ausführbare Reproduktionsfälle** (`repro.py`, `approvals.py`) - ein Rezept aus Argumentlisten, nur erlaubte Befehle und eine an den Digest gebundene Freigabe; jeder Lauf ist ein `ScenarioOutcome` des SDK, und das SDK liefert das Urteil über ein Vorher-nachher-Paar.
3. **Checkout-Cache pro Revision** (`checkouts.py`) - ein Bare-Mirror und ein Git-Worktree pro Commit, ein festgelegter Commit wird geprüft, ein Limit in GB wird durch Entfernen der am längsten nicht genutzten Worktrees eingehalten.
4. **Statusdokument** (`panel.py`) - Warteschlange, Journal und Zustand für ein Dashboard oder ein Studio, in acht Sprachen, als Datei.
5. **Plugin `ecosystem-ci`** (`plugin_ci.py`) - der gemeinsame CI-Validator jedes Repositorys eines Arbeitsbereichs mit einem zusammengefassten Bericht. Im vollständigen Modus (standardmäßig geschlossen) kann es auch den schweren Test ausführen, den jedes Repository deklariert, als Stapel, den ein Mensch anhand seiner Prüfsumme freigibt, ein Repository nach dem anderen, mit Grenzen für Zeit, Ausgabe und freien Speicherplatz.

## 🧩 Rolle in HYDRA-UMC

**HYDRA-UMC-DEVELOPER-NODE** ist der Entwicklungsknoten des Ökosystems: Er liest die Belegpakete von `HYDRA-UMC-LOCAL-TECHNICIAN`, führt einen Cache von Checkouts pro Revision, startet Reproduktionsrezepte und die gemeinsame CI, und jeder dieser Teile bleibt geschlossen, bis die Konfiguration ihn öffnet und ein Mensch den genauen Lauf freigibt.

## 🏛️ Architektur

<p align="center">
  <img src="images/architecture.svg" alt="HYDRA-UMC-DEVELOPER-NODE architecture" width="100%">
</p>

## 🚀 Schnellstart

Benötigt Python 3.11 oder neuer.

```bash
./build.sh  # Linux, macOS (build.bat on Windows)
./run.sh
./run.sh --config configs/developer-node.json evidence verify bundle.json
```

## 🧪 Tests

94 automatische Tests laufen mit `python -m pytest -q tests`. Sie brauchen weder Hardware noch etwas außerhalb dieses Rechners.

Die CI führt `HYDRA_UMC_CI=1 python tools/ci_validate.py` aus; das prüft das Manifest, die Dokumente, die acht READMEs und die Bilder.

## 🏗️ Build und Veröffentlichung

```bash
chmod +x build.sh   # einmalig
./build.sh          # erstellt .venv, pip install -e ".[dev]", prüft die Kompilierung und führt die Tests aus
./run.sh            # prüft die mitgelieferte Konfiguration (alle Schalter geschlossen)
./run.sh --config configs/developer-node.json evidence verify bundle.json
./run.sh --version
```

Unter Windows: `build.bat`, dann `run.bat`. `test.sh` / `test.bat` führen die Tests und die Prüfungen aus, ohne die Version zu ändern. Das Urteil über ein Vorher-nachher-Paar braucht das SDK: `pip install -e ".[dev,sdk]"`.

**Fehlersuche**

- `Abgelehnt: ... is closed`: Der Teil ist ausgeschaltet. Öffne ihn in der Konfigurationsdatei (`"enabled": true`, ein echter Boolean) und lies [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- `no valid approval for this exact recipe`: Gib das Rezept mit `repro approve` erneut frei; eine Freigabe läuft ab und gilt nur einmal.
- `an approval needs a person at a terminal`: Führe die Freigabe in einem Terminal aus, nicht aus einem Skript oder einer Pipe.

## 📂 Struktur des Repositorys

<p align="center">
  <img src="images/repository-structure.svg" alt="Repository structure of HYDRA-UMC-DEVELOPER-NODE" width="100%">
</p>

<details>
<summary>Textversion des Baums</summary>

```text
HYDRA-UMC-DEVELOPER-NODE/
├── src/hydra_umc_developer_node/   Quellcode
│   ├── cli.py                      Befehlszeile
│   ├── settings.py                 Konfiguration und Schalter
│   ├── evidence.py                 Prüfung und Aufnahme von Belegen
│   ├── repro.py                    Reproduktionsrezepte und Läufe
│   ├── checkouts.py                Checkout-Cache pro Revision
│   ├── panel.py                    Statusdokument für Dashboards
│   ├── plugin_ci.py                Plugin ecosystem-ci
│   ├── plugin_full.py              vollständiger Modus des Plugins ecosystem-ci
│   ├── approvals.py                Freigabe durch einen Menschen
│   ├── store.py                    lokale Datenbank und Journal
│   ├── schema.py                   Vertragsprüfung
│   ├── redaction.py                Schwärzung von Geheimnissen
│   └── i18n.py                     Texte in acht Sprachen
├── contracts/                      JSON-Schema-Verträge
├── tests/                          automatische Tests
├── configs/                        Beispielkonfiguration, alles geschlossen
├── docs/                           Dokumente des Projekts
├── tools/                          Projektwerkzeuge und CI-Prüfungen
├── images/                         Medien und App-Icons
├── .github/                        CI-Workflow und Issue-Vorlagen
├── build.sh / build.bat            venv + editierbare Installation + Prüfung + Tests
├── run.sh / run.bat                Leitet einen realen CLI-Befehl weiter
├── bump_version.py                 ausdrückliche Versionserhöhung
├── bump_manifest_version.py        Synchronisiert die Version von hydra-umc.project.json mit der nativen (--sync)
├── CHANGELOG.md                    was sich in jeder Version geändert hat
├── build-test.sh                   Build-Prüfung ohne Änderungen
├── hydra-umc.project.json          Manifest: Version, Reifegrad, Familie
├── pyproject.toml                  Paketmetadaten
└── test.sh                         führt die Tests aus
```

</details>

## 🗺️ Roadmap und bekannte Grenzen

**Bekannte Grenzen heute**

Diese Version liefert die fünf oben genannten Teile. Was noch fehlt:

- **Isolierung eines Laufs.** Ein Rezept läuft mit den Rechten des Benutzers, der den Knoten betreibt, mit einer Liste erlaubter Programme, einer minimalen Umgebung sowie Zeit- und Ausgabegrenzen; eine Sandbox (Container, Namespaces) gibt es noch nicht. Ein Mensch muss ein Rezept lesen, bevor er es freigibt.
- **Eine stärkere Freigabe.** Eine Freigabe ist ein an einem Terminal erstellter Eintrag in der lokalen Datenbank; sie ist nicht mit einem Schlüssel des Freigebenden signiert.
- **Das Dashboard auf der anderen Seite.** Das Statusdokument ist ein Vertrag und eine Datei; `HYDRA-UMC-DASHBOARD-AI` und `HYDRA-UMC-STUDIO` zeigen es noch nicht, und wie die Datei zu ihnen gelangt (ein authentifizierter Tunnel), entscheiden sie selbst.
- **Eine Arbeitsschleife.** Fälle, Rezepte und Checkouts werden über Befehle genutzt; nichts nimmt von selbst einen Fall aus der Warteschlange und bearbeitet ihn, mit Absicht.
- **Ein Lauf auf einem echten Entwicklungshost.** Der Knoten wurde nur auf einem Rechner mit lokalen Git-Repositories getestet.

## 🌍 Sprachen

Diese README und die Dokumente des Repositorys gibt es in acht Sprachen: Englisch, Spanisch, Deutsch, Französisch, Italienisch, Japanisch, Chinesisch und Portugiesisch (Portugal). Sie entstehen gemeinsam, und die CI prüft, dass die acht Dateien dieselben Abschnitte und dieselben Links haben. Dieses Repository hat weder eine eigene Oberfläche noch einen eigenen Meldungskatalog, es gibt also keine Oberflächentexte zu übersetzen.

## 🔗 Verwandte Projekte

Dieses Projekt ist Teil des HYDRA-UMC-Robotik-Ökosystems desselben Autors (JuanenRac / Electro Hobby 3D). Gut zu wissen, da eine Anfrage eigentlich eines dieser Projekte betreffen könnte statt dieses Repositorys.

**Direkt verwandt**
- **[HYDRA-UMC-LOCAL-TECHNICIAN](https://github.com/JuanenRac/HYDRA-UMC-LOCAL-TECHNICIAN)** — erzeugt die Belegpakete, die dieser Knoten liest; der Knoten prüft und speichert sie nur, ändert sie nie und führt nie aus, was darin steht.
- **[HYDRA-UMC-DEV-SERVER](https://github.com/JuanenRac/HYDRA-UMC-DEV-SERVER)** — reproduzierbarer Entwicklungshost mit dauerhafter Aufgabenwarteschlange; dieser Knoten ist der leichtere Ort, an dem ein Fehler untersucht und reproduziert wird, nachdem ein Mensch jeden Lauf freigegeben hat.
- **[HYDRA-UMC-OPS-AGENT](https://github.com/JuanenRac/HYDRA-UMC-OPS-AGENT)** — verwaltet den Lebenszyklus von Wartungsvorfällen (Belege, Diagnose, von Menschen freigegebene Änderung, Canary-Deployment, Verifikation); dieser Knoten liefert den Reproduktionsschritt und gibt nie eine Änderung frei.
- **[HYDRA-UMC-SDK](https://github.com/JuanenRac/HYDRA-UMC-SDK)** — die gemeinsamen Verträge: das Szenarioergebnis jedes Reproduktionslaufs folgt seinem Schema, und das SDK berechnet das Urteil über ein Vorher-nachher-Paar.

**Ebenfalls Teil des Ökosystems**

*Kern-Hardware & Plattform*
- **[HYDRA-UMC](https://github.com/JuanenRac/HYDRA-UMC)** — der Entwurf des Motherboards des Roboterarms: CM5-Host + Dual-Core-STM32H745, gedacht zur Koordination von bis zu 8 Werkzeugarmen über CAN-OTA/SPI-OTA (Firmware in einer frühen Phase; noch keine bestückte Platine).
- **[HYDRA-UMC-OS](https://github.com/JuanenRac/HYDRA-UMC-OS)** — reproduzierbare Raspberry-Pi-OS-Produktschicht für den CM5: schreibgeschützter Agent, validierte Konfiguration/Profile, WiFi-Ersteinrichtung.

*Kern-Backend & Clients*
- **[HYDRA-UMC-SERVER](https://github.com/JuanenRac/HYDRA-UMC-SERVER)** — das reale Headless-Backend (REST/WebSocket), mit dem jeder Steuerungsclient tatsächlich spricht.
- **[HYDRA-UMC-STUDIO](https://github.com/JuanenRac/HYDRA-UMC-STUDIO)** — Web-Steuerungs-Dashboard mit Echtzeit-3D-Visualisierung mehrerer Roboter.
- **[HYDRA-UMC-SUITE](https://github.com/JuanenRac/HYDRA-UMC-SUITE)** — Desktop-Schwarmleitstand (PySide6) für mehrere Server gleichzeitig.
- **[HYDRA-UMC-ANDROID-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-ANDROID-CONTROL)** — native Android-Steuerungs-App mit biometrischem Login und einer gekoppelten Wear-OS-Begleit-App.
- **[HYDRA-UMC-IOS-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-IOS-CONTROL)** — iOS/iPadOS-Steuerungs-App (Flutter) mit Echtzeit-WebSocket-Synchronisierung.
- **[HYDRA-UMC-DSI](https://github.com/JuanenRac/HYDRA-UMC-DSI)** — native Touch-UI für das eingebaute 7"-DSI-Touchscreen, direkt auf dem CM5 eingebettet.
- **[HYDRA-UMC-EDITOR-URDF](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-URDF)** — grafischer Desktop-URDF-Ersteller/-Editor, der fertige Modelle in STUDIOs eigenen Katalog überträgt.
- **[HYDRA-UMC-EDITOR-STL](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-STL)** — Desktop-STL-Modelleditor, der echte Teile im selben Modellkatalog transformiert/ersetzt/entfernt/hinzufügt, den auch HYDRA-UMC-EDITOR-URDF bearbeitet.
- **[HYDRA-UMC-BRIDGE-AMR](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-AMR)** — Koordinationsschranke für AGV-/AMR-Flotten über einen VDA-5050-MQTT-Publisher (nur gegen eine emulierte Flotte getestet).
- **[HYDRA-UMC-BRIDGE-CNC](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-CNC)** — High-Level-Koordinator für CNC-Zellen mit GRBL-Status-/Steuerbyte-Zugriff (nur gegen einen Emulator getestet).
- **[HYDRA-UMC-BRIDGE-DROIDS](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-DROIDS)** — Koordinationsschranke für laufende/humanoide Droiden, mit einem Boston-Dynamics-Spot-Befehlssender (nur gegen einen Emulator getestet).
- **[HYDRA-UMC-BRIDGE-LASER](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-LASER)** — Koordinator für Laserzellen, liest 3 Schlüssel-/Gehäuse-/Verriegelungs-GPIO-Signale (nur gegen einen simulierten Chip getestet; kann keinen Laser scharfschalten oder auslösen).
- **[HYDRA-UMC-BRIDGE-OPENPNP](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-OPENPNP)** — sicherer High-Level-Koordinator für den Leiterplattenfluss von OpenPnP Pick-and-Place.
- **[HYDRA-UMC-BRIDGE-PRINTER3D](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-PRINTER3D)** — sichere Koordinationsschranke für Moonraker/Klipper-3D-Drucker, mit echten gesicherten Job-Befehlen.
- **[HYDRA-UMC-BRIDGE-ROS2](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-ROS2)** — Koordinator mit einem träge importierten rclpy-ROS-2-Transport (noch nicht gegen eine ROS-2-Installation ausgeführt).
- **[HYDRA-UMC-BRIDGE-UAV](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-UAV)** — Koordinationsschranke für kameraausgestattete UAVs, mit einem MAVLink-Befehlssender (nur gegen einen Emulator getestet).

*URTC-Werkzeugplattform*
- **[URTC](https://github.com/JuanenRac/URTC)** — Firmware für die physische Universal-Robot-Tool-Controller-Platine, 25+ Werkzeugprofile über CAN-Bus.
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — Desktop-GUI-Flash-Tool für URTC-Platinen, CAN-OTA plus Full-Chip-SWD/JTAG.
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — Desktop-Live-CAN-Bus-Diagnosetool für URTC-Platinen, ein Panel pro Werkzeugprofil.
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — browserbasierte Alternative zu URTC-TESTER über die Web-Serial-API, ohne lokale Installation.
- **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** — Gateway vor dem CAN-Bus von URTC: Liste erlaubter Kennungen, Ratenbegrenzung und Sitzungsschlüssel; Software auf dem Computer getestet, noch nicht an einem echten Bus.

*Vision-KI-Knoten (Hailo-8)*
- **[HYDRA-UMC-VISION-NODE](https://github.com/JuanenRac/HYDRA-UMC-VISION-NODE)** — Integrationsknoten für die Hailo-8-Vision-Pipeline, mit einer echten stufenweisen Hardware-Bereitschaftsprüfung.
- **[HYDRA-UMC-DETECTION-HEF](https://github.com/JuanenRac/HYDRA-UMC-DETECTION-HEF)** — echte Registry für kompilierte Modelle mit Hailo-Architektur-/Prüfsummen-Safe-Load-Verifizierung.
- **[HYDRA-UMC-VISION-STREAMER](https://github.com/JuanenRac/HYDRA-UMC-VISION-STREAMER)** — echter GStreamer-Pipeline- + MediaMTX-Konfigurationsgenerator mit einer echten HailoRT-Integrationsschranke.
- **[HYDRA-UMC-VISUAL-SERVOING-API](https://github.com/JuanenRac/HYDRA-UMC-VISUAL-SERVOING-API)** — Position-Based-Visual-Servoing-Korrekturgesetz mit Freigabe abhängig vom Zonenstatus; noch keine Posenschätzung per Kamera.
- **[HYDRA-UMC-SAFETY-ZONES](https://github.com/JuanenRac/HYDRA-UMC-SAFETY-ZONES)** — v0-Logik für Zonenverletzung, Kalibrierungsaktualität und E-STOP-Anforderung, die Objektpositionen aus einer Datei nimmt; kein Detektor speist sie, und noch kein physischer E-STOP ist angeschlossen.

*Kognitiver KI-Knoten (Hailo-10)*
- **[HYDRA-UMC-COGNITIVE-NODE](https://github.com/JuanenRac/HYDRA-UMC-COGNITIVE-NODE)** — Integrationsknoten für die Hailo-10-Cognitive-Pipeline (LLM-/VLA-/Sprach-Orchestrierung).
- **[HYDRA-UMC-VLA-ENGINE](https://github.com/JuanenRac/HYDRA-UMC-VLA-ENGINE)** — echte Aktions-Token-Kodierung/-Dekodierung und Trajektoriengenerierung für ein Vision-Language-Action-Modell.
- **[HYDRA-UMC-VOICE-UI](https://github.com/JuanenRac/HYDRA-UMC-VOICE-UI)** — echtes Sprach-Frontend (VAD + Intent-Parser) mit einem begrenzten, bestätigungsgesicherten Watch-Relay - es hat keine Oberfläche für ausgehende Benachrichtigungen, daher veröffentlicht dieses Projekt seine Vorfallereignisse stattdessen im Broker des Ökosystems.
- **[HYDRA-UMC-SEMANTIC-PLANNER](https://github.com/JuanenRac/HYDRA-UMC-SEMANTIC-PLANNER)** — echte regelbasierte Aufgabenzerlegung und semantische Fehlerbehebung über MCU-Fehlercodes.
- **[HYDRA-UMC-DOCS-QA](https://github.com/JuanenRac/HYDRA-UMC-DOCS-QA)** — echte, nur auf der Standardbibliothek basierende TF-IDF-Dokumentensuche über die eigenen Markdown-Dokumente dieses Ökosystems.

*Orchestrierung & Schwarm*
- **[HYDRA-UMC-ORCHESTRATOR](https://github.com/JuanenRac/HYDRA-UMC-ORCHESTRATOR)** — Integrationsknoten mit einem echten gRPC/Protobuf-Health-Report-Vertrag und einer Missions-Zustandsmaschine.
- **[HYDRA-UMC-JOB-DISPATCHER](https://github.com/JuanenRac/HYDRA-UMC-JOB-DISPATCHER)** — echte prioritätsbasierte Job-Queue mit Deduplizierung, über eine echte HTTP-API.
- **[HYDRA-UMC-PATH-PLANNER-3D](https://github.com/JuanenRac/HYDRA-UMC-PATH-PLANNER-3D)** — echter RRT-basierter 3D-Pfadplaner mit echter Hindernis-/Arbeitsraum-Kollisionsvalidierung.
- **[HYDRA-UMC-SWARM-SYNC](https://github.com/JuanenRac/HYDRA-UMC-SWARM-SYNC)** — echte CRDT-LWW-Element-Map-Zustandssynchronisation, eigenschaftsgetestet auf Multi-Zellen-Konvergenz.
- **[HYDRA-UMC-NODE-HEALING](https://github.com/JuanenRac/HYDRA-UMC-NODE-HEALING)** — echter gRPC-basierter Flotten-Gesundheits-Watchdog mit eigenem Retry/Backoff und Identitätsabweichungs-Erkennung.

*Digitaler Zwilling & Simulation*
- **[HYDRA-UMC-TWIN](https://github.com/JuanenRac/HYDRA-UMC-TWIN)** — Integrationsknoten für die Digital-Twin-Engine, mit einem echten Versionskompatibilitäts-Sync-Vertrag.
- **[HYDRA-UMC-HIL-BRIDGE](https://github.com/JuanenRac/HYDRA-UMC-HIL-BRIDGE)** — Hardware-in-the-Loop-Router mit einer Software-Kollisionsverriegelung zwischen Simulation und echter Hardware (ohne echte Hardware getestet).
- **[HYDRA-UMC-PHYSICS-REPLICA](https://github.com/JuanenRac/HYDRA-UMC-PHYSICS-REPLICA)** — echte Vorwärtskinematik und Gelenkgrenzenvalidierung über eine echte URDF-Teilmenge.
- **[HYDRA-UMC-SYNTHETIC-DATA-GEN](https://github.com/JuanenRac/HYDRA-UMC-SYNTHETIC-DATA-GEN)** — echter prozeduraler 2D-Szenengenerator mit YOLO/COCO-Annotationsexport.

*Daten & Analytik*
- **[HYDRA-UMC-DATALAKE](https://github.com/JuanenRac/HYDRA-UMC-DATALAKE)** — echter sqlite3-gestützter Zeitreihenspeicher mit einer echten Ingest-/Abfrage-HTTP-API.
- **[HYDRA-UMC-ANOMALY-DETECTOR](https://github.com/JuanenRac/HYDRA-UMC-ANOMALY-DETECTOR)** — echter FFT- + statistischer Basislinien-Anomaliedetektor mit Drift-Überwachung.
- **[HYDRA-UMC-PRODUCTION-REPORTS](https://github.com/JuanenRac/HYDRA-UMC-PRODUCTION-REPORTS)** — echte OEE-/Verfügbarkeitsberechnung über den DATALAKE-Verlauf, mit reproduzierbarem CSV-Export.
- **[HYDRA-UMC-TELEMETRY-COLLECTOR](https://github.com/JuanenRac/HYDRA-UMC-TELEMETRY-COLLECTOR)** — echte CAN/WebSocket-Ingestion-Pipeline in DATALAKE, mit Sequenz-Deduplizierung.

*Industrie-Gateway*
- **[HYDRA-UMC-GATEWAY-INDUSTRIAL](https://github.com/JuanenRac/HYDRA-UMC-GATEWAY-INDUSTRIAL)** — Integrationsknoten, der zu Industrieprotokollen weiterleitet, mit einer echten Befehls-Allowlist-/Backpressure-Schicht.
- **[HYDRA-UMC-OPCUA-SERVER](https://github.com/JuanenRac/HYDRA-UMC-OPCUA-SERVER)** — echter OPC-UA-Adressraum, verifiziert mit einer echten Binärprotokoll-Client-Session.
- **[HYDRA-UMC-MQTT-BROKER](https://github.com/JuanenRac/HYDRA-UMC-MQTT-BROKER)** — echter MQTT-Broker mit optionaler Pro-Client-Authentifizierung und Topic-ACLs.
- **[HYDRA-UMC-MTCONNECT-ADAPTER](https://github.com/JuanenRac/HYDRA-UMC-MTCONNECT-ADAPTER)** — echte MTConnect-`/probe`- und `/current`-XML-Endpunkte mit Degraded-Mode-Ausgabe.

*Ergänzende Tools*
- **[HYDRA-UMC-DASHBOARD-AI](https://github.com/JuanenRac/HYDRA-UMC-DASHBOARD-AI)** — Smart-Summaries- und Anomaly-Highlighting-Panels über DATALAKE/ANOMALY-DETECTOR, mit einem ehrlichen statistischen Fallback.
- **[HYDRA-UMC-TOOL-CLI](https://github.com/JuanenRac/HYDRA-UMC-TOOL-CLI)** — Flotten-CLI mit einem echten, stabilen Exit-Code-Vertrag, ein echter Live-Client der eigenen API von HYDRA-UMC-SERVER.
- **[HYDRA-UMC-WATCH](https://github.com/JuanenRac/HYDRA-UMC-WATCH)** — WearOS-Begleit-App mit haptischen Alarmmustern und einem Sprach-Relay zum gekoppelten Telefon (noch nicht auf einer physischen Uhr ausgeführt).
- **[HYDRA-UMC-CONNECTOR-HUB](https://github.com/JuanenRac/HYDRA-UMC-CONNECTOR-HUB)** — externer Adapter-Fähigkeitskatalog, per Design nur GET.
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — Firmware für ein Platinenmontagegestell mit echter Werkzeug-ID-Dekodierung und Smart-Idle-Vorheizlogik.
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — Firmware plus ein echter Python-Vision-Begleiter für einen Thermal-/RGB-Inspektionswerkzeugkopf.
- **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** — administratives Desktop-Tool, das jedes Repository in diesem Ökosystem entdeckt, klont und aktualisiert.
- **[HYDRA-UMC-OS-REBUILDER](https://github.com/JuanenRac/HYDRA-UMC-OS-REBUILDER)** — baut ein frisches CM5-Image aus dem Quellcode, ein weiterer Geschwisterprojekt aus "Ecosystem Operations".

## 📚 Dokumentation

Hier steht mehr:

* **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — die Teile, der Ablauf eines Vorfalls und wo der Knoten aufhört.
* **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** — jeder Schalter und jeder einstellbare Wert der Konfigurationsdatei.
* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — jeder Befehl, die Exit-Codes und die Form eines Rezepts.
* **[docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)** — die Regeln, die der Knoten einhält, und was nicht abgedeckt ist.
* **[docs/PANEL_CONTRACT.md](docs/PANEL_CONTRACT.md)** — das Statusdokument für Dashboards und Studios.
* [Sicherheitsgrundlage des Ökosystems](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md)
* [Bedrohungsmodell des Ökosystems](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md)
* [Änderungsprotokoll dieses Repositorys](CHANGELOG.md)
* [Lizenz dieses Repositorys](LICENSE.md)

## 🤝 Mitwirken und Community

* Führe vor einem Pull Request `HYDRA_UMC_CI=1 py -3 tools/ci_validate.py` (oder `HYDRA_UMC_CI=1 python3 tools/ci_validate.py`) aus: Es muss `CI_VALIDATION=PASS` ausgeben. Führe dafür nicht `build.sh` oder `build.bat` aus; Bauen ist keine Prüfung.
* Die acht READMEs entstehen aus einer einzigen Quelle in HYDRA-UMC-DOCS; bearbeite sie nicht von Hand. Ändere die Quelle und schreibe sie mit `tools/make_readmes.py` neu.
* Behaupte in einer README nichts, was nicht gelaufen ist: Schreibe „simuliert“ oder „nicht auf Hardware erprobt“, wo das stimmt.
* Siehe [CONTRIBUTING.md](CONTRIBUTING.md), den [Verhaltenskodex](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md) und [SUPPORT.md](SUPPORT.md).

## 👤 AUTOR

**JuanenRac (Electro Hobby 3D)** · electrohobby3d@gmail.com

## 📜 LIZENZ

GPL-3.0-or-later - [LICENSE](LICENSE).
