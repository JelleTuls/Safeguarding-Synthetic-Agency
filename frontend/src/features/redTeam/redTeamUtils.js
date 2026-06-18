// Red-team frontend utility functions.
//
// These helpers normalize prompt settings, define visible method labels, and
// recompute local score summaries after optional human-in-the-loop overrides.

export const redTeamMethods = [
  ['PBAR', 'Prompt-Based Attack Resistance'],
  ['TBAR', 'Token-Based Attack Resistance'],
  ['EB', 'Epistemic Boundary'],
  ['SFAM', 'Subjective Framing and Authority Modulation'],
  ['SC', 'Stylometric Consistency'],
  ['PG', 'Persuasive Governance'],
];

export function normalizePromptSettings(prompts = []) {
  return prompts.map((prompt) => ({
    ...prompt,
    original_expected_answer: prompt.expected_answer || '',
    expected_answer: prompt.expected_answer || '',
  }));
}

export function recomputeRedTeamScores(cases = []) {
  const methods = {};
  const profileMethods = {};
  const modeMethods = {};
  let marked = 0;
  let reviewed = 0;

  cases.forEach((caseItem) => {
    const review = caseItem.human_review || null;
    if (caseItem.needs_human_review) {
      marked += 1;
    }
    if (review) {
      reviewed += 1;
    }
    const rawScore = review?.score ?? caseItem.automated_score;
    if (rawScore === undefined || rawScore === null || Number.isNaN(Number(rawScore))) {
      return;
    }
    const score = Number(rawScore);
    const profileId = caseItem.profile_id || 'profile';
    const targetMode = caseItem.target_mode || 'guardrailed';
    if (!methods[caseItem.method]) {
      methods[caseItem.method] = [];
    }
    if (!profileMethods[profileId]) {
      profileMethods[profileId] = { label: caseItem.profile_label || profileId, methods: {} };
    }
    if (!profileMethods[profileId].methods[caseItem.method]) {
      profileMethods[profileId].methods[caseItem.method] = [];
    }
    if (!modeMethods[targetMode]) {
      modeMethods[targetMode] = {};
    }
    if (!modeMethods[targetMode][caseItem.method]) {
      modeMethods[targetMode][caseItem.method] = [];
    }
    methods[caseItem.method].push(score);
    profileMethods[profileId].methods[caseItem.method].push(score);
    modeMethods[targetMode][caseItem.method].push(score);
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
  const profileScores = Object.fromEntries(
    Object.entries(profileMethods).map(([profileId, profile]) => {
      const perMethod = Object.fromEntries(
        Object.entries(profile.methods)
          .sort(([left], [right]) => left.localeCompare(right))
          .map(([method, methodValues]) => [
            method,
            methodValues.length
              ? Number((methodValues.reduce((sum, value) => sum + value, 0) / methodValues.length).toFixed(3))
              : 0,
          ])
      );
      const profileValues = Object.values(perMethod);
      return [profileId, {
        profile_id: profileId,
        profile_label: profile.label,
        method_scores: perMethod,
        overall_score: profileValues.length
          ? Number((profileValues.reduce((sum, value) => sum + value, 0) / profileValues.length).toFixed(3))
          : 0,
        case_count: Object.values(profile.methods).reduce((sum, methodValues) => sum + methodValues.length, 0),
      }];
    })
  );
  const profileValues = Object.values(profileScores).map((profile) => profile.overall_score);
  const averageProfileScore = profileValues.length
    ? Number((profileValues.reduce((sum, value) => sum + value, 0) / profileValues.length).toFixed(3))
    : overallScore;
  const targetModeScores = Object.fromEntries(
    Object.entries(modeMethods).map(([mode, methodMap]) => {
      const perMethod = Object.fromEntries(
        Object.entries(methodMap)
          .sort(([left], [right]) => left.localeCompare(right))
          .map(([method, methodValues]) => [
            method,
            methodValues.length
              ? Number((methodValues.reduce((sum, value) => sum + value, 0) / methodValues.length).toFixed(3))
              : 0,
          ])
      );
      const modeValues = Object.values(perMethod);
      return [mode, {
        method_scores: perMethod,
        overall_score: modeValues.length
          ? Number((modeValues.reduce((sum, value) => sum + value, 0) / modeValues.length).toFixed(3))
          : 0,
        case_count: Object.values(methodMap).reduce((sum, methodValues) => sum + methodValues.length, 0),
      }];
    })
  );
  const guardrailed = targetModeScores.guardrailed;
  const lightweight = targetModeScores.lightweight_no_guardrails;
  const guardrailImprovement = guardrailed && lightweight ? {
    overall_delta: Number((guardrailed.overall_score - lightweight.overall_score).toFixed(3)),
    method_deltas: Object.fromEntries(
      [...new Set([
        ...Object.keys(guardrailed.method_scores || {}),
        ...Object.keys(lightweight.method_scores || {}),
      ])]
        .sort()
        .map((method) => [
          method,
          Number(((guardrailed.method_scores?.[method] || 0) - (lightweight.method_scores?.[method] || 0)).toFixed(3)),
        ])
    ),
    guardrailed_score: guardrailed.overall_score,
    lightweight_score: lightweight.overall_score,
  } : null;

  return {
    overall_score: overallScore,
    average_profile_score: averageProfileScore,
    method_scores: methodScores,
    profile_scores: profileScores,
    target_mode_scores: targetModeScores,
    guardrail_improvement: guardrailImprovement,
    human_review_markers: marked,
    pending_human_reviews: 0,
    completed_human_reviews: reviewed,
    is_final: true,
  };
}

export function formatPercent(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return '0%';
  }
  return `${Math.round(Number(value) * 100)}%`;
}
