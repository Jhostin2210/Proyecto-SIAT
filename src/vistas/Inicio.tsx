// Inicio: indicadores de riesgo, reparto por aula y estudiantes que requieren atención (REQ-06 y REQ-08).
import { ArrowRight, Database, ShieldCheck } from "lucide-react";
import { api, type Estado } from "../api";
import { Cargando, Encabezado, ErrorDeCarga, Insignia, ir, miles, pct, Reparto, Tarjeta, TituloTarjeta, useDatos } from "../ui";

function Indicador({ titulo, valor, detalle, color }: { titulo: string; valor: number | string; detalle: string; color?: string }) {
  return (
    <Tarjeta className="p-5">
      <p className="flex items-center gap-2 text-[13px] font-medium text-slate-500">
        {color && <span className={`h-2 w-2 rounded-full ${color}`} />}
        {titulo}
      </p>
      <p className="mt-2 text-3xl font-semibold tabular-nums tracking-tight text-slate-900">{valor}</p>
      <p className="mt-1 text-xs text-slate-500">{detalle}</p>
    </Tarjeta>
  );
}

export default function Inicio({ estado }: { estado: Estado | null }) {
  const estudiantes = useDatos(api.estudiantes);
  const aulas = useDatos(api.aulas);
  const calidad = useDatos(api.calidad);

  if (estudiantes.cargando || aulas.cargando) return <Cargando texto="Cargando el panel…" />;
  if (estudiantes.error || !estudiantes.datos || !aulas.datos) return <ErrorDeCarga mensaje={estudiantes.error ?? aulas.error ?? "Sin respuesta"} reintentar={() => (estudiantes.recargar(), aulas.recargar())} />;

  const lista = estudiantes.datos;
  const total = lista.length;
  const cuenta = (nivel: string) => lista.filter((e) => e.nivel === nivel).length;
  const [alto, medio, bajo] = [cuenta("Riesgo alto"), cuenta("Riesgo medio"), cuenta("Riesgo bajo")];
  const atencion = lista.filter((e) => e.nivel === "Riesgo alto").slice(0, 6);

  if (total === 0)
    return (
      <>
        <Encabezado titulo="Panel de alerta temprana" />
        <Tarjeta className="p-8 text-center text-sm text-slate-500">La base de datos todavía no tiene notas cargadas.</Tarjeta>
      </>
    );

  return (
    <>
      <Encabezado titulo="Panel de alerta temprana" detalle={estado?.periodo_actual ? `Situación al cierre de ${estado.periodo_actual.nombre.toLowerCase()}` : undefined} />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Indicador titulo="Estudiantes evaluados" valor={total} detalle={`${aulas.datos.length} aulas`} />
        <Indicador titulo="Riesgo alto" valor={alto} detalle={`${pct(alto / total)} · requieren acción`} color="bg-red-500" />
        <Indicador titulo="Riesgo medio" valor={medio} detalle={`${pct(medio / total)} · en seguimiento`} color="bg-amber-500" />
        <Indicador titulo="Riesgo bajo" valor={bajo} detalle={`${pct(bajo / total)} · sin señales`} color="bg-emerald-500" />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <Tarjeta className="lg:col-span-3">
          <TituloTarjeta titulo="Riesgo por aula" detalle="Proporción de estudiantes en cada nivel" />
          <ul className="px-3 pb-3 pt-3">
            {aulas.datos.map((a) => (
              <li key={a.grado}>
                <button onClick={() => ir(`/aulas/${encodeURIComponent(a.grado)}`)} className="grid w-full grid-cols-[7.5rem_1fr_auto] items-center gap-4 rounded-xl px-3 py-2.5 text-left transition hover:bg-slate-50">
                  <span className="text-sm font-medium text-slate-800">{a.grado}</span>
                  <Reparto alto={a.alto} medio={a.medio} bajo={a.bajo} />
                  <span className="w-28 text-right text-xs tabular-nums text-slate-500">
                    <span className="font-semibold text-red-600">{a.alto}</span> · <span className="font-semibold text-amber-600">{a.medio}</span> · <span className="font-semibold text-emerald-600">{a.bajo}</span>
                    <span className="ml-1 text-slate-400">de {a.estudiantes}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Tarjeta>

        <Tarjeta className="lg:col-span-2">
          <TituloTarjeta
            titulo="Requieren atención"
            detalle={`${alto} estudiante${alto === 1 ? "" : "s"} en riesgo alto`}
            accion={
              <button onClick={() => ir("/estudiantes")} className="inline-flex items-center gap-1 text-[13px] font-semibold text-blue-700 hover:text-blue-900">
                Ver todos <ArrowRight className="h-3.5 w-3.5" />
              </button>
            }
          />
          {atencion.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-slate-500">Ningún estudiante en riesgo alto.</p>
          ) : (
            <ul className="px-3 pb-3 pt-3">
              {atencion.map((e) => (
                <li key={e.codigo}>
                  <button onClick={() => ir(`/estudiantes/${e.codigo}`)} className="w-full rounded-xl px-3 py-2.5 text-left transition hover:bg-slate-50">
                    <span className="flex items-center justify-between gap-3">
                      <span className="truncate text-sm font-semibold text-slate-900">{e.nombre}</span>
                      <Insignia nivel={e.nivel} />
                    </span>
                    <span className="mt-0.5 block truncate text-xs text-slate-500">
                      {e.grado} · {e.resumen}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <Tarjeta className="p-6">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
              <Database className="h-[18px] w-[18px]" />
            </span>
            <div className="min-w-0">
              <h2 className="text-[15px] font-semibold text-slate-900">Datos y calidad</h2>
              <p className="mt-1 text-[13px] leading-5 text-slate-500">
                {estado ? `${miles(estado.notas)} notas de ${estado.estudiantes} estudiantes en ${estado.periodos.length} periodo${estado.periodos.length === 1 ? "" : "s"}.` : ""}
                {estado?.ultima_carga ? ` Última carga: ${estado.ultima_carga.fecha.slice(0, 16)}.` : ""}
              </p>
              {calidad.datos?.disponible && (
                <p className="mt-2 inline-flex items-center gap-1.5 text-[13px] text-slate-600">
                  <ShieldCheck className={`h-4 w-4 ${calidad.datos.criticas ? "text-red-500" : "text-emerald-600"}`} />
                  {calidad.datos.reglas?.length} reglas revisadas: {calidad.datos.criticas} con fallas críticas y {calidad.datos.avisos} avisos.
                </p>
              )}
            </div>
          </div>
        </Tarjeta>

        <Tarjeta className="p-6">
          <h2 className="text-[15px] font-semibold text-slate-900">De dónde sale el nivel de riesgo</h2>
          <p className="mt-1 text-[13px] leading-5 text-slate-500">{estado?.nivel_de_riesgo.explicacion}</p>
          {estado?.modelo && (
            <p className="mt-2 text-[13px] text-slate-600">
              {estado.modelo.nombre} {estado.modelo.arquitectura}, entrenada con la base {estado.modelo.base}. Exactitud en la prueba: <span className="font-semibold text-slate-900">{pct(estado.modelo.exactitud, 1)}</span>.
            </p>
          )}
          <button onClick={() => ir("/modelo")} className="mt-3 inline-flex items-center gap-1 text-[13px] font-semibold text-blue-700 hover:text-blue-900">
            Ver cómo se entrenó y se probó <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </Tarjeta>
      </div>
    </>
  );
}
