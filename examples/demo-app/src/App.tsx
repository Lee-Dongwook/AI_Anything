import { useState, type FormEvent } from "react";

import { SubmitButton } from "./components/SubmitButton";

export function App() {
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <main>
      <h1>Sign up</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input name="name" defaultValue="Ada" />
        </label>
        <SubmitButton />
      </form>
      {submitted && <p id="result">Thanks!</p>}
    </main>
  );
}
