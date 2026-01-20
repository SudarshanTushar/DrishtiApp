import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { HardwareManager } from '../services/HardwareManager';
import BroadcastModal from './BroadcastModal';
import SafeMap from './SafeMap';
import DroneScanner from './DroneScanner';

// Keep the cool GIF for the "Waiting" state
const DRONE_IDLE_GIF = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmZ5Z3l5aWd5aWd5aWd5aWd5aWd5aWd5aWd5aWd5aWd5aSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKsAdsDqYkR8D0Q/giphy.gif"; 

export default function CommandDashboard({ apiUrl, isConnected, sensors, onOpenReport }) {
  const [sosList, setSosList] = useState([]);
  const [systemTime, setSystemTime] = useState(new Date().toLocaleTimeString());
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [droneMode, setDroneMode] = useState("IDLE"); // IDLE, SCANNING
  const [droneFile, setDroneFile] = useState(null);
  const [pendingDecisions, setPendingDecisions] = useState([]); // Governance Queue

  // 1. CLOCK & SOS SIMULATION
  useEffect(() => {
    const timer = setInterval(() => setSystemTime(new Date().toLocaleTimeString()), 1000);
    
    // Simulate random SOS calls (ambient noise for the demo)
    const sosInterval = setInterval(() => {
        if (Math.random() > 0.85) { 
            const newSOS = {
                id: Math.floor(Math.random() * 9000) + 1000,
                type: Math.random() > 0.5 ? "MEDICAL" : "FLOOD",
                time: new Date().toLocaleTimeString(),
                lat: 26.1 + (Math.random() * 0.05),
                lng: 91.7 + (Math.random() * 0.05),
                status: "PENDING"
            };
            setSosList(prev => [newSOS, ...prev].slice(0, 7));
            try { HardwareManager.vibrate('error'); } catch(e){} 
        }
    }, 4000);
    return () => { clearInterval(timer); clearInterval(sosInterval); };
  }, []);

  // 2. POLL FOR PENDING DECISIONS (GOVERNANCE)
  useEffect(() => {
    if(!isConnected) return;
    const fetchDecisions = async () => {
        try {
            const res = await axios.get(`${apiUrl}/admin/governance/pending`);
            setPendingDecisions(res.data);
            if(res.data.length > 0) HardwareManager.vibrate('pulse'); // Alert the Commander
        } catch(e) {}
    };
    const interval = setInterval(fetchDecisions, 3000);
    return () => clearInterval(interval);
  }, [isConnected, apiUrl]);

  // 3. ACTION HANDLERS
  const handleDecision = async (id, action) => {
    try {
        await axios.post(`${apiUrl}/admin/governance/decide?decision_id=${id}&action=${action}&admin_notes=Verified via CCTV`, {});
        alert(action === "APPROVE" ? "✅ ORDER AUTHORIZED & EXECUTED" : "❌ ORDER REJECTED");
        setPendingDecisions(prev => prev.filter(d => d.id !== id));
    } catch(e) { alert("Error submitting decision"); }
  };

  const handleToggleSimulation = async () => {
      try {
          if (pendingDecisions.length > 0) {
              await axios.post(`${apiUrl}/admin/simulate/stop`);
              setPendingDecisions([]); // Clear local state immediately
              alert("✅ DRILL STOPPED. System Normal.");
          } else {
              await axios.post(`${apiUrl}/admin/simulate/start?scenario=FLASH_FLOOD`);
              alert("🚨 DRILL INITIATED: Flash Flood Scenario Active.");
              // The polling useEffect will catch the new decision in 3 seconds
          }
      } catch (e) {
          console.error(e);
          alert("Connection Error: Could not toggle simulation.");
      }
  };

  const handleGenerateRealReport = () => {
    const realStats = {
        risk: "HIGH",
        active_units: 3,
        sensors_online: sensors ? sensors.length : 0,
        sos_pending: sosList.length
    };
    onOpenReport({
        title: "Situation Report (SITREP)",
        date: new Date().toLocaleString(),
        content: `ALERT: Critical water levels detected in Sector 4. \n\nDeployed Units: 3 NDRF Teams.\nPending SOS: ${sosList.length}.\nRecommendation: Immediate Evacuation of Low-Lying Zones.`,
        stats: realStats,
        logs: sosList
    });
  };

  return (
    <div className="absolute inset-0 bg-slate-950 text-slate-100 font-mono flex flex-col z-[2000] overflow-y-auto selection:bg-emerald-500/30">
      
      {/* 1. TOP COMMAND HEADER */}
      <div className="bg-slate-900 border-b border-slate-800 p-4 flex justify-between items-center shadow-2xl sticky top-0 z-50">
        <div className="flex items-center gap-4">
            <div className="relative">
                <div className={`w-3 h-3 rounded-full absolute inset-0 ${pendingDecisions.length > 0 ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`}></div>
                <div className={`w-3 h-3 rounded-full relative ${pendingDecisions.length > 0 ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
            </div>
            <div>
                <h1 className="text-xl font-black tracking-[0.2em] text-white leading-none">NETRA <span className="text-slate-600">|</span> COMMAND</h1>
                <div className="text-[9px] text-emerald-500 font-bold mt-1">
                    {pendingDecisions.length > 0 ? <span className="text-red-500 animate-pulse">⚠ THREAT DETECTED</span> : "SECURE UPLINK ESTABLISHED"}
                </div>
            </div>
        </div>
        
        {/* ACTION BUTTONS */}
        <div className="flex gap-2">
            {/* SIMULATION TOGGLE */}
            <button 
                onClick={handleToggleSimulation}
                className={`px-3 py-1 rounded text-[10px] font-bold tracking-widest border transition-all ${
                    pendingDecisions.length > 0 
                    ? "bg-slate-800 border-slate-600 text-slate-400 hover:bg-slate-700" 
                    : "bg-amber-900/20 border-amber-500/50 text-amber-500 hover:bg-amber-900/40"
                }`}
            >
                {pendingDecisions.length > 0 ? "🛑 END DRILL" : "⚠️ START SIM"}
            </button>

            <button 
                onClick={() => setShowBroadcast(true)}
                className="bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded text-[10px] font-bold tracking-widest animate-pulse shadow-[0_0_15px_rgba(220,38,38,0.5)]"
            >
                📢 BROADCAST
            </button>
            
            <div className="flex flex-col items-end hidden md:flex">
                <span className="text-[9px] text-slate-500">SYSTEM TIME</span>
                <span className="text-white text-sm font-bold">{systemTime}</span>
            </div>
        </div>
      </div>

      <div className="p-4 grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* GOVERNANCE / APPROVAL DECK (Visible only when decisions pending) */}
        {pendingDecisions.length > 0 && (
            <div className="lg:col-span-12 bg-red-900/20 border border-red-500 rounded-xl p-4 animate-pulse-slow">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-sm font-black text-red-400 flex items-center gap-2">
                        ⚠️ PENDING AUTHORIZATION ({pendingDecisions.length})
                    </h2>
                    <div className="text-[10px] bg-red-500 text-white px-2 py-1 rounded font-bold">ACTION REQUIRED</div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {pendingDecisions.map(d => (
                        <div key={d.id} className="bg-slate-900 border-l-4 border-red-500 p-4 rounded shadow-xl relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-5 text-6xl font-black text-white pointer-events-none">CONFIDENTIAL</div>
                            
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-mono text-xs text-slate-400">ID: {d.id}</span>
                                <span className="font-bold text-xs text-red-400">{d.urgency} PRIORITY</span>
                            </div>
                            
                            <h3 className="text-lg font-black text-white mb-1">{d.type.replace(/_/g, " ")}</h3>
                            <p className="text-sm text-slate-300 mb-4 leading-relaxed">
                                <span className="text-slate-500">REASON:</span> {d.reason}<br/>
                                <span className="text-slate-500">SOURCE:</span> {d.source_intel} (Confidence: {d.ai_confidence}%)
                            </p>
                            
                            <div className="flex gap-3">
                                <button 
                                    onClick={() => handleDecision(d.id, "APPROVE")}
                                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded font-bold text-xs tracking-widest shadow-lg transition-transform hover:scale-105"
                                >
                                    AUTHORIZE (SIGN)
                                </button>
                                <button 
                                    onClick={() => handleDecision(d.id, "REJECT")}
                                    className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-400 py-3 rounded font-bold text-xs tracking-widest border border-slate-600"
                                >
                                    REJECT
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* 2. REAL MAP & SENSORS (Left Panel - 7 Cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
            <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden h-[350px] relative">
                <div className="absolute top-2 left-2 z-10 bg-black/80 text-emerald-400 text-[9px] px-2 py-1 rounded border border-emerald-500/30">
                    LIVE SATELLITE FEED
                </div>
                <SafeMap /> 
            </div>

            <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-4">
                <h2 className="text-xs font-bold text-slate-400 mb-2 flex items-center gap-2">📡 SENSOR TELEMETRY</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {sensors && sensors.length > 0 ? sensors.map(s => (
                        <div key={s.id} className="bg-slate-800/50 p-2 rounded border-l-2 border-emerald-500">
                            <div className="text-[9px] text-slate-500">{s.location}</div>
                            <div className="font-bold text-sm text-white">{s.value} <span className="text-[9px]">{s.unit}</span></div>
                        </div>
                    )) : <div className="text-[9px] text-slate-600 col-span-4 text-center">Connecting to Sensor Mesh...</div>}
                </div>
            </div>
        </div>

        {/* 3. RIGHT PANEL (Drone & SOS - 5 Cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-1 backdrop-blur-sm relative overflow-hidden">
                <div className="bg-black aspect-video rounded border border-slate-800 relative overflow-hidden flex items-center justify-center">
                    {droneMode === 'IDLE' ? (
                        <img src={DRONE_IDLE_GIF} alt="Drone Feed" className="w-full h-full object-cover opacity-60" />
                    ) : (
                        <div className="w-full h-full bg-slate-900 p-2">
                             <DroneScanner 
                                file={droneFile} 
                                onAnalysisComplete={(res) => {
                                    alert(`DAMAGE DETECTED: ${res.damage_score}%\nAction: ${res.auto_action}`);
                                    setDroneMode("IDLE");
                                }} 
                                apiUrl={apiUrl} 
                            />
                        </div>
                    )}
                </div>

                <div className="p-2 grid grid-cols-2 gap-2">
                    <button 
                        onClick={() => setDroneMode(droneMode === 'IDLE' ? 'SCANNING' : 'IDLE')}
                        className="bg-blue-600 hover:bg-blue-500 text-white py-2 rounded text-[10px] font-bold tracking-widest"
                    >
                        {droneMode === 'IDLE' ? 'UPLOAD DRONE FOOTAGE' : 'CANCEL SCAN'}
                    </button>
                    <button 
                        onClick={handleGenerateRealReport}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded text-[10px] font-bold tracking-widest border border-slate-600"
                    >
                        GENERATE SITREP PDF
                    </button>
                </div>
            </div>

            <div className="flex-1 bg-slate-900/50 border border-slate-700/50 rounded-xl p-4 overflow-hidden flex flex-col">
                <div className="flex justify-between items-end border-b border-slate-700 pb-2 mb-2">
                    <h2 className="text-xs font-bold text-slate-400">🚨 SOS SIGNALS</h2>
                    <div className="text-[9px] text-red-500">{sosList.length} ACTIVE</div>
                </div>
                <div className="overflow-y-auto space-y-2 max-h-[250px]">
                    {sosList.map(sos => (
                        <div key={sos.id} className="bg-slate-800 p-2 rounded border-l-4 border-red-500 hover:bg-slate-700 cursor-pointer">
                            <div className="flex justify-between">
                                <span className="text-[10px] font-bold text-red-400">#{sos.id}</span>
                                <span className="text-[9px] text-slate-500">{sos.time}</span>
                            </div>
                            <div className="text-xs font-bold text-white">{sos.type} EMERGENCY</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

      </div>

      <BroadcastModal isOpen={showBroadcast} onClose={() => setShowBroadcast(false)} onSend={(msg) => {
          alert(`BROADCAST SENT: "${msg}" to all active nodes.`);
          setShowBroadcast(false);
      }} />
      
    </div>
  );
}
