// Datos: pantalla del administrador (encargado de TI). Cargas, reconciliación y calidad de los datos (paquetes 1.2.1 y 1.2.2; REQ-01 y REQ-02).
import { useState } from "react";
import { CheckCircle2, Download, ExternalLink, Loader2, ShieldCheck, TriangleAlert } from "lucide-react";
import { api } from "../api";
import { Boton, Cargando, Encabezado, ErrorDeCarga, miles, Tarjeta, TituloTarjeta, useDatos } from "../ui";

const ACCIONES_GITHUB = "https://github.com/Jhostin2210/Proyecto-SIAT/actions";


const fecha = (t: string) => {
  const [d, h] = t.split(/[ T]/);
  const [a, m, dia] = d.split("-");
  return `${dia}/${m}/${a}${h ? ` ${h.slice(0, 5)}` : ""}`;
};
const nombreRegla = (r: string) => r.replace(/_/g, " ").replace(/^./, (x) => x.toUpperCase());

function Dato({ titulo, valor, detalle }: { titulo: string; valor: string; detalle?: string }) {
  return (
    <Tarjeta className="p-5">
      <p className="text-[13px] font-medium text-slate-500">{titulo}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight text-slate-900">{valor}</p>
      {detalle && <p className="mt-1 text-xs text-slate-500">{detalle}</p>}
    </Tarjeta>
  );
}

export default function Datos() {
  const estado = useDatos(api.estado);
  const cargas = useDatos(api.cargas);
  const calidad = useDatos(api.calidad);
  const historial = useDatos(api.historialCalidad);
  const [validando, setValidando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validar = async () => {
    setValidando(true);
    setError(null);
    try {
      await api.ejecutarValidacion();
      calidad.recargar();
      historial.recargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setValidando(false);
    }
  };

  if (estado.cargando || cargas.cargando || calidad.cargando) return <Cargando />;
  if (estado.error || cargas.error || calidad.error) return <ErrorDeCarga mensaje={estado.error ?? cargas.error ?? calidad.error ?? "Sin respuesta"} reintentar={() => (estado.recargar(), cargas.recargar(), calidad.recargar())} />;

  const e = estado.datos!;
  const c = calidad.datos!;
  const reglas = c.reglas ?? [];

  return (
    <>
      <Encabezado
        titulo="Datos y calidad"
        detalle="Entregable E-01 · Módulo de integración y limpieza de datos (paquetes 1.2.1 y 1.2.2 de la EDT)"
        acciones={
          <>
            <a href={api.urlExportarNotas()} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              <Download className="h-4 w-4" /> Exportar notas
            </a>
            <Boton onClick={validar} deshabilitado={validando}>
              {validando ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
              {validando ? "Validando…" : "Validar ahora"}
            </Boton>
          </>
        }
      />
      {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-800">No se pudo validar: {error}</div>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Dato titulo="Notas en la base" valor={miles(e.notas)} detalle={`${e.estudiantes} estudiantes`} />
        <Dato titulo="Periodos" valor={String(e.periodos.length)} detalle={e.periodos.length ? `${e.periodos[0].nombre} a ${e.periodos[e.periodos.length - 1].nombre}` : "Sin periodos"} />
        <Dato titulo="Cargas registradas" valor={String(cargas.datos!.length)} detalle={cargas.datos![0] ? `Última: ${fecha(cargas.datos![0].fecha)}` : "Ninguna"} />
        <Dato titulo="Última validación" valor={c.disponible ? `${c.criticas} críticas` : "—"} detalle={c.disponible ? `${c.avisos} avisos · ${fecha(c.fecha!)}` : "Todavía no se ha ejecutado"} />
      </div>

      <Tarjeta className="mt-5">
        <TituloTarjeta titulo="Bitácora de cargas y reconciliación" detalle="Cada carga compara las notas válidas del archivo con las que quedaron en la base. Es correcta si todas están, sin duplicados." />
        <div className="overflow-x-auto pb-2 pt-3">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs text-slate-500">
                <th className="px-6 py-2.5 font-medium">Fecha</th>
                <th className="px-3 py-2.5 font-medium">Archivo</th>
                <th className="px-3 py-2.5 text-center font-medium">Filas</th>
                <th className="px-3 py-2.5 text-center font-medium">Notas válidas</th>
                <th className="px-3 py-2.5 text-center font-medium">Cargadas</th>
                <th className="px-3 py-2.5 text-center font-medium">Ya estaban</th>
                <th className="px-3 py-2.5 text-center font-medium">No cargadas</th>
                <th className="px-6 py-2.5 font-medium">Reconciliación</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {cargas.datos!.map((x) => {
                const correcta = x.notas_leidas === x.notas_cargadas + x.notas_repetidas;
                return (
                  <tr key={x.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-6 py-3 text-slate-700">{fecha(x.fecha)}</td>
                    <td className="px-3 py-3 font-medium text-slate-900">{x.archivo}</td>
                    <td className="px-3 py-3 text-center text-slate-600">{miles(x.filas_origen)}</td>
                    <td className="px-3 py-3 text-center text-slate-600">{miles(x.notas_leidas)}</td>
                    <td className="px-3 py-3 text-center font-semibold text-slate-900">{miles(x.notas_cargadas)}</td>
                    <td className="px-3 py-3 text-center text-slate-600">{miles(x.notas_repetidas)}</td>
                    <td className="px-3 py-3 text-center text-slate-600">{miles(x.notas_rechazadas)}</td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center gap-1.5 text-[13px] font-semibold ${correcta ? "text-emerald-700" : "text-red-700"}`}>
                        {correcta ? <CheckCircle2 className="h-4 w-4" /> : <TriangleAlert className="h-4 w-4" />}
                        {correcta ? "Correcta" : "Con diferencias"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Tarjeta>

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <Tarjeta className="lg:col-span-3">
          <TituloTarjeta titulo="Reglas de calidad" detalle={c.disponible ? `Resultado de la última validación, ${fecha(c.fecha!)}. Las críticas detienen la validación nocturna.` : "Todavía no se ha ejecutado la validación."} />
          <ul className="px-3 pb-3 pt-3">
            {reglas.map((r) => {
              const ok = r.severidad === "correcta";
              const tono = ok ? "text-emerald-700 bg-emerald-50 border-emerald-200" : r.severidad === "critica" ? "text-red-700 bg-red-50 border-red-200" : "text-amber-700 bg-amber-50 border-amber-200";
              return (
                <li key={r.regla} className="flex items-start justify-between gap-4 rounded-xl px-3 py-2.5">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-900">
                      {nombreRegla(r.regla)} <span className="ml-1 text-[11px] font-normal text-slate-400">{r.tipo === "critica" ? "crítica" : "aviso"}</span>
                    </p>
                    <p className="text-xs leading-5 text-slate-500">{r.detalle}</p>
                  </div>
                  <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-semibold tabular-nums ${tono}`}>{ok ? "Correcta" : `${miles(r.cantidad)} ${r.severidad === "critica" ? "fallas" : "avisos"}`}</span>
                </li>
              );
            })}
          </ul>
        </Tarjeta>

        <Tarjeta className="lg:col-span-2">
          <TituloTarjeta
            titulo="Validaciones"
            detalle="Las de esta base. La validación nocturna se ejecuta cada noche en GitHub Actions."
            accion={
              <a href={ACCIONES_GITHUB} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[13px] font-semibold text-pf-enlace hover:text-pf-enlace-fuerte">
                Ver en GitHub <ExternalLink className="h-3.5 w-3.5" />
              </a>
            }
          />
          {historial.datos && historial.datos.length > 0 ? (
            <ul className="px-3 pb-3 pt-3">
              {historial.datos.slice(0, 8).map((h) => (
                <li key={h.fecha} className="flex items-center justify-between gap-3 rounded-xl px-3 py-2 text-[13px]">
                  <span className="tabular-nums text-slate-700">{fecha(h.fecha)}</span>
                  <span className={`font-semibold ${h.criticas ? "text-red-700" : "text-emerald-700"}`}>
                    {h.criticas ? `${h.criticas} críticas` : "Sin fallas críticas"}
                    <span className="ml-1 font-normal text-slate-500">· {h.avisos} avisos</span>
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-6 py-6 text-sm text-slate-500">Sin ejecuciones registradas.</p>
          )}
        </Tarjeta>
      </div>

    </>
  );
}
