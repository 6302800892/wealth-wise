import { useState } from "react";
import { BandBadge, Card, ErrorNotice, Loading } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { titleCase } from "../../lib/format.js";

async function load(api) {
  const [questionnaire, profile] = await Promise.all([
    api.get("/api/v1/questionnaire"),
    api.get("/api/v1/me/risk-profile"),
  ]);
  return { questionnaire, profile };
}

export default function RiskProfilePage({ api }) {
  const state = useResource(() => load(api), [api]);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const { run, error, busy } = useAction();
  if (!state.data) return <Loading state={state} />;
  const { questionnaire, profile } = state.data;

  const submit = async (event) => {
    event.preventDefault();
    const payload = {
      rule_set_version: questionnaire.rule_set_version,
      answers: Object.entries(answers).map(([question_id, option_id]) => ({ question_id, option_id })),
    };
    const created = await run(() => api.post("/api/v1/me/risk-assessments", payload));
    if (created) {
      setResult(created);
      state.reload();
    }
  };

  return (
    <div className="page">
      <h1>Risk profile</h1>
      <Card title="Current band" testId="current-band">
        <BandBadge band={profile.risk_band} />
        {profile.source && <p className="muted">Source: {titleCase(profile.source)}</p>}
      </Card>
      {result && (
        <Card title="Your result" testId="assessment-result">
          <p>
            Score <strong data-testid="assessment-score">{result.total_score}</strong> → <BandBadge band={result.risk_band} />
          </p>
        </Card>
      )}
      <form className="card" onSubmit={submit} data-testid="questionnaire">
        <h2>Questionnaire (v{questionnaire.rule_set_version})</h2>
        {questionnaire.questions.map((question, index) => (
          <fieldset key={question.question_id} className="question">
            <legend>
              {index + 1}. {question.text}
            </legend>
            {question.options.map((option) => (
              <label key={option.option_id} className="option">
                <input
                  type="radio"
                  name={question.question_id}
                  value={option.option_id}
                  checked={answers[question.question_id] === option.option_id}
                  onChange={() => setAnswers({ ...answers, [question.question_id]: option.option_id })}
                  data-testid={`answer-${option.option_id}`}
                />
                {option.text}
              </label>
            ))}
          </fieldset>
        ))}
        <ErrorNotice error={error} />
        <button type="submit" className="primary" disabled={busy} data-testid="submit-assessment">
          Submit answers
        </button>
      </form>
    </div>
  );
}
