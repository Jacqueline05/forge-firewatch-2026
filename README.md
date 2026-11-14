# Borneo FireWatch — Hackathon Prototype

This is a separate, presentation-focused prototype built from the current
FireWatch MVP. It reuses the repository's tested hotspot matching, fire-area
grouping and attention-scoring logic, while keeping this demo's report form
isolated from the production feedback file.

## Run it

With the prototype dependencies installed:

```powershell
streamlit run app.py
```

When this folder is inside the main FireWatch repository, run
`streamlit run prototype/app.py` instead.

No login, NASA FIRMS key or live network data is required. Use the sidebar's
three-step demo flow:

1. **Situation** — review priority areas and the overview map.
2. **Investigate** — compare satellite detections and match status.
3. **Ground report** — submit an example report stored only in the current
   Streamlit session.

## Demo-data notice

The bundled satellite records are fictional and the peat polygons are
illustrative, not authoritative boundaries. The prototype is not a live
monitoring or emergency-response tool. Ground reports are not persisted or
sent to responders.
