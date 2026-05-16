import { useCallback, useEffect, useState } from 'react';

import './App.css';
import PersonaChat from './modules/persona_chat_modules/personaChat';
import RedTeamPanel from './modules/red_team_modules/redTeamPanel';

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

function App() {
  const [personas, setPersonas] = useState([]);
  const [activePersona, setActivePersona] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetCount, setTargetCount] = useState(30);
  const [isComplete, setIsComplete] = useState(false);
  const [redTeamRun, setRedTeamRun] = useState(null);
  const [redTeamReviewItems, setRedTeamReviewItems] = useState([]);
  const [redTeamError, setRedTeamError] = useState(null);
  const [showRedTeamPanel, setShowRedTeamPanel] = useState(false);
  const [selectedRedTeamMethods, setSelectedRedTeamMethods] = useState(redTeamMethods.map(([method]) => method));
  const [redTeamTargetMode, setRedTeamTargetMode] = useState('guardrailed');

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

  async function startRedTeamRun() {
    if (selectedRedTeamMethods.length === 0) {
      setRedTeamError('Select at least one red-team method.');
      return;
    }
    const methodsToRun = selectedRedTeamMethods;
    const totalCases = methodsToRun.length * 10;
    setShowRedTeamPanel(true);
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

      const response = await fetch(`${redTeamApiUrl}/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backend_url: backendApiUrl,
          country: 'netherlands',
          selected_methods: methodsToRun,
          target_mode: redTeamTargetMode,
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
      setShowRedTeamPanel(false);
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

  return (
    <main className={`ChatApp unbounded-weight300 ${activePersona || showRedTeamPanel ? 'isBlurred' : ''}`}>
      <div className="pageSurface">
        <section className="chatHero">
          <p className="eyebrow">Synthetic social agent integrity</p>
          <h1 className="unbounded-weight400">Safeguarding Synthetic Agency</h1>
          <p>
            A framework for measuring and operationalizing system integrity in synthetic social agent systems.
          </p>
          <div className="redTeamControls" aria-label="Red-team configuration">
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
          <button
            className="redTeamKickoff"
            disabled={selectedRedTeamMethods.length === 0}
            type="button"
            onClick={startRedTeamRun}
          >
            Run red-team evaluation
          </button>
        </section>

        {loading && <p className="statusText">Loading personas...</p>}
        {!loading && !error && !isComplete && (
          <p className="statusText">
            Showing {personas.length} saved agents while the profile set completes to {targetCount}.
          </p>
        )}
        {error && <p className="statusText errorText">{error}</p>}

        <section className="personaGrid" aria-label="Synthetic social agent profiles">
          {personas.map((persona) => (
            <article className="personaCard" key={persona.id}>
              <div className="personaCardHeader">
                <h2 className="unbounded-weight400">{persona.label}</h2>
                <span>{persona.traits?.municipality}</span>
              </div>

              <div className="traitList">
                {Object.entries(persona.traits ?? {}).map(([key, value]) => (
                  <span key={key}>{value}</span>
                ))}
              </div>

              <p>{persona.biography}</p>

              <button type="button" onClick={() => setActivePersona(persona)}>
                Open agent
              </button>
            </article>
          ))}
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

      {showRedTeamPanel && (
        <RedTeamPanel
          run={redTeamRun}
          reviewItems={redTeamReviewItems}
          error={redTeamError}
          onCancel={cancelRedTeamRun}
          onClose={() => setShowRedTeamPanel(false)}
          onRefresh={() => loadRedTeamRun(redTeamRun?.run_id).catch((err) => setRedTeamError(err.message))}
          onSaveFinalResults={finalizeRedTeamRun}
          onSubmitReview={submitHumanReview}
        />
      )}
    </main>
  );
}

export default App;
