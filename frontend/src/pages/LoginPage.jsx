import { useState } from "react";
import { ErrorNotice } from "../components/ui.jsx";
import { useAction } from "../hooks/useResource.js";

const DEMO_USERS = [
  ["customer.alpha", "Customer · drifted portfolio"],
  ["customer.beta", "Customer · new, not profiled"],
  ["customer.gamma", "Customer · KYC pending"],
  ["advisor.one", "Advisor"],
  ["admin.one", "Admin"],
];

export default function LoginPage({ api, onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const { run, error, busy } = useAction();

  const submit = async (event) => {
    event.preventDefault();
    const result = await run(() => api.post("/api/v1/auth/login", { username, password }));
    if (result) onLogin(result);
  };

  return (
    <div className="login-page">
      <form className="card login-card" onSubmit={submit} data-testid="login-form">
        <h1>WealthWise</h1>
        <p className="muted">Robo-advisory demo. All data is synthetic.</p>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} data-testid="login-username"
                 autoComplete="username" required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 data-testid="login-password" autoComplete="current-password" required />
        </label>
        <ErrorNotice error={error} />
        <button type="submit" className="primary" disabled={busy} data-testid="login-submit">
          Log in
        </button>
        <div className="demo-users">
          <span className="muted">Demo users (password in README):</span>
          {DEMO_USERS.map(([name, hint]) => (
            <button key={name} type="button" className="link-button" onClick={() => setUsername(name)}>
              {name} <span className="muted">— {hint}</span>
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
