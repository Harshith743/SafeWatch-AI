import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Pill, Trash2, Plus, AlertCircle } from 'lucide-react';

export default function MedicineCabinet() {
    const { token } = useAuth();
    const [medications, setMedications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [newDrug, setNewDrug] = useState('');
    const [newDosage, setNewDosage] = useState('');

    const fetchMedications = async () => {
        try {
            const res = await fetch('/api/user/medications', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to fetch medications');
            const data = await res.json();
            setMedications(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMedications();
    }, [token]);

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newDrug.trim()) return;

        try {
            const res = await fetch('/api/user/medications', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ drug_name: newDrug.trim(), dosage: newDosage.trim() })
            });
            if (!res.ok) throw new Error('Failed to add medication');

            setNewDrug('');
            setNewDosage('');
            fetchMedications();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDelete = async (id) => {
        try {
            const res = await fetch(`/api/user/medications/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to remove medication');
            fetchMedications();
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <div className="text-slate-400 py-4">Loading your cabinet...</div>;

    return (
        <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 shadow-xl mb-8">
            <div className="flex items-center gap-3 mb-6">
                <Pill className="text-teal-400" />
                <h2 className="text-xl font-semibold text-white">My Medicine Cabinet</h2>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-xl flex items-center gap-2 mb-4 text-sm">
                    <AlertCircle size={16} />
                    {error}
                </div>
            )}

            <form onSubmit={handleAdd} className="flex gap-4 mb-6">
                <input
                    type="text"
                    value={newDrug}
                    onChange={(e) => setNewDrug(e.target.value)}
                    placeholder="Drug name (e.g., Lisinopril)"
                    required
                    className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                />
                <input
                    type="text"
                    value={newDosage}
                    onChange={(e) => setNewDosage(e.target.value)}
                    placeholder="Dosage (Optional)"
                    className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                />
                <button
                    type="submit"
                    className="bg-teal-500 hover:bg-teal-400 text-white px-6 py-2 rounded-xl transition-all font-medium flex items-center gap-2"
                >
                    <Plus size={18} /> Add
                </button>
            </form>

            {medications.length === 0 ? (
                <div className="text-slate-500 text-center py-6 bg-slate-800/30 rounded-xl border border-slate-700/30">
                    Your medicine cabinet is empty. Add drugs you take actively so our AI can screen for safety interactions during chats.
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {medications.map((med) => (
                        <div key={med.id} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-start group">
                            <div>
                                <h3 className="font-semibold text-white capitalize">{med.drug_name}</h3>
                                {med.dosage && <p className="text-sm text-slate-400 mt-1">{med.dosage}</p>}
                            </div>
                            <button
                                onClick={() => handleDelete(med.id)}
                                className="text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 p-1.5 rounded-lg transition-colors opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100"
                                aria-label="Remove medication"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
