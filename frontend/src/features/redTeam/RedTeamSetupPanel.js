import settingsIcon from '../../assets/images/Icon_Settings.png';
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
  redTeamMethodScores,
  redTeamRun,
  redTeamScores,
  redTeamStatusTitle,
  redTeamTargetMode,
  resetRedTeamRun,
  selectedRedTeamMethods,
  setRedTeamSettingsOpen,
  setRedTeamTargetMode,
  startRedTeamRun,
  toggleRedTeamMethod,
}) {
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
              <SettingsButton onClick={() => setRedTeamSettingsOpen(true)} />
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
  );
}

export default RedTeamSetupPanel;
