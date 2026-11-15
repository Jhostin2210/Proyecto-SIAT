// Evolución por mes (REQ-08): filtro por mes y comparación con el mes anterior, en total y por aula.
// También muestra cuándo fue la última clasificación automática semanal (REQ-04).
import { useEffect, useState } from "react";
import { ArrowDownRight, ArrowUpRight, CalendarClock, Minus } from "lucide-react";
import { api, type Periodo, type ResumenMes } from "../api";
import { Reparto, Tarjeta, TituloTarjeta, nota, useDatos } from "../ui";

const fecha = (iso: string | null) => (iso ? new Date(iso).toLocaleString("es-PE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—");

// Diferencia frente al mes anterior. «mejor» indica si subir es bueno (promedio) o malo (riesgo alto).
function Cambio({ ahora, antes, mejorSiSube, decimales = 0 }: { ahora: number | null; antes: number | null | undefined; mejorSiSube: boolean; decimales?: number }) {
  if (ahora === null || antes === null || antes === undefined) return <span className="text-[11px] text-slate-400">—</span>;
  const d = Math.round((ahora - antes) * 10 ** decimales) / 10 ** decimales;
  if (d === 0)
    return (
      <span className="inline-flex items-center gap-0.5 text-[11px] text-slate-400">
        <Minus className="h-3 w-3" /> igual
      </span>
    );
  const bueno = d > 0 === mejorSiSube;
  const Icono = d > 0 ? ArrowUpRight : ArrowDownRight;
  return (
    <span className={`inline-flex items-center gap-0.5 text-[11px] font-semibold ${bueno ? "text-emerald-600" : "text-red-600"}`}>
      <Icono className="h-3 w-3" />
      {d > 0 ? "+" : ""}
      {d.toFixed(decimales).replace(".", ",")}
    </span>
  );
}

function Cifra({ titulo, valor, antes, color, mejorSiSube, decimales }: { titulo: string; valor: number | null; antes?: number | null; color?: string; mejorSiSube: boolean; decimales?: number }) {
  return (
    <div className="rounded-xl border border-slate-200 px-4 py-3">
      <p className="flex items-center gap-1.5 text-xs text-slate-500">
        {color && <span className={`h-2 w-2 rounded-full ${color}`} />}
        {titulo}
      </p>
      <p className="mt-1 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums text-slate-900">{valor === null ? "—" : decimales ? nota(valor) : valor}</span>
        <Cambio ahora={valor} antes={antes} mejorSiSube={mejorSiSube} decimales={decimales} />
      </p>
    </div>
  );
}

export function ClasificacionSemanal() {
  const { datos } = useDatos(api.clasificaciones);
  if (!datos?.ultima) return null;
  const ultima = datos.historial[0];
  return (
    <p className="mb-4 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-[13px] text-slate-600">
      <CalendarClock className="h-4 w-4 text-pf-enlace" />
      <span>
        Clasificación automática cada {datos.frecuencia_dias} días. Última: <strong className="text-slate-900">{fecha(datos.ultima)}</strong> ({ultima.motivo}).
      </span>
      <span className="text-slate-400">Próxima: {fecha(datos.proxima)}</span>
    </p>
  );
}

export default function EvolucionPorMes() {
  const { datos } = useDatos(api.evolucion);
  const [elegido, setElegido] = useState<string | null>(null);
  useEffect(() => {
    if (datos?.length && !elegido) setElegido(datos[datos.length - 1].periodo);
  }, [datos, elegido]);
  if (!datos || datos.length === 0) return null;
  const actual = datos.find((p) => p.periodo === elegido) ?? datos[datos.length - 1];
  const anterior: Periodo | undefined = datos.find((p) => p.periodo === actual.anterior);
  const aulaAntes = (grado: string): ResumenMes | undefined => anterior?.aulas.find((a) => a.grado === grado);

  return (
    <Tarjeta className="mt-5">
      <TituloTarjeta
        titulo="Evolución por mes"
        detalle={anterior ? `${actual.periodo_nombre} frente a ${anterior.periodo_nombre.toLowerCase()}` : `${actual.periodo_nombre} · primer mes con datos`}
      />
      <div className="flex flex-wrap gap-1.5 px-5 pt-4">
        {datos.map((p) => (
          <button
            key={p.periodo}
            onClick={() => setElegido(p.periodo)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition ${p.periodo === actual.periodo ? "border-pf-enlace bg-pf-enlace text-white" : "border-slate-200 text-slate-600 hover:border-pf-enlace"}`}
          >
            {p.periodo_nombre.replace(" de 2026", "").replace(" de 2027", "")}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3 px-5 pt-4 lg:grid-cols-4">
        <Cifra titulo="Riesgo alto" valor={actual.alto} antes={anterior?.alto} color="bg-red-500" mejorSiSube={false} />
        <Cifra titulo="Riesgo medio" valor={actual.medio} antes={anterior?.medio} color="bg-amber-500" mejorSiSube={false} />
        <Cifra titulo="Riesgo bajo" valor={actual.bajo} antes={anterior?.bajo} color="bg-emerald-500" mejorSiSube />
        <Cifra titulo="Promedio de notas" valor={actual.promedio} antes={anterior?.promedio} mejorSiSube decimales={1} />
      </div>
      <div className="overflow-x-auto px-5 pb-5 pt-4">
        <table className="w-full min-w-[560px] text-left text-[13px]">
          <thead>
            <tr className="border-b border-slate-200 text-xs text-slate-500">
              <th className="py-2 font-medium">Aula</th>
              <th className="py-2 font-medium">Niveles</th>
              <th className="py-2 text-center font-medium">Riesgo alto</th>
              <th className="py-2 text-center font-medium">Promedio</th>
              <th className="py-2 text-right font-medium">Estudiantes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {actual.aulas.map((a) => {
              const antes = aulaAntes(a.grado);
              return (
                <tr key={a.grado}>
                  <td className="py-2 font-medium text-slate-800">{a.grado}</td>
                  <td className="w-40 py-2">
                    <Reparto alto={a.alto} medio={a.medio} bajo={a.bajo} />
                  </td>
                  <td className="py-2 text-center tabular-nums">
                    {a.alto} <Cambio ahora={a.alto} antes={antes?.alto} mejorSiSube={false} />
                  </td>
                  <td className="py-2 text-center tabular-nums">
                    {nota(a.promedio)} <Cambio ahora={a.promedio} antes={antes?.promedio} mejorSiSube decimales={1} />
                  </td>
                  <td className="py-2 text-right tabular-nums text-slate-500">{a.estudiantes}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="mt-2 text-[11px] text-slate-400">Flecha verde: mejora frente al mes anterior; roja: empeora. Cada estudiante cuenta en los meses en que tiene notas.</p>
      </div>
    </Tarjeta>
  );
}
