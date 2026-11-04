# Role

You are an impartial evaluator assessing the documentation quality of a software installation guide.

# Task

Evaluate the supplied installation guide using the criteria and rating scale
below. For each criterion, assign one score from 1 to 5 and provide a brief
reason for your score.

# Evaluation instructions

- Review the complete installation guide before assigning any scores.
- Use only information contained in the installation guide as evidence.

# Criteria and rating scale

```json
{
  "rating_scale": [
    {
      "score": 1,
      "label": "Very poor"
    },
    {
      "score": 2,
      "label": "Poor"
    },
    {
      "score": 3,
      "label": "Adequate"
    },
    {
      "score": 4,
      "label": "Good"
    },
    {
      "score": 5,
      "label": "Excellent"
    }
  ],
  "criteria": {
    "completeness": "How would you rate the guide's coverage of the information needed to install, configure where required, and verify the software?",
    "structure": "Is the installation guide arranged so that the user can find what is needed and follow the installation process in the required order?",
    "clarity": "Are instructions, commands, prerequisites, configuration values, and expected outcomes stated precisely and without ambiguity?",
    "understandability": "How easy was it to understand the installation or setup steps? Consider whether the guide explained the technical terms and concepts or required you to know them beforehand."
  }
}
```

# Evaluation procedure

For each criterion:

1. Read the criterion name and its evaluation question.
2. Determine how well the guide meets the criterion described by the question.
3. Select one score from 1 to 5 using the rating scale.
4. Provide a brief reason for the score using evidence from the guide.

# Installation guide

## Konfiguration

Sie können einige Standardeinstellungen von [QuattroMap](https://kreis-viersen.usercontent.opencode.de/quattromap) festlegen, indem Sie diese in der [config.json](./src/config.json) bearbeiten:


|Parameter|Erklärung|Beispiel|
|:---|:---|:---|
|"center"|Gibt die Zentrumskoordinate des Kartenfensters beim Starten an. Angabe geographisch mit Längen- und Breitenangabe in EPSG 4326.|"center": [6.391263, 51.258812]|
|"zoom"|Definiert die Zoomstufe beim Start. Wertebereich: 0 (fern) - 22 (nah)|"zoom": 16|
|"maps"|Optionale Angabe über die Anzahl der Kartenfenster. Mögliche Werte: 1, 2, 3, 4; Standardwert: 4| "maps": 2|
|"crosshair"| Optionale Definition der Fadenkreuzfarbe. Mögliche Werte: black, red, orange, yellow, green, blue, pink; Standardwert: black|"crosshair": "red"|
|"map_x": {"layer": `layername`} *Optional*: "overlay": `layername`, "overlay_opacity": `opacity-value`, }|Voreinstellung der dargestellten Dienste des Kartenfensters x (1-4) beim Starten der QuattroMap. `layer` enthält einen Namen eines Dienstes, die unter "layer" definiert sind. `overlay` enthält einen Namen eines Dienstes, der als Abdeckungslayer dient und muss nur angegeben werden, wenn ein Abdeckungslayer verwendet werden soll. `overlay_opacity` definiert die Deckkraft des Abdeckungslayers. Mögliche Werte: 0 (transparent) - 1 (opak); Standardwert: 0.5| "map_1": {"layer": "NRW Luftbild Farbe", "overlay": "NRW Schummerung", "overlay_opacity": 0.4}|
|"layer": [ .. ]|Enthält die Definitionen der wählbaren Dienste im Dropdown Menü||
|"name"|Name des Dienstes, der im Dropdown Menü und beim Klick auf den Info-Button erscheint.|"name": "NRW Alkis TN"|
|"attribution"|Attribution zur Beschreibung der verwendeten Dienste, die über den Info-Button dargestellt wird. HTML-Tags können verwendet werden.|"attribution": "Land NRW (2021) Deutschland ? Zero ? Version 2.0 (`<a target='_blank' rel='noopener noreferrer' href='https://www.govdata.de/dl-de/zero-2-0'>www.govdata.de/dl-de/zero-2-0</a>`)"|
|"url"|URL des WMS 1.3.0 Dienstes oder OpenStreetMap XYZ-Tiles|"url": "`https://www.wms.nrw.de/geobasis/wms_nw_alkis`"|
|"layer"|Darzustellende Layer des Dienstes. Mehrere Layer werden mit Komma getrennt.|"layer": "nutzungsarten,flurstuecke"|
|"format"| Abzurufendes Rasterformat (`png` oder `jpeg`) der Kacheln. Da png Transparenz ermöglicht, ist png zu empfehlen. Jedoch können nicht alle Dienste png liefern.|"format": "png"|
|"category"|Begriff zur Kategorisierung der Dienste im Dropdown-Menü.|"category": "GeoBasis NRW"|
|"onlyOverlay"|Mit diesem optionalen Parameter lässt sich der entsprechende Dienst nur als Overlay verwenden.|"onlyOverlay": true|
|"style"|Optionaler Parameter zur Auswahl eines bestimmten Stils. Stile können von Diensten angeboten werden.|"style": "Farbe"|
|"compactAttribution"|Mit diesem optionalen Parameter lässt sich festlegen, ob die Attribution mit dem Layernamen bei Auswahl des Layers ausgeklappt (`false`) oder eingeklappt ist (`true` = Standardwert).|"compactAttribution": "false"|

## Develop

```bash
# clone the repository
git clone https://github.com/kreis-viersen/quattromap/
cd quattromap
```
Install the deps, start the dev server and open the web browser on `http://localhost:8080/`.

```bash
# install dependencies
npm install
# start dev server
npm start
```

The build process will watch for changes to the filesystem, rebuild and autoreload QuattroMap. However note this from the [webpack-dev-server docs](https://webpack.js.org/configuration/dev-server/):

> webpack uses the file system to get notified of file changes. In some cases this does not work. For example, when using Network File System (NFS). Vagrant also has a lot of problems with this. In these cases, use polling. ([snippet source](https://webpack.js.org/configuration/dev-server/#devserverwatchoptions-))

```bash
# build the app
npm run build
```
Once the build is finished, you'll find it at `dist/`.

```bash
# publish files to a gh-pages branch on GitHub
npm run deploy
```
