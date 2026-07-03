import React from "react";

export default function KpiCard({ title, value, change, icon: Icon, color = "blue", onClick }) {
  const colors = {
    blue: {
      bg: "bg-blue-50 border-blue-100",
      text: "text-blue-600",
      iconBg: "bg-blue-500 text-white"
    },
    red: {
      bg: "bg-red-50 border-red-100",
      text: "text-red-600",
      iconBg: "bg-red-500 text-white"
    },
    amber: {
      bg: "bg-amber-50 border-amber-100",
      text: "text-amber-600",
      iconBg: "bg-amber-500 text-white"
    },
    emerald: {
      bg: "bg-emerald-50 border-emerald-100",
      text: "text-emerald-600",
      iconBg: "bg-emerald-500 text-white"
    }
  };

  const selectedColor = colors[color] || colors.blue;

  return (
    <div 
      onClick={onClick}
      className={`p-6 bg-white rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between transition-all duration-300 hover:shadow-md hover:-translate-y-0.5 ${onClick ? "cursor-pointer" : ""}`}
    >
      <div className="space-y-2">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold text-slate-800 tracking-tight">{value}</span>
        </div>
        {change && (
          <p className="text-xs font-medium flex items-center">
            <span className={`mr-1 px-1.5 py-0.5 rounded-md font-semibold ${
              change.startsWith("+") 
                ? "bg-emerald-50 text-emerald-600" 
                : change.startsWith("-") || change.includes("riesgo")
                  ? "bg-red-50 text-red-600"
                  : "bg-slate-50 text-slate-500"
            }`}>
              {change}
            </span>
            <span className="text-slate-400">vs período anterior</span>
          </p>
        )}
      </div>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${selectedColor.iconBg} shadow-inner`}>
        <Icon className="w-6 h-6" />
      </div>
    </div>
  );
}
