
import { useEffect, useState } from "react";
import "./App.css";
import GraphRAGChat from "./GraphRAGChat";
import GraphVisualization from "./GraphVisualization";
const API_URL = "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState("");
  const [progressStep, setProgressStep] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");

  const [documentReady, setDocumentReady] = useState(false);
  const [copied, setCopied] = useState(false);

  // =====================================
  // CHECK CELERY JOB STATUS AUTOMATICALLY
  // =====================================

  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    let timer;

    async function checkStatus() {
      try {
        const response = await fetch(
          `${API_URL}/documents/status/${jobId}`
        );

        if (!response.ok) {
          throw new Error(`Status request failed: ${response.status}`);
        }

        const data = await response.json();

        if (cancelled) return;

        setJobStatus(data.status);

        if (data.status === "PROGRESS") {
          setProgressStep(
            data.progress?.step || "Processing document..."
          );
        }

        if (data.status === "SUCCESS") {
          setDocumentReady(true);
          setProgressStep("");

          setUploadMessage(
            `PDF processed successfully. ${
              data.result?.stored_vectors ?? 0
            } vectors stored.`
          );

          return;
        }

        if (data.status === "FAILURE") {
          setDocumentReady(false);
          setProgressStep("");

          setUploadMessage(
            `PDF processing failed: ${
              data.error || "Unknown error"
            }`
          );

          return;
        }

        // Check again after two seconds.
        timer = setTimeout(checkStatus, 2000);

      } catch (error) {
        if (cancelled) return;

        setUploadMessage(
          `Could not check status: ${error.message}. Retrying...`
        );

        timer = setTimeout(checkStatus, 3000);
      }
    }

    checkStatus();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [jobId]);

  // =====================================
  // UPLOAD PDF
  // =====================================

  async function uploadPDF(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadMessage("Please select a PDF file.");
      event.target.value = "";
      return;
    }

    if (file.size === 0) {
      setUploadMessage("The selected PDF is empty.");
      event.target.value = "";
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadMessage("File size must be below 10 MB.");
      event.target.value = "";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setDocumentReady(false);

    setJobId("");
    setJobStatus("");
    setProgressStep("");
    setCopied(false);

    setUploadMessage("Uploading PDF...");

    try {
      const response = await fetch(
        `${API_URL}/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      if (!data.job_id) {
        throw new Error("Backend did not return a job ID.");
      }

      setJobId(data.job_id);
      setJobStatus(data.status || "PENDING");

      setUploadMessage(
        `Uploaded ${data.filename}. Waiting for processing...`
      );

    } catch (error) {
      setUploadMessage(`Upload error: ${error.message}`);

    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  // =====================================
  // COPY JOB ID
  // =====================================

  async function copyJobId() {
    if (!jobId) return;

    try {
      await navigator.clipboard.writeText(jobId);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);

    } catch (error) {
      setUploadMessage(
        "Unable to copy Job ID. Please copy it manually."
      );
    }
  }

  // =====================================
  // SEND CHAT MESSAGE
  // =====================================

  async function sendMessage() {
    if (!question.trim() || loading || !documentReady) return;

    const userQuestion = question.trim();

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        text: userQuestion,
        sources: [],
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          question: userQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Chat request failed"
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: data.answer || "No answer returned.",
          sources: Array.isArray(data.sources)
            ? data.sources
            : [],
        },
      ]);

    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: `Error: ${error.message}`,
          sources: [],
        },
      ]);

    } finally {
      setLoading(false);
    }
  }

  // =====================================
  // UI
  // =====================================

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div className="brand">
          <div className="brand-icon">G</div>

          <div>
            <h1>GraphRAG Brain</h1>
            <p>Enterprise Knowledge Assistant</p>
          </div>
        </div>

        <span className="api-status">
          <span className="status-dot"></span>
          Local API
        </span>

      </header>


      {/* MAIN CONTENT */}

      <main className="main">

        {/* WELCOME AND UPLOAD */}

        <section className="welcome">

          <h2>Ask your documents anything.</h2>

          <p className="subtitle">
            Upload your documents and ask questions.
            Get answers supported by retrieved document sources.
          </p>


          {/* UPLOAD BUTTON */}

          <label className="upload-button">

            <span>
              {uploading ? "Uploading..." : "+ Upload PDF"}
            </span>

            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={uploadPDF}
              disabled={uploading}
              hidden
            />

          </label>


          {/* UPLOAD STATUS */}

          {uploadMessage && (

            <div className="upload-status">

              <p className="upload-message">
                {uploadMessage}
              </p>


              {/* JOB ID */}

              {jobId && (

                <div className="job-id-container">

                  <div className="job-id-heading">
                    Job ID
                  </div>

                  <div className="job-id-row">

                    <code className="job-id-value">
                      {jobId}
                    </code>

                    <button
                      className="copy-button"
                      onClick={copyJobId}
                      type="button"
                    >
                      {copied ? "Copied!" : "Copy"}
                    </button>

                  </div>

                </div>

              )}


              {/* STATUS */}

              {jobStatus && (

                <div className="status-row">

                  <span>Job status:</span>

                  <strong
                    className={`job-status ${jobStatus.toLowerCase()}`}
                  >
                    {jobStatus}
                  </strong>

                </div>

              )}


              {/* PROCESSING STEP */}

              {progressStep && (

                <p className="progress-step">
                  Current step: {progressStep}
                </p>

              )}


              {/* PROGRESS BAR */}

              {["PENDING", "STARTED", "PROGRESS"].includes(
                jobStatus
              ) && (

                <div className="progress-track">
                  <div className="progress-indicator"></div>
                </div>

              )}

            </div>

          )}

        </section>


        {/* CHAT SECTION */}

        <section className="chat-box">

          {/* MESSAGES */}

          <div className="messages">

            {messages.length === 0 && (

              <div className="empty">

                <div className="empty-icon">✦</div>

                <h3>Start a conversation</h3>

                <p>
                  {documentReady
                    ? "Ask a question about your uploaded documents."
                    : "Upload and process a PDF before asking questions."}
                </p>

              </div>

            )}


            {/* DISPLAY MESSAGES */}

            {messages.map((message, index) => (

              <div
                className={`message ${message.role}`}
                key={index}
              >

                <strong className="message-author">
                  {message.role === "user"
                    ? "You"
                    : "AI Assistant"}
                </strong>

                <p className="message-text">
                  {message.text}
                </p>


                {/* SOURCES */}

                {message.sources?.length > 0 && (

                  <div className="sources">

                    <strong>Document Sources</strong>

                    {message.sources.map((source, sourceIndex) => (

                      <div
                        className="source-item"
                        key={sourceIndex}
                      >

                        <span className="source-number">
                          {sourceIndex + 1}
                        </span>

                        <div>
                          <p>
                            {source.filename || "Document"}
                          </p>

                          {source.page_number != null && (
                            <small>
                              Page {source.page_number}
                            </small>
                          )}
                        </div>

                      </div>

                    ))}

                  </div>

                )}

              </div>

            ))}


            {/* AI LOADING */}

            {loading && (

              <div className="message assistant">

                <strong className="message-author">
                  AI Assistant
                </strong>

                <p className="message-text">
                  Searching documents and generating an answer...
                </p>

                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>

              </div>

            )}

          </div>


          {/* CHAT INPUT */}

          <div className="input-area">

            <input
              type="text"
              placeholder={
                documentReady
                  ? "Ask something about your documents..."
                  : "Upload and process a PDF first..."
              }
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  sendMessage();
                }
              }}
              disabled={!documentReady || loading}
            />

            <button
              onClick={sendMessage}
              disabled={
                !documentReady ||
                loading ||
                !question.trim()
              }
            >
              {loading ? "..." : "Send"}
            </button>

          </div>
           <GraphRAGChat />
<GraphVisualization />
        </section>

      </main>

    </div>
  );
}

export default App;
