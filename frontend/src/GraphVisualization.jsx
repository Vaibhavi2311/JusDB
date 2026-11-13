
import { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";

import "./GraphVisualization.css";

const API_URL = "http://127.0.0.1:8000";

function GraphVisualization() {

  const containerRef = useRef(null);

  const [entityName, setEntityName] = useState("");
  const [entityType, setEntityType] = useState("ORGANIZATION");

  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function searchGraph(event) {

    event.preventDefault();

    if (!entityName.trim()) {
      setError("Enter an entity name.");
      return;
    }

    setLoading(true);
    setError("");
    setGraphData(null);
    setSelectedNode(null);

    try {

      const params = new URLSearchParams({
        entity_name: entityName.trim(),
        entity_type: entityType,
        limit: "100"
      });

      const response = await fetch(
        `${API_URL}/graph/visualization?${params}`
      );

      if (!response.ok) {
        throw new Error("Graph retrieval failed.");
      }

      const data = await response.json();

      if (!data.nodes || data.nodes.length === 0) {
        setError("Entity not found in the knowledge graph.");
      } else {
        setGraphData(data);
      }

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }
  }

  useEffect(() => {

    if (!graphData || !containerRef.current) {
      return;
    }

    const cy = cytoscape({

      container: containerRef.current,

      elements: [
        ...graphData.nodes,
        ...graphData.edges
      ],

      style: [

        {
          selector: "node",

          style: {
            "background-color": "#1976aa",
            "label": "data(label)",
            "color": "#ffffff",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "11px",
            "width": 55,
            "height": 55,
            "text-wrap": "wrap",
            "text-max-width": "75px",
            "border-width": 2,
            "border-color": "#8bc9ee"
          }
        },

        {
          selector: "edge",

          style: {
            "width": 2,
            "line-color": "#71869a",
            "target-arrow-color": "#71869a",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "label": "data(label)",
            "font-size": "9px",
            "color": "#dce8f1",
            "text-background-color": "#15232f",
            "text-background-opacity": 1,
            "text-background-padding": "3px"
          }
        },

        {
          selector: "node:selected",

          style: {
            "background-color": "#20a77b",
            "border-color": "#ffffff",
            "border-width": 4
          }
        }

      ],

      layout: {
        name: "cose",
        animate: true,
        fit: true,
        padding: 40
      }

    });

    cy.on("tap", "node", (event) => {

      setSelectedNode(
        event.target.data()
      );

    });

    return () => {
      cy.destroy();
    };

  }, [graphData]);

  return (

    <div className="graph-page">

      <div className="graph-heading">

        <h2>Knowledge Graph Explorer</h2>

        <p>
          Explore entities and their relationships
        </p>

      </div>

      <form
        className="graph-search"
        onSubmit={searchGraph}
      >

        <input
          type="text"
          placeholder="Enter entity name..."
          value={entityName}
          onChange={(e) => setEntityName(e.target.value)}
        />

        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
        >

          <option value="PERSON">Person</option>
          <option value="ORGANIZATION">Organization</option>
          <option value="TECHNOLOGY">Technology</option>
          <option value="PROJECT">Project</option>
          <option value="CONCEPT">Concept</option>
          <option value="LOCATION">Location</option>
          <option value="DOCUMENT">Document</option>
          <option value="DATE">Date</option>

        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Explore Graph"}
        </button>

      </form>

      {error && (
        <p className="graph-error">{error}</p>
      )}

      <div className="graph-workspace">

        <div
          className="cytoscape-container"
          ref={containerRef}
        />

        <div className="node-information">

          <h3>Entity Details</h3>

          {selectedNode ? (

            <>

              <p>
                <strong>Name:</strong>{" "}
                {selectedNode.label}
              </p>

              <p>
                <strong>Type:</strong>{" "}
                {selectedNode.type}
              </p>

              <p>
                <strong>Description:</strong>{" "}
                {selectedNode.description ||
                  "No description available"}
              </p>

              <p>
                <strong>Key:</strong>{" "}
                {selectedNode.id}
              </p>

            </>

          ) : (

            <p>
              Click a graph node to see its details.
            </p>

          )}

        </div>

      </div>

      {graphData && (

        <div className="graph-counts">

          <span>
            Nodes: {graphData.nodes.length}
          </span>

          <span>
            Relationships: {graphData.edges.length}
          </span>

        </div>

      )}

    </div>

  );

}

export default GraphVisualization;
