"use client";

import React, { useState } from "react";
import PanelPrincipal from "@/frontend/components/PanelPrincipal";

export default function DashboardPage() {
  // Estado básico simulado en Next.js
  const [estudiantes, setEstudiantes] = useState([
    {
      id: 1,
      codigo_anonimizado: "A001",
      nombres: "María Fernanda",
      apellidos: "López",
      grado: "3° Secundaria",
      seccion: "A",
      nivel_educativo: "secundaria",
      inasistencias: 2,
      estado_pension: "al_dia",
      ultima_prediccion: { probabilidad: 0.82, nivel: "Riesgo alto", fecha: "2026-07-01T10:30:00" }
    },
    {
      id: 2,
      codigo_anonimizado: "A002",
      nombres: "Juan Diego",
      apellidos: "Martínez",
      grado: "2° Secundaria",
      seccion: "B",
      nivel_educativo: "secundaria",
      inasistencias: 4,
      estado_pension: "atraso_leve",
      ultima_prediccion: { probabilidad: 0.68, nivel: "Riesgo medio", fecha: "2026-07-01T09:15:00" }
    },
    {
      id: 3,
      codigo_anonimizado: "A003",
      nombres: "Ana Sofía",
      apellidos: "Vargas",
      grado: "1° Secundaria",
      seccion: "A",
      nivel_educativo: "secundaria",
      inasistencias: 6,
      estado_pension: "al_dia",
      ultima_prediccion: { probabilidad: 0.35, nivel: "Riesgo bajo", fecha: "2026-06-30T16:45:00" }
    },
    {
      id: 4,
      codigo_anonimizado: "A004",
      nombres: "Luis Antonio",
      apellidos: "Pérez",
      grado: "3° Secundaria",
      seccion: "C",
      nivel_educativo: "secundaria",
      inasistencias: 1,
      estado_pension: "deuda",
      ultima_prediccion: { probabilidad: 0.42, nivel: "Riesgo bajo", fecha: "2026-07-01T11:05:00" }
    },
    {
      id: 5,
      codigo_anonimizado: "A005",
      nombres: "Camila Torres",
      apellidos: "Ruiz",
      grado: "2° Secundaria",
      seccion: "A",
      nivel_educativo: "secundaria",
      inasistencias: 0,
      estado_pension: "al_dia",
      ultima_prediccion: { probabilidad: 0.05, nivel: "Sin riesgo", fecha: "2026-07-02T08:00:00" }
    }
  ]);

  const [alertas, setAlertas] = useState([
    { id: 1, mensaje: "Riesgo alto detectado: María Fernanda López - Descendió notas de Matemáticas", fecha: "Hoy, 10:30 am", atendida: false },
    { id: 2, mensaje: "Riesgo medio detectado: Juan Diego Martínez - Alerta de pensión atrasada", fecha: "Hoy, 09:15 am", atendida: false },
    { id: 3, mensaje: "Riesgo medio detectado: Ana Sofía Vargas - Alerta por 6 inasistencias acumuladas", fecha: "Ayer, 04:45 pm", atendida: false }
  ]);

  const handleAtenderAlerta = (alertaId) => {
    setAlertas(prev => prev.map(a => a.id === alertaId ? { ...a, atendida: true } : a));
  };

  const handleVerEstudiante = (estudiante) => {
    alert(`Visualizando detalles de ${estudiante.nombres} ${estudiante.apellidos} en entorno de desarrollo.`);
  };

  return (
    <PanelPrincipal 
      estudiantes={estudiantes} 
      alertas={alertas} 
      onVerEstudiante={handleVerEstudiante}
      onAtenderAlerta={handleAtenderAlerta}
    />
  );
}
