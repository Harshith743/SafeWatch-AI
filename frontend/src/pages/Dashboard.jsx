import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Clock, FileText, AlertCircle, ArrowLeft, Download } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
    const { token, user } = useAuth();
    const [history, setHistory] = useState([]);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const headers = { 'Authorization': `Bearer ${token}` };

                // Fetch search history
                const historyRes = await fetch('/api/user/history', { headers });
                if (historyRes.status === 401) {
                    logout();
                    return;
                }
                if (!historyRes.ok) throw new Error('Failed to fetch history');
                const historyData = await historyRes.json();

                // Fetch user reports
                const reportsRes = await fetch('/api/user/reports', { headers });
                if (reportsRes.status === 401) {
                    logout();
                    return;
                }
                if (!reportsRes.ok) throw new Error('Failed to fetch reports');
                const reportsData = await reportsRes.json();

                setHistory(historyData);
                setReports(reportsData);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchDashboardData();
        }
    }, [token]);

    const handleDownloadReport = async (reportId) => {
        try {
            const response = await fetch(`/api/export/report/${reportId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                if (response.status === 401) logout();
                throw new Error('Failed to download report PDF');
            }

            // Convert byte stream to blob
            const blob = await response.blob();
            // Create a temporary link element to trigger the download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `safewatch_report_${reportId}.pdf`;
            document.body.appendChild(a);
            a.click();

            // Clean up
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) {
        return <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">Loading Dashboard...</div>;
    }

    return (
        <div className="min-h-screen bg-[#0A0C10] text-slate-200 p-8 w-full flex justify-center">
            <div className="max-w-5xl w-full">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">User Dashboard</h1>
                        <p className="text-slate-400">Welcome back, {user?.username} ({user?.email})</p>
                    </div>
                    <Link to="/" className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-all shadow-md">
                        <ArrowLeft size={18} />
                        Back to Chat
                    </Link>
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl flex items-center gap-3 mb-8">
                        <AlertCircle size={20} />
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Search History Column */}
                    <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 shadow-xl">
                        <div className="flex items-center gap-3 mb-6">
                            <Clock className="text-indigo-400" />
                            <h2 className="text-xl font-semibold text-white">Search History</h2>
                        </div>

                        {history.length === 0 ? (
                            <div className="text-slate-500 text-center py-8">No search history found.</div>
                        ) : (
                            <div className="space-y-3">
                                {history.map((record) => (
                                    <div key={record.id} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 hover:bg-slate-800 transition-colors">
                                        <div className="font-semibold text-white text-lg capitalize">{record.drug}</div>
                                        <div className="text-xs text-slate-500 mt-2">
                                            {new Date(record.timestamp).toLocaleString()}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Submitted Reports Column */}
                    <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 shadow-xl">
                        <div className="flex items-center gap-3 mb-6">
                            <FileText className="text-rose-400" />
                            <h2 className="text-xl font-semibold text-white">Submitted Reports</h2>
                        </div>

                        {reports.length === 0 ? (
                            <div className="text-slate-500 text-center py-8">No reports submitted yet.</div>
                        ) : (
                            <div className="space-y-4">
                                {reports.map((report) => (
                                    <div key={report.id} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 hover:bg-slate-800 transition-colors">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="font-semibold text-white text-lg capitalize">{report.drug}</div>
                                            <div className="flex gap-2 items-center">
                                                <span className="px-2 py-1 bg-rose-500/10 text-rose-400 text-xs rounded-full font-medium">Report #{report.id}</span>
                                                <button
                                                    onClick={() => handleDownloadReport(report.id)}
                                                    className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg transition-colors border border-slate-700 hover:border-slate-600"
                                                    title="Download PDF Report"
                                                >
                                                    <Download size={14} />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="text-slate-300 mb-3">{report.reaction}</div>

                                        <div className="flex gap-4 text-xs text-slate-400 bg-slate-900/50 p-2 rounded-lg">
                                            <div><span className="text-slate-500">Age:</span> {report.age || 'N/A'}</div>
                                            <div><span className="text-slate-500">Gender:</span> {report.gender || 'N/A'}</div>
                                        </div>

                                        <div className="text-xs text-slate-500 mt-4 text-right">
                                            {new Date(report.timestamp).toLocaleString()}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
