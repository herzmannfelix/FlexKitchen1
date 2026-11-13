KITCHENFLEX – VORBEREITETES ONLINE-BACKEND
==========================================

Was dieses Paket bereitstellt
- FastAPI-Server für /api/health und /api/import-video
- Dockerfile mit FFmpeg, damit die Audiospur verarbeitet werden kann
- Render Blueprint (render.yaml), Region Frankfurt
- KITCHENFLEX-Oberfläche (index.html) mit Feld für die Backend-Basisadresse

WICHTIG: Der Server ist vorbereitet, aber noch NICHT online geschaltet.
Dazu brauchst du einen Hosting-Account und deinen eigenen OpenAI-API-Schlüssel.
Der API-Schlüssel gehört ausschließlich in die Server-Umgebungsvariable
OPENAI_API_KEY – niemals in die App, in index.html oder in eine öffentliche Datei.

EINRICHTUNG MIT RENDER (empfohlener einfacher Weg)
-------------------------------------------------
1. Lege einen Account bei https://render.com an.
2. Lade den Inhalt dieses Ordners in ein privates GitHub-Repository hoch.
   (Bei GitHub ein neues privates Repository anlegen und die Dateien hochladen.)
3. Öffne Render und wähle „New“ → „Blueprint“.
4. Verbinde das GitHub-Repository mit Render.
5. Render erkennt render.yaml und zeigt den Dienst „kitchenflex-api“ an.
6. Beim Feld OPENAI_API_KEY trägst du deinen API-Schlüssel ein. Render erzeugt automatisch einen privaten KITCHENFLEX_ACCESS_TOKEN.
7. Starte das Deployment und warte, bis der Dienst „Live“ ist.
8. Render zeigt dir eine Adresse ähnlich:
   https://kitchenflex-api-xxxx.onrender.com
9. Teste im Browser:
   https://DEINE-ADRESSE/api/health
   Erwartete Antwort: {"ok":true,"service":"KITCHENFLEX"}
10. Öffne im Render-Dienst die Environment-Variablen und kopiere den Wert von
    KITCHENFLEX_ACCESS_TOKEN. Halte ihn privat.
11. Öffne KITCHENFLEX, gehe zum KI-Rezept-Import und trage als Backend-Adresse
    NUR die Basisadresse ein, z. B. https://kitchenflex-api-xxxx.onrender.com.
    NICHT /api/health und NICHT /api/import-video anhängen. Trage darunter den
    KITCHENFLEX_ACCESS_TOKEN ein und drücke „Speichern“.
12. Drücke „Verbindung testen“. Danach kannst du „Rezept extrahieren“ testen.

OPENAI-API-SCHLÜSSEL
--------------------
Den Schlüssel erstellst du im OpenAI Platform Dashboard:
https://platform.openai.com/api-keys
Die API-Nutzung wird separat nach Verbrauch abgerechnet. Ein ChatGPT-Abo
enthält nicht automatisch API-Guthaben. Hinterlege ein Ausgabenlimit/Budget.

KOSTEN / HOSTING
----------------
Das Render-Blueprint ist auf einen bezahlten Starter-Webdienst gesetzt, weil
Video-Downloads und Transkription Arbeitsspeicher und Laufzeit benötigen.
Hosting und OpenAI-API-Verbrauch können Kosten verursachen. Preise bitte vor
Bestätigung direkt bei Render und OpenAI prüfen. Bei einem kostenlosen
Hosting-Tarif kann der Dienst schlafen gehen oder bei langen Videojobs abbrechen.

WICHTIGE GRENZEN
----------------
- Das Backend kann nur Videos verarbeiten, die der Server rechtmäßig und ohne
  Login-/DRM-Umgehung abrufen kann. Plattformen können Downloads blockieren.
- Private, altersbeschränkte, gelöschte oder anderweitig gesperrte Videos gehen
  möglicherweise nicht. Bei Bedarf das Transkript/Untertitel in der App nutzen.
- Der Import-Endpunkt ist mit einem privaten Bearer-Token geschützt. Bewahre
  den Token sicher auf und teile ihn nicht. Für öffentlichen Betrieb sollten
  zusätzlich Rate-Limits und Nutzungsüberwachung ergänzt werden.
- Die App speichert Rezepte lokal auf dem Gerät. Dieses Backend synchronisiert
  keine Rezeptbibliothek zwischen Geräten.

LOKALER TEST (WINDOWS)
---------------------
Python 3.11+ und FFmpeg installieren. Dann im Ordner:
  pip install -r requirements.txt
  set OPENAI_API_KEY=dein_api_schluessel
  uvicorn server:app --host 127.0.0.1 --port 8000
Als Backend-Adresse in KITCHENFLEX dann:
  http://127.0.0.1:8000
Für Android außerhalb desselben Rechners ist localhost nicht erreichbar;
verwende dafür die veröffentlichte HTTPS-Adresse des Hosters.
