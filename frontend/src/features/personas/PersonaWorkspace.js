function PersonaWorkspace({
  error,
  isComplete,
  loading,
  personas,
  selectedPersona,
  setActivePersona,
  setSelectedPersona,
  targetCount,
}) {
  const selectedTraits = Object.entries(selectedPersona?.traits ?? {}).filter(([, value]) => Boolean(value));
  const selectedDetails = selectedPersona?.details || {};

  return (
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
  );
}

export default PersonaWorkspace;
