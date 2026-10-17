// SIA-T: estructura de la página (menú, rótulo de datos y vistas).
import { useEffect, useState } from "react";
import { BrainCircuit, ClipboardPen, Database, LayoutDashboard, Menu, Moon, School, Sun, Users, X } from "lucide-react";
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

// Alterna el modo oscuro: clase «dark» en <html> y preferencia guardada en el navegador.
function BotonTema({ conTexto = false }: { conTexto?: boolean }) {
  const [oscuro, setOscuro] = useState(() => document.documentElement.classList.contains("dark"));
  const alternar = () => {
    const nuevo = !oscuro;
    document.documentElement.classList.toggle("dark", nuevo);
    try {
      localStorage.setItem("tema", nuevo ? "oscuro" : "claro");
    } catch {
      /* sin almacenamiento: el cambio dura hasta recargar */
    }
    setOscuro(nuevo);
  };
  return (
    <button
      onClick={alternar}
      aria-label={oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      title={oscuro ? "Modo claro" : "Modo oscuro"}
      className={`inline-flex items-center gap-2 rounded-lg text-slate-300 transition hover:bg-white/10 hover:text-white ${conTexto ? "px-2 py-1.5 text-xs font-medium" : "p-1.5"}`}
    >
      {oscuro ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      {conTexto && (oscuro ? "Modo claro" : "Modo oscuro")}
    </button>
  );
}

const Logo = ({ chico = false }: { chico?: boolean }) => (
  <span className={`flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-white ring-2 ring-pf-acento/70 ${chico ? "h-7 w-7" : "h-10 w-10"}`}>
    <img src="/logo.jpeg" alt="Insignia del Colegio Peruano Francés" className="h-full w-full object-contain" />
  </span>
);

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
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${activo ? "bg-white/10 text-white shadow-[inset_3px_0_0_var(--color-pf-acento)]" : "text-slate-300 hover:bg-white/5 hover:text-white"}`}
          >
            <Icono className={`h-[18px] w-[18px] ${activo ? "text-pf-acento-claro" : "text-slate-400"}`} />
            {texto}
          </button>
        );
      })}
    </nav>
  );

  const marca = (
    <div className="flex items-center gap-3 px-5 py-5">
      <Logo />
      <div>
        <p className="text-sm font-semibold leading-4 text-white">SIA-T</p>
        <p className="text-[11px] leading-4 text-slate-400">Alerta temprana</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 lg:flex">
      {/* Menú lateral en pantallas grandes */}
      <aside className="isla sticky top-0 hidden h-screen w-60 shrink-0 flex-col bg-pf-lateral lg:flex">
        <div className="h-1 bg-[linear-gradient(90deg,var(--color-pf-acento)_0_33%,#fff_33%_66%,var(--color-pf-acento)_66%)]" />
        {marca}
        {menu}
        <div className="border-t border-white/10 px-5 py-4 text-[11px] leading-4 text-slate-400">
          <p className="font-medium text-slate-300">I.E.P. Peruano Francés</p>
          <p>{estado?.periodo_actual ? `Periodo: ${estado.periodo_actual.nombre}` : "Sin periodo cargado"}</p>
          <div className="mt-3 -ml-2">
            <BotonTema conTexto />
          </div>
        </div>
      </aside>

      {/* Barra superior en pantallas pequeñas */}
      <header className="isla sticky top-0 z-30 flex items-center justify-between border-t-4 border-pf-acento bg-pf-lateral px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Logo chico /> SIA-T
        </div>
        <div className="flex items-center gap-1">
          <BotonTema />
          <button onClick={() => setMenuAbierto(!menuAbierto)} aria-label="Abrir el menú" className="rounded-lg p-1.5 text-slate-200 hover:bg-white/10">
          {menuAbierto ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>
      {menuAbierto && <div className="isla sticky top-[56px] z-20 bg-pf-lateral pb-3 lg:hidden">{menu}</div>}

      <div className="min-w-0 flex-1">
        <Rotulo estado={estado} />
        <main className="mx-auto max-w-6xl px-4 py-7 sm:px-8">{vista()}</main>
        {estado?.tipo_datos === "practica" && <footer className="mx-auto max-w-6xl px-4 pb-6 text-[11px] text-slate-400 sm:px-8">SIA-T · Datos de práctica</footer>}
      </div>
    </div>
  );
}
