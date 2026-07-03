"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Home, 
  Users, 
  AlertTriangle, 
  Bell, 
  FileText, 
  Sparkles, 
  MessageSquare, 
  Settings, 
  ChevronRight,
  LogOut
} from "lucide-react";

export default function DashboardLayout({ children }) {
  const pathname = usePathname();
  const [activeAlerts, setActiveAlerts] = useState(8);

  const menuItems = [
    { name: "Inicio", icon: Home, path: "/dashboard" },
    { name: "Estudiantes", icon: Users, path: "/estudiantes" },
    { name: "Riesgos", icon: AlertTriangle, path: "/riesgos", badge: activeAlerts },
    { name: "Reportes", icon: FileText, path: "/reportes" },
    { name: "Recomendaciones", icon: Sparkles, path: "/recomendaciones" },
    { name: "Comunicación", icon: MessageSquare, path: "/comunicacion" },
    { name: "Configuración", icon: Settings, path: "/configuracion" }
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar Lateral */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col justify-between border-r border-slate-800 shrink-0">
        <div>
          {/* Logo / Cabecera Sidebar */}
          <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
            <div className="w-9 h-9 bg-red-600 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-md">
              S
            </div>
            <div>
              <h1 className="font-bold text-lg leading-none tracking-tight">SIA-T</h1>
              <p className="text-[10px] text-slate-400 mt-1">Alerta Temprana de Riesgo</p>
            </div>
          </div>

          {/* Menú de Navegación */}
          <nav className="p-4 space-y-1">
            {menuItems.map((item) => {
              const isActive = pathname === item.path || (item.path !== "/dashboard" && pathname?.startsWith(item.path));
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium transition-colors group ${
                    isActive 
                      ? "bg-red-600 text-white shadow-md shadow-red-900/10" 
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <item.icon className={`w-5 h-5 ${isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"}`} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      isActive ? "bg-white text-red-600" : "bg-red-600 text-white"
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Perfil del Usuario en la base */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center space-x-3 p-2 bg-slate-800/40 rounded-xl border border-slate-800/60">
            <div className="relative">
              <div className="w-10 h-10 rounded-full bg-slate-700 overflow-hidden border border-slate-600 flex items-center justify-center font-bold text-slate-200 text-sm">
                CR
              </div>
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 border-2 border-slate-900 rounded-full"></span>
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-sm font-semibold text-slate-100 truncate">Carlos Ramírez</h2>
              <p className="text-xs text-slate-400 truncate">Coordinador Académico</p>
            </div>
            <button className="text-slate-400 hover:text-red-400 p-1 rounded-lg transition-colors" title="Cerrar Sesión">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Contenedor de Contenido Principal */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Cabecera Superior de la aplicación */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
          <div>
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Colegio Peruano - Francés</span>
            <h1 className="text-lg font-bold text-slate-800 leading-none">Plataforma Analítica SIA-T</h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-medium text-slate-500">Periodo Lectivo Activo</p>
              <p className="text-sm font-bold text-slate-800">2025 - IV</p>
            </div>
            <div className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full cursor-pointer transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
            </div>
          </div>
        </header>

        {/* Área de Visualización Scrolleable */}
        <div className="flex-1 overflow-y-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
