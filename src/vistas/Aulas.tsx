// Aulas: resumen por grado y evaluación del aula completa con el modelo (REQ-08 y REQ-09).
import { useState } from "react";
import { ArrowLeft, CheckCircle2, Download, Loader2, PlayCircle } from "lucide-react";
import { api, type Estudiante } from "../api";
import { Barra, Boton, Cargando, Encabezado, ErrorDeCarga, Insignia, ir, nota, Reparto, Tarjeta, useDatos } from "../ui";

export function TablaEstudiantes({ lista, conGrado = false }: { lista: Estudiante[]; conGrado?: boolean }) {
  if (lista.length === 0) return <p className="px-6 py-10 text-center text-sm text-slate-500">Ningún estudiante con esos criterios.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs font-medium text-slate-500">
            <th className="px-6 py-3 font-medium">Estudiante</th>
            {conGrado && <th className="px-3 py-3 font-medium">Grado</th>}
            <th className="px-3 py-3 text-center font-medium">Promedio</th>
            <th className="px-3 py-3 font-medium">Nivel</th>
            <th className="px-3 py-3 font-medium">Probabilidad</th>
            <th className="px-6 py-3 font-medium">Cursos en riesgo</th>
          </tr>
        </thead>
        <tbody>
          {lista.map((e) => (
            <tr key={e.codigo} onClick={() => ir(`/estudiantes/${e.codigo}`)} className="cursor-pointer border-b border-slate-100 transition last:border-0 hover:bg-slate-50">
              <td className="px-6 py-3">
                <span className="font-medium text-slate-900">{e.nombre}</span>
                <span className="ml-2 text-xs text-slate-400">{e.codigo}</span>
              </td>
              {conGrado && <td className="px-3 py-3 text-slate-600">{e.grado}</td>}
              <td className="px-3 py-3 text-center tabular-nums text-slate-700">{nota(e.promedio)}</td>
              <td className="px-3 py-3">
                <Insignia nivel={e.nivel} />
              </td>
              <td className="px-3 py-3">
                <Barra valor={e.probabilidad} nivel={e.nivel} />
              </td>
              <td className="px-6 py-3 text-[13px] text-slate-600">
                {e.cursos_alto + e.cursos_medio === 0 ? (
                  <span className="text-slate-400">Ninguno</span>
                ) : (
                  <>
                    {e.cursos_alto > 0 && <span className="font-semibold text-red-600">{e.cursos_alto} alto</span>}
                    {e.cursos_alto > 0 && e.cursos_medio > 0 && " · "}
                    {e.cursos_medio > 0 && <span className="font-semibold text-amber-600">{e.cursos_medio} medio</span>}
                    <span className="text-slate-400"> de {e.cursos}</span>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Aula({ grado }: { grado: string }) {
  const estudiantes = useDatos(api.estudiantes);
  const [evaluando, setEvaluando] = useState(false);
  const [resultado, setResultado] = useState<{ evaluados: number; milisegundos: number; fecha: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const evaluar = async () => {
    setEvaluando(true);
    setError(null);
    try {
      const r = await api.evaluarAula(grado);
      setResultado(r);
      estudiantes.recargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEvaluando(false);
    }
  };

  if (estudiantes.cargando && !estudiantes.datos) return <Cargando />;
  if (estudiantes.error || !estudiantes.datos) return <ErrorDeCarga mensaje={estudiantes.error ?? "Sin respuesta"} reintentar={estudiantes.recargar} />;
  const lista = estudiantes.datos.filter((e) => e.grado === grado);
  const cuenta = (n: string) => lista.filter((e) => e.nivel === n).length;

  return (
    <>
      <button onClick={() => ir("/aulas")} className="mb-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-slate-900">
        <ArrowLeft className="h-4 w-4" /> Aulas
      </button>
      <Encabezado
        titulo={grado}
        detalle={`${lista.length} estudiantes · ${lista[0]?.periodo_nombre ?? ""}`}
        acciones={
          <>
            <a href={api.urlExportarAula(grado)} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              <Download className="h-4 w-4" /> Exportar
            </a>
            <Boton onClick={evaluar} deshabilitado={evaluando}>
              {evaluando ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
              {evaluando ? "Evaluando…" : "Evaluar aula"}
            </Boton>
          </>
        }
      />
      {resultado && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-[13px] text-emerald-800">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          El modelo evaluó a los {resultado.evaluados} estudiantes del aula en {(resultado.milisegundos / 1000).toFixed(1).replace(".", ",")} segundos ({resultado.fecha.slice(11, 16)}).
        </div>
      )}
      {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-800">No se pudo evaluar: {error}</div>}
      <Tarjeta>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-slate-100 px-6 py-4 text-[13px] text-slate-600">
          <div className="w-48">
            <Reparto alto={cuenta("Riesgo alto")} medio={cuenta("Riesgo medio")} bajo={cuenta("Riesgo bajo")} />
          </div>
          <span>
            <span className="font-semibold text-red-600">{cuenta("Riesgo alto")}</span> en riesgo alto
          </span>
          <span>
            <span className="font-semibold text-amber-600">{cuenta("Riesgo medio")}</span> en medio
          </span>
          <span>
            <span className="font-semibold text-emerald-600">{cuenta("Riesgo bajo")}</span> en bajo
          </span>
        </div>
        <TablaEstudiantes lista={lista} />
      </Tarjeta>
    </>
  );
}

export default function Aulas({ grado }: { grado?: string }) {
  const aulas = useDatos(api.aulas);
  if (grado) return <Aula grado={grado} />;
  if (aulas.cargando) return <Cargando />;
  if (aulas.error || !aulas.datos) return <ErrorDeCarga mensaje={aulas.error ?? "Sin respuesta"} reintentar={aulas.recargar} />;
  const niveles = [...new Set(aulas.datos.map((a) => a.nivel_educativo))];
  return (
    <>
      <Encabezado titulo="Aulas" detalle="Elija un aula para ver a sus estudiantes y evaluarla completa" />
      {niveles.map((nivel) => (
        <div key={nivel} className="mb-7">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">{nivel}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {aulas.datos!
              .filter((a) => a.nivel_educativo === nivel)
              .map((a) => (
                <button key={a.grado} onClick={() => ir(`/aulas/${encodeURIComponent(a.grado)}`)} className="rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition hover:border-slate-300 hover:shadow-md">
                  <div className="flex items-baseline justify-between">
                    <span className="text-base font-semibold text-slate-900">{a.grado}</span>
                    <span className="text-xs text-slate-500">{a.estudiantes} estudiantes</span>
                  </div>
                  <div className="mt-4">
                    <Reparto alto={a.alto} medio={a.medio} bajo={a.bajo} />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                    <span>
                      <span className="font-semibold text-red-600">{a.alto}</span> alto · <span className="font-semibold text-amber-600">{a.medio}</span> medio · <span className="font-semibold text-emerald-600">{a.bajo}</span> bajo
                    </span>
                    <span>Promedio {nota(a.promedio)}</span>
                  </div>
                </button>
              ))}
          </div>
        </div>
      ))}
    </>
  );
}
