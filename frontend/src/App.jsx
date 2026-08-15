import React from "react";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { create } from "zustand";

const useStore = create((set) => ({
  dark: true,
  toggle: () => set((s) => ({ dark: !s.dark })),
}));

function ErrorBoundary({ children }) {
  const [err, setErr] = React.useState(null);
  try {
    if (err) throw err;
    return <ErrorBoundaryInner onError={setErr}>{children}</ErrorBoundaryInner>;
  } catch (e) {
    return <div className="p-4 text-red-400">Error: {e.message}</div>;
  }
}

class ErrorBoundaryInner extends React.Component {
  componentDidCatch(e) { this.props.onError(e); }
  render() { return this.props.children; }
}

export default function App() {
  const { dark, toggle } = useStore();
  const [endpoints, setEndpoints] = React.useState("");
  const [query, setQuery] = React.useState("query { __typename }");

  const mutation = useMutation({
    mutationFn: (body) =>
      axios.post("/stitch", body, { "axios-retry": { retries: 2 } }).then((r) => r.data),
  });

  const run = () => {
    const urls = endpoints.split("\n").map((s) => s.trim()).filter(Boolean);
    mutation.mutate({ endpoints: urls, query });
  };

  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className="min-h-screen p-4 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">GraphQL Gateway</h1>
        <button onClick={toggle} className="px-3 py-1 rounded bg-gray-700 text-sm">
          {dark ? "☀️" : "🌙"}
        </button>
      </div>

      <label className="block text-sm mb-1">Endpoints (one per line)</label>
      <textarea
        className="w-full p-2 rounded bg-gray-800 border border-gray-600 font-mono text-sm mb-3"
        rows={3}
        value={endpoints}
        onChange={(e) => setEndpoints(e.target.value)}
        placeholder="http://localhost:4001/graphql"
      />

      <label className="block text-sm mb-1">Query</label>
      <textarea
        className="w-full p-2 rounded bg-gray-800 border border-gray-600 font-mono text-sm mb-3"
        rows={8}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button
        onClick={run}
        disabled={mutation.isPending}
        className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 mb-4"
      >
        {mutation.isPending ? "Executing..." : "Execute"}
      </button>

      {mutation.isError && (
        <pre className="p-3 rounded bg-red-900/50 text-red-300 text-sm mb-3 overflow-auto">
          {String(mutation.error)}
        </pre>
      )}

      {mutation.data && (
        <pre className="p-3 rounded bg-gray-800 border border-gray-600 text-sm overflow-auto max-h-[60vh]">
          {JSON.stringify(mutation.data, null, 2)}
        </pre>
      )}
    </div>
  );
}
