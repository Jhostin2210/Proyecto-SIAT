// Estudiantes: lista completa con búsqueda y filtros por nivel de riesgo y grado.
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { api, type Nivel } from "../api";
import { Cargando, Encabezado, ErrorDeCarga, ESTILO, NIVELES, Tarjeta, useDatos } from "../ui";
import { TablaEstudiantes } from "./Aulas";

const sinTildes = (t: string) => t.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export default function Estudiantes() {
  const estudiantes = useDatos(api.estudiantes);
  const [busqueda, setBusqueda] = useState("");
  const [nivel, setNivel] = useState<Nivel | "">("");
  const [grado, setGrado] = useState("");
  const [visibles, setVisibles] = useState(30);

  const lista = estudiantes.datos ?? [];
  const grados = useMemo(() => [...new Set(lista.map((e) => e.grado))], [lista]);
  const filtrada = useMemo(() => {
    const q = sinTildes(busqueda.trim());
    return lista.filter((e) => (!nivel || e.nivel === nivel) && (!grado || e.grado === grado) && (!q || sinTildes(`${e.nombre} ${e.codigo}`).includes(q)));
  }, [lista, busqueda, nivel, grado]);

  if (estudiantes.cargando) return <Cargando />;
  if (estudiantes.error) return <ErrorDeCarga mensaje={estudiantes.error} reintentar={estudiantes.recargar} />;

  return (
    <>
      <Encabezado titulo="Estudiantes" detalle={`${filtrada.length} de ${lista.length} estudiantes, ordenados de mayor a menor riesgo`} />
      <Tarjeta>
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-6 py-4">
          <label className="relative min-w-[14rem] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por nombre o código"
              aria-label="Buscar estudiante"
              className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </label>
          <div className="flex items-center gap-1.5" role="group" aria-label="Filtrar por nivel de riesgo">
            <button onClick={() => setNivel("")} className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${nivel === "" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`}>
              Todos
            </button>
            {NIVELES.map((n) => (
              <button
                key={n}
                onClick={() => setNivel(nivel === n ? "" : n)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${nivel === n ? `${ESTILO[n].fondo} ${ESTILO[n].texto} ${ESTILO[n].borde}` : "border-transparent text-slate-600 hover:bg-slate-100"}`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${ESTILO[n].punto}`} />
                {ESTILO[n].corto}
              </button>
            ))}
          </div>
          <select value={grado} onChange={(e) => setGrado(e.target.value)} aria-label="Filtrar por grado" className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
            <option value="">Todos los grados</option>
            {grados.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
        <TablaEstudiantes lista={filtrada.slice(0, visibles)} conGrado />
        {filtrada.length > visibles && (
          <div className="border-t border-slate-100 px-6 py-4 text-center">
            <button onClick={() => setVisibles(visibles + 30)} className="text-[13px] font-semibold text-blue-700 hover:text-blue-900">
              Mostrar 30 más ({filtrada.length - visibles} restantes)
            </button>
          </div>
        )}
      </Tarjeta>
    </>
  );
}
