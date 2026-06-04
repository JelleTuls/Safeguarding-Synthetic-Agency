function RedTeamSettingsView({
  editedPromptCount,
  loadPromptSettings,
  promptSettingsStatus,
  resetPromptExpectedAnswer,
  selectedPromptSetting,
  setRedTeamSettingsOpen,
  setSelectedPromptId,
  updatePromptExpectedAnswer,
  visiblePromptSettings,
}) {
  return (
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
            &lt;
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
            disabled={promptSettingsStatus === 'loading'}
            type="button"
            onClick={loadPromptSettings}
          >
            Refresh settings
          </button>
        </div>
      </div>
      {promptSettingsStatus === 'loading' && (
        <p className="statusText">Loading red-team question settings...</p>
      )}
      {promptSettingsStatus === 'error' && (
        <div className="redTeamSettingsFallback">
          <p className="statusText errorText">Question settings are unavailable.</p>
          <button className="redTeamSecondaryButton" type="button" onClick={loadPromptSettings}>
            Try again
          </button>
        </div>
      )}
      {promptSettingsStatus === 'ready' && selectedPromptSetting && (
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
      {promptSettingsStatus === 'ready' && !selectedPromptSetting && (
        <div className="redTeamEmptyState">
          <h2 className="unbounded-weight400">No methods selected</h2>
          <p>Select at least one method to edit its expected answer behavior.</p>
        </div>
      )}
    </div>
  );
}

export default RedTeamSettingsView;
