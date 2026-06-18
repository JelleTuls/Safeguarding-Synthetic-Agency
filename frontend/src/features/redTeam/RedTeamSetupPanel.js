// Red-team setup and results sidebar.
//
// This component lets the user select profiles/methods, start a run, download
// final reports, and inspect high-level guardrailed-vs-lightweight outcomes.

import { useMemo, useState } from 'react';

import settingsIcon from '../../assets/images/Icon_Settings.png';
import { finalReportJsonUrl, finalReportPdfUrl } from './redTeamApi';
import { formatPercent, redTeamMethods } from './redTeamUtils';

function SettingsButton({ onClick }) {
  return (
    <button
      aria-label="Open question settings"
      className="redTeamSettingsTextButton"
      type="button"
      onClick={onClick}
    >
      <img alt="" src={settingsIcon} />
    </button>
  );
}

function RedTeamSetupPanel({
  redTeamError,
  redTeamRun,
  redTeamScores,
  redTeamTargetMode,
  redTeamAvailableProfileCount,
  redTeamDetailsMode,
  personas,
  finalizeRedTeamRun,
  resetRedTeamRun,
  selectedResultProfileId,
  selectedRedTeamProfileIds,
  selectedRedTeamMethods,
  setRedTeamSettingsOpen,
  setRedTeamDetailsMode,
  setSelectedResultProfileId,
  setSelectedRedTeamProfileIds,
  setRedTeamTargetMode,
  startRedTeamRun,
  toggleRedTeamMethod,
}) {
  const [finalizing, setFinalizing] = useState(false);
  const [finalizeError, setFinalizeError] = useState(null);
  const selectedProfileCount = selectedRedTeamProfileIds.length;
  const profileSelectionIsInvalid = selectedProfileCount < 1;
  const runIsCompleted = redTeamRun?.status === 'completed';
  const runIsSavedFinalReport = Boolean(redTeamRun?.loaded_from_final_report);
  const modeScores = redTeamScores.target_mode_scores || {};
  const guardrailedAverage = modeScores.guardrailed?.overall_score ?? redTeamScores.overall_score;
  const lightweightAverage = modeScores.lightweight_no_guardrails?.overall_score;
  const selectedModeDetails = modeScores[redTeamDetailsMode] || null;
  const selectedModeMethodScores = selectedModeDetails?.method_scores || {};
  const finalReport = redTeamRun?.final_report || null;
  const profileScores = useMemo(() => redTeamScores.profile_scores || {}, [redTeamScores.profile_scores]);
  const resultProfiles = useMemo(() => {
    const fromRun = Array.isArray(redTeamRun?.profiles) ? redTeamRun.profiles : [];
    const fromScores = Object.entries(profileScores).map(([profileId, score]) => ({
      id: profileId,
      label: score.profile_label || profileId,
    }));
    const merged = [...fromRun, ...fromScores].filter(Boolean);
    const seen = new Set();
    return merged.filter((profile) => {
      const id = profile.id || profile.profile_id;
      if (!id || seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }, [profileScores, redTeamRun?.profiles]);

  function toggleProfile(profileId) {
    setSelectedRedTeamProfileIds((current) => (
      current.includes(profileId)
        ? current.filter((id) => id !== profileId)
        : [...current, profileId]
    ));
  }

  return (
    <section className="redTeamSetupPanel">
      {!redTeamRun ? (
        <>
          <div className="panelHeader">
            <span>Evaluation setup</span>
            <div className="panelHeaderActions">
              <strong>{selectedRedTeamMethods.length} selected</strong>
              <SettingsButton onClick={() => setRedTeamSettingsOpen(true)} />
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
                  checked={redTeamTargetMode === 'full_analysis_stack'}
                  name="red-team-target-mode"
                  onChange={() => setRedTeamTargetMode('full_analysis_stack')}
                  type="radio"
                />
                <span>Full analysis stack: compare guardrailed and lightweight</span>
              </label>
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
          <div className="redTeamControlGroup">
            <h2 className="unbounded-weight400">Profiles</h2>
            <div className="redTeamProfileSelectionHeader">
              <span>{selectedProfileCount}/{redTeamAvailableProfileCount || 0} selected</span>
              <button type="button" onClick={() => setSelectedRedTeamProfileIds((personas || []).map((profile) => profile.id))}>
                Select all
              </button>
              <button type="button" onClick={() => setSelectedRedTeamProfileIds([])}>
                Clear
              </button>
            </div>
            <div className="redTeamProfileList">
              {(personas || []).map((profile) => (
                <label key={profile.id}>
                  <input
                    checked={selectedRedTeamProfileIds.includes(profile.id)}
                    onChange={() => toggleProfile(profile.id)}
                    type="checkbox"
                  />
                  <span>{profile.label}</span>
                  <small>{profile.traits?.municipality || profile.country}</small>
                </label>
              ))}
            </div>
            {profileSelectionIsInvalid && (
              <p className="redTeamInlineError">
                Select at least one profile before starting the run.
              </p>
            )}
          </div>
          {redTeamError && <p className="statusText errorText">{redTeamError}</p>}
          <button
            className="redTeamKickoff"
            disabled={selectedRedTeamMethods.length === 0 || profileSelectionIsInvalid}
            type="button"
            onClick={startRedTeamRun}
          >
            Start red-teaming
          </button>
        </>
      ) : (
        <>
          <div className="redTeamRunHeading isCompact">
            <div className="redTeamRunHeadingTopline">
              <span>Red-team evaluation</span>
              <SettingsButton onClick={() => setRedTeamSettingsOpen(true)} />
            </div>
          </div>
          <div className="redTeamRunSummary" aria-label="Red-team run summary">
            <div className="redTeamScorePair">
              <div className="redTeamScoreCard">
                <span>Guardrailed avg.</span>
                <strong>{formatPercent(guardrailedAverage)}</strong>
              </div>
              <div className="redTeamScoreCard">
                <span>Lightweight avg.</span>
                <strong>{lightweightAverage === undefined ? 'N/A' : formatPercent(lightweightAverage)}</strong>
              </div>
            </div>

            <div className="redTeamModeToggle" aria-label="Score detail mode">
              <button
                className={redTeamDetailsMode === 'guardrailed' ? 'isActive' : ''}
                type="button"
                onClick={() => setRedTeamDetailsMode('guardrailed')}
              >
                Guardrailed
              </button>
              <button
                className={redTeamDetailsMode === 'lightweight_no_guardrails' ? 'isActive' : ''}
                type="button"
                onClick={() => setRedTeamDetailsMode('lightweight_no_guardrails')}
              >
                Lightweight
              </button>
            </div>

            {selectedModeDetails && (
              <div className="redTeamScoreCards">
                <span className="redTeamScoreSectionLabel">
                  {redTeamDetailsMode === 'lightweight_no_guardrails' ? 'Lightweight details' : 'Guardrailed details'}
                </span>
                {Object.entries(selectedModeMethodScores).map(([method, value]) => (
                  <div className="redTeamScoreCard isMethodScore" key={method}>
                    <span>{method}</span>
                    <strong>{formatPercent(value)}</strong>
                  </div>
                ))}
              </div>
            )}

            {redTeamScores.guardrail_improvement && (
              <div className={redTeamScores.guardrail_improvement.overall_delta >= 0 ? 'redTeamScoreCard isImprovement isPositive' : 'redTeamScoreCard isImprovement isNegative'}>
                <span>Guardrail gain</span>
                <strong>{formatPercent(redTeamScores.guardrail_improvement.overall_delta)}</strong>
              </div>
            )}

            {resultProfiles.length > 0 && (
              <div className="redTeamResultProfiles">
                <span className="redTeamScoreSectionLabel">Profiles</span>
                <button
                  className={selectedResultProfileId === 'all' ? 'isActive' : ''}
                  type="button"
                  onClick={() => setSelectedResultProfileId('all')}
                >
                  All profiles
                </button>
                {resultProfiles.map((profile) => {
                  const id = profile.id || profile.profile_id;
                  return (
                    <button
                      className={selectedResultProfileId === id ? 'isActive' : ''}
                      key={id}
                      type="button"
                      onClick={() => setSelectedResultProfileId(id)}
                    >
                      {profile.label || id}
                    </button>
                  );
                })}
              </div>
            )}

            <div className="redTeamDownloadActions">
              {!runIsSavedFinalReport && (
                <button
                  type="button"
                  disabled={!runIsCompleted || finalizing}
                  onClick={async () => {
                    setFinalizeError(null);
                    setFinalizing(true);
                    try {
                      await finalizeRedTeamRun();
                    } catch (err) {
                      setFinalizeError(err.message);
                    } finally {
                      setFinalizing(false);
                    }
                  }}
                >
                  {finalizing ? 'Preparing report' : finalReport ? 'Rebuild downloads' : 'Create downloads'}
                </button>
              )}
              <a
                aria-disabled={!finalReport?.download_url}
                className={!finalReport?.download_url ? 'isDisabled' : ''}
                href={finalReport?.download_url ? finalReportJsonUrl(redTeamRun.run_id) : undefined}
              >
                Download JSON
              </a>
              <a
                aria-disabled={!finalReport?.pdf_download_url}
                className={!finalReport?.pdf_download_url ? 'isDisabled' : ''}
                href={finalReport?.pdf_download_url ? finalReportPdfUrl(redTeamRun.run_id) : undefined}
              >
                Download PDF
              </a>
            </div>
            {finalizeError && <p className="statusText errorText">{finalizeError}</p>}
            {!finalReport?.download_url && runIsCompleted && (
              <p className="redTeamInlineNote">Create downloads first. Human edits are optional.</p>
            )}
          </div>
          {redTeamError && <p className="statusText errorText">{redTeamError}</p>}
          <button className="redTeamResetButton" type="button" onClick={resetRedTeamRun}>
            New Red-Teaming Evaluation
          </button>
        </>
      )}
    </section>
  );
}

export default RedTeamSetupPanel;
