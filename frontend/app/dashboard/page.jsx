"use client";
import React, { useState, useEffect } from "react";
import PanelPrincipal from "@/frontend/components/PanelPrincipal";

export default function DashboardPage() {
  // 1. Iniciamos los estados completamente vacíos
  const [estudiantes, setEstudiantes] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [cargando, setCargando] = useState(true);

  // 2. Usamos useEffect para llamar a tu API en Render apenas cargue la página
  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        // Hacemos la petición a tu backend. 
        // Nota: Asegúrate de que '/estudiantes' sea la ruta correcta en tu FastAPI. 
        // Si usaste algo como '/api/estudiantes', agrégalo aquí.
        const respuesta = await fetch("https://proyecto-siat.onrender.com/estudiantes");
        
        if (respuesta.ok) {
          const datosReales = await respuesta.json();
          // Guardamos los datos de la base de datos en el estado
          setEstudiantes(datosReales);
        } else {
          console.error("Error al consultar la base de datos");
        }

        // Si tienes un endpoint para alertas, puedes llamarlo aquí también
        // const respuestaAlertas = await fetch("https://proyecto-siat.onrender.com/alertas");
        // ...

      } catch (error) {
        console.error("Error de conexión con el servidor de Render:", error);
      } finally {
        // Ocultamos la pantalla de carga
        setCargando(false);
      }
    };

    obtenerDatos();
  }, []);

  const handleAtenderAlerta = (alertaId) => {
    setAlertas(prev => prev.map(a => a.id === alertaId ? { ...a, atendida: true } : a));
  };

  const handleVerEstudiante = (estudiante) => {
    alert(`Visualizando detalles de ${estudiante.nombres} ${estudiante.apellidos}`);
  };

  // 3. Mostramos un texto mientras llegan los datos
  if (cargando) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500 font-medium">
        Sincronizando datos con el servidor SIA-T...
      </div>
    );
  }

  // 4. Renderizamos el panel con los datos reales
  return (
    <PanelPrincipal 
      estudiantes={estudiantes} 
      alertas={alertas} 
      onVerEstudiante={handleVerEstudiante}
      onAtenderAlerta={handleAtenderAlerta}
    />
  );
}