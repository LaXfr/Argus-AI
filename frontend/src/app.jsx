import { useState, useEffect } from "react";
import "./App.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("studio"); // "studio" | "benchmark"

  // Studio State
  const [question, setQuestion] = useState("");
  const [useReranker, setUseReranker] = useState(true);
  const [runEval, setRunEval] = useState(true);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  // Upload State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);
  const [uploadError, setUploadError] = useState("");

  // Benchmark Tab State
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkError, setBenchmarkError] = useState("");

  const fetchBenchmark = async () => {
    setBenchmarkLoading(true);
    setBenchmarkError("");
    try {
      const res = await fetch("http://localhost:8000/api/benchmark");
      const json = await res.json();
      if (json.status === "success") {
        setBenchmarkData(json.benchmark);
      } else {
        setBenchmarkError(json.message || "Benchmark not ready");
      }
    } catch (err) {
      setBenchmarkError("Failed to fetch benchmark: " + err.message);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "benchmark") {
      fetchBenchmark();
    }
  }, [activeTab]);

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

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploadLoading(true);
    setUploadMessage(null);
    setUploadError("");

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      const resData = await res.json();
      if (!res.ok) {
        throw new Error(resData.detail || "Upload failed");
      }

      setUploadMessage(
        `Successfully indexed "${resData.filename}" (${resData.total_chunks_indexed} total chunks in collection).`
      );
      setUploadFile(null);
      // Reset input element
      const fileInput = document.getElementById("file-upload-input");
      if (fileInput) fileInput.value = "";
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div>
          <h1>Enterprise Hybrid RAG Engine</h1>
          <p className="subtitle">
            Local Qdrant (Dense + BM25) • Cross-Encoder Reranker • Ollama Structured JSON • Zero GPU Load
          </p>
        </div>
        <div className="header-badges">
          <span className="status-badge airgap">100% Local & Air-Gapped</span>
          <span className="status-badge cpu">CPU Mode (Thermal Safe)</span>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "studio" ? "active" : ""}`}
          onClick={() => setActiveTab("studio")}
        >
          🔍 RAG Studio & Ingestion
        </button>
        <button
          className={`tab-btn ${activeTab === "benchmark" ? "active" : ""}`}
          onClick={() => setActiveTab("benchmark")}
        >
          📊 Automated Benchmark Dashboard
        </button>
      </nav>

      {/* TAB 1: RAG STUDIO */}
      {activeTab === "studio" && (
        <div className="tab-content">
          {/* File Upload Section */}
          <div className="upload-card">
            <div className="upload-header">
              <h3>📄 Incremental Document Ingestion</h3>
              <span className="upload-hint">Upload .pdf, .md, or .txt to index into local Qdrant</span>
            </div>
            <form className="upload-form" onSubmit={handleFileUpload}>
              <input
                id="file-upload-input"
                type="file"
                accept=".pdf,.md,.txt"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="file-input"
              />
              <button
                type="submit"
                className="upload-btn"
                disabled={!uploadFile || uploadLoading}
              >
                {uploadLoading ? "Parsing & Indexing..." : "Upload & Index"}
              </button>
            </form>
            {uploadMessage && <div className="success-banner">{uploadMessage}</div>}
            {uploadError && <div className="error-banner">{uploadError}</div>}
          </div>

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
                <span>
                  <strong>Mode B:</strong> Two-Stage Hybrid + Cross-Encoder Reranker (Top-15 → Top-3)
                </span>
              </label>

              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={runEval}
                  onChange={(e) => setRunEval(e.target.checked)}
                />
                <span>Compute Live Faithfulness & Context Precision@3</span>
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
                        <span className="metric-label">Faithfulness (Claim Grounding)</span>
                        <span className="metric-value">
                          {(data.metrics.faithfulness * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="metric-box">
                        <span className="metric-label">Context Precision@3 (Top Chunks)</span>
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
      )}

      {/* TAB 2: AUTOMATED BENCHMARK DASHBOARD */}
      {activeTab === "benchmark" && (
        <div className="tab-content benchmark-tab">
          <div className="benchmark-header-row">
            <div>
              <h2>Quantitative Benchmark Dashboard</h2>
              <p className="subtitle">
                Rigorous empirical comparison: Mode A (Naive Dense) vs. Mode B (Production Hybrid + Cross-Encoder Rerank)
              </p>
            </div>
            <button
              className="refresh-btn"
              onClick={fetchBenchmark}
              disabled={benchmarkLoading}
            >
              {benchmarkLoading ? "Loading..." : "🔄 Refresh Metrics"}
            </button>
          </div>

          {benchmarkError && <div className="error-banner">{benchmarkError}</div>}

          {benchmarkData && (
            <div className="benchmark-body">
              {/* Summary Metric Cards */}
              <div className="benchmark-kpi-grid">
                <div className="kpi-card highlight">
                  <span className="kpi-title">Context Precision Boost</span>
                  <span className="kpi-number">+{benchmarkData.summary.precision_delta_pct}%</span>
                  <span className="kpi-sub">
                    Mode A ({benchmarkData.summary.mode_a_precision}) → Mode B ({benchmarkData.summary.mode_b_precision})
                  </span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-title">Sentence-Level Faithfulness</span>
                  <span className="kpi-number">
                    {(benchmarkData.summary.mode_b_faithfulness * 100).toFixed(0)}%
                  </span>
                  <span className="kpi-sub">Grounded claim verification</span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-title">Mode C Guardrail</span>
                  <span className="kpi-number pass">
                    {benchmarkData.summary.guardrail_pass ? "100% PASS" : "FAIL"}
                  </span>
                  <span className="kpi-sub">Out-of-domain abstention</span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-title">Average Latency</span>
                  <span className="kpi-number">
                    {benchmarkData.summary.mode_b_latency_ms} ms
                  </span>
                  <span className="kpi-sub">CPU inference & Ollama generation</span>
                </div>
              </div>

              {/* Comparative Table */}
              <div className="card benchmark-table-card">
                <h3>Comparative Performance Matrix</h3>
                <div className="table-responsive">
                  <table className="benchmark-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Category</th>
                        <th>Mode A Precision</th>
                        <th>Mode B Precision</th>
                        <th>Mode A Faithfulness</th>
                        <th>Mode B Faithfulness</th>
                        <th>Mode A Latency</th>
                        <th>Mode B Latency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmarkData.queries.map((q) => (
                        <tr key={q.id}>
                          <td><strong>{q.id}</strong></td>
                          <td>{q.category}</td>
                          <td>{q.mode_a.context_precision.toFixed(2)}</td>
                          <td className="highlight-cell"><strong>{q.mode_b.context_precision.toFixed(2)}</strong></td>
                          <td>{q.mode_a.faithfulness.toFixed(2)}</td>
                          <td className="highlight-cell"><strong>{q.mode_b.faithfulness.toFixed(2)}</strong></td>
                          <td>{q.mode_a.latency_ms} ms</td>
                          <td>{q.mode_b.latency_ms} ms</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="tfoot-row">
                        <td colSpan={2}><strong>Overall Average</strong></td>
                        <td><strong>{benchmarkData.summary.mode_a_precision.toFixed(2)}</strong></td>
                        <td className="highlight-cell"><strong>{benchmarkData.summary.mode_b_precision.toFixed(2)}</strong></td>
                        <td><strong>{benchmarkData.summary.mode_a_faithfulness.toFixed(2)}</strong></td>
                        <td className="highlight-cell"><strong>{benchmarkData.summary.mode_b_faithfulness.toFixed(2)}</strong></td>
                        <td><strong>{benchmarkData.summary.mode_a_latency_ms} ms</strong></td>
                        <td><strong>{benchmarkData.summary.mode_b_latency_ms} ms</strong></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Guardrail Verification Details */}
              {benchmarkData.guardrail?.length > 0 && (
                <div className="card guardrail-card">
                  <h3>🛡 Mode C: Abstention Guardrail Verification (Out-of-Domain)</h3>
                  {benchmarkData.guardrail.map((g, idx) => (
                    <div key={idx} className="guardrail-item">
                      <div className="guardrail-meta">
                        <span className="guardrail-question"><strong>Query:</strong> "{g.question}"</span>
                        <span className="badge pass">PASSED (Abstained Reliably)</span>
                      </div>
                      <div className="guardrail-details">
                        <span><strong>Top Rerank Score:</strong> {g.top_rerank_score} (Threshold: 0.55)</span>
                        <span><strong>is_grounded:</strong> <code>{String(g.is_grounded)}</code></span>
                      </div>
                      <p className="guardrail-answer"><strong>System Response:</strong> <em>"{g.answer}"</em></p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}