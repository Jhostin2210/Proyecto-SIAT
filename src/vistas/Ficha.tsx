// Ficha del estudiante: nivel general, resultado por curso, informe con acciones, evolución y perfil (REQ-10 y REQ-12).
import { useMemo, useState } from "react";
import { ArrowDownRight, ArrowLeft, ArrowUpRight, FileDown, MessageCircle, X } from "lucide-react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, type Ficha as TFicha } from "../api";
import { Aviso, Barra, Boton, Cargando, ErrorDeCarga, ESTILO, Insignia, ir, nota, pct, Tarjeta, TituloTarjeta, useDatos } from "../ui";

const COLORES = ["#2563eb", "#db2777", "#0d9488", "#d97706", "#7c3aed", "#475569", "#dc2626", "#65a30d"];
const GRUPOS: [string, string][] = [
  ["historial", "Historial y colegio"],
  ["familia", "Familia"],
  ["habitos", "Hábitos"],
];

function Comunicado({ ficha, cerrar }: { ficha: TFicha; cerrar: () => void }) {
  const [mensaje, setMensaje] = useState(ficha.informe.comunicado ?? "");
  const [numero, setNumero] = useState("");
  const digitos = numero.replace(/\D/g, "");
  const destino = digitos.length >= 9 ? (digitos.length === 9 ? `51${digitos}` : digitos) : "";
  const enlace = `https://wa.me/${destino}?text=${encodeURIComponent(mensaje)}`;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-6" role="dialog" aria-modal="true" aria-label="Comunicado al apoderado">
      <div className="flex max-h-[92vh] w-full max-w-xl flex-col rounded-t-2xl bg-white shadow-xl sm:rounded-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Comunicado al apoderado</h2>
            <p className="mt-0.5 text-[13px] text-slate-500">Revise el mensaje antes de enviarlo. Puede editarlo.</p>
          </div>
          <button onClick={cerrar} aria-label="Cerrar" className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4 overflow-y-auto px-6 py-5">
          <textarea value={mensaje} onChange={(e) => setMensaje(e.target.value)} rows={13} aria-label="Mensaje" className="w-full resize-y rounded-xl border border-slate-200 p-3 text-sm leading-6 text-slate-800 outline-none focus:border-pf-enlace focus:ring-2 focus:ring-pf-suave" />
          <label className="block text-[13px] font-medium text-slate-700">
            Número de WhatsApp del apoderado (opcional)
            <input
              value={numero}
              onChange={(e) => setNumero(e.target.value)}
              inputMode="tel"
              placeholder="Ej.: 987 654 321"
              className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal outline-none focus:border-pf-enlace focus:ring-2 focus:ring-pf-suave"
            />
            <span className="mt-1 block text-xs font-normal text-slate-500">Si lo deja vacío, WhatsApp le pedirá elegir el contacto. El número no se guarda.</span>
          </label>
          <Aviso>WhatsApp solo recibe el texto. Para enviar también el reporte, descárguelo en PDF y adjúntelo en la conversación.</Aviso>
        </div>
        <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 px-6 py-4">
          <Boton variante="secundario" onClick={cerrar}>
            Cancelar
          </Boton>
          <a href={enlace} target="_blank" rel="noreferrer" onClick={cerrar} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700">
            <MessageCircle className="h-4 w-4" /> Abrir WhatsApp
          </a>
        </div>
      </div>
    </div>
  );
}

export default function Ficha({ codigo }: { codigo: string }) {
  const { datos: f, cargando, error, recargar } = useDatos(() => api.ficha(codigo), [codigo]);
  const [comunicado, setComunicado] = useState(false);

  const evolucion = useMemo(() => {
    if (!f) return { filas: [], cursos: [] as string[] };
    const cursos = [...new Set(f.historial.map((h) => h.curso))];
    const periodos = [...new Set(f.historial.map((h) => h.periodo_nombre))];
    const filas = periodos.map((p) => {
      const fila: Record<string, string | number> = { periodo: p.replace(/ de \d{4}$/, "") };
      f.historial.filter((h) => h.periodo_nombre === p).forEach((h) => (fila[h.curso] = h.nota));
      return fila;
    });
    return { filas, cursos };
  }, [f]);

  if (cargando) return <Cargando texto="Cargando la ficha…" />;
  if (error || !f) return <ErrorDeCarga mensaje={error ?? "Sin respuesta"} reintentar={recargar} />;
  const inf = f.informe;
  const e = ESTILO[inf.nivel];
  const esAlto = inf.nivel === "Riesgo alto";

  return (
    <>
      <button onClick={() => window.history.length > 1 ? window.history.back() : ir("/estudiantes")} className="mb-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-slate-900">
        <ArrowLeft className="h-4 w-4" /> Volver
      </button>

      {/* Cabecera: quién es y cuál es su nivel general */}
      <Tarjeta className="overflow-hidden">
        <div className={`h-1 ${e.barra}`} />
        <div className="flex flex-wrap items-start justify-between gap-5 p-6">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{f.nombre}</h1>
            <p className="mt-1 text-sm text-slate-500">
              {f.grado} · Código {f.codigo} · {inf.periodo_nombre}
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Insignia nivel={inf.nivel} grande />
              <span className="text-sm text-slate-600">
                Probabilidad estimada <span className="font-semibold tabular-nums text-slate-900">{pct(inf.probabilidad)}</span>
              </span>
              <span className="text-sm text-slate-600">
                Promedio <span className="font-semibold tabular-nums text-slate-900">{nota(f.promedio)}</span>
              </span>
            </div>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-700">{inf.resumen}</p>
          </div>
          <div className="flex flex-col items-stretch gap-2">
            <a href={api.urlReporte(f.codigo)} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              <FileDown className="h-4 w-4" /> Exportar reporte PDF
            </a>
            <Boton variante="verde" deshabilitado={!esAlto} onClick={() => setComunicado(true)} titulo={esAlto ? undefined : "El comunicado al apoderado se usa solo en riesgo alto"}>
              <MessageCircle className="h-4 w-4" /> Avisar al apoderado
            </Boton>
            {!esAlto && <p className="max-w-[13.5rem] text-center text-[11px] leading-4 text-slate-400">El aviso al apoderado se usa solo en riesgo alto.</p>}
          </div>
        </div>
      </Tarjeta>

      {/* Resultado por curso */}
      <Tarjeta className="mt-5">
        <TituloTarjeta titulo="Resultado por curso" detalle="La nota del curso es el promedio del examen y de los trabajos del periodo" />
        <div className="overflow-x-auto pb-2 pt-3">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs text-slate-500">
                <th className="px-6 py-2.5 font-medium">Curso</th>
                <th className="px-3 py-2.5 text-center font-medium">Nota</th>
                <th className="px-3 py-2.5 text-center font-medium">Examen</th>
                <th className="px-3 py-2.5 text-center font-medium">Trabajos</th>
                <th className="px-3 py-2.5 text-center font-medium">Periodo anterior</th>
                <th className="px-3 py-2.5 font-medium">Probabilidad</th>
                <th className="px-6 py-2.5 font-medium">Nivel</th>
              </tr>
            </thead>
            <tbody>
              {inf.cursos.map((c) => (
                <tr key={c.curso} className="border-b border-slate-100 last:border-0">
                  <td className="px-6 py-3 font-medium text-slate-900">{c.curso}</td>
                  <td className="px-3 py-3 text-center font-semibold tabular-nums text-slate-900">{nota(c.nota)}</td>
                  <td className="px-3 py-3 text-center tabular-nums text-slate-600">{nota(c.examen)}</td>
                  <td className="px-3 py-3 text-center tabular-nums text-slate-600">{nota(c.trabajos)}</td>
                  <td className="px-3 py-3 text-center tabular-nums text-slate-600">
                    {nota(c.nota_previa)}
                    {c.cambio !== null && Math.abs(c.cambio) >= 1 && (
                      <span className={`ml-1 inline-flex items-center text-xs ${c.cambio < 0 ? "text-red-600" : "text-emerald-600"}`}>
                        {c.cambio < 0 ? <ArrowDownRight className="h-3.5 w-3.5" /> : <ArrowUpRight className="h-3.5 w-3.5" />}
                        {nota(Math.abs(c.cambio))}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <Barra valor={c.probabilidad} nivel={c.nivel} />
                  </td>
                  <td className="px-6 py-3">
                    <Insignia nivel={c.nivel} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Tarjeta>

      {/* Informe: lo que se observa y qué hacer */}
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <Tarjeta>
          <TituloTarjeta titulo="Lo que se observa" />
          <ul className="space-y-2.5 px-6 pb-6 pt-4">
            {inf.patrones.map((p) => (
              <li key={p.clave} className="flex gap-2.5 text-sm leading-6 text-slate-700">
                <span className={`mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full ${p.clave === "sin_senales" ? "bg-emerald-500" : e.punto}`} />
                {p.texto}
              </li>
            ))}
          </ul>
        </Tarjeta>
        <Tarjeta>
          <TituloTarjeta titulo="Acciones recomendadas" detalle="Propuesta por validar con los docentes y con psicología" />
          <ol className="space-y-2.5 px-6 pb-6 pt-4">
            {inf.acciones.map((a, i) => (
              <li key={a} className="flex gap-3 text-sm leading-6 text-slate-700">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-600">{i + 1}</span>
                {a}
              </li>
            ))}
          </ol>
        </Tarjeta>
      </div>

      {/* Evolución de las notas */}
      {evolucion.filas.length > 1 && (
        <Tarjeta className="mt-5">
          <TituloTarjeta titulo="Evolución de las notas" detalle="Nota de cada curso por periodo. La línea punteada marca la nota aprobatoria (11)." />
          <div className="h-64 px-3 pb-4 pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={evolucion.filas} margin={{ top: 6, right: 18, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="periodo" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} tickLine={false} />
                <YAxis domain={[0, 20]} ticks={[0, 5, 11, 15, 20]} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <ReferenceLine y={11} stroke="#94a3b8" strokeDasharray="4 4" />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                {evolucion.cursos.map((c, i) => (
                  <Line key={c} type="monotone" dataKey={c} stroke={COLORES[i % COLORES.length]} strokeWidth={2} dot={{ r: 3 }} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Tarjeta>
      )}

      {/* Perfil: lo que el modelo usa además de las notas */}
      {f.perfil.length > 0 && (
        <Tarjeta className="mt-5">
          <TituloTarjeta titulo="Perfil del estudiante" detalle="Datos que el modelo usa además de las notas" />
          <div className="grid gap-x-8 gap-y-5 px-6 pb-6 pt-4 md:grid-cols-3">
            {GRUPOS.map(([clave, titulo]) => (
              <div key={clave}>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">{titulo}</h3>
                <dl className="space-y-1.5">
                  {f.perfil
                    .filter((p) => p.grupo === clave)
                    .map((p) => (
                      <div key={p.clave} className="flex justify-between gap-3 text-[13px]">
                        <dt className="text-slate-500">{p.etiqueta}</dt>
                        <dd className="text-right font-medium text-slate-800">{p.texto}</dd>
                      </div>
                    ))}
                </dl>
              </div>
            ))}
          </div>
        </Tarjeta>
      )}

      <p className="mt-5 text-xs leading-5 text-slate-500">El nivel de riesgo es una estimación de apoyo para el tutor. No reemplaza el criterio del docente ni es una calificación.</p>
      {comunicado && <Comunicado ficha={f} cerrar={() => setComunicado(false)} />}
    </>
  );
}
