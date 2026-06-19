# Frontend

React interface for the synthetic social agent chat, red-teaming, and
computational-analysis prototype.

```bash
npm install
npm start
```

The app loads 30 cached persona profiles from the backend, lets the user choose
between guardrailed and lightweight chat before opening a conversation, includes
the integrated red-team setup/review interface, and exposes a Computational
analysis tab for saved final-results JSON reports.

## Main Scripts

- `src/App.js`: top-level shell for the Chat, Red-teaming, and Computational analysis tabs plus the global back button.
- `src/config/api.js`: backend and red-team service URL configuration.
- `src/features/personas/`: persona loading, profile selection, and pre-chat pipeline controls.
- `src/features/analysis/`: saved final-report browser, analysis generation, plot previews, per-plot PNG downloads, dataset deletion, and dataset JSON downloads.
- `src/modules/persona_chat_modules/`: chat popup, message bubbles, waiting state, and analysis hover windows.
- `src/features/redTeam/`: red-team run setup, profile/method selection, saved-report loading, polling, prompt editing, finalization, and local score utilities.
- `src/modules/red_team_modules/redTeamPanel.js`: answer review panel for paired lightweight/guardrailed results and embedded generated analysis previews.

## Runtime Tabs

- **Chat:** persona list, pipeline selector, chat popup, and hover inspection
  panels for user-message signals and final response validation metadata.
- **Red-teaming:** manual profile selection, method selection, full-analysis
  stack execution, progress display, answer review, optional score overrides,
  saved report loading, and final JSON/PDF downloads.
- **Computational analysis:** list finalized red-team JSON datasets, select one
  dataset, regenerate reproducible analysis artifacts, preview thesis figures,
  download each plot as PNG at a selected size, download the full JSON dataset,
  and remove a dataset with its paired PDF.

All first-party frontend scripts include a short top-of-file comment describing
their role. The comments are intentionally concise so the UI code remains easy
to scan.
