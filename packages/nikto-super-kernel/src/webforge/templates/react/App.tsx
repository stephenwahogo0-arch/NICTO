import React from 'react';

interface AppProps {
  title: string;
  message: string;
}

const App: React.FC<AppProps> = ({ title, message }) => {
  return (
    <div className="app">
      <header>
        <h1>{title}</h1>
      </header>
      <main>
        <p>{message}</p>
        <div className="dashboard">
          <div className="card">
            <h3>Boot Status</h3>
            <p id="boot-status">Loading...</p>
          </div>
          <div className="card">
            <h3>Neural Memory</h3>
            <p id="neural-count">0 records</p>
          </div>
          <div className="card">
            <h3>Swarm Agents</h3>
            <p id="swarm-count">0 connected</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
