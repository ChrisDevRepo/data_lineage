/**
 * Developer Panel Component (v0.9.0)
 *
 * Read-only panel for developers to:
 * - View recent logs (debugging)
 * - Browse YAML rules (read-only)
 * - Clear backend logs
 *
 * Note: Rule editing/reset must be done manually via filesystem
 */

import React, { useState, useEffect } from 'react';
import { X, RefreshCw, FileCode, Terminal, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../config';

interface LogEntry {
  text: string;
  level?: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
}

interface Rule {
  filename: string;
  name: string;
  description: string;
  priority: number;
  enabled: boolean;
  category: string;
  size_bytes: number;
}

interface DeveloperPanelProps {
  isOpen: boolean;
  onClose: () => void;
  dialect: string;
}

export function DeveloperPanel({ isOpen, onClose, dialect }: DeveloperPanelProps) {
  const [activeTab, setActiveTab] = useState<'logs' | 'rules'>('logs');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [selectedRule, setSelectedRule] = useState<string | null>(null);
  const [ruleContent, setRuleContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [currentLogLevel, setCurrentLogLevel] = useState<string>('');
  // Filtering state
  const [logFilter, setLogFilter] = useState<string>('');
  const [logLevelFilter, setLogLevelFilter] = useState<string>('ALL');
  const [ruleFilter, setRuleFilter] = useState<string>('');

  // Fetch current log level
  const fetchLogLevel = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/debug/log-level`, { credentials: 'same-origin' });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setCurrentLogLevel(data.log_level);
    } catch (err) {
      console.error('Failed to fetch log level:', err);
      // Don't show error to user, just log it
    }
  };

  // Fetch logs
  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/debug/logs?lines=500`, { credentials: 'same-origin' });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      const parsedLogs = data.logs.map((line: string) => {
        let level: LogEntry['level'] = undefined;
        if (line.includes(' ERROR ')) level = 'ERROR';
        else if (line.includes(' WARNING ')) level = 'WARNING';
        else if (line.includes(' INFO ')) level = 'INFO';
        else if (line.includes(' DEBUG ')) level = 'DEBUG';

        return { text: line, level };
      });

      setLogs(parsedLogs);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to fetch logs: ${errorMsg}`);
      console.error('Fetch logs error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch rules
  const fetchRules = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/rules/${dialect}`, { credentials: 'same-origin' });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setRules(data.rules || []);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to fetch rules: ${errorMsg}`);
      console.error('Fetch rules error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch rule content
  const fetchRuleContent = async (filename: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/rules/${dialect}/${filename}`, { credentials: 'same-origin' });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setRuleContent(data.content);
      setSelectedRule(filename);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to fetch rule ${filename}: ${errorMsg}`);
      console.error('Fetch rule content error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Clear backend log file
  const confirmClearLogs = async () => {
    setShowClearConfirm(false);

    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/debug/logs/clear`, {
        method: 'DELETE',
        credentials: 'same-origin'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Clear UI state and refresh to show empty log
        setLogs([]);
        await fetchLogs();
      } else {
        setError(data.message || 'Failed to clear logs');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to clear logs: ${errorMsg}`);
      console.error('Clear logs error:', err);
    } finally {
      setLoading(false);
    }
  };


  // Load data when tab changes or panel opens
  useEffect(() => {
    if (!isOpen) return;

    // Always fetch log level when panel opens
    fetchLogLevel();

    if (activeTab === 'logs') {
      fetchLogs();
    } else if (activeTab === 'rules') {
      fetchRules();
    }
  }, [isOpen, activeTab, dialect]);

  // Filter logs
  const filteredLogs = logs.filter(log => {
    const matchesText = logFilter === '' || log.text.toLowerCase().includes(logFilter.toLowerCase());
    const matchesLevel = logLevelFilter === 'ALL' || log.level === logLevelFilter;
    return matchesText && matchesLevel;
  });

  // Filter rules
  const filteredRules = rules.filter(rule => {
    return ruleFilter === '' ||
      rule.filename.toLowerCase().includes(ruleFilter.toLowerCase()) ||
      rule.name.toLowerCase().includes(ruleFilter.toLowerCase());
  });

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold">Developer Panel</h2>
            {currentLogLevel && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                currentLogLevel === 'DEBUG'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {currentLogLevel} Mode
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab('logs')}
          className={`px-6 py-3 font-medium ${
            activeTab === 'logs'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            <span>Logs</span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`px-6 py-3 font-medium ${
            activeTab === 'rules'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <FileCode className="w-4 h-4" />
            <span>YAML Rules ({dialect})</span>
          </div>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-3 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-700">{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="h-full flex flex-col">
            <div className="p-4 bg-gray-50 border-b">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-600">
                  Showing {filteredLogs.length} of {logs.length} log entries
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowClearConfirm(true)}
                    disabled={loading}
                    className="flex items-center gap-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400 text-sm"
                  >
                    <X className="w-4 h-4" />
                    <span>Clear</span>
                  </button>
                  <button
                    onClick={() => {
                      fetchLogs();
                      fetchLogLevel();
                    }}
                    disabled={loading}
                    className="flex items-center gap-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Filter logs..."
                  value={logFilter}
                  onChange={(e) => setLogFilter(e.target.value)}
                  className="flex-1 px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select
                  value={logLevelFilter}
                  onChange={(e) => setLogLevelFilter(e.target.value)}
                  className="px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ALL">All Levels</option>
                  <option value="ERROR">ERROR</option>
                  <option value="WARNING">WARNING</option>
                  <option value="INFO">INFO</option>
                  <option value="DEBUG">DEBUG</option>
                </select>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 bg-gray-900 font-mono text-xs text-gray-300">
              {filteredLogs.map((log, index) => (
                <div
                  key={index}
                  className={`py-1 ${
                    log.level === 'ERROR' ? 'text-red-400' :
                    log.level === 'WARNING' ? 'text-yellow-400' :
                    log.level === 'DEBUG' ? 'text-blue-300' :
                    'text-gray-300'
                  }`}
                >
                  {log.text}
                </div>
              ))}
              {filteredLogs.length === 0 && (
                <div className="text-gray-500 text-center py-4">No logs match the filter</div>
              )}
            </div>
          </div>
        )}

        {/* Rules Tab */}
        {activeTab === 'rules' && (
          <div className="h-full flex">
            {/* Rules List */}
            <div className="w-1/3 border-r overflow-auto">
              <div className="p-4 bg-gray-50 border-b">
                <div className="mb-3">
                  <span className="text-sm font-medium">{filteredRules.length} of {rules.length} Rules</span>
                </div>
                <input
                  type="text"
                  placeholder="Filter rules..."
                  value={ruleFilter}
                  onChange={(e) => setRuleFilter(e.target.value)}
                  className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="divide-y">
                {filteredRules.map((rule) => (
                  <button
                    key={rule.filename}
                    onClick={() => fetchRuleContent(rule.filename)}
                    className={`w-full text-left p-3 hover:bg-blue-50 transition-colors ${
                      selectedRule === rule.filename ? 'bg-blue-100' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-mono text-sm font-medium text-gray-900">
                          {rule.filename}
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                          {rule.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Priority: {rule.priority} | {rule.category}
                        </div>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs ${
                        rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {rule.enabled ? 'Enabled' : 'Disabled'}
                      </div>
                    </div>
                  </button>
                ))}
                {filteredRules.length === 0 && (
                  <div className="text-gray-500 text-center py-4">No rules match the filter</div>
                )}
              </div>
            </div>

            {/* Rule Content */}
            <div className="flex-1 overflow-auto bg-gray-900">
              {ruleContent ? (
                <pre className="p-4 text-gray-300 font-mono text-xs">
                  {ruleContent}
                </pre>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  Select a rule to view its content
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      </div>

      {/* Confirmation Modal for Clear Logs */}
      {showClearConfirm && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/50 z-[60]" onClick={() => setShowClearConfirm(false)} />

          {/* Modal */}
          <div className="fixed inset-0 z-[61] flex items-center justify-center p-4 pointer-events-none">
            <div className="bg-white rounded-lg shadow-2xl max-w-md w-full pointer-events-auto" onClick={(e) => e.stopPropagation()}>
              {/* Header */}
              <div className="flex items-center gap-3 px-6 py-4 border-b">
                <AlertCircle className="w-6 h-6 text-red-600" />
                <h3 className="text-lg font-semibold text-gray-900">Clear Log File</h3>
              </div>

              {/* Content */}
              <div className="px-6 py-4">
                <p className="text-gray-700">
                  Are you sure you want to clear the backend log file? This action cannot be undone.
                </p>
              </div>

              {/* Footer with buttons */}
              <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 rounded-b-lg">
                <button
                  onClick={() => setShowClearConfirm(false)}
                  autoFocus
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 font-medium focus:outline-none focus:ring-2 focus:ring-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmClearLogs}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-medium focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
