# StoryMaker

**Interaktiva berättelser med AI och piktogram för läsförståelseträning**

StoryMaker är en GTK4/Adwaita-app som skapar interaktiva, grenade berättelser för barn 6-12 år. Appen använder AI (OpenAI/Anthropic) för att generera åldersanpassade berättelser med beslutspunkter, visuellt stöd via ARASAAC-piktogram, och läsförståelsequiz efter varje berättelse.

## Funktioner

- **Interaktiva berättelser** - Barnet väljer vägar genom berättelsen med 3 valalternativ per kapitel
- **AI-genererat innehåll** - Berättelser skapas dynamiskt med OpenAI eller Anthropic, anpassade efter barnets ålder och intressen
- **Demo-läge** - Fungerar utan API-nyckel med inbyggda berättelser
- **Piktogram-stöd** - ARASAAC-piktogram och emoji-fallback för visuell förståelse
- **Läsförståelse-quiz** - Automatiskt genererade frågor efter varje berättelse
- **Personalisering** - Barnets namn, ålder, avatar och intressen påverkar berättelserna
- **Text-till-tal (TTS)** - Uppläsning via espeak-ng eller macOS `say`
- **Framstegsföljning** - Statistik över lästa ord, kapitel, berättelser och quizresultat
- **Svenska & engelska** - Fullt lokaliserad med gettext

## Skärmdumpar

Appen använder GNOME Adwaita-design med barnanpassad typografi och färgglada valalternativ.

## Installation

### Krav

- Python 3.10+
- GTK4 och libadwaita
- PyGObject

### Ubuntu/Debian

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gdkpixbuf-2.0

# Valfritt: TTS-stöd
sudo apt install espeak-ng

# Valfritt: AI-providers
pip install openai        # För OpenAI
pip install anthropic     # För Anthropic Claude
```

### Fedora

```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-cairo

# Valfritt: TTS-stöd
sudo dnf install espeak-ng
```

### Arch Linux

```bash
sudo pacman -S python-gobject gtk4 libadwaita python-cairo

# Valfritt
sudo pacman -S espeak-ng
```

### macOS (Homebrew)

```bash
brew install pygobject3 gtk4 libadwaita

# TTS fungerar automatiskt via macOS "say"
```

### Installation av appen

```bash
git clone https://github.com/yeager/StoryMaker.git
cd StoryMaker
pip install -e .

# Eller kör direkt:
python -m storymaker
```

## Användning

### Starta appen

```bash
storymaker
# eller
python -m storymaker
```

### Första gången

1. Klicka **"➕ Ny läsare"** för att skapa en profil
2. Fyll i namn, ålder och välj intressen
3. Klicka **"Spela"** på din profil
4. Välj ett tema eller skriv ditt eget
5. Läs berättelsen och välj vägar!
6. Gör quiz efter berättelsen

### AI-konfiguration

Appen fungerar i demo-läge utan API-nyckel. För AI-genererade berättelser:

1. Öppna **Inställningar** (kugghjulet)
2. Välj AI-tjänst (OpenAI eller Anthropic)
3. Ange din API-nyckel
4. Spara

API-nyckeln lagras lokalt i `~/.config/storymaker/settings.json` med begränsade filrättigheter.

## Projektstruktur

```
StoryMaker/
├── storymaker/
│   ├── __main__.py          # Startpunkt
│   ├── application.py       # Adw.Application
│   ├── config.py             # Konfiguration
│   ├── engine/
│   │   └── story_engine.py  # Berättelselogik
│   ├── models/               # Datamodeller
│   │   ├── child_profile.py
│   │   ├── story.py
│   │   ├── quiz.py
│   │   └── progress.py
│   ├── services/
│   │   ├── ai_provider.py   # AI-integration (OpenAI/Anthropic/Demo)
│   │   ├── arasaac_client.py # Piktogram-API
│   │   └── tts_service.py   # Text-till-tal
│   ├── storage/
│   │   └── database.py      # SQLite-databas
│   ├── ui/                    # GTK4-vyer
│   │   ├── window.py
│   │   ├── welcome_view.py
│   │   ├── story_view.py
│   │   ├── quiz_view.py
│   │   ├── profile_view.py
│   │   ├── progress_view.py
│   │   └── settings_view.py
│   └── utils/
│       ├── i18n.py           # Lokalisering
│       └── async_helper.py   # Trådhantering
├── data/
│   ├── org.github.storymaker.desktop
│   └── icons/
├── po/                        # Översättningar
│   ├── storymaker.pot
│   ├── sv.po
│   └── en.po
├── setup.py
├── requirements.txt
└── README.md
```

## Teknisk arkitektur

- **UI**: GTK4 + libadwaita med `Adw.NavigationView` för sidnavigering
- **Berättelse-engine**: Trädstruktur med noder och val, JSON-serialiserat
- **AI**: Abstraktionslager med OpenAI/Anthropic/Demo-providers
- **Piktogram**: ARASAAC REST API med lokal disk-cache, emoji-fallback
- **Databas**: SQLite via Python stdlib
- **TTS**: espeak-ng (Linux) / say (macOS)
- **i18n**: GNU gettext med .pot/.po-filer
- **Asynkronitet**: Bakgrundstrådar + GLib.idle_add för UI-uppdatering

## Bidra

1. Forka repot
2. Skapa en feature-branch
3. Skicka en pull request

## Licens

GPL-3.0
