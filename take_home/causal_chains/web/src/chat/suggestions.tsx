import { useAui } from "@assistant-ui/react";

export const PLAY_PROMPTS = [
  "The Strait of Hormuz is going to open next week.",
  "Republicans win the House but Democrats take the senate during the Midterm.",
  "Oil stays elevated if the Strait is still closed next month.",
];

export function Suggestions({ on_pick }: { on_pick?: (text: string) => void }) {
  const aui = useAui();
  return (
    <ul className="suggestions">
      {PLAY_PROMPTS.map((prompt) => (
        <li key={prompt}>
          <button
            type="button"
            className="suggestion"
            onClick={() => {
              if (on_pick) {
                on_pick(prompt);
                return;
              }
              aui.composer.setText(prompt);
            }}
          >
            {prompt}
          </button>
        </li>
      ))}
    </ul>
  );
}
