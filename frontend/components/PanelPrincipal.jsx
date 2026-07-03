"use client";

import React from "react";
import {
  Users,
  AlertTriangle,
  Bell,
  TrendingUp,
  ChevronRight,
  Eye,
  CheckCircle,
  Lightbulb
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar
} from "recharts";
import KpiCard from "./KpiCard";

export default function PanelPrincipal({
  estudiantes = [],
  alertas = [],
  onVerEstudiante,
  onAtenderAlerta
}) {
  // Datos simulados para gráficos
  const datosDistribucionRiesgo = [
    { name: "Sin riesgo", value: 193, color: "#10b981" },
    { name: "Riesgo bajo", value: 56, color: "#3b82f6" },
    { name: "Riesgo medio", value: 41, color: "#f59e0b" },
    { name: "Riesgo alto", value: 22, color: "#ef4444" }
  ];

  const datosTendenciaRiesgo = [
    { name: "Mar", "Riesgo bajo": 40, "Riesgo medio": 20, "Riesgo alto": 8 },
    { name: "Abr", "Riesgo bajo": 52, "Riesgo medio": 25, "Riesgo alto": 12 },
    { name: "May", "Riesgo bajo": 48, "Riesgo medio": 22, "Riesgo alto": 10 },
    { name: "Jun", "Riesgo bajo": 55, "Riesgo medio": 28, "Riesgo alto": 15 },
    { name: "Jul", "Riesgo bajo": 50, "Riesgo medio": 26, "Riesgo alto": 11 },
    { name: "Ago", "Riesgo bajo": 56, "Riesgo medio": 27, "Riesgo alto": 14 }
  ];

  const datosDistribucionGrado = [
    { name: "1° Sec.", estudiantes: 18 },
    { name: "2° Sec.", estudiantes: 14 },
    { name: "3° Sec.", estudiantes: 11 },
    { name: "4° Sec.", estudiantes: 7 },
    { name: "5° Sec.", estudiantes: 3 }
  ];

  return (
    <div className="space-y-8">
      {/* Fila superior de KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Estudiantes registrados"
          value={estudiantes.length.toString()} // Usa el número real
          change="+12 este mes"
          icon={Users}
          color="blue"
        />
        <KpiCard
          title="Estudiantes en riesgo"
          value={estudiantes.filter(e => e.ultima_prediccion.nivel !== "Sin riesgo").length.toString()}
          change="8.7% del total"
          icon={AlertTriangle}
          color="amber"
        />
        <KpiCard
          title="Alertas activas"
          value={alertas.filter(a => !a.atendida).length.toString() || "8"}
          change="Acción requerida"
          icon={Bell}
          color="red"
        />
        <KpiCard
          title="Promedio institucional"
          value="78%"
          change="+3% vs anterior"
          icon={TrendingUp}
          color="emerald"
        />
      </div>

      {/* Grid de Reportes Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Gráfico 1: Distribución de Riesgo */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Distribución de Riesgo</h3>
            <p className="text-xs text-slate-400 mb-4">Proporción general de estudiantes según nivel de riesgo analizado.</p>
          </div>
          <div className="h-64 flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={datosDistribucionRiesgo}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {datosDistribucionRiesgo.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`${value} Alumnos`, "Cantidad"]}
                  contentStyle={{ borderRadius: "12px", border: "1px solid #f1f5f9" }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Texto en medio de la dona */}
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-black text-slate-800 leading-none">{estudiantes.length}</span>
              <span className="text-[10px] font-bold text-slate-400 mt-1 uppercase tracking-wider">Total Alumnos</span>
            </div>
          </div>
          {/* Leyenda personalizada */}
          <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-50">
            {datosDistribucionRiesgo.map((entry) => (
              <div key={entry.name} className="flex items-center space-x-2 text-xs">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }}></span>
                <span className="font-semibold text-slate-600">{entry.name}</span>
                <span className="text-slate-400">({Math.round(entry.value / 3.12)}%)</span>
              </div>
            ))}
          </div>
        </div>

        {/* Gráfico 2: Tendencia de Riesgo en el tiempo */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm lg:col-span-2">
          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Tendencia de Riesgo en el Tiempo</h3>
            <p className="text-xs text-slate-400 mb-4">Evolución mensual de las alertas de riesgo predictivo en la institución.</p>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={datosTendenciaRiesgo} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #f1f5f9" }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                <Line type="monotone" dataKey="Riesgo bajo" stroke="#3b82f6" strokeWidth={3} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="Riesgo medio" stroke="#f59e0b" strokeWidth={3} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="Riesgo alto" stroke="#ef4444" strokeWidth={3} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Fila intermedia: Alertas Recientes y Distribución por Grado */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Alertas Recientes */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Alertas Recientes</h3>
              <button className="text-xs text-red-600 font-bold hover:underline flex items-center">
                Ver todas <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-4 max-h-72 overflow-y-auto pr-1">
              {alertas.slice(0, 3).map((alerta) => (
                <div
                  key={alerta.id}
                  className={`p-4 rounded-xl border flex items-start space-x-3 transition-colors ${alerta.atendida
                    ? "bg-slate-50 border-slate-200 opacity-60"
                    : alerta.mensaje.includes("alto")
                      ? "bg-red-50/50 border-red-100"
                      : "bg-amber-50/50 border-amber-100"
                    }`}
                >
                  <div className={`p-1.5 rounded-lg shrink-0 ${alerta.mensaje.includes("alto") ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"
                    }`}>
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-800 leading-tight">{alerta.mensaje}</p>
                    <p className="text-[10px] text-slate-400 mt-1">{alerta.fecha}</p>
                  </div>
                  {!alerta.atendida && (
                    <button
                      onClick={() => onAtenderAlerta(alerta.id)}
                      className="p-1 text-slate-400 hover:text-emerald-600 rounded-lg transition-colors shrink-0"
                      title="Marcar como atendida"
                    >
                      <CheckCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
              {alertas.length === 0 && (
                <div className="text-center py-12 text-slate-400 text-sm">
                  No hay alertas pendientes en este trimestre.
                </div>
              )}
            </div>
          </div>
          {/* Recomendación Institucional rápida */}
          <div className="mt-6 p-4 bg-blue-50/60 rounded-xl border border-blue-100/60 flex items-start space-x-3">
            <Lightbulb className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1">Recomendación</h4>
              <p className="text-[11px] text-blue-700 leading-relaxed">
                Priorizar tutorías integradas de Matemática y Física en 3° de Secundaria; allí se concentra el 41% del riesgo alto.
              </p>
            </div>
          </div>
        </div>

        {/* Distribución por Grado (Riesgo Alto) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm lg:col-span-2 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Distribución por Grado (Riesgo Alto)</h3>
            <p className="text-xs text-slate-400 mb-4">Grados académicos con mayor volumen de estudiantes calificados en riesgo alto.</p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={datosDistribucionGrado} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #f1f5f9" }} />
                <Bar dataKey="estudiantes" fill="#ef4444" radius={[6, 6, 0, 0]} maxBarSize={35} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-xs text-center text-slate-400 font-medium pt-2">
            El grado de <span className="font-bold text-red-500">1° de Secundaria</span> registra la tasa más elevada con 18 estudiantes en riesgo.
          </div>
        </div>
      </div>

      {/* Tabla: Estudiantes en Riesgo */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Listado de Estudiantes en Riesgo</h3>
            <p className="text-xs text-slate-400">Identificación inmediata de perfiles con criticidad académica media o alta.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <th className="px-6 py-4">Estudiante</th>
                <th className="px-6 py-4">Grado</th>
                <th className="px-6 py-4">Nivel de Riesgo</th>
                <th className="px-6 py-4">Inasistencias</th>
                <th className="px-6 py-4">Última Predicción</th>
                <th className="px-6 py-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {estudiantes.filter(e => e.ultima_prediccion.nivel !== "Sin riesgo").map((est) => {
                const badgeColor = {
                  "Riesgo alto": "bg-red-50 text-red-600 border-red-100",
                  "Riesgo medio": "bg-amber-50 text-amber-600 border-amber-100",
                  "Riesgo bajo": "bg-blue-50 text-blue-600 border-blue-100"
                }[est.ultima_prediccion.nivel] || "bg-slate-50 text-slate-600 border-slate-100";

                return (
                  <tr key={est.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs">
                        {est.nombres[0]}{est.apellidos[0]}
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">{est.nombres} {est.apellidos}</p>
                        <p className="text-[10px] text-slate-400 font-medium">Código: {est.codigo_anonimizado}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-medium">{est.grado}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${badgeColor}`}>
                        {est.ultima_prediccion.nivel}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-semibold">{est.inasistencias} clases</td>
                    <td className="px-6 py-4 text-slate-400 text-xs font-medium">
                      {new Date(est.ultima_prediccion.fecha).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => onVerEstudiante(est)}
                        className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all inline-flex items-center space-x-1"
                        title="Ver detalle de perfil"
                      >
                        <Eye className="w-4 h-4" />
                        <span className="text-xs font-bold">Perfil</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
