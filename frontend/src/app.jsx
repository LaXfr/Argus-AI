import { useState } from "react";
import "./App.css";

export default function App() {
  const [question, setQuestion] = useState("");
  const [useReranker, setUseReranker] = useState(true);
  const [runEval, setRunEval] = useState(true);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    setData(null);

    try {
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          use_reranker: useReranker,
          run_eval: runEval,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error occurred");
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div>
          <h1>Enterprise Hybrid RAG Engine</h1>
          <p className="subtitle">
            Local Qdrant (Dense + BM25) • Cross-Encoder Reranker • Ollama Structured JSON
          </p>
        </div>
        <span className="status-badge">100% Local & Air-Gapped</span>
      </header>

      {/* Search & Controls Bar */}
      <form className="search-card" onSubmit={handleSearch}>
        <div className="input-row">
          <input
            type="text"
            placeholder="Ask a technical question about your indexed documents..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? "Running Pipeline..." : "Run Query"}
          </button>
        </div>

        <div className="controls-row">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={useReranker}
              onChange={(e) => setUseReranker(e.target.checked)}
            />
            <span>Enable Cross-Encoder Reranker (Top-15 → Top-5)</span>
          </label>

          <label className="toggle-label">
            <input
              type="checkbox"
              checked={runEval}
              onChange={(e) => setRunEval(e.target.checked)}
            />
            <span>Compute Live Faithfulness & Precision Metrics</span>
          </label>
        </div>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {/* Main Results Grid */}
      {data && (
        <div className="results-grid">
          {/* Left Column: Answer, Citations, Quotes & Metrics */}
          <div className="left-col">
            <div className="card">
              <div className="card-header">
                <h2>Synthesized Response</h2>
                <div className="badge-group">
                  <span className={`badge ${data.is_grounded ? "grounded" : "abstained"}`}>
                    {data.is_grounded ? "✓ Grounded in Context" : "⚠ Abstained (Low Confidence)"}
                  </span>
                  <span className="badge latency">{data.latency_ms} ms</span>
                </div>
              </div>

              <p className="answer-text">{data.answer}</p>

              {data.citations?.length > 0 && (
                <div className="section-block">
                  <h4>Verified Chunk Citations</h4>
                  <div className="citation-tags">
                    {data.citations.map((cit, idx) => (
                      <code key={idx} className="citation-chip">
                        {cit}
                      </code>
                    ))}
                  </div>
                </div>
              )}

              {data.verbatim_quotes?.length > 0 && (
                <div className="section-block">
                  <h4>Verbatim Supporting Quotes</h4>
                  {data.verbatim_quotes.map((quote, idx) => (
                    <blockquote key={idx} className="verbatim-quote">
                      "{quote}"
                    </blockquote>
                  ))}
                </div>
              )}
            </div>

            {/* Quantitative Evaluation Card */}
            {data.metrics && (
              <div className="card metrics-card">
                <h2>Quantitative RAG Evaluation</h2>
                <div className="metrics-grid">
                  <div className="metric-box">
                    <span className="metric-label">Faithfulness (No Hallucination)</span>
                    <span className="metric-value">
                      {(data.metrics.faithfulness * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-label">Context Precision (Retrieval Quality)</span>
                    <span className="metric-value">
                      {(data.metrics.context_precision * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <p className="metric-reasoning">{data.metrics.reasoning}</p>
              </div>
            )}
          </div>

          {/* Right Column: Retrieved & Reranked Chunks */}
          <div className="right-col">
            <div className="card">
              <h2>Retrieved Context Chunks ({data.chunks.length})</h2>
              <div className="chunks-list">
                {data.chunks.map((chunk, index) => (
                  <details key={index} className="chunk-item" open={index === 0}>
                    <summary className="chunk-summary">
                      <span className="rank-badge">#{index + 1}</span>
                      <span className="chunk-title">{chunk.chunk_id}</span>
                      <div className="score-pills">
                        {useReranker && (
                          <span className="pill rerank">Rerank: {chunk.rerank_score}</span>
                        )}
                        <span className="pill hybrid">RRF: {chunk.hybrid_score}</span>
                      </div>
                    </summary>
                    <div className="chunk-body">
                      <div className="chunk-meta">
                        <strong>Source:</strong> {chunk.source} | <strong>Section:</strong>{" "}
                        {chunk.section}
                      </div>
                      <p>{chunk.text}</p>
                    </div>
                  </details>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}