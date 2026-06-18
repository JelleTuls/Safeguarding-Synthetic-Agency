# Frontend

React interface for the synthetic social agent chat and red-teaming prototype.

```bash
npm install
npm start
```

The app loads 30 cached persona profiles from the backend, lets the user choose
between guardrailed and lightweight chat before opening a conversation, and
includes the integrated red-team setup/review interface.

## Main Scripts

- `src/App.js`: top-level shell for the Chat and Red-teaming tabs.
- `src/config/api.js`: backend and red-team service URL configuration.
- `src/features/personas/`: persona loading, profile selection, and pre-chat pipeline controls.
- `src/modules/persona_chat_modules/`: chat popup, message bubbles, waiting state, and analysis hover windows.
- `src/features/redTeam/`: red-team run setup, polling, prompt editing, and local score utilities.
- `src/modules/red_team_modules/redTeamPanel.js`: answer review panel for paired lightweight/guardrailed results.

All first-party frontend scripts include a short top-of-file comment describing
their role. The comments are intentionally concise so the UI code remains easy
to scan.
