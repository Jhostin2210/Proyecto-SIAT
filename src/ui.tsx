// Piezas de interfaz compartidas por todas las vistas.
import { useEffect, useState, type ReactNode } from "react";
import { Loader2 } from "lucide-react";
import type { Nivel } from "./api";

export const NIVELES: Nivel[] = ["Riesgo alto", "Riesgo medio", "Riesgo bajo"];

export const ESTILO: Record<Nivel, { corto: string; punto: string; texto: string; fondo: string; borde: string; barra: string; hex: string }> = {
  "Riesgo alto": { corto: "Alto", punto: "bg-red-500", texto: "text-red-700", fondo: "bg-red-50", borde: "border-red-200", barra: "bg-red-500", hex: "#ef4444" },
  "Riesgo medio": { corto: "Medio", punto: "bg-amber-500", texto: "text-amber-700", fondo: "bg-amber-50", borde: "border-amber-200", barra: "bg-amber-500", hex: "#f59e0b" },
  "Riesgo bajo": { corto: "Bajo", punto: "bg-emerald-500", texto: "text-emerald-700", fondo: "bg-emerald-50", borde: "border-emerald-200", barra: "bg-emerald-500", hex: "#10b981" },
};

/** Cambia de vista. Las rutas viven en el hash: #/estudiantes/P-0001 */
export const ir = (ruta: string) => {
  window.location.hash = ruta;
  window.scrollTo({ top: 0 });
};

export const miles = (v: number) => String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
export const pct = (v: number, decimales = 0) => `${(v * 100).toFixed(decimales).replace(".", ",")} %`;
export const nota = (v: number | null | undefined) => (v === null || v === undefined ? "—" : Number.isInteger(v) ? String(v) : v.toFixed(1).replace(".", ","));

/** Carga datos de la API y expone el estado de la petición. */
export function useDatos<T>(cargar: () => Promise<T>, dependencias: unknown[] = []) {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [vuelta, setVuelta] = useState(0);
  useEffect(() => {
    let vigente = true;
    setCargando(true);
    setError(null);
    cargar()
      .then((d) => vigente && setDatos(d))
      .catch((e) => vigente && setError(e.message || "No se pudo conectar con el servidor."))
      .finally(() => vigente && setCargando(false));
    return () => {
      vigente = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencias, vuelta]);
  return { datos, error, cargando, recargar: () => setVuelta((v) => v + 1) };
}

export function Tarjeta({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-slate-200 bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)] ${className}`}>{children}</section>;
}

export function TituloTarjeta({ titulo, detalle, accion }: { titulo: string; detalle?: ReactNode; accion?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 px-6 pt-5">
      <div>
        <h2 className="text-[15px] font-semibold text-slate-900">{titulo}</h2>
        {detalle && <p className="mt-0.5 text-[13px] leading-5 text-slate-500">{detalle}</p>}
      </div>
      {accion}
    </div>
  );
}

export function Insignia({ nivel, grande = false }: { nivel: Nivel; grande?: boolean }) {
  const e = ESTILO[nivel];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${e.fondo} ${e.texto} ${e.borde} ${grande ? "px-3.5 py-1.5 text-sm" : "px-2.5 py-0.5 text-xs"}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${e.punto}`} />
      {grande ? nivel : e.corto}
    </span>
  );
}

/** Barra de probabilidad con el color del nivel. */
export function Barra({ valor, nivel, ancho = "w-24" }: { valor: number; nivel: Nivel; ancho?: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`h-1.5 overflow-hidden rounded-full bg-slate-100 ${ancho}`}>
        <span className={`block h-full rounded-full ${ESTILO[nivel].barra}`} style={{ width: `${Math.max(3, valor * 100)}%` }} />
      </span>
      <span className="w-10 text-right text-xs tabular-nums text-slate-600">{pct(valor)}</span>
    </span>
  );
}

/** Barra apilada con la proporción de cada nivel. */
export function Reparto({ alto, medio, bajo, alto_px = "h-2" }: { alto: number; medio: number; bajo: number; alto_px?: string }) {
  const total = Math.max(1, alto + medio + bajo);
  return (
    <div className={`flex w-full overflow-hidden rounded-full bg-slate-100 ${alto_px}`} role="img" aria-label={`${alto} en riesgo alto, ${medio} en medio y ${bajo} en bajo`}>
      <span className="bg-red-500" style={{ width: `${(alto / total) * 100}%` }} />
      <span className="bg-amber-400" style={{ width: `${(medio / total) * 100}%` }} />
      <span className="bg-emerald-400" style={{ width: `${(bajo / total) * 100}%` }} />
    </div>
  );
}

export function Boton({
  children,
  onClick,
  variante = "primario",
  deshabilitado = false,
  titulo,
  tipo = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variante?: "primario" | "secundario" | "verde";
  deshabilitado?: boolean;
  titulo?: string;
  tipo?: "button" | "submit";
}) {
  const estilos = {
    primario: "bg-slate-900 text-white hover:bg-slate-800",
    secundario: "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
    verde: "bg-emerald-600 text-white hover:bg-emerald-700",
  }[variante];
  return (
    <button
      type={tipo}
      onClick={onClick}
      disabled={deshabilitado}
      title={titulo}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-45 ${estilos}`}
    >
      {children}
    </button>
  );
}

export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" /> {texto}
    </div>
  );
}

export function Aviso({ children, tono = "neutro" }: { children: ReactNode; tono?: "neutro" | "error" }) {
  return (
    <div className={`rounded-xl border px-4 py-3 text-[13px] leading-5 ${tono === "error" ? "border-red-200 bg-red-50 text-red-800" : "border-slate-200 bg-slate-50 text-slate-600"}`}>{children}</div>
  );
}

export function ErrorDeCarga({ mensaje, reintentar }: { mensaje: string; reintentar: () => void }) {
  return (
    <Tarjeta className="p-8 text-center">
      <p className="text-sm font-semibold text-slate-900">No se pudieron cargar los datos</p>
      <p className="mx-auto mt-1 max-w-md text-[13px] text-slate-500">{mensaje}. Si el servidor estaba en reposo, puede tardar cerca de un minuto en responder.</p>
      <div className="mt-4">
        <Boton variante="secundario" onClick={reintentar}>
          Reintentar
        </Boton>
      </div>
    </Tarjeta>
  );
}

export function Encabezado({ titulo, detalle, acciones }: { titulo: string; detalle?: ReactNode; acciones?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{titulo}</h1>
        {detalle && <p className="mt-1 text-sm text-slate-500">{detalle}</p>}
      </div>
      {acciones && <div className="flex flex-wrap items-center gap-2">{acciones}</div>}
    </div>
  );
}
