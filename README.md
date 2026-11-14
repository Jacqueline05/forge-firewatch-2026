# Forge FireWatch — Hackathon Prototype

Forge FireWatch is designed for international fire monitoring. This prototype
uses illustrative sample detections from regions across several continents.
Use its tabs to view the map, a short satellite-signal summary, or submit a demo
ground report.

## Run it

With the prototype dependencies installed:

```powershell
streamlit run app.py
```

When this folder is inside the main Forge FireWatch repository, run
`streamlit run prototype/app.py` instead.

No login, NASA FIRMS key or live network data is required for the local demo.

The **Situation** tab shows the map and key counts. **Investigate** shows the
latest satellite signals and matched pairs. **Ground report** keeps sample
reports in the current Streamlit session only.

## Publish it publicly

To keep the prototype available when your computer is off, deploy it to
[Streamlit Community Cloud](https://share.streamlit.io/) from this GitHub
repository:

1. Sign in to Streamlit Community Cloud with GitHub.
2. Choose **Create app**, then select `Jacqueline05/forge-firewatch-2026`,
   branch `main`, and `app.py`.
3. Deploy the app. Streamlit will build it using `requirements.txt` and provide
   a public `*.streamlit.app` URL that you can share.

Once deployed, the app and its bundled demo data run in the cloud. Demo reports
are temporary and are not saved or sent to responders.

## Demo-data notice

The global satellite records are fictional, illustrative examples—not live
detections. The bundled peat polygons only illustrate Borneo and are not used
for scoring in this global demo. It is not a live monitoring or
emergency-response tool.
