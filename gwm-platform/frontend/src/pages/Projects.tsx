import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { PlusCircle, Folder } from 'lucide-react';
import Navbar from '../components/Navbar';
import api from '../services/api';

export default function Projects() {
  const { token } = useAuth();
  const [projects, setProjects] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const fetchProjects = async () => {
    try {
      const res = await api.get('/projects');
      setProjects(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (token) fetchProjects();
  }, [token]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/projects', { name, description });
      setShowModal(false);
      setName('');
      setDescription('');
      fetchProjects();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="animate-fade-in">
      <Navbar title="Projects" subtitle="Manage your simulation workspaces" />

      <div className="p-8 space-y-6">
        <div className="flex justify-end">
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <PlusCircle size={16} /> New Project
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.length === 0 ? (
            <div className="card p-12 col-span-full flex flex-col items-center justify-center text-slate-500">
              <Folder size={48} className="mb-4 text-slate-700" />
              <p>You haven't created any projects yet.</p>
            </div>
          ) : (
            projects.map(proj => (
              <div key={proj.id} className="card p-6 flex flex-col gap-3 group hover:border-brand-500/30 transition-colors">
                <div className="flex items-center gap-3 text-slate-200 font-semibold text-lg">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 group-hover:bg-brand-500/20 transition-colors">
                    <Folder size={18} className="text-slate-400 group-hover:text-brand-400 transition-colors" />
                  </div>
                  {proj.name}
                </div>
                <p className="text-slate-400 text-sm flex-1 leading-relaxed">{proj.description}</p>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => window.location.href='/generate'} className="btn-primary flex-1 py-1.5 text-xs flex justify-center">
                    Generate Dataset
                  </button>
                </div>
                <div className="pt-4 border-t border-slate-800/60 flex justify-between items-center mt-2">
                  <span className="text-xs text-slate-500 font-mono">{proj.id.slice(0, 8)}</span>
                  <p className="text-xs text-slate-500">Created {new Date(proj.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))
          )}
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
            <div className="card p-6 w-full max-w-md shadow-2xl shadow-brand-500/10 border border-slate-700 animate-slide-up">
              <h2 className="text-xl font-bold mb-4 text-white">Create New Project</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="label">Project Name</label>
                  <input required type="text" value={name} onChange={e => setName(e.target.value)} className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all placeholder-slate-500" placeholder="e.g. Tokyo Night Dataset" />
                </div>
                <div>
                  <label className="label">Description</label>
                  <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all placeholder-slate-500" placeholder="Optional context..." rows={3}></textarea>
                </div>
                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
                  <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancel</button>
                  <button type="submit" className="btn-primary">Create</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
