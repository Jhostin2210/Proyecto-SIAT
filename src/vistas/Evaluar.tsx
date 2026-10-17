// Evaluar estudiante: se ingresan los datos de un caso y la red neuronal estima su riesgo. No guarda nada.
import { useEffect, useState } from "react";
import { Check, Loader2, RotateCcw, Sparkles } from "lucide-react";
import { api, type Campo, type ResultadoEvaluacion } from "../api";
import { Aviso, Boton, Cargando, Encabezado, ErrorDeCarga, ESTILO, Insignia, pct, Tarjeta, useDatos } from "../ui";

const PASOS = ["Ingreso de datos", "Procesamiento", "Resultado"];
const ETAPAS = ["Validando los datos ingresados", "Estandarizando las variables", "Ejecutando la red neuronal", "Asignando el nivel de riesgo"];
const COLUMNAS: [Campo["grupo"], string][] = [
  ["historial", "Historial y colegio"],
  ["familia", "Familia"],
  ["habitos", "Hábitos"],
];
const entrada = "mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-pf-enlace focus:ring-2 focus:ring-pf-suave";

function Pasos({ actual }: { actual: number }) {
  return (
    <ol className="mb-6 flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3.5">
      {PASOS.map((p, i) => (
        <li key={p} className="flex flex-1 items-center gap-2.5 last:flex-none">
          <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${i < actual ? "bg-emerald-500 text-white" : i === actual ? "bg-pf-boton text-white" : "bg-slate-100 text-slate-400"}`}>
            {i < actual ? <Check className="h-3.5 w-3.5" /> : i + 1}
          </span>
          <span className={`hidden text-[13px] font-medium sm:inline ${i <= actual ? "text-slate-900" : "text-slate-400"}`}>{p}</span>
          {i < PASOS.length - 1 && <span className={`mx-2 h-px flex-1 ${i < actual ? "bg-emerald-300" : "bg-slate-200"}`} />}
        </li>
      ))}
    </ol>
  );
}

function CampoPerfil({ campo, valor, cambiar }: { campo: Campo; valor: string | number; cambiar: (v: string) => void }) {
  return (
    <label className="block text-[13px] font-medium text-slate-700">
      {campo.etiqueta}
      {campo.opciones ? (
        <select value={String(valor)} onChange={(e) => cambiar(e.target.value)} className={entrada}>
          {campo.opciones.map((o) => (
            <option key={String(o.valor)} value={String(o.valor)}>
              {o.texto}
            </option>
          ))}
        </select>
      ) : (
        <input type="number" min={campo.minimo} max={campo.maximo} value={valor} onChange={(e) => cambiar(e.target.value)} className={entrada} />
      )}
    </label>
  );
}

export default function Evaluar() {
  const formulario = useDatos(api.formulario);
  const [perfil, setPerfil] = useState<Record<string, string | number>>({});
  const [notaActual, setNotaActual] = useState("");
  const [notaAnterior, setNotaAnterior] = useState("");
  const [paso, setPaso] = useState(0);
  const [etapa, setEtapa] = useState(0);
  const [resultado, setResultado] = useState<ResultadoEvaluacion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (formulario.datos) setPerfil(Object.fromEntries(formulario.datos.campos.map((c) => [c.clave, c.valor])));
  }, [formulario.datos]);

  if (formulario.cargando) return <Cargando />;
  if (formulario.error || !formulario.datos) return <ErrorDeCarga mensaje={formulario.error ?? "Sin respuesta"} reintentar={formulario.recargar} />;
  const campos = formulario.datos.campos;

  const notaValida = (t: string) => t !== "" && Number(t) >= 0 && Number(t) <= 20;
  const evaluar = async (ev: { preventDefault: () => void }) => {
    ev.preventDefault();
    if (!notaValida(notaActual) || (notaAnterior !== "" && !notaValida(notaAnterior))) {
      setError("Ingrese las notas entre 0 y 20.");
      return;
    }
    setError(null);
    setPaso(1);
    setEtapa(0);
    const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));
    try {
      const pedido = api.evaluar({ nota_actual: Number(notaActual), nota_anterior: notaAnterior === "" ? null : Number(notaAnterior), perfil });
      for (let i = 1; i < ETAPAS.length; i++) {
        await espera(380);
        setEtapa(i);
      }
      const r = await pedido;
      await espera(320);
      setResultado(r);
      setPaso(2);
    } catch (e) {
      setError((e as Error).message);
      setPaso(0);
    }
  };

  return (
    <>
      <Encabezado titulo="Evaluar estudiante" detalle="Ingrese los datos de un caso y la red neuronal estima el riesgo en el curso. No se guarda nada en la base." />
      <Pasos actual={paso} />

      {paso === 0 && (
        <form onSubmit={evaluar}>
          <Tarjeta className="p-6">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Notas del curso</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="block text-[13px] font-medium text-slate-700">
                Nota del periodo actual
                <input type="number" min={0} max={20} step="0.5" required value={notaActual} onChange={(e) => setNotaActual(e.target.value)} placeholder="De 0 a 20" className={entrada} />
                <span className="mt-1 block text-xs font-normal text-slate-500">Promedio del examen y de los trabajos. Se aprueba con {formulario.datos.nota_aprobatoria}.</span>
              </label>
              <label className="block text-[13px] font-medium text-slate-700">
                Nota del periodo anterior
                <input type="number" min={0} max={20} step="0.5" value={notaAnterior} onChange={(e) => setNotaAnterior(e.target.value)} placeholder="Opcional" className={entrada} />
                <span className="mt-1 block text-xs font-normal text-slate-500">Si se deja vacía, se toma la misma nota actual.</span>
              </label>
            </div>

            <div className="mt-7 grid gap-x-8 gap-y-6 lg:grid-cols-3">
              {COLUMNAS.map(([grupo, titulo]) => (
                <div key={grupo}>
                  <h2 className="mb-3 border-b border-slate-100 pb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">{titulo}</h2>
                  <div className="space-y-3.5">
                    {campos
                      .filter((c) => c.grupo === grupo)
                      .map((c) => (
                        <CampoPerfil key={c.clave} campo={c} valor={perfil[c.clave] ?? c.valor} cambiar={(v) => setPerfil({ ...perfil, [c.clave]: v })} />
                      ))}
                  </div>
                </div>
              ))}
            </div>

            {error && (
              <div className="mt-5">
                <Aviso tono="error">{error}</Aviso>
              </div>
            )}
            <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
              <p className="text-xs text-slate-500">Los datos del perfil parten del valor más frecuente; cámbielos según el caso.</p>
              <Boton tipo="submit">
                <Sparkles className="h-4 w-4" /> Evaluar con la red neuronal
              </Boton>
            </div>
          </Tarjeta>
        </form>
      )}

      {paso === 1 && (
        <Tarjeta className="mx-auto max-w-lg p-8">
          <ul className="space-y-4">
            {ETAPAS.map((t, i) => (
              <li key={t} className={`flex items-center gap-3 text-sm ${i <= etapa ? "text-slate-900" : "text-slate-400"}`}>
                <span className="flex h-6 w-6 items-center justify-center">
                  {i < etapa ? <Check className="h-4 w-4 text-emerald-600" /> : i === etapa ? <Loader2 className="h-4 w-4 animate-spin text-pf-enlace" /> : <span className="h-1.5 w-1.5 rounded-full bg-slate-300" />}
                </span>
                {t}
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}

      {paso === 2 && resultado && (
        <div className="mx-auto max-w-2xl">
          <Tarjeta className="overflow-hidden">
            <div className={`h-1 ${ESTILO[resultado.nivel].barra}`} />
            <div className="p-7">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Dictamen de la red neuronal</p>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
                <Insignia nivel={resultado.nivel} grande />
                <p className="text-sm text-slate-600">
                  Probabilidad estimada <span className="text-2xl font-semibold tabular-nums text-slate-900">{pct(resultado.probabilidad, 1)}</span>
                </p>
              </div>
              {/* Barra con los cortes de los tres niveles */}
              <div className="relative mt-6">
                <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                  <div className={`h-full rounded-full ${ESTILO[resultado.nivel].barra}`} style={{ width: `${Math.max(2, resultado.probabilidad * 100)}%` }} />
                </div>
                {(["medio", "alto"] as const).map((c) => (
                  <span key={c} className="absolute -top-1 h-[18px] w-px bg-slate-500" style={{ left: `${resultado.umbrales[c] * 100}%` }} />
                ))}
                <div className="mt-2 flex justify-between text-[11px] text-slate-500">
                  <span>0 %</span>
                  <span>
                    Medio desde {pct(resultado.umbrales.medio)} · Alto desde {pct(resultado.umbrales.alto)}
                  </span>
                  <span>100 %</span>
                </div>
              </div>
              <p className="mt-5 text-sm leading-6 text-slate-700">{resultado.mensaje}</p>
              <p className="mt-1 text-[13px] text-slate-500">
                Notas ingresadas: actual {notaActual.replace(".", ",")}
                {notaAnterior !== "" ? `, anterior ${notaAnterior.replace(".", ",")}` : ""}.
              </p>
            </div>
          </Tarjeta>
          <div className="mt-4">
            <Aviso>Es una estimación de apoyo para el tutor. No reemplaza el criterio del docente ni es una calificación.</Aviso>
          </div>
          <div className="mt-4 flex flex-wrap justify-end gap-2">
            <Boton variante="secundario" onClick={() => setPaso(0)}>
              Cambiar los datos
            </Boton>
            <Boton
              onClick={() => {
                setNotaActual("");
                setNotaAnterior("");
                setPerfil(Object.fromEntries(campos.map((c) => [c.clave, c.valor])));
                setResultado(null);
                setPaso(0);
              }}
            >
              <RotateCcw className="h-4 w-4" /> Nueva evaluación
            </Boton>
          </div>
        </div>
      )}
    </>
  );
}
