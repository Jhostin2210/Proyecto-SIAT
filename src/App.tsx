import React, { useState, useEffect } from "react";
import { 
  Home, 
  Users, 
  AlertTriangle, 
  Bell, 
  FileText, 
  Sparkles, 
  MessageSquare, 
  Settings, 
  ChevronRight, 
  LogOut,
  Search,
  UserPlus,
  Filter,
  Eye,
  CheckCircle,
  Lightbulb,
  Info,
  RefreshCcw,
  TrendingUp
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

// Interfaz para Tipado de Estudiantes
interface Estudiante {
  id: number;
  codigo_anonimizado: string;
  nombres: string;
  apellidos: string;
  grado: string;
  seccion: string;
  nivel_educativo: string;
  inasistencias: number;
  estado_pension: string;
  nota_final: number;
  ultima_prediccion: {
    probabilidad: number;
    nivel: string;
    fecha: string;
  };
}

export default function App() {
  const [seccionActiva, setSeccionActiva] = useState<"inicio" | "estudiantes" | "riesgos">("inicio");
  const [activeAlertsCount, setActiveAlertsCount] = useState(3);

  // Estado general de estudiantes (Sincronizado de manera interactiva)
  const [estudiantes, setEstudiantes] = useState<Estudiante[]>([
    {
      id: 1,
      codigo_anonimizado: "A001",
      nombres: "María Fernanda",
      apellidos: "López",
      grado: "3° Secundaria",
      seccion: "A",
      nivel_educativo: "secundaria",
      inasistencias: 2,
      estado_pension: "al_dia",
      nota_final: 10.1,
      ultima_prediccion: { probabilidad: 0.82, nivel: "Riesgo alto", fecha: "2026-07-01T10:30:00" }
    },
    {
      id: 2,
      codigo_anonimizado: "A002",
      nombres: "Juan Diego",
      apellidos: "Martínez",
      grado: "2° Secundaria",
      seccion: "B",
      nivel_educativo: "secundaria",
      inasistencias: 4,
      estado_pension: "atraso_leve",
      nota_final: 10.6,
      ultima_prediccion: { probabilidad: 0.68, nivel: "Riesgo medio", fecha: "2026-07-01T09:15:00" }
    },
    {
      id: 3,
      codigo_anonimizado: "A003",
      nombres: "Ana Sofía",
      apellidos: "Vargas",
      grado: "1° Secundaria",
      seccion: "A",
      nivel_educativo: "secundaria",
      inasistencias: 6,
      estado_pension: "al_dia",
      nota_final: 12.1,
      ultima_prediccion: { probabilidad: 0.35, nivel: "Riesgo bajo", fecha: "2026-06-30T16:45:00" }
    },
    {
      id: 4,
      codigo_anonimizado: "A004",
      nombres: "Luis Antonio",
      apellidos: "Pérez",
      grado: "3° Secundaria",
      seccion: "C",
      nivel_educativo: "secundaria",
      inasistencias: 1,
      estado_pension: "deuda",
      nota_final: 12.0,
      ultima_prediccion: { probabilidad: 0.42, nivel: "Riesgo bajo", fecha: "2026-07-01T11:05:00" }
    },
    {
      id: 5,
      codigo_anonimizado: "A005",
      nombres: "Camila Torres",
      apellidos: "Ruiz",
      grado: "2° Secundaria",
      seccion: "A",
      nivel_educativo: "secundaria",
      inasistencias: 0,
      estado_pension: "al_dia",
      nota_final: 16.1,
      ultima_prediccion: { probabilidad: 0.05, nivel: "Sin riesgo", fecha: "2026-07-02T08:00:00" }
    }
  ]);

  // Alertas del sistema
  const [alertas, setAlertas] = useState([
    { id: 1, estudiante: "María Fernanda López", grado: "3° Sec. A", criticidad: "alto", mensaje: "Riesgo alto detectado: María Fernanda López - Bajo rendimiento en Matemática y Física", fecha: "Hoy, 10:30 am", atendida: false },
    { id: 2, estudiante: "Juan Diego Martínez", grado: "2° Sec. B", criticidad: "medio", mensaje: "Riesgo medio detectado: Juan Diego Martínez - Alerta por atraso de pensión y bajo rendimiento", fecha: "Hoy, 09:15 am", atendida: false },
    { id: 3, estudiante: "Ana Sofía Vargas", grado: "1° Sec. A", criticidad: "medio", mensaje: "Riesgo medio detectado: Ana Sofía Vargas - Alerta por 6 inasistencias acumuladas", fecha: "Ayer, 04:45 pm", atendida: false }
  ]);

  useEffect(() => {
    const fetchEstudiantes = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/estudiantes");
        if (response.ok) {
          const data = await response.json();
          if (data && data.length > 0) {
            setEstudiantes(data);
            
            // Generar alertas dinámicas basadas en los alumnos con riesgo medio/alto de la base de datos
            const alumnosRiesgo = data.filter((e: any) => e.ultima_prediccion?.nivel === "Riesgo alto" || e.ultima_prediccion?.nivel === "Riesgo medio");
            if (alumnosRiesgo.length > 0) {
              const nuevasAlertas = alumnosRiesgo.map((e: any, idx: number) => ({
                id: idx + 1,
                estudiante: `${e.nombres} ${e.apellidos}`,
                grado: `${e.grado} ${e.seccion}`,
                criticidad: e.ultima_prediccion?.nivel === "Riesgo alto" ? "alto" : "medio",
                mensaje: `${e.ultima_prediccion?.nivel} detectado: ${e.nombres} ${e.apellidos} - Nota final registrada de ${e.notas?.nota_final || e.nota_final}`,
                fecha: "Sincronizado de la BD",
                atendida: false
              }));
              setAlertas(nuevasAlertas);
              setActiveAlertsCount(nuevasAlertas.length);
            } else {
              setAlertas([]);
              setActiveAlertsCount(0);
            }
          }
        }
      } catch (err) {
        console.warn("FastAPI backend no disponible en localhost:8000. Utilizando datos simulados locales.", err);
      }
    };
    fetchEstudiantes();
  }, []);

  // Variables para la simulación
  const [nivelEducativo, setNivelEducativo] = useState("secundaria");
  const [notaLibro, setNotaLibro] = useState(10);
  const [notaCuaderno, setNotaCuaderno] = useState(10);
  const [notaExamen, setNotaExamen] = useState(9);
  const [conducta, setConducta] = useState(12);
  const [inasistencias, setInasistencias] = useState(4);
  const [estadoPension, setEstadoPension] = useState("atraso_leve");
  const [resultadoSimulado, setResultadoSimulado] = useState<{
    probabilidad: number;
    nivel: string;
    color: string;
    sugerencia: string;
    factores: string[];
  } | null>(null);

  // Variables de Registro de estudiantes
  const [mostrarModal, setMostrarModal] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevoApellido, setNuevoApellido] = useState("");
  const [nuevoGrado, setNuevoGrado] = useState("3° Secundaria");
  const [nuevoNivel, setNuevoNivel] = useState("secundaria");
  const [nuevoSeccion, setNuevoSeccion] = useState("A");
  const [regNotaLibro, setRegNotaLibro] = useState(14);
  const [regNotaCuaderno, setRegNotaCuaderno] = useState(14);
  const [regNotaExamen, setRegNotaExamen] = useState(14);
  const [regConducta, setRegConducta] = useState(15);
  const [regInasistencias, setRegInasistencias] = useState(0);
  const [regEstadoPension, setRegEstadoPension] = useState("al_dia");

  // Perfil seleccionado para ver detalle
  const [perfilSeleccionado, setPerfilSeleccionado] = useState<Estudiante | null>(null);

  // Filtros rápidos de estudiantes
  const [buscar, setBuscar] = useState("");
  const [filtroGrado, setFiltroGrado] = useState("");
  const [filtroRiesgo, setFiltroRiesgo] = useState("");

  // Lógica de clasificación emulada del Random Forest del Colab
  const predecirRiesgoSimulado = (
    nLibro: number,
    nCuaderno: number,
    nExamen: number,
    cond: number,
    inasist: number,
    pension: string
  ) => {
    let score = 0.05;
    const factores: string[] = [];

    const promedio = (nLibro + nCuaderno + nExamen) / 3;
    if (promedio < 11.0) {
      score += 0.45;
      factores.push(`Promedio académico desaprobatorio (${promedio.toFixed(1)})`);
    } else if (promedio < 14.0) {
      score += 0.15;
      factores.push(`Promedio académico regular (${promedio.toFixed(1)})`);
    }

    if (nExamen < 11.0) {
      score += 0.15;
      factores.push("Examen final del trimestre desaprobado");
    }

    if (cond < 11.0) {
      score += 0.20;
      factores.push(`Conducta desaprobatoria (${cond.toFixed(1)})`);
    }

    if (inasist >= 5) {
      score += 0.25;
      factores.push(`Inasistencias acumuladas elevadas (${inasist})`);
    } else if (inasist >= 3) {
      score += 0.10;
      factores.push(`Frecuencia de inasistencias en aumento (${inasist})`);
    }

    if (pension === "deuda") {
      score += 0.15;
      factores.push("Estado administrativo de deuda");
    } else if (pension === "atraso_leve") {
      score += 0.05;
      factores.push("Atraso en pensiones regular");
    }

    const prob = Math.min(Math.max(score, 0.01), 0.99);

    let nivel = "Sin riesgo";
    let color = "emerald";
    let sugerencia = "Estudiante con rendimiento y conducta estable. Continuar con monitoreo.";

    if (prob >= 0.75) {
      nivel = "Riesgo alto";
      color = "red";
      sugerencia = "¡ALERTA CRÍTICA! Se requiere plan de tutoría inmediato y consejería psicopedagógica urgente.";
    } else if (prob >= 0.50) {
      nivel = "Riesgo medio";
      color = "amber";
      sugerencia = "Intervención de tutoría sugerida para nivelar al estudiante en las materias críticas.";
    } else if (prob >= 0.25) {
      nivel = "Riesgo bajo";
      color = "blue";
      sugerencia = "Se sugiere acompañamiento preventivo de notas.";
    }

    return { probabilidad: prob, nivel, color, sugerencia, factores };
  };

  const handleSimularForm = (e: React.FormEvent) => {
    e.preventDefault();
    const resultado = predecirRiesgoSimulado(
      parseFloat(notaLibro.toString()),
      parseFloat(notaCuaderno.toString()),
      parseFloat(notaExamen.toString()),
      parseFloat(conducta.toString()),
      parseInt(inasistencias.toString()),
      estadoPension
    );
    setResultadoSimulado(resultado);
  };

  const handleCrearEstudiante = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoNombre || !nuevoApellido) {
      alert("Por favor complete los nombres y apellidos.");
      return;
    }

    const { probabilidad, nivel } = predecirRiesgoSimulado(
      parseFloat(regNotaLibro.toString()),
      parseFloat(regNotaCuaderno.toString()),
      parseFloat(regNotaExamen.toString()),
      parseFloat(regConducta.toString()),
      parseInt(regInasistencias.toString()),
      regEstadoPension
    );

    const prom = parseFloat(((parseFloat(regNotaLibro.toString()) + parseFloat(regNotaCuaderno.toString()) + parseFloat(regNotaExamen.toString())) / 3).toFixed(1));

    const nuevoEst: Estudiante = {
      id: estudiantes.length + 1,
      codigo_anonimizado: `A00${estudiantes.length + 1}`,
      nombres: nuevoNombre,
      apellidos: nuevoApellido,
      grado: nuevoGrado,
      seccion: nuevoSeccion,
      nivel_educativo: nuevoNivel,
      inasistencias: parseInt(regInasistencias.toString()),
      estado_pension: regEstadoPension,
      nota_final: prom,
      ultima_prediccion: {
        probabilidad,
        nivel,
        fecha: new Date().toISOString()
      }
    };

    setEstudiantes(prev => [nuevoEst, ...prev]);

    // Generar alerta automática si el nivel es medio o alto
    if (nivel === "Riesgo alto" || nivel === "Riesgo medio") {
      const nuevaAlerta = {
        id: alertas.length + 1,
        estudiante: `${nuevoNombre} ${nuevoApellido}`,
        grado: `${nuevoGrado} ${nuevoSeccion}`,
        criticidad: nivel === "Riesgo alto" ? "alto" : "medio",
        mensaje: `${nivel} detectado: ${nuevoNombre} ${nuevoApellido} - Evaluado recientemente con promedio de ${prom}`,
        fecha: "Hace un momento",
        atendida: false
      };
      setAlertas(prev => [nuevaAlerta, ...prev]);
      setActiveAlertsCount(prev => prev + 1);
    }

    setMostrarModal(false);
    // Resetear
    setNuevoNombre("");
    setNuevoApellido("");
    setRegInasistencias(0);
    setRegNotaLibro(14);
    setRegNotaCuaderno(14);
    setRegNotaExamen(14);
    setRegConducta(15);
    setRegEstadoPension("al_dia");
  };

  const handleAtenderAlerta = (alertaId: number) => {
    setAlertas(prev => prev.map(a => a.id === alertaId ? { ...a, atendida: true } : a));
    setActiveAlertsCount(prev => Math.max(0, prev - 1));
  };

  // Filtrar estudiantes
  const estudiantesFiltrados = estudiantes.filter(est => {
    const cumpleBusqueda = `${est.nombres} ${est.apellidos}`.toLowerCase().includes(buscar.toLowerCase()) || est.codigo_anonimizado.toLowerCase().includes(buscar.toLowerCase());
    const cumpleGrado = filtroGrado ? est.grado === filtroGrado : true;
    const cumpleRiesgo = filtroRiesgo ? est.ultima_prediccion.nivel === filtroRiesgo : true;
    return cumpleBusqueda && cumpleGrado && cumpleRiesgo;
  });

  // Datos para Recharts
  const datosDistribucionRiesgo = [
    { name: "Sin riesgo", value: estudiantes.filter(e => e.ultima_prediccion.nivel === "Sin riesgo").length, color: "#10b981" },
    { name: "Riesgo bajo", value: estudiantes.filter(e => e.ultima_prediccion.nivel === "Riesgo bajo").length, color: "#3b82f6" },
    { name: "Riesgo medio", value: estudiantes.filter(e => e.ultima_prediccion.nivel === "Riesgo medio").length, color: "#f59e0b" },
    { name: "Riesgo alto", value: estudiantes.filter(e => e.ultima_prediccion.nivel === "Riesgo alto").length, color: "#ef4444" }
  ];

  const totalRiesgoAltoReal = estudiantes.filter(e => e.ultima_prediccion.nivel === "Riesgo alto").length;
  const totalRiesgoMedioReal = estudiantes.filter(e => e.ultima_prediccion.nivel === "Riesgo medio").length;
  const totalRiesgoBajoReal = estudiantes.filter(e => e.ultima_prediccion.nivel === "Riesgo bajo").length;

  const datosTendenciaRiesgo = [
    { name: "Mar", "Riesgo bajo": Math.max(1, Math.round(totalRiesgoBajoReal * 0.7)), "Riesgo medio": Math.max(1, Math.round(totalRiesgoMedioReal * 0.7)), "Riesgo alto": Math.max(0, Math.round(totalRiesgoAltoReal * 0.6)) },
    { name: "Abr", "Riesgo bajo": Math.max(1, Math.round(totalRiesgoBajoReal * 0.9)), "Riesgo medio": Math.max(1, Math.round(totalRiesgoMedioReal * 0.9)), "Riesgo alto": Math.max(0, Math.round(totalRiesgoAltoReal * 0.8)) },
    { name: "May", "Riesgo bajo": Math.max(1, Math.round(totalRiesgoBajoReal * 0.8)), "Riesgo medio": Math.max(1, Math.round(totalRiesgoMedioReal * 0.8)), "Riesgo alto": Math.max(0, Math.round(totalRiesgoAltoReal * 0.7)) },
    { name: "Jun", "Riesgo bajo": Math.max(1, Math.round(totalRiesgoBajoReal * 1.0)), "Riesgo medio": Math.max(1, Math.round(totalRiesgoMedioReal * 1.0)), "Riesgo alto": Math.max(0, Math.round(totalRiesgoAltoReal * 1.0)) },
    { name: "Jul", "Riesgo bajo": totalRiesgoBajoReal, "Riesgo medio": totalRiesgoMedioReal, "Riesgo alto": totalRiesgoAltoReal }
  ];

  const gradosUnicos = Array.from(new Set(estudiantes.map(e => e.grado))).sort();
  const datosDistribucionGrado = gradosUnicos.map(grado => {
    const cantRiesgoAlto = estudiantes.filter(e => e.grado === grado && e.ultima_prediccion.nivel === "Riesgo alto").length;
    return {
      name: grado,
      estudiantes: cantRiesgoAlto
    };
  });

  const gradoConMasRiesgo = (() => {
    if (estudiantes.length === 0) return "Ninguno";
    const conteos: { [key: string]: number } = {};
    estudiantes.forEach(e => {
      if (e.ultima_prediccion.nivel === "Riesgo alto") {
        conteos[e.grado] = (conteos[e.grado] || 0) + 1;
      }
    });
    let maxGrado = "";
    let maxVal = -1;
    Object.entries(conteos).forEach(([g, val]) => {
      if (val > maxVal) {
        maxVal = val;
        maxGrado = g;
      }
    });
    return maxGrado || "Ninguno";
  })();

  const cantRiesgoTotal = totalRiesgoAltoReal + totalRiesgoMedioReal;
  const porcentajeRiesgoTotal = estudiantes.length > 0 ? ((cantRiesgoTotal / estudiantes.length) * 100).toFixed(1) : "0.0";
  
  const averageGrade = estudiantes.length > 0
    ? estudiantes.reduce((sum, e) => sum + (e.nota_final || 0), 0) / estudiantes.length
    : 0;
  const promedioInstitucional = estudiantes.length > 0
    ? `${Math.round((averageGrade / 20) * 100)}%`
    : "0%";

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      
      {/* Sidebar Lateral */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col justify-between border-r border-slate-800 shrink-0">
        <div>
          {/* Logo */}
          <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
            <div className="w-9 h-9 bg-red-600 rounded-lg flex items-center justify-center text-white font-black text-xl shadow-md shadow-red-900/40">
              S
            </div>
            <div>
              <h1 className="font-extrabold text-lg leading-none tracking-tight">SIA-T</h1>
              <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wider font-semibold">Alerta Temprana</p>
            </div>
          </div>

          {/* Menú de Navegación */}
          <nav className="p-4 space-y-1">
            <button
              onClick={() => { setSeccionActiva("inicio"); setPerfilSeleccionado(null); }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                seccionActiva === "inicio" 
                  ? "bg-red-600 text-white shadow-lg shadow-red-900/20" 
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Home className="w-5 h-5" />
                <span>Inicio</span>
              </div>
            </button>

            <button
              onClick={() => { setSeccionActiva("estudiantes"); setPerfilSeleccionado(null); }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                seccionActiva === "estudiantes" 
                  ? "bg-red-600 text-white shadow-lg shadow-red-900/20" 
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Users className="w-5 h-5" />
                <span>Estudiantes</span>
              </div>
            </button>

            <button
              onClick={() => { setSeccionActiva("riesgos"); setPerfilSeleccionado(null); }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                seccionActiva === "riesgos" 
                  ? "bg-red-600 text-white shadow-lg shadow-red-900/20" 
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
              }`}
            >
              <div className="flex items-center space-x-3">
                <AlertTriangle className="w-5 h-5" />
                <span>Riesgos & Alertas</span>
              </div>
              {activeAlertsCount > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-extrabold ${
                  seccionActiva === "riesgos" ? "bg-white text-red-600" : "bg-red-600 text-white"
                }`}>
                  {activeAlertsCount}
                </span>
              )}
            </button>
          </nav>
        </div>

        {/* Perfil del Usuario en la base */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center space-x-3 p-2 bg-slate-800/40 rounded-xl border border-slate-800/60">
            <div className="relative">
              <div className="w-10 h-10 rounded-full bg-slate-700 overflow-hidden border border-slate-600 flex items-center justify-center font-bold text-slate-200 text-sm">
                CR
              </div>
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 border-2 border-slate-900 rounded-full"></span>
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-sm font-bold text-slate-100 truncate">Carlos Ramírez</h2>
              <p className="text-[10px] text-slate-400 font-semibold truncate uppercase">Coordinador Académico</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Contenido Principal */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Cabecera Superior */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
          <div>
            <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">Colegio Particular "Peruano Francés"</span>
            <h1 className="text-base font-black text-slate-800 uppercase tracking-tight">
              {seccionActiva === "inicio" && "Panel Principal de Alerta Temprana"}
              {seccionActiva === "estudiantes" && "Gestión de Estudiantes"}
              {seccionActiva === "riesgos" && "Simulador de Riesgo & Alertas de ML"}
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <p className="text-[10px] font-bold text-slate-400 uppercase">Trimestre Activo</p>
              <p className="text-sm font-black text-slate-800">2024 - II</p>
            </div>
            <div className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full cursor-pointer transition-all">
              <Bell className="w-5 h-5" />
              {activeAlertsCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
              )}
            </div>
          </div>
        </header>

        {/* Cuerpo Principal Scrolleable */}
        <div className="flex-1 overflow-y-auto p-8">
          
          {perfilSeleccionado ? (
            /* Vista de Detalle de Estudiante */
            <div className="space-y-6">
              <button 
                onClick={() => setPerfilSeleccionado(null)}
                className="text-xs text-red-600 font-bold hover:underline mb-2 flex items-center"
              >
                ← Volver al listado
              </button>

              <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex items-center space-x-4 border-b border-slate-100 pb-6 mb-6">
                  <div className="w-16 h-16 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-black text-slate-700 text-xl shadow-inner">
                    {perfilSeleccionado.nombres[0]}{perfilSeleccionado.apellidos[0]}
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-slate-800 tracking-tight">{perfilSeleccionado.nombres} {perfilSeleccionado.apellidos}</h2>
                    <p className="text-xs text-slate-400 font-bold">Código del alumno: {perfilSeleccionado.codigo_anonimizado} | Grado: {perfilSeleccionado.grado} - Secc. "{perfilSeleccionado.seccion}"</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Tarjeta de Nivel de Riesgo */}
                  <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 space-y-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Predicción del Modelo ML</span>
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-1.5 rounded-full text-xs font-black border ${
                        perfilSeleccionado.ultima_prediccion.nivel === "Riesgo alto" 
                          ? "bg-red-50 text-red-600 border-red-100" 
                          : "bg-amber-50 text-amber-600 border-amber-100"
                      }`}>
                        {perfilSeleccionado.ultima_prediccion.nivel}
                      </span>
                      <span className="text-xl font-extrabold text-slate-800">
                        {Math.round(perfilSeleccionado.ultima_prediccion.probabilidad * 100)}% Probabilidad
                      </span>
                    </div>
                    <div className="pt-2 border-t border-slate-200/60 text-xs text-slate-500 font-semibold leading-relaxed">
                      Sugerencia institucional: {
                        perfilSeleccionado.ultima_prediccion.nivel === "Riesgo alto"
                          ? "Activar plan de tutorías de emergencia y programar cita presencial con psicopedagogía."
                          : "Realizar seguimiento preventivo de calificaciones de tareas."
                      }
                    </div>
                  </div>

                  {/* Tarjeta Académica */}
                  <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 space-y-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Calificaciones del Trimestre</span>
                    <div className="flex justify-between text-xs font-bold text-slate-600">
                      <span>Promedio General:</span>
                      <span className={perfilSeleccionado.nota_final < 11 ? "text-red-500 font-black" : "text-emerald-600 font-black"}>
                        {perfilSeleccionado.nota_final} / 20
                      </span>
                    </div>
                    <div className="pt-2 border-t border-slate-200/60 space-y-1 text-xs text-slate-500">
                      <p className="flex justify-between"><span>Examen Final:</span> <span className="font-bold text-slate-700">10.0</span></p>
                      <p className="flex justify-between"><span>Cuaderno Diario:</span> <span className="font-bold text-slate-700">11.0</span></p>
                      <p className="flex justify-between"><span>Libro / Actividades:</span> <span className="font-bold text-slate-700">9.5</span></p>
                    </div>
                  </div>

                  {/* Asistencia & Pensiones */}
                  <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 space-y-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Asistencia & Administrativo</span>
                    <div className="flex justify-between text-xs font-bold text-slate-600">
                      <span>Inasistencias:</span>
                      <span className={perfilSeleccionado.inasistencias >= 3 ? "text-red-500 font-black" : "text-slate-800"}>
                        {perfilSeleccionado.inasistencias} clases
                      </span>
                    </div>
                    <div className="flex justify-between text-xs font-bold text-slate-600">
                      <span>Estado Pensión:</span>
                      <span className={perfilSeleccionado.estado_pension === "deuda" ? "text-red-500 font-black" : "text-emerald-600"}>
                        {perfilSeleccionado.estado_pension.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Sección 1: Inicio */}
              {seccionActiva === "inicio" && (
                <div className="space-y-8">
                  {/* Fila de KPIs */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between transition-all duration-300 hover:shadow-md">
                      <div>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Estudiantes registrados</p>
                        <span className="text-3xl font-black text-slate-800 mt-1 block">{estudiantes.length}</span>
                        <p className="text-[10px] text-emerald-600 font-bold mt-1">Sincronizados de la BD ↑</p>
                      </div>
                      <div className="w-12 h-12 bg-blue-500 text-white rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/10">
                        <Users className="w-6 h-6" />
                      </div>
                    </div>

                    <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between transition-all duration-300 hover:shadow-md">
                      <div>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Estudiantes en riesgo</p>
                        <span className="text-3xl font-black text-slate-800 mt-1 block">{cantRiesgoTotal}</span>
                        <p className="text-[10px] text-red-600 font-bold mt-1">{porcentajeRiesgoTotal}% del total</p>
                      </div>
                      <div className="w-12 h-12 bg-amber-500 text-white rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/10">
                        <AlertTriangle className="w-6 h-6" />
                      </div>
                    </div>

                    <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between transition-all duration-300 hover:shadow-md">
                      <div>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Alertas activas</p>
                        <span className="text-3xl font-black text-slate-800 mt-1 block">
                          {alertas.filter(a => !a.atendida).length}
                        </span>
                        <p className="text-[10px] text-red-600 font-bold mt-1">Acción requerida</p>
                      </div>
                      <div className="w-12 h-12 bg-red-500 text-white rounded-xl flex items-center justify-center shadow-lg shadow-red-500/10">
                        <Bell className="w-6 h-6" />
                      </div>
                    </div>

                    <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between transition-all duration-300 hover:shadow-md">
                      <div>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Promedio institucional</p>
                        <span className="text-3xl font-black text-slate-800 mt-1 block">{promedioInstitucional}</span>
                        <p className="text-[10px] text-emerald-600 font-bold mt-1">Calificación: {averageGrade.toFixed(1)} / 20</p>
                      </div>
                      <div className="w-12 h-12 bg-emerald-500 text-white rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/10">
                        <TrendingUp className="w-6 h-6" />
                      </div>
                    </div>
                  </div>

                  {/* Grid de Reportes Gráficos */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Gráfico 1: Distribución de Riesgo */}
                    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                      <div>
                        <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider mb-1">Distribución de Riesgo</h3>
                        <p className="text-[11px] text-slate-400">Proporción general de estudiantes según nivel de riesgo analizado.</p>
                      </div>
                      <div className="h-56 flex items-center justify-center relative mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={datosDistribucionRiesgo}
                              cx="50%"
                              cy="50%"
                              innerRadius={55}
                              outerRadius={75}
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
                        <div className="absolute flex flex-col items-center justify-center">
                          <span className="text-2xl font-black text-slate-800 leading-none">{estudiantes.length}</span>
                          <span className="text-[9px] font-bold text-slate-400 mt-1 uppercase tracking-wider">Alumnos</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-100">
                        {datosDistribucionRiesgo.map((entry) => (
                          <div key={entry.name} className="flex items-center space-x-2 text-xs">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }}></span>
                            <span className="font-semibold text-slate-600">{entry.name}</span>
                            <span className="text-slate-400">({estudiantes.length > 0 ? Math.round((entry.value / estudiantes.length) * 100) : 0}%)</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Gráfico 2: Tendencia de Riesgo */}
                    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm lg:col-span-2 flex flex-col justify-between">
                      <div>
                        <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider mb-1">Tendencia de Riesgo en el Tiempo</h3>
                        <p className="text-[11px] text-slate-400">Evolución mensual de las alertas de riesgo predictivo en la institución.</p>
                      </div>
                      <div className="h-64 w-full mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={datosTendenciaRiesgo} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                            <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                            <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #f1f5f9" }} />
                            <Legend iconType="circle" wrapperStyle={{ fontSize: 10, paddingTop: 10 }} />
                            <Line type="monotone" dataKey="Riesgo bajo" stroke="#3b82f6" strokeWidth={3} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="Riesgo medio" stroke="#f59e0b" strokeWidth={3} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="Riesgo alto" stroke="#ef4444" strokeWidth={3} activeDot={{ r: 6 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Fila intermedia: Alertas e Identificación por Grado */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Alertas Recientes */}
                    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider">Alertas Recientes</h3>
                        </div>
                        <div className="space-y-4 max-h-[220px] overflow-y-auto pr-1">
                          {alertas.slice(0, 3).map((alerta) => (
                            <div 
                              key={alerta.id} 
                              className={`p-3.5 rounded-xl border flex items-start space-x-3 transition-colors ${
                                alerta.atendida 
                                  ? "bg-slate-50 border-slate-200 opacity-60" 
                                  : alerta.criticidad === "alto" 
                                    ? "bg-red-50/50 border-red-100" 
                                    : "bg-amber-50/50 border-amber-100"
                              }`}
                            >
                              <div className={`p-1.5 rounded-lg shrink-0 ${
                                alerta.criticidad === "alto" ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"
                              }`}>
                                <AlertTriangle className="w-3.5 h-3.5" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-bold text-slate-800 leading-tight">{alerta.mensaje}</p>
                                <p className="text-[9px] text-slate-400 mt-1 font-semibold">{alerta.fecha}</p>
                              </div>
                              {!alerta.atendida && (
                                <button 
                                  onClick={() => handleAtenderAlerta(alerta.id)}
                                  className="p-1 text-slate-400 hover:text-emerald-600 rounded-lg transition-colors shrink-0"
                                  title="Atender alerta"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Recomendación Institucional */}
                      <div className="mt-4 p-4 bg-blue-50/60 rounded-xl border border-blue-100/60 flex items-start space-x-3">
                        <Lightbulb className="w-5 h-5 text-blue-600 shrink-0 mt-0.5 animate-bounce" />
                        <div>
                          <h4 className="text-xs font-extrabold text-blue-900 uppercase tracking-wider mb-0.5">Recomendación</h4>
                          <p className="text-[11px] text-blue-700 leading-relaxed font-medium">
                            Se recomienda priorizar intervenciones en {gradoConMasRiesgo}; allí se concentra la mayor tasa de riesgo académico.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Distribución por Grado */}
                    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm lg:col-span-2 flex flex-col justify-between">
                      <div>
                        <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider mb-1">Distribución por Grado (Riesgo Alto)</h3>
                        <p className="text-[11px] text-slate-400">Grados escolares que concentran estudiantes en riesgo alto.</p>
                      </div>
                      <div className="h-56 w-full mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={datosDistribucionGrado} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                            <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                            <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #f1f5f9" }} />
                            <Bar dataKey="estudiantes" fill="#ef4444" radius={[6, 6, 0, 0]} maxBarSize={35} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="text-[11px] text-slate-400 font-bold text-center mt-2 uppercase tracking-wide">
                        SIA-T Alerta: La tasa más alta se concentra en {gradoConMasRiesgo}.
                      </div>
                    </div>
                  </div>

                  {/* Tabla: Alumnos en Riesgo */}
                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-100">
                      <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider mb-1">Estudiantes en Riesgo Detectados</h3>
                      <p className="text-[11px] text-slate-400">Visualización de los alumnos que requieren intervención preventiva.</p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-50 text-[9px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                            <th className="px-6 py-4">Estudiante</th>
                            <th className="px-6 py-4">Grado</th>
                            <th className="px-6 py-4">Nivel de Riesgo</th>
                            <th className="px-6 py-4">Inasistencias</th>
                            <th className="px-6 py-4 text-center">Acción</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-sm">
                          {estudiantes.filter(e => e.ultima_prediccion.nivel !== "Sin riesgo").map((est) => {
                            const badgeColor = {
                              "Riesgo alto": "bg-red-50 text-red-600 border-red-100",
                              "Riesgo medio": "bg-amber-50 text-amber-600 border-amber-100",
                              "Riesgo bajo": "bg-blue-50 text-blue-600 border-blue-100"
                            }[est.ultima_prediccion.nivel];

                            return (
                              <tr key={est.id} className="hover:bg-slate-50/50 transition-colors">
                                <td className="px-6 py-4 flex items-center space-x-3">
                                  <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs">
                                    {est.nombres[0]}{est.apellidos[0]}
                                  </div>
                                  <div>
                                    <p className="font-bold text-slate-800">{est.nombres} {est.apellidos}</p>
                                    <p className="text-[10px] text-slate-400 font-semibold">Código: {est.codigo_anonimizado}</p>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-slate-600 font-semibold">{est.grado}</td>
                                <td className="px-6 py-4">
                                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${badgeColor}`}>
                                    {est.ultima_prediccion.nivel}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-slate-600 font-semibold">{est.inasistencias} inasistencias</td>
                                <td className="px-6 py-4 text-center">
                                  <button 
                                    onClick={() => setPerfilSeleccionado(est)}
                                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all inline-flex items-center space-x-1"
                                  >
                                    <Eye className="w-4 h-4" />
                                    <span className="text-xs font-bold">Ver Perfil</span>
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
              )}

              {/* Sección 2: Listado de Estudiantes */}
              {seccionActiva === "estudiantes" && (
                <div className="space-y-6">
                  {/* Controles de Búsqueda */}
                  <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
                    <div className="relative flex-1 max-w-md">
                      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                      <input
                        type="text"
                        placeholder="Buscar estudiante por nombre o código..."
                        value={buscar}
                        onChange={(e) => setBuscar(e.target.value)}
                        className="w-full pl-11 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-red-500 shadow-sm"
                      />
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <div className="flex items-center space-x-2 bg-white border border-slate-200 px-3 py-2 rounded-xl text-sm text-slate-600">
                        <Filter className="w-4 h-4 text-slate-400" />
                        <select
                          value={filtroGrado}
                          onChange={(e) => setFiltroGrado(e.target.value)}
                          className="bg-transparent focus:outline-none text-xs font-bold"
                        >
                          <option value="">Todos los Grados</option>
                          <option value="1° Secundaria">1° Sec.</option>
                          <option value="2° Secundaria">2° Sec.</option>
                          <option value="3° Secundaria">3° Sec.</option>
                        </select>
                      </div>

                      <div className="flex items-center space-x-2 bg-white border border-slate-200 px-3 py-2 rounded-xl text-sm text-slate-600">
                        <AlertTriangle className="w-4 h-4 text-slate-400" />
                        <select
                          value={filtroRiesgo}
                          onChange={(e) => setFiltroRiesgo(e.target.value)}
                          className="bg-transparent focus:outline-none text-xs font-bold"
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
                        className="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl flex items-center space-x-2 shadow-md active:scale-95 transition-all"
                      >
                        <UserPlus className="w-4 h-4" />
                        <span>Registrar Alumno</span>
                      </button>
                    </div>
                  </div>

                  {/* Tabla Principal de Estudiantes */}
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
                            <th className="px-6 py-4">Pensión</th>
                            <th className="px-6 py-4 text-center">Detalles</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-sm">
                          {estudiantesFiltrados.map((est) => {
                            const badgeColor = {
                              "Riesgo alto": "bg-red-50 text-red-600 border-red-100",
                              "Riesgo medio": "bg-amber-50 text-amber-600 border-amber-100",
                              "Riesgo bajo": "bg-blue-50 text-blue-600 border-blue-100",
                              "Sin riesgo": "bg-emerald-50 text-emerald-600 border-emerald-100"
                            }[est.ultima_prediccion.nivel];

                            return (
                              <tr key={est.id} className="hover:bg-slate-50/50 transition-colors">
                                <td className="px-6 py-4 flex items-center space-x-3">
                                  <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs shadow-inner">
                                    {est.nombres[0]}{est.apellidos[0]}
                                  </div>
                                  <div>
                                    <p className="font-bold text-slate-800">{est.nombres} {est.apellidos}</p>
                                    <p className="text-[10px] text-slate-400 font-semibold">Código: {est.codigo_anonimizado}</p>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-slate-600 font-semibold">{est.grado} - Secc. "{est.seccion}"</td>
                                <td className="px-6 py-4">
                                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${badgeColor}`}>
                                    {est.ultima_prediccion.nivel}
                                  </span>
                                </td>
                                <td className="px-6 py-4">
                                  <span className={`text-sm font-extrabold ${est.nota_final < 11 ? "text-red-500" : "text-slate-800"}`}>
                                    {est.nota_final}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-slate-600 font-semibold">{est.inasistencias} inasistencias</td>
                                <td className="px-6 py-4">
                                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                    est.estado_pension === "al_dia" 
                                      ? "bg-emerald-50 text-emerald-700" 
                                      : "bg-red-50 text-red-700"
                                  }`}>
                                    {est.estado_pension.toUpperCase()}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-center">
                                  <button 
                                    onClick={() => setPerfilSeleccionado(est)}
                                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                  >
                                    <Eye className="w-4 h-4" />
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
              )}

              {/* Sección 3: Riesgos & Simulador */}
              {seccionActiva === "riesgos" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Alertas */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                      <div className="flex justify-between items-center mb-6">
                        <div>
                          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Alertas Activas de ML</h3>
                          <p className="text-xs text-slate-400">Notificaciones automáticas ante perfiles estudiantiles en riesgo crítico.</p>
                        </div>
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
                                <span className="text-[10px] text-slate-400 font-semibold">{alerta.fecha}</span>
                              </div>
                              <p className="text-xs text-slate-500 font-bold mt-0.5">{alerta.grado}</p>
                              <p className="text-xs text-slate-600 leading-relaxed mt-2">{alerta.mensaje}</p>
                              
                              {!alerta.atendida && (
                                <button 
                                  onClick={() => handleAtenderAlerta(alerta.id)}
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

                  {/* Simulador */}
                  <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm h-fit">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-1">Simulador de Riesgo Académico</h3>
                      <p className="text-xs text-slate-400 mb-6">Realice simulaciones hipotéticas del modelo Random Forest (No altera base de datos).</p>
                    </div>

                    <form onSubmit={handleSimularForm} className="space-y-4">
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
                            onChange={(e) => setNotaLibro(parseFloat(e.target.value) || 0)}
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
                            onChange={(e) => setNotaCuaderno(parseFloat(e.target.value) || 0)}
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
                            onChange={(e) => setNotaExamen(parseFloat(e.target.value) || 0)}
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
                            onChange={(e) => setConducta(parseFloat(e.target.value) || 0)}
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
                            onChange={(e) => setInasistencias(parseInt(e.target.value) || 0)}
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

                        {resultadoSimulado.factores.length > 0 && (
                          <div className="space-y-1.5">
                            <span className="text-[10px] font-bold text-slate-400 uppercase block">Factores críticos:</span>
                            <div className="space-y-1">
                              {resultadoSimulado.factores.map((fact, idx) => (
                                <p key={idx} className="text-[11px] text-slate-600 font-semibold flex items-center">
                                  <span className="w-1.5 h-1.5 bg-red-500 rounded-full mr-1.5"></span>
                                  {fact}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                          <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Acción recomendada:</span>
                          <p className="text-[11px] text-slate-600 leading-relaxed font-semibold">
                            {resultadoSimulado.sugerencia}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Modal Registrar Alumno */}
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
                      value={regNotaLibro}
                      onChange={(e) => setRegNotaLibro(parseFloat(e.target.value) || 0)}
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
                      value={regNotaCuaderno}
                      onChange={(e) => setRegNotaCuaderno(parseFloat(e.target.value) || 0)}
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
                      value={regNotaExamen}
                      onChange={(e) => setRegNotaExamen(parseFloat(e.target.value) || 0)}
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
                      value={regConducta}
                      onChange={(e) => setRegConducta(parseFloat(e.target.value) || 0)}
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
                    value={regInasistencias}
                    onChange={(e) => setRegInasistencias(parseInt(e.target.value) || 0)}
                    className="w-full px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-2">Estado de Pensión</label>
                  <select
                    value={regEstadoPension}
                    onChange={(e) => setRegEstadoPension(e.target.value)}
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
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>Registrar & Predicción ML</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
