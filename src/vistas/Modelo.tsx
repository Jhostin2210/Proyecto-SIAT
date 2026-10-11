// Modelo: con qué se entrenó la red neuronal, cómo se probó y qué pasó al aplicarla en el colegio (paquetes 1.3.1 y 1.3.3).
import { Area, AreaChart, CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ExternalLink } from "lucide-react";
import { api, type Modelo as TModelo } from "../api";
import { Aviso, Cargando, Encabezado, ErrorDeCarga, miles, pct, Tarjeta, TituloTarjeta, useDatos } from "../ui";

function Dato({ titulo, valor, detalle }: { titulo: string; valor: string; detalle?: string }) {
  return (
    <Tarjeta className="p-5">
      <p className="text-[13px] font-medium text-slate-500">{titulo}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight text-slate-900">{valor}</p>
      {detalle && <p className="mt-1 text-xs leading-4 text-slate-500">{detalle}</p>}
    </Tarjeta>
  );
}

/** Dibujo de la red: una columna de neuronas por capa. */
function Red({ capas }: { capas: { n: number; nombre: string }[] }) {
  const ancho = 520, alto = 190, visibles = 7;
  const x = (i: number) => 50 + (i * (ancho - 100)) / (capas.length - 1);
  const ys = (n: number) => {
    const k = Math.min(n, visibles);
    return Array.from({ length: k }, (_, j) => 22 + ((j + 0.5) * (alto - 62)) / k);
  };
  return (
    <svg viewBox={`0 0 ${ancho} ${alto}`} className="w-full" role="img" aria-label={`Red neuronal con capas de ${capas.map((c) => c.n).join(", ")} neuronas`}>
      {capas.slice(0, -1).map((c, i) => ys(c.n).map((y1) => ys(capas[i + 1].n).map((y2) => <line key={`${i}-${y1}-${y2}`} x1={x(i)} y1={y1} x2={x(i + 1)} y2={y2} stroke="#cbd5e1" strokeWidth={0.5} />)))}
      {capas.map((c, i) => (
        <g key={i}>
          {ys(c.n).map((y) => (
            <circle key={y} cx={x(i)} cy={y} r={5.5} fill={i === 0 ? "#38bdf8" : i === capas.length - 1 ? "#0f172a" : "#2563eb"} />
          ))}
          <text x={x(i)} y={alto - 22} textAnchor="middle" fontSize={13} fontWeight={600} fill="#0f172a">
            {c.n}
          </text>
          <text x={x(i)} y={alto - 7} textAnchor="middle" fontSize={10} fill="#64748b">
            {c.nombre}
          </text>
        </g>
      ))}
    </svg>
  );
}

function Matriz({ m, filas, columnas }: { m: TModelo["prueba"]["matriz"]; filas: [string, string]; columnas: [string, string] }) {
  const celda = (valor: number, acierto: boolean) => (
    <td className={`rounded-xl px-4 py-5 text-center ${acierto ? "bg-emerald-50" : "bg-red-50"}`}>
      <span className={`block text-2xl font-semibold tabular-nums ${acierto ? "text-emerald-700" : "text-red-700"}`}>{valor}</span>
      <span className="text-[11px] text-slate-500">{acierto ? "acierto" : "error"}</span>
    </td>
  );
  return (
    <table className="w-full border-separate border-spacing-1.5 text-sm">
      <thead>
        <tr className="text-xs text-slate-500">
          <th />
          <th className="pb-1 font-medium">{columnas[0]}</th>
          <th className="pb-1 font-medium">{columnas[1]}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th className="pr-2 text-right text-xs font-medium text-slate-500">{filas[0]}</th>
          {celda(m.verdaderos_negativos, true)}
          {celda(m.falsos_positivos, false)}
        </tr>
        <tr>
          <th className="pr-2 text-right text-xs font-medium text-slate-500">{filas[1]}</th>
          {celda(m.falsos_negativos, false)}
          {celda(m.verdaderos_positivos, true)}
        </tr>
      </tbody>
    </table>
  );
}

export default function Modelo() {
  const { datos: m, cargando, error, recargar } = useDatos(api.modelo);
  if (cargando) return <Cargando />;
  if (error || !m) return <ErrorDeCarga mensaje={error ?? "Sin respuesta"} reintentar={recargar} />;
  if (!m.disponible) return <Aviso>{m.mensaje}</Aviso>;

  const p = m.prueba;
  const total = m.particion.prueba;
  const col = m.aplicacion_colegio;
  const perdida = m.red.curva_de_perdida.map((v, i) => ({ epoca: i + 1, perdida: v }));
  const capas = [{ n: m.red.entradas, nombre: "entradas" }, ...m.red.capas_ocultas.map((n) => ({ n, nombre: "oculta" })), { n: 1, nombre: "salida" }];

  return (
    <>
      <Encabezado titulo="Modelo de riesgo" detalle={`${m.nombre} ${m.red.arquitectura} · entrenada el ${m.fecha_entrenamiento}`} />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Dato titulo="Exactitud en la prueba" valor={pct(p.exactitud, 1)} detalle={`${p.matriz.verdaderos_negativos + p.matriz.verdaderos_positivos} aciertos de ${total} casos que la red no vio`} />
        <Dato titulo="AUC" valor={p.auc_roc.toFixed(2).replace(".", ",")} detalle="Qué tan bien ordena de mayor a menor riesgo (1 es perfecto)" />
        <Dato titulo="Detecta" valor={pct(p.le_va_mal.recall)} detalle="De los estudiantes a los que les fue mal" />
        <Dato titulo="Aciertos de sus alertas" valor={pct(p.le_va_mal.precision)} detalle={`Sin modelo, decir que a nadie le va mal acierta ${pct(m.exactitud_sin_modelo)}`} />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Tarjeta>
          <TituloTarjeta titulo="Base de entrenamiento" detalle={`${m.base.nombre}, de ${m.base.autores}`} />
          <div className="space-y-3 px-6 pb-6 pt-4 text-sm leading-6 text-slate-700">
            <p>{m.base.descripcion}</p>
            <p>
              <span className="font-semibold tabular-nums text-slate-900">{miles(m.base.registros)}</span> registros de {m.base.estudiantes} estudiantes; a <span className="font-semibold tabular-nums text-slate-900">{m.base.con_mal_resultado}</span> les fue mal en el
              curso.
            </p>
            <p>
              <span className="font-semibold text-slate-900">Qué predice.</span> {m.que_predice}
            </p>
            <p className="text-[13px] text-slate-500">
              Se usan {m.variables.length} variables: las notas de los dos periodos anteriores, inasistencias, historial, familia y hábitos. {m.particion.metodo}
            </p>
            <a href={m.base.enlace} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[13px] font-semibold text-blue-700 hover:text-blue-900">
              {m.base.origen} <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </Tarjeta>

        <Tarjeta>
          <TituloTarjeta titulo="Arquitectura" detalle={`Activación ${m.red.activacion} · optimizador ${m.red.optimizador} · variables con ${m.red.escalado}`} />
          <div className="px-4 pb-4 pt-2">
            <Red capas={capas} />
          </div>
        </Tarjeta>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Tarjeta>
          <TituloTarjeta titulo="Matriz de confusión" detalle={`Prueba con ${total} registros que la red no vio en el entrenamiento`} />
          <div className="px-5 pb-3 pt-3">
            <Matriz m={p.matriz} filas={["Le fue bien", "Le fue mal"]} columnas={["Predijo que bien", "Predijo que mal"]} />
          </div>
          <div className="overflow-x-auto px-6 pb-6">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr className="border-b border-slate-200 text-xs text-slate-500">
                  <th className="py-2 font-medium">Clase</th>
                  <th className="py-2 text-center font-medium">Precisión</th>
                  <th className="py-2 text-center font-medium">Recall</th>
                  <th className="py-2 text-center font-medium">F1</th>
                </tr>
              </thead>
              <tbody className="tabular-nums text-slate-700">
                {(
                  [
                    ["Le va bien", p.le_va_bien],
                    ["Le va mal", p.le_va_mal],
                  ] as const
                ).map(([nombre, c]) => (
                  <tr key={nombre} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 font-medium text-slate-900">{nombre}</td>
                    <td className="py-2 text-center">{c.precision.toFixed(2).replace(".", ",")}</td>
                    <td className="py-2 text-center">{c.recall.toFixed(2).replace(".", ",")}</td>
                    <td className="py-2 text-center">{c.f1.toFixed(2).replace(".", ",")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              En el entrenamiento la exactitud fue {pct(m.entrenamiento.exactitud, 1)}. En validación cruzada de 5 partes, {pct(m.validacion_cruzada.exactitud.media, 1)} ± {pct(m.validacion_cruzada.exactitud.desviacion, 1)}.
            </p>
          </div>
        </Tarjeta>

        <Tarjeta>
          <TituloTarjeta titulo="Aprendizaje" detalle={`Pérdida en cada época. Se detuvo en la época ${m.red.epocas}, cuando dejó de mejorar.`} />
          <div className="h-72 px-3 pb-4 pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={perdida} margin={{ top: 6, right: 18, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="epoca" type="number" domain={[1, "dataMax"]} tickCount={7} allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} domain={["auto", "auto"]} />
                <Tooltip formatter={(v: number) => [v.toFixed(3).replace(".", ","), "Pérdida"]} labelFormatter={(e) => `Época ${e}`} contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Line type="monotone" dataKey="perdida" stroke="#2563eb" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Tarjeta>
      </div>

      <Tarjeta className="mt-5">
        <TituloTarjeta titulo="De la probabilidad a los tres niveles" detalle={m.niveles.equivalencia} />
        <div className="grid gap-6 px-6 pb-6 pt-4 lg:grid-cols-[1fr_17rem]">
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={m.niveles.curva} margin={{ top: 6, right: 12, left: -14, bottom: 0 }}>
                <CartesianGrid stroke="#f1f5f9" vertical={false} />
                <ReferenceArea x1={5} x2={9.5} fill="#fee2e2" fillOpacity={0.6} />
                <ReferenceArea x1={9.5} x2={14.5} fill="#fef3c7" fillOpacity={0.6} />
                <ReferenceArea x1={14.5} x2={20} fill="#d1fae5" fillOpacity={0.6} />
                <XAxis dataKey="nota" type="number" domain={[5, 20]} ticks={[5, 8, 10, 11, 15, 18, 20]} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={{ stroke: "#e2e8f0" }} tickLine={false} />
                <YAxis tickFormatter={(v) => `${Math.round(v * 100)} %`} domain={[0, 1]} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: number) => [pct(v, 1), "Probabilidad"]} labelFormatter={(n) => `Nota ${n}`} contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Area type="monotone" dataKey="probabilidad" stroke="#0f172a" strokeWidth={2} fill="#0f172a" fillOpacity={0.06} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-3 text-sm">
            {(
              [
                ["Riesgo alto", "bg-red-500", `Probabilidad de ${pct(m.niveles.alto_desde)} o más`],
                ["Riesgo medio", "bg-amber-500", `De ${pct(m.niveles.medio_desde)} a ${pct(m.niveles.alto_desde)}`],
                ["Riesgo bajo", "bg-emerald-500", `Menos de ${pct(m.niveles.medio_desde)}`],
              ] as const
            ).map(([nombre, color, texto]) => (
              <div key={nombre} className="flex items-start gap-2.5">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${color}`} />
                <p className="leading-5 text-slate-700">
                  <span className="font-semibold text-slate-900">{nombre}.</span> {texto}
                </p>
              </div>
            ))}
            <p className="pt-1 text-xs leading-5 text-slate-500">La curva muestra la probabilidad que la red da a cada nota del colegio en un estudiante típico. Los demás datos del estudiante pueden moverlo de nivel.</p>
          </div>
        </div>
      </Tarjeta>

      {col && (
        <Tarjeta className="mt-5">
          <TituloTarjeta titulo="Aplicación en el colegio" detalle={`${col.casos} casos de ${col.estudiantes} estudiantes · ${col.fecha.slice(0, 10)}`} />
          <div className="px-6 pb-6 pt-4">
            <p className="max-w-3xl text-sm leading-6 text-slate-700">
              {col.como} En {col.les_fue_mal} de los {col.casos} casos ({pct(col.proporcion, 1)}) la nota del curso fue desaprobatoria en el periodo siguiente.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {(
                [
                  ["Riesgo alto", "alto", "border-red-200 bg-red-50 text-red-800"],
                  ["Riesgo medio", "medio", "border-amber-200 bg-amber-50 text-amber-800"],
                  ["Riesgo bajo", "bajo", "border-emerald-200 bg-emerald-50 text-emerald-800"],
                ] as const
              ).map(([nombre, clave, clase]) => {
                const n = col.niveles[clave];
                return (
                  <div key={clave} className={`rounded-xl border p-4 ${clase}`}>
                    <p className="text-xs font-semibold uppercase tracking-wide">{nombre}</p>
                    <p className="mt-1.5 text-2xl font-semibold tabular-nums">{pct(n.les_fue_mal / Math.max(1, n.casos))}</p>
                    <p className="text-xs opacity-80">
                      les fue mal después: {n.les_fue_mal} de {n.casos} casos
                    </p>
                  </div>
                );
              })}
            </div>
            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[520px] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-slate-200 text-xs text-slate-500">
                    <th className="py-2 font-medium">Si se alerta…</th>
                    <th className="py-2 text-center font-medium">Exactitud</th>
                    <th className="py-2 text-center font-medium">Detecta</th>
                    <th className="py-2 text-center font-medium">Aciertos de sus alertas</th>
                  </tr>
                </thead>
                <tbody className="tabular-nums text-slate-700">
                  {(
                    [
                      ["Solo el nivel alto", col.alerta_solo_alto],
                      ["Los niveles medio y alto", col.alerta_medio_y_alto],
                    ] as const
                  ).map(([nombre, a]) => (
                    <tr key={nombre} className="border-b border-slate-100 last:border-0">
                      <td className="py-2 font-medium text-slate-900">{nombre}</td>
                      <td className="py-2 text-center">{pct(a.exactitud, 1)}</td>
                      <td className="py-2 text-center">
                        {pct(a.detecta)} ({a.matriz.verdaderos_positivos} de {col.les_fue_mal})
                      </td>
                      <td className="py-2 text-center">{pct(a.aciertos)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              AUC en el colegio: {col.auc_roc.toFixed(2).replace(".", ",")}. Sin modelo, decir que a nadie le irá mal acierta {pct(col.exactitud_sin_modelo, 1)}: por eso la exactitud sola no basta para juzgar las alertas.
            </p>
          </div>
        </Tarjeta>
      )}

      <Tarjeta className="mt-5">
        <TituloTarjeta titulo="Límites" />
        <ul className="list-disc space-y-1.5 px-6 pb-6 pl-10 pt-3 text-sm leading-6 text-slate-700">
          <li>La red se entrenó con estudiantes de secundaria de otro país. Lo que mejor se traslada es la relación entre la nota y el riesgo.</li>
          <li>En el colegio hay pocos casos con mal resultado; los porcentajes pueden cambiar con más datos.</li>
          <li>El nivel medio acierta poco: sirve como lista de seguimiento, no como alerta.</li>
          <li>Falta comprobar las alertas en un periodo nuevo y contrastarlas con el criterio de los docentes, en el piloto.</li>
          <li>Cuando el colegio acumule uno o dos años completos de datos, conviene volver a entrenar con ellos.</li>
        </ul>
      </Tarjeta>
    </>
  );
}
