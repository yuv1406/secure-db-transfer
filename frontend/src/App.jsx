import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [config, setConfig] = useState({
    mysql_host: 'localhost',
    mysql_port: 3306,
    mysql_username: 'user',
    mysql_password: 'password',
    mysql_database: 'source_db',
    postgres_host: 'localhost',
    postgres_port: 5432,
    postgres_username: 'user',
    postgres_password: 'password',
    postgres_database: 'target_db'
  });

  const [progress, setProgress] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('transfer'); // transfer, audit, query
  const [testResult, setTestResult] = useState(null);
  
  // SQL Console state
  const [sqlTarget, setSqlTarget] = useState('source');
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM users LIMIT 5');
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: name.includes('port') ? parseInt(value) : value }));
  };

  const testConnection = async () => {
    setTestResult({ status: 'testing', message: 'Testing connections...' });
    try {
      const resp = await fetch(`${API_BASE}/test-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await resp.json();
      setTestResult(data);
      setTimeout(() => setTestResult(null), 5000);
    } catch (err) {
      setTestResult({ status: 'error', message: 'Failed to reach API' });
    }
  };

  const startTransfer = async () => {
    try {
      const resp = await fetch(`${API_BASE}/start-transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (resp.ok) {
        pollProgress();
      }
    } catch (err) {
      console.error("Failed to start transfer", err);
    }
  };

  const pollProgress = async () => {
    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`${API_BASE}/progress`);
        const data = await resp.json();
        setProgress(data);
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval);
          fetchAuditLogs();
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 1000);
  };

  const fetchAuditLogs = async () => {
    try {
      const resp = await fetch(`${API_BASE}/audit-logs`);
      const data = await resp.json();
      setAuditLogs(data.reverse());
    } catch (err) {
      console.error("Failed to fetch audit logs", err);
    }
  };

  const executeQuery = async () => {
    setQueryLoading(true);
    setQueryResult(null);
    try {
      const resp = await fetch(`${API_BASE}/execute-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config,
          target: sqlTarget,
          query: sqlQuery
        })
      });
      const data = await resp.json();
      setQueryResult(data);
    } catch (err) {
      setQueryResult({ error: "Failed to execute query" });
    }
    setQueryLoading(false);
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  return (
    <div className="app-container">
      <div className="sidebar">
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Collections</h2>
        </div>
        <div 
          className={`sidebar-item ${activeTab === 'transfer' ? 'active' : ''}`} 
          onClick={() => setActiveTab('transfer')}
          style={{ padding: '12px 20px', fontSize: '13px', cursor: 'pointer', backgroundColor: activeTab === 'transfer' ? 'var(--bg-tertiary)' : 'transparent' }}
        >
          🚀 DB Transfer Pipeline
        </div>
        <div 
          className={`sidebar-item ${activeTab === 'query' ? 'active' : ''}`} 
          onClick={() => setActiveTab('query')}
          style={{ padding: '12px 20px', fontSize: '13px', cursor: 'pointer', backgroundColor: activeTab === 'query' ? 'var(--bg-tertiary)' : 'transparent' }}
        >
          🔍 SQL Query Console
        </div>
        <div 
          className={`sidebar-item ${activeTab === 'audit' ? 'active' : ''}`} 
          onClick={() => setActiveTab('audit')}
          style={{ padding: '12px 20px', fontSize: '13px', cursor: 'pointer', backgroundColor: activeTab === 'audit' ? 'var(--bg-tertiary)' : 'transparent' }}
        >
          📜 Audit Trail
        </div>
      </div>

      <div className="main-content">
        <div className="header">
          <h1>{activeTab === 'transfer' ? 'Project: Secure Hybrid Transfer' : activeTab === 'query' ? 'SQL Console' : 'Immutable Audit Logs'}</h1>
          <div style={{ display: 'flex', gap: '10px' }}>
            <span className={`status-badge ${progress?.status || 'idle'}`}>
              {progress?.status || 'offline'}
            </span>
          </div>
        </div>

        <div style={{ padding: '30px', maxWidth: '1000px' }}>
          {activeTab === 'transfer' ? (
            <div className="transfer-view">
              <div className="card">
                <h3 style={{ marginBottom: '20px', fontSize: '14px' }}>Connection Configuration</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <div className="source-config">
                    <h4 style={{ color: 'var(--accent-primary)', fontSize: '12px', marginBottom: '15px' }}>SOURCE DATABASE</h4>
                    <div className="form-group" style={{ display: 'flex', gap: '10px' }}>
                      <div style={{ flex: 2 }}>
                        <label>Host Address</label>
                        <input className="form-input" name="mysql_host" value={config.mysql_host} onChange={handleInputChange} placeholder="e.g. localhost" />
                      </div>
                      <div style={{ flex: 1 }}>
                        <label>Port</label>
                        <input className="form-input" name="mysql_port" type="number" value={config.mysql_port} onChange={handleInputChange} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>User</label>
                      <input className="form-input" name="mysql_username" value={config.mysql_username} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                      <label>Password</label>
                      <input className="form-input" type="password" name="mysql_password" value={config.mysql_password} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                      <label>DB Name</label>
                      <input className="form-input" name="mysql_database" value={config.mysql_database} onChange={handleInputChange} />
                    </div>
                  </div>
                  <div className="dest-config">
                    <h4 style={{ color: 'var(--success)', fontSize: '12px', marginBottom: '15px' }}>DESTINATION DATABASE</h4>
                    <div className="form-group" style={{ display: 'flex', gap: '10px' }}>
                      <div style={{ flex: 2 }}>
                        <label>Host Address</label>
                        <input className="form-input" name="postgres_host" value={config.postgres_host} onChange={handleInputChange} placeholder="e.g. localhost" />
                      </div>
                      <div style={{ flex: 1 }}>
                        <label>Port</label>
                        <input className="form-input" name="postgres_port" type="number" value={config.postgres_port} onChange={handleInputChange} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>User</label>
                      <input className="form-input" name="postgres_username" value={config.postgres_username} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                      <label>Password</label>
                      <input className="form-input" type="password" name="postgres_password" value={config.postgres_password} onChange={handleInputChange} />
                    </div>
                    <div className="form-group">
                      <label>DB Name</label>
                      <input className="form-input" name="postgres_database" value={config.postgres_database} onChange={handleInputChange} />
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                  <button className="button" onClick={startTransfer} disabled={progress?.status === 'running'}>
                    {progress?.status === 'running' ? 'Transferring...' : 'Start Transfer'}
                  </button>
                  <button className="button secondary" onClick={testConnection}>Test Connection</button>
                </div>
                {testResult && (
                  <div style={{ 
                    marginTop: '15px', 
                    fontSize: '12px', 
                    padding: '8px', 
                    borderRadius: '4px',
                    backgroundColor: testResult.status === 'success' ? 'rgba(12, 187, 82, 0.1)' : 'rgba(235, 32, 19, 0.1)',
                    color: testResult.status === 'success' ? 'var(--success)' : 'var(--error)',
                    border: `1px solid ${testResult.status === 'success' ? 'var(--success)' : 'var(--error)'}`
                  }}>
                    {testResult.message}
                  </div>
                )}
              </div>

              {progress && (
                <div className="card">
                  <h3 style={{ marginBottom: '20px', fontSize: '14px' }}>Execution Progress</h3>
                  <div style={{ marginBottom: '15px', color: 'var(--accent-primary)', fontWeight: 'bold' }}>
                    Current Step: {progress.current_step}
                  </div>
                  <div className="log-container">
                    {progress.logs.map((log, i) => (
                      <div key={i}>{log}</div>
                    ))}
                  </div>
                  {progress.status === 'completed' && (
                    <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>PRE-TRANSFER HASH</label>
                          <div style={{ fontSize: '12px', wordBreak: 'break-all' }}>{progress.result?.hash_before}</div>
                        </div>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>POST-TRANSFER HASH</label>
                          <div style={{ fontSize: '12px', wordBreak: 'break-all' }}>{progress.result?.hash_after}</div>
                        </div>
                      </div>
                      <div style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '20px' }}>
                        <div style={{ color: progress.result?.success ? 'var(--success)' : 'var(--error)', fontWeight: 'bold' }}>
                           INTEGRITY CHECK: {progress.result?.success ? 'PASS' : 'FAIL'}
                        </div>
                        <a href={`${API_BASE}/download-report`} className="button secondary" style={{ textDecoration: 'none' }}>
                          Download PDF Audit Report
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : activeTab === 'query' ? (
            <div className="query-view">
              <div className="card">
                <h3 style={{ marginBottom: '20px', fontSize: '14px' }}>Database Query Console</h3>
                <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <label style={{ fontSize: '13px' }}>Target:</label>
                    <select 
                      className="form-input" 
                      style={{ width: '150px' }} 
                      value={sqlTarget} 
                      onChange={(e) => setSqlTarget(e.target.value)}
                    >
                      <option value="source">Source (MySQL)</option>
                      <option value="destination">Destination (Postgres)</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <textarea 
                    className="form-input" 
                    style={{ height: '100px', fontFamily: 'monospace', resize: 'vertical' }}
                    value={sqlQuery}
                    onChange={(e) => setSqlQuery(e.target.value)}
                    placeholder="Enter SQL query..."
                  />
                </div>
                <button 
                  className="button" 
                  onClick={executeQuery} 
                  disabled={queryLoading}
                >
                  {queryLoading ? 'Executing...' : 'Run Query'}
                </button>

                {queryResult && (
                  <div style={{ marginTop: '20px' }}>
                    <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Results</h4>
                    <div className="log-container" style={{ color: '#fff', maxHeight: '400px' }}>
                      {queryResult.error ? (
                        <span style={{ color: 'var(--error)' }}>{queryResult.error || JSON.stringify(queryResult)}</span>
                      ) : Array.isArray(queryResult) ? (
                        queryResult.length === 0 ? (
                          <span>No records found.</span>
                        ) : (
                          <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                              <thead>
                                <tr>
                                  {Object.keys(queryResult[0]).map(k => (
                                    <th key={k} style={{ textAlign: 'left', padding: '5px', borderBottom: '1px solid #333' }}>{k}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {queryResult.map((row, i) => (
                                  <tr key={i}>
                                    {Object.values(row).map((v, j) => (
                                      <td key={j} style={{ padding: '5px', borderBottom: '1px solid #222' }}>{String(v)}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )
                      ) : (
                        <pre>{JSON.stringify(queryResult, null, 2)}</pre>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="audit-view">
              <div className="card">
                <h3 style={{ marginBottom: '20px', fontSize: '14px' }}>Immutable Audit Trail (Hash Chained)</h3>
                <table className="audit-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Transfer Status</th>
                      <th>Current Entry Hash</th>
                      <th>Previous Hash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log, i) => (
                      <tr key={i}>
                        <td>{new Date(log.timestamp).toLocaleString()}</td>
                        <td><span className={`status-badge ${log.data.transfer_status.toLowerCase()}`}>{log.data.transfer_status}</span></td>
                        <td style={{ fontSize: '10px', wordBreak: 'break-all' }}>{log.current_hash}</td>
                        <td style={{ fontSize: '10px', wordBreak: 'break-all' }}>{log.previous_hash.substring(0, 16)}...</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
      <style>{`
        .sidebar-item.active { background-color: var(--bg-tertiary) !important; color: var(--accent-primary) !important; border-left: 3px solid var(--accent-primary); }
        .sidebar-item:hover { background-color: var(--bg-tertiary); }
      `}</style>
    </div>
  );
}

export default App;
