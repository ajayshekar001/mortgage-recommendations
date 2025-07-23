import React from "react";

export default function Navigation({ currentPage, setCurrentPage }) {
  const navStyle = {
    backgroundColor: "#343a40",
    padding: "15px 0",
    marginBottom: "20px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
  };

  const containerStyle = {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "0 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  };

  const logoStyle = {
    color: "white",
    fontSize: "24px",
    fontWeight: "bold",
    margin: 0
  };

  const navLinksStyle = {
    display: "flex",
    gap: "20px",
    listStyle: "none",
    margin: 0,
    padding: 0
  };

  const linkStyle = {
    color: "white",
    textDecoration: "none",
    padding: "10px 20px",
    borderRadius: "4px",
    fontSize: "16px",
    transition: "background-color 0.3s ease",
    cursor: "pointer"
  };

  const activeLinkStyle = {
    ...linkStyle,
    backgroundColor: "#007bff"
  };

  const inactiveLinkStyle = {
    ...linkStyle,
    backgroundColor: "transparent"
  };

  return (
    <nav style={navStyle}>
      <div style={containerStyle}>
        <h1 style={logoStyle}>Loan Processing System</h1>
        <ul style={navLinksStyle}>
          <li>
            <span
              style={currentPage === "loan-validation" ? activeLinkStyle : inactiveLinkStyle}
              onClick={() => setCurrentPage("loan-validation")}
              onMouseEnter={(e) => {
                if (currentPage !== "loan-validation") {
                  e.target.style.backgroundColor = "#495057";
                }
              }}
              onMouseLeave={(e) => {
                if (currentPage !== "loan-validation") {
                  e.target.style.backgroundColor = "transparent";
                }
              }}
            >
              Loan Validation
            </span>
          </li>
          <li>
            <span
              style={currentPage === "compare-query" ? activeLinkStyle : inactiveLinkStyle}
              onClick={() => setCurrentPage("compare-query")}
              onMouseEnter={(e) => {
                if (currentPage !== "compare-query") {
                  e.target.style.backgroundColor = "#495057";
                }
              }}
              onMouseLeave={(e) => {
                if (currentPage !== "compare-query") {
                  e.target.style.backgroundColor = "transparent";
                }
              }}
            >
              Compare Query
            </span>
          </li>
        </ul>
      </div>
    </nav>
  );
} 