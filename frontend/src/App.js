import { useCallback, useEffect, useState } from 'react';

import './App.css';
import PersonaChat from './modules/persona_chat_modules/personaChat';
import RedTeamPanel from './modules/red_team_modules/redTeamPanel';
import arrowBackIcon from './assets/images/Icon_ArrowBack.png';
import settingsIcon from './assets/images/Icon_Settings.png';

const backendApiUrl = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const redTeamApiUrl = (process.env.REACT_APP_RED_TEAM_API_URL || 'http://127.0.0.1:8010').replace(/\/$/, '');
const redTeamMethods = [
  ['PBAR', 'Prompt-Based Attack Resistance'],
  ['TBAR', 'Token-Based Attack Resistance'],
  ['EB', 'Epistemic Boundary'],
  ['SFAM', 'Subjective Framing and Authority Modulation'],
  ['SC', 'Stylometric Consistency'],
  ['PG', 'Persuasive Governance'],
];

function normalizePromptSettings(prompts = []) {
  return prompts.map((prompt) => ({
    ...prompt,
    original_expected_answer: prompt.expected_answer || '',
    expected_answer: prompt.expected_answer || '',
  }));
}

function recomputeRedTeamScores(cases = []) {
  const methods = {};
  let pending = 0;
  let reviewed = 0;

  cases.forEach((caseItem) => {
    const review = caseItem.human_review || null;
    if (caseItem.needs_human_review && !review) {
      pending += 1;
    }
    if (review) {
      reviewed += 1;
    }
    const score = Number(review?.score ?? caseItem.automated_score ?? 0);
    if (!methods[caseItem.method]) {
      methods[caseItem.method] = [];
    }
    methods[caseItem.method].push(score);
  });

  const methodScores = Object.fromEntries(
    Object.entries(methods)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([method, values]) => [
        method,
        values.length ? Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(3)) : 0,
      ])
  );
  const values = Object.values(methodScores);
  const overallScore = values.length
    ? Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(3))
    : 0;

  return {
    overall_score: overallScore,
    method_scores: methodScores,
    pending_human_reviews: pending,
    completed_human_reviews: reviewed,
    is_final: pending === 0,
  };
}

function formatPercent(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return '0%';
  }
  return `${Math.round(Number(value) * 100)}%`;
}

function App() {
  const [personas, setPersonas] = useState([]);
  const [activePersona, setActivePersona] = useState(null);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetCount, setTargetCount] = useState(30);
  const [isComplete, setIsComplete] = useState(false);
  const [redTeamRun, setRedTeamRun] = useState(null);
  const [redTeamReviewItems, setRedTeamReviewItems] = useState([]);
  const [redTeamError, setRedTeamError] = useState(null);
  const [selectedRedTeamMethods, setSelectedRedTeamMethods] = useState(redTeamMethods.map(([method]) => method));
  const [redTeamTargetMode, setRedTeamTargetMode] = useState('guardrailed');
  const [redTeamPromptSettings, setRedTeamPromptSettings] = useState([]);
  const [redTeamPromptSettingsStatus, setRedTeamPromptSettingsStatus] = useState('idle');
  const [selectedPromptId, setSelectedPromptId] = useState(null);
  const [redTeamSettingsOpen, setRedTeamSettingsOpen] = useState(false);

  const loadRedTeamRun = useCallback(async (runId) => {
    if (!runId) {
      return;
    }
    const runResponse = await fetch(`${redTeamApiUrl}/api/runs/${runId}`);
    if (!runResponse.ok) {
      throw new Error(`Red-team run request failed with status ${runResponse.status}`);
    }
    const runPayload = await runResponse.json();
    setRedTeamRun(runPayload);

    if (['completed', 'cancelled', 'error'].includes(runPayload.status)) {
      const reviewResponse = await fetch(`${redTeamApiUrl}/api/runs/${runId}/review-items`);
      if (reviewResponse.ok) {
        const reviewPayload = await reviewResponse.json();
        setRedTeamReviewItems(reviewPayload.cases || []);
      }
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadPersonas() {
      try {
        setLoading(true);
        const response = await fetch(`${backendApiUrl}/api/chat/personas?country=netherlands&limit=30`);

        if (!response.ok) {
          throw new Error(`Persona request failed with status ${response.status}`);
        }

        const payload = await response.json();
        if (!cancelled) {
          setPersonas(payload.personas ?? []);
          setSelectedPersona((current) => current || payload.personas?.[0] || null);
          setTargetCount(payload.target_count ?? 30);
          setIsComplete(Boolean(payload.is_complete));
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPersonas();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const status = redTeamRun?.status;
    if (!redTeamRun?.run_id || !['created', 'running', 'cancelling'].includes(status)) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      loadRedTeamRun(redTeamRun.run_id).catch((err) => setRedTeamError(err.message));
    }, 1600);

    return () => window.clearInterval(intervalId);
  }, [loadRedTeamRun, redTeamRun?.run_id, redTeamRun?.status]);

  const ensureRedTeamService = useCallback(async () => {
    const serviceResponse = await fetch(`${backendApiUrl}/api/red-team/service/start`, {
      method: 'POST',
    });
    if (!serviceResponse.ok) {
      throw new Error(`Could not start red-team service: ${serviceResponse.status}`);
    }
    const servicePayload = await serviceResponse.json();
    if (!servicePayload.ready) {
      throw new Error('Red-team service did not become ready.');
    }
    return servicePayload;
  }, []);

  const loadRedTeamPromptSettings = useCallback(async () => {
    try {
      setRedTeamPromptSettingsStatus('loading');
      setRedTeamError(null);
      await ensureRedTeamService();
      const response = await fetch(`${redTeamApiUrl}/api/prompt-settings`);
      if (!response.ok) {
        throw new Error(`Could not load red-team prompt settings: ${response.status}`);
      }
      const payload = await response.json();
      const prompts = normalizePromptSettings(payload.prompts || []);
      setRedTeamPromptSettings(prompts);
      setSelectedPromptId((current) => current || prompts[0]?.prompt_id || null);
      setRedTeamPromptSettingsStatus('ready');
      return prompts;
    } catch (err) {
      setRedTeamPromptSettingsStatus('error');
      setRedTeamError(err.message);
      return [];
    }
  }, [ensureRedTeamService]);

  useEffect(() => {
    if (activeTab === 'red-team' && redTeamPromptSettingsStatus === 'idle') {
      loadRedTeamPromptSettings();
    }
  }, [activeTab, loadRedTeamPromptSettings, redTeamPromptSettingsStatus]);

  async function startRedTeamRun() {
    if (selectedRedTeamMethods.length === 0) {
      setRedTeamError('Select at least one red-team method.');
      return;
    }
    const promptSettingsForRun = redTeamPromptSettingsStatus === 'ready'
      ? redTeamPromptSettings
      : await loadRedTeamPromptSettings();
    const methodsToRun = selectedRedTeamMethods;
    const totalCases = methodsToRun.length * 10;
    const expectedAnswerOverrides = Object.fromEntries(
      promptSettingsForRun
        .filter((prompt) => methodsToRun.includes(prompt.method))
        .filter((prompt) => prompt.expected_answer.trim() !== prompt.original_expected_answer.trim())
        .map((prompt) => [prompt.prompt_id, prompt.expected_answer.trim()])
    );
    setActiveTab('red-team');
    setRedTeamError(null);
    setRedTeamReviewItems([]);
    setRedTeamRun({
      status: 'starting',
      final_scores: {},
      progress: {
        total_cases: totalCases,
        completed_cases: 0,
        current_step: 'starting standalone red-team service',
      },
    });
    try {
      await ensureRedTeamService();

      const response = await fetch(`${redTeamApiUrl}/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backend_url: backendApiUrl,
          country: 'netherlands',
          selected_methods: methodsToRun,
          target_mode: redTeamTargetMode,
          expected_answer_overrides: expectedAnswerOverrides,
        }),
      });
      if (!response.ok) {
        throw new Error(`Could not start red-team run: ${response.status}`);
      }
      const payload = await response.json();
      setRedTeamRun({
        ...payload,
        progress: {
          total_cases: totalCases,
          completed_cases: 0,
          current_step: 'queued in red-team service',
        },
      });
      await loadRedTeamRun(payload.run_id);
    } catch (err) {
      setRedTeamError(err.message);
      setRedTeamRun({
        status: 'error',
        final_scores: {},
        progress: { current_step: 'red-team service unavailable' },
      });
    }
  }

  async function cancelRedTeamRun() {
    if (!redTeamRun?.run_id) {
      return;
    }
    try {
      const response = await fetch(`${redTeamApiUrl}/api/runs/${redTeamRun.run_id}/cancel`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Could not cancel red-team run: ${response.status}`);
      }
      await loadRedTeamRun(redTeamRun.run_id);
    } catch (err) {
      setRedTeamError(err.message);
    }
  }

  const submitHumanReview = useCallback(async (caseId, review) => {
    if (!redTeamRun?.run_id) {
      return;
    }
    const runId = redTeamRun.run_id;
    const boundedReview = {
      ...review,
      score: Math.max(0, Math.min(1, Number(review.score))),
    };
    setRedTeamReviewItems((current) => current.map((item) => (
      item.case_id === caseId
        ? { ...item, human_review: { score: boundedReview.score, passed: boundedReview.score >= 0.5, notes: boundedReview.notes || '' } }
        : item
    )));
    setRedTeamRun((current) => {
      if (!current?.cases) {
        return current;
      }
      const updatedCases = current.cases.map((item) => (
        item.case_id === caseId
          ? { ...item, human_review: { score: boundedReview.score, passed: boundedReview.score >= 0.5, notes: boundedReview.notes || '' } }
          : item
      ));
      return {
        ...current,
        cases: updatedCases,
        final_scores: recomputeRedTeamScores(updatedCases),
      };
    });
    const response = await fetch(`${redTeamApiUrl}/api/runs/${runId}/review-items/${caseId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(boundedReview),
    });
    if (!response.ok) {
      throw new Error(`Could not save human review: ${response.status}`);
    }
  }, [redTeamRun?.run_id]);

  async function finalizeRedTeamRun() {
    if (!redTeamRun?.run_id) {
      return;
    }
    const response = await fetch(`${redTeamApiUrl}/api/runs/${redTeamRun.run_id}/finalize`, {
      method: 'POST',
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(`Could not save final results: ${response.status} ${message}`);
    }
    await loadRedTeamRun(redTeamRun.run_id);
  }

  function toggleRedTeamMethod(method) {
    setSelectedRedTeamMethods((current) => {
      if (current.includes(method)) {
        return current.filter((item) => item !== method);
      }
      return [...current, method];
    });
  }

  function updatePromptExpectedAnswer(promptId, value) {
    setRedTeamPromptSettings((current) => current.map((prompt) => (
      prompt.prompt_id === promptId ? { ...prompt, expected_answer: value } : prompt
    )));
  }

  function resetPromptExpectedAnswer(promptId) {
    setRedTeamPromptSettings((current) => current.map((prompt) => (
      prompt.prompt_id === promptId
        ? { ...prompt, expected_answer: prompt.original_expected_answer }
        : prompt
    )));
  }

  function resetRedTeamRun() {
    setRedTeamRun(null);
    setRedTeamReviewItems([]);
    setRedTeamError(null);
  }

  const selectedTraits = Object.entries(selectedPersona?.traits ?? {}).filter(([, value]) => Boolean(value));
  const selectedDetails = selectedPersona?.details || {};
  const redTeamIsRunning = ['starting', 'created', 'running', 'cancelling'].includes(redTeamRun?.status);
  const redTeamScores = redTeamRun?.final_scores || {};
  const redTeamMethodScores = redTeamScores.method_scores || {};
  const redTeamStatus = String(redTeamRun?.status || '').replaceAll('_', ' ');
  const redTeamStatusTitle = redTeamIsRunning
    ? 'Red-team evaluation running'
    : `Red-team evaluation ${redTeamStatus || 'completed'}`;
  const visiblePromptSettings = redTeamPromptSettings.filter((prompt) => selectedRedTeamMethods.includes(prompt.method));
  const selectedPromptSetting = visiblePromptSettings.find((prompt) => prompt.prompt_id === selectedPromptId) || visiblePromptSettings[0] || null;
  const editedPromptCount = redTeamPromptSettings.filter((prompt) => (
    prompt.expected_answer.trim() !== prompt.original_expected_answer.trim()
  )).length;
  const redTeamSettingsView = (
    <div className="redTeamSettingsPage">
      <div className="redTeamSettingsHeader">
        <div className="redTeamSettingsTitleCluster">
          <button
            aria-label="Back to evaluation"
            className="redTeamBackButton"
            title="Back to evaluation"
            type="button"
            onClick={() => setRedTeamSettingsOpen(false)}
          >
            <img alt="" src={arrowBackIcon} />
          </button>
          <div>
            <span>Question settings</span>
            <h2 className="unbounded-weight400">Expected direction and vibe</h2>
          </div>
        </div>
        <div className="redTeamSettingsHeaderActions">
          <div className="redTeamSettingsMeta">
            <span>{visiblePromptSettings.length} questions</span>
            <span>{editedPromptCount} edited</span>
          </div>
          <button
            className="redTeamSecondaryButton"
            disabled={redTeamPromptSettingsStatus === 'loading'}
            type="button"
            onClick={loadRedTeamPromptSettings}
          >
            Refresh settings
          </button>
        </div>
      </div>
      {redTeamPromptSettingsStatus === 'loading' && (
        <p className="statusText">Loading red-team question settings...</p>
      )}
      {redTeamPromptSettingsStatus === 'error' && (
        <div className="redTeamSettingsFallback">
          <p className="statusText errorText">Question settings are unavailable.</p>
          <button className="redTeamSecondaryButton" type="button" onClick={loadRedTeamPromptSettings}>
            Try again
          </button>
        </div>
      )}
      {redTeamPromptSettingsStatus === 'ready' && selectedPromptSetting && (
        <div className="redTeamSettingsGrid">
          <div className="redTeamQuestionList" aria-label="Red-team questions">
            {visiblePromptSettings.map((prompt) => {
              const isEdited = prompt.expected_answer.trim() !== prompt.original_expected_answer.trim();
              return (
                <button
                  className={prompt.prompt_id === selectedPromptSetting.prompt_id ? 'isSelected' : ''}
                  key={prompt.prompt_id}
                  type="button"
                  onClick={() => setSelectedPromptId(prompt.prompt_id)}
                >
                  <span>{prompt.prompt_id}</span>
                  <strong>{prompt.method_name}</strong>
                  <p>{prompt.message}</p>
                  {isEdited && <b>edited</b>}
                </button>
              );
            })}
          </div>
          <section className="redTeamPromptEditor" aria-label="Expected answer editor">
            <div className="redTeamPromptEditorTopline">
              <span>{selectedPromptSetting.prompt_id}</span>
              <strong>{selectedPromptSetting.target_guardrail}</strong>
            </div>
            <p className="redTeamPromptMessage">{selectedPromptSetting.message}</p>
            <label>
              Expected answer behavior
              <textarea
                value={selectedPromptSetting.expected_answer}
                onChange={(event) => updatePromptExpectedAnswer(selectedPromptSetting.prompt_id, event.target.value)}
              />
            </label>
            <button
              className="redTeamSecondaryButton"
              type="button"
              onClick={() => resetPromptExpectedAnswer(selectedPromptSetting.prompt_id)}
            >
              Reset this expectation
            </button>
          </section>
        </div>
      )}
      {redTeamPromptSettingsStatus === 'ready' && !selectedPromptSetting && (
        <div className="redTeamEmptyState">
          <h2 className="unbounded-weight400">No methods selected</h2>
          <p>Select at least one method to edit its expected answer behavior.</p>
        </div>
      )}
    </div>
  );

  return (
    <main className={`ChatApp unbounded-weight300 ${activePersona ? 'isBlurred' : ''}`}>
      <div className="pageSurface">
        <header className="appHeader">
          <div>
            <p className="eyebrow">Synthetic social agent integrity</p>
            <h1 className="unbounded-weight400">Safeguarding Synthetic Agency</h1>
          </div>
          <nav className="workspaceTabs" aria-label="Workspace tabs">
            <button
              className={activeTab === 'chat' ? 'isActive' : ''}
              type="button"
              onClick={() => setActiveTab('chat')}
            >
              Chat
            </button>
            <button
              className={activeTab === 'red-team' ? 'isActive' : ''}
              type="button"
              onClick={() => setActiveTab('red-team')}
            >
              Red-teaming
            </button>
          </nav>
        </header>

        <section className="workspaceShell">
          {activeTab === 'chat' && (
            <div className="chatWorkspace">
              <aside className="personaSelectionPanel" aria-label="Persona selection">
                <div className="panelHeader">
                  <span>Personas</span>
                  <strong>{personas.length}/{targetCount}</strong>
                </div>
                {loading && <p className="statusText">Loading personas...</p>}
                {error && <p className="statusText errorText">{error}</p>}
                {!loading && !error && !isComplete && (
                  <p className="panelHint">Showing saved agents while the profile set completes.</p>
                )}
                <div className="personaNameList">
                  {personas.map((persona) => (
                    <button
                      className={selectedPersona?.id === persona.id ? 'isSelected' : ''}
                      key={persona.id}
                      type="button"
                      onClick={() => setSelectedPersona(persona)}
                    >
                      <span>{persona.label}</span>
                      <small>{persona.traits?.municipality || persona.country}</small>
                    </button>
                  ))}
                </div>
              </aside>

              <article className="personaDetailPanel" aria-live="polite">
                {selectedPersona ? (
                  <>
                    <div className="personaDetailTopline">
                      <span>{selectedPersona.country || 'Synthetic profile'}</span>
                      <strong>{selectedPersona.traits?.municipality || 'Persona'}</strong>
                    </div>
                    <h2 className="unbounded-weight400">{selectedPersona.label}</h2>
                    <div className="personaDetailTraits">
                      {selectedTraits.slice(0, 10).map(([key, value]) => (
                        <span key={key}>{value}</span>
                      ))}
                    </div>
                    <div className="personaDetailBody">
                      <section>
                        <h3>Biography</h3>
                        <p>{selectedPersona.biography}</p>
                      </section>
                      {(selectedDetails.occupation || selectedDetails.education || selectedDetails.political_interest) && (
                        <section className="personaFactGrid">
                          {selectedDetails.occupation && (
                            <div>
                              <span>Occupation</span>
                              <strong>{selectedDetails.occupation}</strong>
                            </div>
                          )}
                          {selectedDetails.education && (
                            <div>
                              <span>Education</span>
                              <strong>{selectedDetails.education}</strong>
                            </div>
                          )}
                          {selectedDetails.political_interest && (
                            <div>
                              <span>Political interest</span>
                              <strong>{selectedDetails.political_interest}</strong>
                            </div>
                          )}
                        </section>
                      )}
                    </div>
                    <button className="startChatButton" type="button" onClick={() => setActivePersona(selectedPersona)}>
                      Start chat
                    </button>
                  </>
                ) : (
                  <div className="emptyDetailState">
                    <h2 className="unbounded-weight400">Select a persona</h2>
                    <p>Choose a synthetic social agent from the list to inspect the profile and open a chat.</p>
                  </div>
                )}
              </article>
            </div>
          )}

          {activeTab === 'red-team' && redTeamSettingsOpen && (
            <div className="redTeamSettingsFullWindow">
              {redTeamSettingsView}
            </div>
          )}

          {activeTab === 'red-team' && !redTeamSettingsOpen && (
            <div className="redTeamWorkspace">
              <section className="redTeamSetupPanel">
                {!redTeamRun ? (
                  <>
                    <div className="panelHeader">
                      <span>Evaluation setup</span>
                      <div className="panelHeaderActions">
                        <strong>{selectedRedTeamMethods.length} selected</strong>
                        <button
                          className="redTeamSettingsTextButton"
                          aria-label="Open question settings"
                          type="button"
                          onClick={() => setRedTeamSettingsOpen(true)}
                        >
                          <img alt="" src={settingsIcon} />
                        </button>
                      </div>
                    </div>
                    <div className="redTeamControlGroup">
                      <h2 className="unbounded-weight400">Red-team methods</h2>
                      <div className="redTeamMethodControls">
                        {redTeamMethods.map(([method, label]) => (
                          <label key={method}>
                            <input
                              checked={selectedRedTeamMethods.includes(method)}
                              onChange={() => toggleRedTeamMethod(method)}
                              type="checkbox"
                            />
                            <span>{label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                    <div className="redTeamControlGroup">
                      <h2 className="unbounded-weight400">Guardrail version</h2>
                      <div className="redTeamModeControls">
                        <label>
                          <input
                            checked={redTeamTargetMode === 'guardrailed'}
                            name="red-team-target-mode"
                            onChange={() => setRedTeamTargetMode('guardrailed')}
                            type="radio"
                          />
                          <span>Guardrailed target</span>
                        </label>
                        <label>
                          <input
                            checked={redTeamTargetMode === 'lightweight_no_guardrails'}
                            name="red-team-target-mode"
                            onChange={() => setRedTeamTargetMode('lightweight_no_guardrails')}
                            type="radio"
                          />
                          <span>Lightweight baseline, no guardrails</span>
                        </label>
                      </div>
                    </div>
                    {redTeamError && <p className="statusText errorText">{redTeamError}</p>}
                    <button
                      className="redTeamKickoff"
                      disabled={selectedRedTeamMethods.length === 0}
                      type="button"
                      onClick={startRedTeamRun}
                    >
                      Start red-teaming
                    </button>
                  </>
                ) : (
                  <>
                    <div className="redTeamRunHeading">
                      <div className="redTeamRunHeadingTopline">
                        <span>Red-team evaluation</span>
                        <button
                          className="redTeamSettingsTextButton"
                          aria-label="Open question settings"
                          type="button"
                          onClick={() => setRedTeamSettingsOpen(true)}
                        >
                          <img alt="" src={settingsIcon} />
                        </button>
                      </div>
                      <h2 className="unbounded-weight400">{redTeamStatusTitle}</h2>
                    </div>
                    <div className="redTeamRunSummary" aria-label="Red-team run summary">
                      <div className="redTeamScoreCards">
                        <div className="redTeamScoreCard">
                          <span>Overall score</span>
                          <strong>{formatPercent(redTeamScores.overall_score)}</strong>
                        </div>
                        <div className="redTeamScoreCard">
                          <span>Pending human review</span>
                          <strong>{redTeamScores.pending_human_reviews ?? 0}</strong>
                        </div>
                        <div className="redTeamScoreCard">
                          <span>Completed review</span>
                          <strong>{redTeamScores.completed_human_reviews ?? 0}</strong>
                        </div>
                        {Object.entries(redTeamMethodScores).map(([method, value]) => (
                          <div className="redTeamScoreCard isMethodScore" key={method}>
                            <span>{method}</span>
                            <strong>{formatPercent(value)}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                    {redTeamError && <p className="statusText errorText">{redTeamError}</p>}
                    <button className="redTeamResetButton" type="button" onClick={resetRedTeamRun}>
                      Start new red-teaming process
                    </button>
                  </>
                )}
              </section>

              <section className="redTeamContentPanel">
                {redTeamRun ? (
                  <RedTeamPanel
                    embedded
                    run={redTeamRun}
                    reviewItems={redTeamReviewItems}
                    error={redTeamError}
                    onCancel={cancelRedTeamRun}
                    onClose={() => setRedTeamRun(null)}
                    onRefresh={() => loadRedTeamRun(redTeamRun?.run_id).catch((err) => setRedTeamError(err.message))}
                    onSaveFinalResults={finalizeRedTeamRun}
                    onSubmitReview={submitHumanReview}
                  />
                ) : (
                  <div className="redTeamEmptyState">
                    <h2 className="unbounded-weight400">Ready to evaluate</h2>
                    <p>Select methods, choose the guardrail version, then start a run. Results and human review items will appear here.</p>
                  </div>
                )}
              </section>
            </div>
          )}
        </section>
      </div>

      {activePersona && (
        <PersonaChat
          personaProfile={activePersona}
          personaDetails={activePersona.details}
          personaCountry={activePersona.country}
          showChat={() => setActivePersona(null)}
        />
      )}

    </main>
  );
}

export default App;
