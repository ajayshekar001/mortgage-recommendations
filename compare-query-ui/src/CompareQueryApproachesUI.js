import React, { useState } from "react";

export default function CompareQueryApproachesUI() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/compare-query-approaches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          max_results: 8,
          max_hops: 4,
          include_chain_of_thought: true,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: "Failed to fetch results." });
    }
    setLoading(false);
  };

  return (
    <div style={{ 
      maxWidth: 1200, 
      margin: "0 auto", 
      padding: "20px",
      fontFamily: "Arial, sans-serif"
    }}>
      <div style={{
        backgroundColor: "white",
        padding: "30px",
        borderRadius: "8px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.1)"
      }}>
        <h1 style={{ 
          color: "#333", 
          textAlign: "center",
          marginBottom: "30px",
          borderBottom: "3px solid #007bff",
          paddingBottom: "10px"
        }}>
          Compare Query Approaches
        </h1>
      <form onSubmit={handleSubmit}>
        <textarea
          rows={4}
          style={{ width: "100%", fontSize: 18, padding: 10 }}
          placeholder="Enter a complex mortgage/underwriting question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          style={{
            marginTop: 10,
            padding: "10px 30px",
            fontSize: 18,
            background: "#1976d2",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
          }}
          disabled={loading || !question.trim()}
        >
          {loading ? "Loading..." : "Compare Approaches"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: 40 }}>
          {result.error && <div style={{ color: "red" }}>{result.error}</div>}
          {result.comparison_results && (
            <>
              <h3>Results for: <em>{result.query}</em></h3>
              <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                {Object.entries(result.comparison_results).map(([key, approach]) => (
                  <div
                    key={key}
                    style={{
                      flex: 1,
                      minWidth: 280,
                      background: "#f9f9f9",
                      border: "1px solid #ddd",
                      borderRadius: 8,
                      padding: 20,
                      marginBottom: 20,
                    }}
                  >
                    <h4>
                      {approach.approach}
                      {result.evaluation_summary?.best_approach?.toLowerCase().includes(key) && (
                        <span style={{
                          background: "#43a047",
                          color: "#fff",
                          borderRadius: 4,
                          padding: "2px 8px",
                          marginLeft: 10,
                          fontSize: 14,
                        }}>Best</span>
                      )}
                    </h4>
                    <div style={{ fontStyle: "italic", color: "#555" }}>{approach.description}</div>
                    <pre style={{
                      background: "#fff",
                      padding: 10,
                      borderRadius: 4,
                      fontSize: 14,
                      maxHeight: 250,
                      overflow: "auto"
                    }}>{approach.response}</pre>
                    {result.evaluation_summary?.scores_summary?.[key] && (
                      <div style={{ marginTop: 10, fontSize: 14 }}>
                        <b>Scores:</b>
                        <ul>
                          <li>Accuracy: {result.evaluation_summary.scores_summary[key].accuracy_score}</li>
                          <li>Completeness: {result.evaluation_summary.scores_summary[key].completeness_score}</li>
                          <li>Practical Value: {result.evaluation_summary.scores_summary[key].practical_value_score}</li>
                          <li>Overall: {result.evaluation_summary.scores_summary[key].overall_score}</li>
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 30 }}>
                <h4>Evaluation Summary</h4>
                <b>Best Approach:</b> {result.evaluation_summary?.best_approach}
                <ul>
                  {result.evaluation_summary?.key_insights?.map((insight, i) => (
                    <li key={i}>{insight}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
      </div>
    </div>
  );
} 