import React, { useState } from "react";
import Navigation from "./Navigation";
import LoanValidationUI from "./LoanValidationUI";
import CompareQueryApproachesUI from "./CompareQueryApproachesUI";

function App() {
  const [currentPage, setCurrentPage] = useState("loan-validation");

  const renderCurrentPage = () => {
    switch (currentPage) {
      case "loan-validation":
        return <LoanValidationUI />;
      case "compare-query":
        return <CompareQueryApproachesUI />;
      default:
        return <LoanValidationUI />;
    }
  };

  return (
    <div style={{ 
      minHeight: "100vh", 
      backgroundColor: "#f8f9fa",
      margin: 0,
      padding: 0
    }}>
      <Navigation 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage} 
      />
      {renderCurrentPage()}
    </div>
  );
}

export default App;
