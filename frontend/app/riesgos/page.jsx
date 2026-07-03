"use client";

import React, { useState } from "react";
import { Sparkles, HelpCircle, FileDown, CheckCircle, RefreshCcw, Info, Settings } from "lucide-react";

export default function RiesgosPage() {
  const [alertas, setAlertas] = useState([
    { id: 1, estudiante: "María Fernanda López", grado: "3° Sec. A", criticidad: "alto", mensaje: "Alerta crítica: Calificaciones en Matemáticas y Física por debajo de 10.5. Alta probabilidad de deserción.", fecha: "Hoy, 10:30 am", atendida: false },
    { id: 2, estudiante: "Juan Diego Martínez", grado: "2° Sec. B", criticidad: "medio", mensaje: "Alerta media: Acumula 4 inasistencias y estado de pensión en mora (atraso_leve).", fecha: "Hoy, 09:15 am", atendida: false },
    { id: 3, estudiante: "Ana Sofía Vargas", grado: "1° Sec. A", criticidad: "medio", mensaje: "Alerta de inasistencias: Ha acumulado 6 ausencias injustificadas consecutivas.", fecha: "Ayer, 04:45 pm", atendida: false }
  ]);

  // Simulador Local (Sin registrar en BD)
  const [nivelEducativo, setNivelEducativo] = useState("secundaria");
  const [notaLibro, setNotaLibro] = useState(10);
  const [notaCuaderno, setNotaCuaderno] = useState(10);
  const [notaExamen, setNotaExamen] = useState(9);
  const [conducta, setConducta] = useState(12);
  const [inasistencias, setInasistencias] = useState(4);
  const [estadoPension, setEstadoPension] = useState("atraso_leve");

  const [resultadoSimulado, setResultadoSimulado] = useState(null);

  const handleSimular = (e) => {
    e.preventDefault();

    // Lógica del clasificador heurístico
    let score = 0.05;
    const factores = [];

    const prom = (parseFloat(notaLibro) + parseFloat(notaCuaderno) + parseFloat(notaExamen)) / 3;
    if (prom < 11.0) {
      score += 0.45;
      factores.push(`Promedio desaprobatorio (${prom.toFixed(1)})`);
    } else if (prom < 14.0) {
      score += 0.15;
      factores.push(`Promedio regular (${prom.toFixed(1)})`);
    }

    if (parseFloat(notaExamen) < 11) {
      score += 0.15;
      factores.push("Examen final desaprobado");
    }

    if (parseFloat(conducta) < 11) {
      score += 0.20;
      factores.push("Falla crítica en conducta conductual");
    }

    if (parseInt(inasistencias) >= 5) {
      score += 0.25;
      factores.push(`Alto volumen de inasistencias (${inasistencias})`);
    } else if (parseInt(inasistencias) >= 3) {
      score += 0.10;
      factores.push(`Inasistencias recurrentes (${inasistencias})`);
    }

    if (estadoPension === "deuda") {
      score += 0.15;
      factores.push("Pensiones en estado crítico de deuda");
    } else if (estadoPension === "atraso_leve") {
      score += 0.05;
      factores.push("Pensión con atraso administrativo");
    }

    const prob = Math.min(Math.max(score, 0.01), 0.99);

    let nivel = "Sin riesgo";
    let color = "emerald";
    let sugerencia = "Estudiante estable académicamente. Se sugiere monitoreo regular.";

    if (prob >= 0.75) {
      nivel = "Riesgo alto";
      color = "red";
      sugerencia = "¡ALERTA CRÍTICA! Programar tutoría psicopedagógica urgente, citar de inmediato al padre de familia y coordinar plan de recuperación.";
    } else if (prob >= 0.50) {
      nivel = "Riesgo medio";
      color = "amber";
      sugerencia = "Intervención de tutoría sugerida para nivelar al estudiante en las asignaturas críticas.";
    } else if (prob >= 0.25) {
      nivel = "Riesgo bajo";
      color = "blue";
      sugerencia = "Se sugiere acompañamiento preventivo de notas.";
    }

    setResultadoSimulado({
      probabilidad: prob,
      nivel,
      color,
      sugerencia,
      factores
    });
  };

  const handleAtender = (id) => {
    setAlertas(prev => prev.map(a => a.id === id ? { ...a, atendida: true } : a));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Panel de Gestión de Alertas */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Alertas Activas del Sistema</h3>
              <p className="text-xs text-slate-400">Notificaciones automáticas generadas por el modelo Random Forest el fin de semana.</p>
            </div>
            <button className="text-xs bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg flex items-center space-x-1.5 font-semibold text-slate-600">
              <RefreshCcw className="w-3.5 h-3.5" />
              <span>Sincronizar</span>
            </button>
          </div>

          <div className="space-y-4">
            {alertas.map((alerta) => (
              <div 
                key={alerta.id} 
                className={`p-5 rounded-2xl border flex items-start space-x-4 transition-all ${
                  alerta.atendida 
                    ? "bg-slate-50 border-slate-100 opacity-60" 
                    : alerta.criticidad === "alto" 
                      ? "bg-red-50/50 border-red-100" 
                      : "bg-amber-50/50 border-amber-100"
                }`}
              >
                <div className={`p-2 rounded-xl shrink-0 ${
                  alerta.criticidad === "alto" ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"
                }`}>
                  <Info className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-slate-800">{alerta.estudiante}</h4>
                    <span className="text-[10px] text-slate-400 font-medium">{alerta.fecha}</span>
                  </div>
                  <p className="text-xs text-slate-500 font-semibold mt-0.5">{alerta.grado}</p>
                  <p className="text-xs text-slate-600 leading-relaxed mt-2">{alerta.mensaje}</p>
                  
                  {!alerta.atendida && (
                    <button 
                      onClick={() => handleAtender(alerta.id)}
                      className="mt-4 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold rounded-lg flex items-center space-x-1 transition-all"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Marcar como Atendida</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Simulador de Riesgo Académico */}
      <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm h-fit">
        <div>
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Simulador de Riesgo Académico</h3>
          <p className="text-xs text-slate-400 mb-6">Realice simulaciones hipotéticas y visualice predicciones inmediatas del modelo.</p>
        </div>

        <form onSubmit={handleSimular} className="space-y-4">
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Nivel Educativo</label>
            <select
              value={nivelEducativo}
              onChange={(e) => setNivelEducativo(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none"
            >
              <option value="primaria">Primaria</option>
              <option value="secundaria">Secundaria</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Nota Libro</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={notaLibro}
                onChange={(e) => setNotaLibro(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Nota Cuaderno</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={notaCuaderno}
                onChange={(e) => setNotaCuaderno(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Nota Examen</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={notaExamen}
                onChange={(e) => setNotaExamen(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Conducta</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={conducta}
                onChange={(e) => setConducta(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Inasistencias</label>
              <input
                type="number"
                min="0"
                value={inasistencias}
                onChange={(e) => setInasistencias(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">Pensión</label>
              <select
                value={estadoPension}
                onChange={(e) => setEstadoPension(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none"
              >
                <option value="al_dia">Al día</option>
                <option value="atraso_leve">Atraso leve</option>
                <option value="deuda">Deuda</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold py-2.5 rounded-xl flex items-center justify-center space-x-2 shadow-md transition-all active:scale-[0.98] mt-2"
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Ejecutar Simulación</span>
          </button>
        </form>

        {/* Resultados de la Simulación */}
        {resultadoSimulado && (
          <div className="mt-6 pt-6 border-t border-slate-100 space-y-4">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Resultado de Predicción</h4>
            
            <div className={`p-4 rounded-xl border flex items-center justify-between ${
              resultadoSimulado.color === "red" 
                ? "bg-red-50 border-red-100" 
                : resultadoSimulado.color === "amber"
                  ? "bg-amber-50 border-amber-100"
                  : resultadoSimulado.color === "blue"
                    ? "bg-blue-50 border-blue-100"
                    : "bg-emerald-50 border-emerald-100"
            }`}>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Clasificación</span>
                <span className={`text-sm font-black ${
                  resultadoSimulado.color === "red" ? "text-red-600" : resultadoSimulado.color === "amber" ? "text-amber-600" : "text-emerald-600"
                }`}>
                  {resultadoSimulado.nivel}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Probabilidad</span>
                <span className="text-sm font-black text-slate-800">
                  {Math.round(resultadoSimulado.probabilidad * 100)}%
                </span>
              </div>
            </div>

            {/* Factores Críticos */}
            {resultadoSimulado.factores.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Factores que Aumentan el Riesgo:</span>
                <div className="space-y-1">
                  {resultadoSimulado.factores.map((fact, index) => (
                    <p key={index} className="text-[11px] text-slate-600 font-semibold flex items-center">
                      <span className="w-1.5 h-1.5 bg-red-500 rounded-full mr-1.5"></span>
                      {fact}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Sugerencias de Mitigación */}
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Acción Recomendada:</span>
              <p className="text-[11px] text-slate-600 leading-relaxed font-medium">
                {resultadoSimulado.sugerencia}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
