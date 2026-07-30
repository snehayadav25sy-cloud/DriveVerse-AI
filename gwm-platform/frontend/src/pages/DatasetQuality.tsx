import { useQuery } from '@tanstack/react-query';
import Navbar from '../components/Navbar';
import QualityGauge from '../components/QualityGauge';
import { ShieldCheck, AlertTriangle, Info, CheckCircle2, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function DatasetQuality() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['analyticsQuality'],
    queryFn: async () => {
      const res = await api.get('/analytics/quality');
      return res.data;
    },
    refetchInterval: 5000,
  });

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="text-emerald-400 shrink-0 mt-0.5" size={20} />;
      case 'warning':
        return <AlertTriangle className="text-amber-400 shrink-0 mt-0.5" size={20} />;
      default:
        return <Info className="text-blue-400 shrink-0 mt-0.5" size={20} />;
    }
  };

  const getBgClass = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200';
      case 'warning':
        return 'bg-amber-500/10 border-amber-500/20 text-amber-200';
      default:
        return 'bg-blue-500/10 border-blue-500/20 text-blue-200';
    }
  };

  return (
    <div className="animate-fade-in">
      <Navbar title="Dataset Quality" subtitle="Real-time quality analytics and validation metrics" />
      <div className="p-8 space-y-8">
        {isLoading ? (
          <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
            <Loader2 className="animate-spin" size={20} />
            <span>Computing real-time dataset metrics…</span>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card p-6 flex flex-col items-center justify-center text-center">
                <QualityGauge score={metrics?.overall_quality ?? 0} title="Overall Quality" />
                <p className="text-sm text-slate-400 mt-4 font-mono">
                  Based on {(metrics?.total_frames ?? 0).toLocaleString()} generated frames
                </p>
              </div>
              <div className="card p-6 flex flex-col items-center justify-center text-center">
                <QualityGauge score={metrics?.label_accuracy ?? 0} title="Label Accuracy" />
                <p className="text-sm text-slate-400 mt-4">
                  {(metrics?.total_annotations ?? 0).toLocaleString()} verified 2D/3D boxes
                </p>
              </div>
              <div className="card p-6 flex flex-col items-center justify-center text-center">
                <QualityGauge score={metrics?.scenario_diversity ?? 0} title="Scenario Diversity" />
                <p className="text-sm text-slate-400 mt-4">Environments & multi-sensor coverage</p>
              </div>
            </div>

            <div className="card p-6">
              <h3 className="section-title mb-4 flex items-center gap-2">
                <ShieldCheck className="text-brand-400" /> Dynamic Validation Report
              </h3>
              <div className="space-y-4">
                {metrics?.validation_report?.map((item: any, idx: number) => (
                  <div key={idx} className={`p-4 rounded-lg border flex gap-4 ${getBgClass(item.type)}`}>
                    {getIcon(item.type)}
                    <div>
                      <h4 className="font-semibold">{item.title}</h4>
                      <p className="text-sm text-slate-400 mt-1">{item.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
