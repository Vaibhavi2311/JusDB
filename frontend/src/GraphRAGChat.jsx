
import { useState } from "react";
import "./GraphRAGChat.css";

const API_URL = "http://127.0.0.1:8000";

function GraphRAGChat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAsk(event) {
    event.preventDefault();

    const userQuestion = question.trim();

    if (!userQuestion || loading) {
      return;
    }

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userQuestion
      }
    ]);

    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const url =
        `${API_URL}/graphrag/ask?question=` +
        encodeURIComponent(userQuestion);

      const response = await fetch(url);

      if (!response.ok) {
        const errorData = await response.json();

        throw new Error(
          errorData.detail || "Request failed"
        );
      }

      const data = await response.json();

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer,
          supported: data.supported,
          sources: data.sources || [],
          graphEntities: data.graph_entities || [],
          graphPaths: data.graph_paths || []
        }
      ]);

    } catch (err) {
      setError(err.message || "Unable to connect to backend.");

    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="graphrag-container">

      <div className="graphrag-header">
        <div>
          <h2>GraphRAG Enterprise Brain</h2>
          <p>
            Ask questions about your uploaded documents
          </p>
        </div>

        <span className="status-indicator">
          AI Assistant
        </span>
      </div>

      <div className="graphrag-messages">

        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>How can I help you?</h3>
            <p>
              Ask a question about your uploaded documents.
            </p>
          </div>
        )}

        {messages.map((message, index) => (

          <div
            key={index}
            className={`message ${message.role}`}
          >

            <div className="message-label">
              {message.role === "user"
                ? "You"
                : "GraphRAG Assistant"}
            </div>

            <div className="message-content">
              {message.content}
            </div>

            {message.role === "assistant" && (

              <div className="answer-details">

                <p className="support-status">
                  Evidence status:{" "}
                  {message.supported
                    ? "Model marked evidence as sufficient"
                    : "Insufficient evidence"}
                </p>

                {message.sources.length > 0 && (
                  <div className="source-section">
                    <h4>Source chunk IDs</h4>

                    {message.sources.map((source) => (
                      <span
                        className="source-tag"
                        key={source}
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                )}

                {message.graphEntities.length > 0 && (
                  <div className="source-section">
                    <h4>Graph entities</h4>

                    {message.graphEntities.map(
                      (entity, i) => (
                        <span
                          className="source-tag"
                          key={i}
                        >
                          {entity.name || "Entity"}
                        </span>
                      )
                    )}
                  </div>
                )}

                {message.graphPaths.length > 0 && (
                  <details className="graph-details">
                    <summary>
                      View graph retrieval details
                    </summary>

                    <pre>
                      {JSON.stringify(
                        message.graphPaths,
                        null,
                        2
                      )}
                    </pre>
                  </details>
                )}

              </div>
            )}

          </div>

        ))}

        {loading && (
          <div className="loading-message">
            Searching documents and knowledge graph...
          </div>
        )}

      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <form
        className="graphrag-input-area"
        onSubmit={handleAsk}
      >

        <input
          type="text"
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Ask your documents anything..."
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading || !question.trim()}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>

      </form>

    </div>
  );
}

export default GraphRAGChat;
