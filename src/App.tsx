// SIA-T: estructura de la página (menú, rótulo de datos y vistas).
import { useEffect, useState } from "react";
import { BrainCircuit, ClipboardPen, Database, LayoutDashboard, Menu, School, Users, X } from "lucide-react";
import { api, type Estado } from "./api";
import { ir, useDatos } from "./ui";
import Inicio from "./vistas/Inicio";
import Aulas from "./vistas/Aulas";
import Estudiantes from "./vistas/Estudiantes";
import Ficha from "./vistas/Ficha";
import Evaluar from "./vistas/Evaluar";
import Modelo from "./vistas/Modelo";
import Datos from "./vistas/Datos";

function useRuta(): string[] {
  const leer = () => window.location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const [ruta, setRuta] = useState<string[]>(leer);
  useEffect(() => {
    const alCambiar = () => setRuta(leer());
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  }, []);
  return ruta;
}

const MENU = [
  { clave: "inicio", texto: "Inicio", icono: LayoutDashboard },
  { clave: "aulas", texto: "Aulas", icono: School },
  { clave: "estudiantes", texto: "Estudiantes", icono: Users },
  { clave: "evaluar", texto: "Evaluar estudiante", icono: ClipboardPen },
  { clave: "modelo", texto: "Modelo", icono: BrainCircuit },
  { clave: "datos", texto: "Datos", icono: Database },
];

function Rotulo({ estado }: { estado: Estado | null }) {
  if (!estado || estado.base_de_datos.conectada) return null;
  return <div className="border-b border-red-200 bg-red-50 px-6 py-2 text-[13px] text-red-800">No hay conexión con la base de datos.</div>;
}

export default function App() {
  const ruta = useRuta();
  const seccion = ruta[0] ?? "inicio";
  const [menuAbierto, setMenuAbierto] = useState(false);
  const { datos: estado } = useDatos(api.estado);
  useEffect(() => setMenuAbierto(false), [ruta.join("/")]);

  const vista = () => {
    if (seccion === "aulas") return <Aulas grado={ruta[1]} />;
    if (seccion === "estudiantes") return ruta[1] ? <Ficha codigo={ruta[1]} /> : <Estudiantes />;
    if (seccion === "evaluar") return <Evaluar />;
    if (seccion === "modelo") return <Modelo />;
    if (seccion === "datos") return <Datos />;
    return <Inicio estado={estado} />;
  };

  const menu = (
    <nav className="flex flex-1 flex-col gap-1 px-3">
      {MENU.map(({ clave, texto, icono: Icono }) => {
        const activo = seccion === clave;
        return (
          <button
            key={clave}
            onClick={() => ir(`/${clave}`)}
            aria-current={activo ? "page" : undefined}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${activo ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"}`}
          >
            <Icono className={`h-[18px] w-[18px] ${activo ? "text-sky-300" : "text-slate-400"}`} />
            {texto}
          </button>
        );
      })}
    </nav>
  );

  const marca = (
    <div className="flex items-center gap-3 px-5 py-5">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 text-sm font-bold text-white">S</div>
      <div>
        <p className="text-sm font-semibold leading-4 text-white">SIA-T</p>
        <p className="text-[11px] leading-4 text-slate-400">Alerta temprana</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 lg:flex">
      {/* Menú lateral en pantallas grandes */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col bg-slate-900 lg:flex">
        {marca}
        {menu}
        <div className="border-t border-white/10 px-5 py-4 text-[11px] leading-4 text-slate-400">
          <p className="font-medium text-slate-300">I.E.P. Peruano Francés</p>
          <p>{estado?.periodo_actual ? `Periodo: ${estado.periodo_actual.nombre}` : "Sin periodo cargado"}</p>
        </div>
      </aside>

      {/* Barra superior en pantallas pequeñas */}
      <header className="sticky top-0 z-30 flex items-center justify-between bg-slate-900 px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-blue-600 text-xs font-bold">S</span> SIA-T
        </div>
        <button onClick={() => setMenuAbierto(!menuAbierto)} aria-label="Abrir el menú" className="rounded-lg p-1.5 text-slate-200 hover:bg-white/10">
          {menuAbierto ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>
      {menuAbierto && <div className="sticky top-[52px] z-20 bg-slate-900 pb-3 lg:hidden">{menu}</div>}

      <div className="min-w-0 flex-1">
        <Rotulo estado={estado} />
        <main className="mx-auto max-w-6xl px-4 py-7 sm:px-8">{vista()}</main>
        {estado?.tipo_datos === "practica" && <footer className="mx-auto max-w-6xl px-4 pb-6 text-[11px] text-slate-400 sm:px-8">SIA-T · Datos de práctica</footer>}
      </div>
    </div>
  );
}
