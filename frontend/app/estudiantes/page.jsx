"use client";

import React, { useState, useEffect } from "react";
import { Search, UserPlus, Filter, Sparkles, BookOpen, AlertTriangle } from "lucide-react";

export default function EstudiantesPage() {
  const [buscar, setBuscar] = useState("");
  const [filtroGrado, setFiltroGrado] = useState("");
  const [filtroRiesgo, setFiltroRiesgo] = useState("");
  
  // 1. Iniciamos los estados completamente vacíos para recibir los reales
  const [estudiantes, setEstudiantes] = useState([]);
  const [cargando, setCargando] = useState(true);

  // 2. Traemos a los estudiantes reales desde la API
  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        const respuesta = await fetch("https://proyecto-siat.onrender.com/api/estudiantes");
        if (respuesta.ok) {
          const datosReales = await respuesta.json();
          setEstudiantes(datosReales);
        }
      } catch (error) {
        console.error("Error al traer estudiantes:", error);
      } finally {
        setCargando(false);
      }
    };
    obtenerDatos();
  }, []);

  // Formulario para registrar un estudiante con predicción automática simulada
  const [mostrarModal, setMostrarModal] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevoApellido, setNuevoApellido] = useState("");
  const [nuevoGrado, setNuevoGrado] = useState("3° Secundaria");
  const [nuevoNivel, setNuevoNivel] = useState("secundaria");
  const [nuevoSeccion, setNuevoSeccion] = useState("A");
  const [notaLibro, setNotaLibro] = useState(14);
  const [notaCuaderno, setNotaCuaderno] = useState(14);
  const [notaExamen, setNotaExamen] = useState(14);
  const [conducta, setConducta] = useState(15);
  const [inasistencias, setInasistencias] = useState(0);
  const [estadoPension, setEstadoPension] = useState("al_dia");

  // Función para simular el Random Forest y determinar el nivel de riesgo en base a los inputs ingresados
  const predecirRiesgoSimulado = (nLibro, nCuaderno, nExamen, cond, inasist, pension, nivelEduc) => {
    let score = 0.05;
    const prom = (nLibro + nCuaderno + nExamen) / 3;
    if (prom < 11.0) score += 0.45;
    else if (prom < 14.0) score += 0.15;
    
    if (nExamen < 11.0) score += 0.15;
    if (cond < 11.0) score += 0.20;
    
    if (inasist >= 5) score += 0.25;
    else if (inasist >= 3) score += 0.10;
    
    if (pension === "deuda") score += 0.15;
    else if (pension === "atraso_leve") score += 0.05;

    const prob = Math.min(Math.max(score, 0.01), 0.99);
    
    let nivel = "Sin riesgo";
    if (prob >= 0.75) nivel = "Riesgo alto";
    else if (prob >= 0.50) nivel = "Riesgo medio";
    else if (prob >= 0.25) nivel = "Riesgo bajo";

    return { probabilidad: prob, nivel };
  };

  const handleCrearEstudiante = (e) => {
    e.preventDefault();
    if (!nuevoNombre || !nuevoApellido) {
      alert("Por favor complete los nombres y apellidos del estudiante.");
      return;
    }

    const { probabilidad, nivel } = predecirRiesgoSimulado(
      parseFloat(notaLibro),
      parseFloat(notaCuaderno),
      parseFloat(notaExamen),
      parseFloat(conducta),
      parseInt(inasistencias),
      estadoPension,
      nuevoNivel
    );

    const prom_calculado = parseFloat(((parseFloat(notaLibro) + parseFloat(notaCuaderno) + parseFloat(notaExamen)) / 3).toFixed(1));

    const nuevoEstudiante = {
      id: estudiantes.length + 1,
      codigo_anonimizado: `A00${estudiantes.length + 1}`,
      nombres: nuevoNombre,
      apellidos: nuevoApellido,
      grado: nuevoGrado,
      seccion: nuevoSeccion,
      nivel_educativo: nuevoNivel,
      inasistencias: parseInt(inasistencias),
      estado_pension: estadoPension,
      nota_final: prom_calculado,
      ultima_prediccion: { probabilidad, nivel }
    };

    setEstudiantes(prev => [nuevoEstudiante, ...prev]);
    setMostrarModal(false);
    
    // Resetear formulario
    setNuevoNombre("");
    setNuevoApellido("");
    setInasistencias(0);
    setNotaLibro(14);
    setNotaCuaderno(14);
    setNotaExamen(14);
    setConducta(15);
    setEstadoPension("al_dia");
  };

  const estudiantesFiltrados = estudiantes.filter(est => {
    const cumpleBusqueda = `${est.nombres} ${est.apellidos}`.toLowerCase().includes(buscar.toLowerCase()) || est.codigo_anonimizado.toLowerCase().includes(buscar.toLowerCase());
    const cumpleGrado = filtroGrado ? est.grado === filtroGrado : true;
    const cumpleRiesgo = filtroRiesgo ? est.ultima_prediccion?.nivel === filtroRiesgo : true;
    return cumpleBusqueda && cumpleGrado && cumpleRiesgo;
  });

  // 3. Mostramos indicador de carga mientras llega la respuesta del servidor
  if (cargando) {
    return (
      <div className="flex h-[50vh] items-center justify-center text-slate-500 font-medium">
        Cargando lista de estudiantes desde la base de datos...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controles de Búsqueda y Registro */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Barra de búsqueda */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Buscar estudiante por nombre o código..."
            value={buscar}
            onChange={(e) => setBuscar(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 shadow-sm transition-all"
          />
        </div>

        {/* Filtros rápidos y botón Registrar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 bg-white border border-slate-200 px-3 py-2 rounded-xl text-sm text-slate-600 shadow-sm">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={filtroGrado}
              onChange={(e) => setFiltroGrado(e.target.value)}
              className="bg-transparent focus:outline-none text-xs font-semibold cursor-pointer"
            >
              <option value="">Todos los Grados</option>
              <option value="1° Secundaria">1° Sec.</option>
              <option value="2° Secundaria">2° Sec.</option>
              <option value="3° Secundaria">3° Sec.</option>
            </select>
          </div>

          <div className="flex items-center space-x-2 bg-white border border-slate-200 px-3 py-2 rounded-xl text-sm text-slate-600 shadow-sm">
            <AlertTriangle className="w-4 h-4 text-slate-400" />
            <select
              value={filtroRiesgo}
              onChange={(e) => setFiltroRiesgo(e.target.value)}
              className="bg-transparent focus:outline-none text-xs font-semibold cursor-pointer"
            >
              <option value="">Todos los Riesgos</option>
              <option value="Sin riesgo">Sin riesgo</option>
              <option value="Riesgo bajo">Riesgo bajo</option>
              <option value="Riesgo medio">Riesgo medio</option>
              <option value="Riesgo alto">Riesgo alto</option>
            </select>
          </div>

          <button
            onClick={() => setMostrarModal(true)}
            className="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl flex items-center space-x-2 shadow-md shadow-red-900/10 active:scale-[0.98] transition-all"
          >
            <UserPlus className="w-4 h-4" />
            <span>Registrar Estudiante</span>
          </button>
        </div>
      </div>

      {/* Tabla Principal */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <th className="px-6 py-4">Estudiante</th>
                <th className="px-6 py-4">Grado & Sección</th>
                <th className="px-6 py-4">Nivel de Riesgo</th>
                <th className="px-6 py-4">Promedio Académico</th>
                <th className="px-6 py-4">Inasistencias</th>
                <th className="px-6 py-4">Estado Pensión</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {estudiantesFiltrados.map((est) => {
                const nivelRiesgo = est.ultima_prediccion?.nivel || "Sin riesgo";
                const badgeColor = {
                  "Riesgo alto": "bg-red-50 text-red-600 border-red-100",
                  "Riesgo medio": "bg-amber-50 text-amber-600 border-amber-100",
                  "Riesgo bajo": "bg-blue-50 text-blue-600 border-blue-100",
                  "Sin riesgo": "bg-emerald-50 text-emerald-600 border-emerald-100"
                }[nivelRiesgo] || "bg-slate-50 text-slate-600 border-slate-100";

                return (
                  <tr key={est.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 flex items-center space-x-3">
                      <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs shadow-inner">
                        {est.nombres ? est.nombres[0] : ""}{est.apellidos ? est.apellidos[0] : ""}
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">{est.nombres} {est.apellidos}</p>
                        <p className="text-[10px] text-slate-400 font-semibold">Código: {est.codigo_anonimizado}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-semibold">{est.grado} - Secc. "{est.seccion || 'A'}"</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${badgeColor}`}>
                        {nivelRiesgo}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-1.5">
                        <span className={`text-sm font-extrabold ${est.nota_final < 11 ? "text-red-500" : "text-slate-800"}`}>
                          {est.nota_final}
                        </span>
                        <span className="text-slate-400 text-xs">/20</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-medium">{est.inasistencias} inasistencias</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        est.estado_pension === "al_dia" 
                          ? "bg-emerald-50 text-emerald-700" 
                          : est.estado_pension === "atraso_leve"
                            ? "bg-amber-50 text-amber-700"
                            : "bg-red-50 text-red-700"
                      }`}>
                        {(est.estado_pension || "al_dia").toUpperCase().replace("_", " ")}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {estudiantesFiltrados.length === 0 && (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-slate-400">
                    No se encontraron estudiantes que coincidan con la búsqueda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Registrar Estudiante */}
      {mostrarModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-2xl">
              <div>
                <h3 className="text-lg font-black text-slate-800 tracking-tight flex items-center space-x-2">
                  <UserPlus className="w-5 h-5 text-red-600" />
                  <span>Registrar Estudiante & Evaluar Inteligente</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ingrese notas y asistencia. SIA-T calculará en tiempo real el riesgo predictivo.
                </p>
              </div>
              <button 
                onClick={() => setMostrarModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold p-1 rounded-full text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCrearEstudiante} className="p-6 space-y-6">
              {/* Información Personal */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Nombres</label>
                  <input
                    type="text"
                    required
                    value={nuevoNombre}
                    onChange={(e) => setNuevoNombre(e.target.value)}
                    placeholder="Ej. María Fernanda"
                    className="w-full px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-red-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Apellidos</label>
                  <input
                    type="text"
                    required
                    value={nuevoApellido}
                    onChange={(e) => setNuevoApellido(e.target.value)}
                    placeholder="Ej. López Sotomayor"
                    className="w-full px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-red-500"
                  />
                </div>
              </div>

              {/* Parámetros Académicos */}
              <div className="border-t border-slate-100 pt-4">
                <h4 className="text-xs font-bold text-slate-400 uppercase mb-4 tracking-wider">Historial de Calificaciones (0 - 20)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 mb-1">Nota Libro</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      step="0.1"
                      value={notaLibro}
                      onChange={(e) => setNotaLibro(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 mb-1">Nota Cuaderno</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      step="0.1"
                      value={notaCuaderno}
                      onChange={(e) => setNotaCuaderno(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 mb-1">Nota Examen</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      step="0.1"
                      value={notaExamen}
                      onChange={(e) => setNotaExamen(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 mb-1">Conducta</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      step="0.1"
                      value={conducta}
                      onChange={(e) => setConducta(e.target.value)}
                      className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                </div>
              </div>

              {/* Asistencia y Pensión */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-100 pt-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">Inasistencias Trimestrales</label>
                  <input
                    type="number"
                    min="0"
                    value={inasistencias}
                    onChange={(e) => setInasistencias(e.target.value)}
                    className="w-full px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">Estado de Pensión</label>
                  <select
                    value={estadoPension}
                    onChange={(e) => setEstadoPension(e.target.value)}
                    className="w-full px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm"
                  >
                    <option value="al_dia">Al día</option>
                    <option value="atraso_leve">Atraso leve</option>
                    <option value="deuda">Deuda</option>
                  </select>
                </div>
              </div>

              {/* Botones */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setMostrarModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-slate-500 text-xs font-bold"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl flex items-center space-x-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Evaluar & Guardar</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}