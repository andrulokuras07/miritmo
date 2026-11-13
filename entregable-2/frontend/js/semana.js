// Pantalla Mi semana: gráfica de los últimos 7 días (RF-06) y resumen (RF-07).
(() => {
  const sesion = MiRitmo.sesion();
  if (!sesion) return;

  document.getElementById("saludo").textContent = `Hola, ${sesion.nombre}`;
  document.getElementById("salir").addEventListener("click", MiRitmo.cerrarSesion);

  const hoy = MiRitmo.hoy();
  const desde = MiRitmo.sumarDias(hoy, -6);
  const fechas = Array.from({ length: 7 }, (_, i) => MiRitmo.sumarDias(desde, i));
  const formatoNumero = new Intl.NumberFormat("es-MX", { maximumFractionDigits: 1 });
  const color = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();

  document.getElementById("rango").textContent =
    `Calificación de los últimos 7 días: ${MiRitmo.formatoFecha(desde).toLowerCase()} a ${MiRitmo.formatoFecha(hoy).toLowerCase()}.`;

  // ------------------------------------------------------------------ resumen
  function mostrarResumen(registros) {
    const promedio = document.getElementById("promedio");
    const registrados = document.getElementById("registrados");
    const mejor = document.getElementById("mejor");
    const mejorFecha = document.getElementById("mejor-fecha");

    registrados.textContent = `${registros.length} de 7 días registrados`;
    if (registros.length === 0) {
      promedio.textContent = "–";
      mejor.textContent = "–";
      mejorFecha.textContent = "Registra tu primer día";
      return;
    }
    const suma = registros.reduce((total, r) => total + r.calificacion, 0);
    promedio.textContent = formatoNumero.format(suma / registros.length);

    // Mejor día: la calificación más alta (si hay empate, el más reciente).
    const top = registros.reduce((a, b) => (b.calificacion >= a.calificacion ? b : a));
    mejor.textContent = top.calificacion;
    mejorFecha.textContent = MiRitmo.etiquetaFecha(top.fecha);
  }

  // ------------------------------------------------------------------ gráfica
  // Escribe la calificación sobre cada barra y "Sin registro" en los días vacíos.
  const etiquetasBarras = {
    id: "etiquetasBarras",
    afterDatasetsDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      const barras = chart.getDatasetMeta(0).data;
      ctx.save();
      ctx.textAlign = "center";
      chart.data.datasets[0].data.forEach((valor, i) => {
        const x = scales.x.getPixelForValue(i);
        if (valor === null) {
          // Texto vertical para que quepa en pantallas de 360 px.
          ctx.save();
          ctx.translate(x, chartArea.bottom - 6);
          ctx.rotate(-Math.PI / 2);
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillStyle = color("--tinta-suave");
          ctx.font = "500 11px system-ui, sans-serif";
          ctx.fillText("Sin registro", 0, 0);
          ctx.restore();
        } else {
          ctx.fillStyle = color("--tinta");
          ctx.font = "700 12px system-ui, sans-serif";
          ctx.fillText(valor, x, barras[i].y - 6);
        }
      });
      ctx.restore();
    },
  };

  function dibujarGrafica(porFecha) {
    const datos = fechas.map((f) => (porFecha[f] ? porFecha[f].calificacion : null));
    new Chart(document.getElementById("grafica"), {
      type: "bar",
      data: {
        labels: fechas.map((f) => (f === hoy ? "Hoy" : MiRitmo.formatoFecha(f, { corta: true }))),
        datasets: [{
          label: "Calificación",
          data: datos,
          backgroundColor: color("--acento"),
          borderRadius: 6,
          maxBarThickness: 36,
        }],
      },
      options: {
        maintainAspectRatio: false,
        animation: matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 500 },
        layout: { padding: { top: 18 } },
        scales: {
          y: {
            min: 0,
            max: 100,
            ticks: { stepSize: 25, color: color("--tinta-suave") },
            grid: { color: color("--borde") },
            border: { display: false },
          },
          x: {
            ticks: { color: color("--tinta-suave"), font: { size: 11 }, maxRotation: 0, autoSkip: false },
            grid: { display: false },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => MiRitmo.formatoFecha(fechas[items[0].dataIndex]),
              label: (item) => `Calificación: ${item.raw}`,
            },
          },
        },
      },
      plugins: [etiquetasBarras],
    });
  }

  // ---------------------------------------------------------------- día a día
  function mostrarLista(porFecha) {
    const lista = document.getElementById("dias");
    lista.replaceChildren(
      ...fechas.slice().reverse().map((fecha) => {
        const registro = porFecha[fecha];
        const li = document.createElement("li");
        const nombre = document.createElement("span");
        nombre.className = "dia-nombre";
        nombre.textContent = MiRitmo.etiquetaFecha(fecha);
        const valor = document.createElement("span");
        valor.className = registro ? "dia-valor" : "dia-valor vacio";
        valor.textContent = registro ? registro.calificacion : "Sin registro";
        const enlace = document.createElement("a");
        enlace.href = `dia.html?fecha=${fecha}`;
        enlace.textContent = registro ? "Editar" : "Registrar";
        enlace.setAttribute("aria-label", `${enlace.textContent} ${MiRitmo.formatoFecha(fecha)}`);
        li.append(nombre, valor, enlace);
        return li;
      }),
    );
  }

  async function cargar() {
    try {
      const { registros } = await MiRitmo.api("GET", `/registros?desde=${desde}&hasta=${hoy}`);
      const porFecha = Object.fromEntries(registros.map((r) => [r.fecha, r]));
      mostrarResumen(registros);
      dibujarGrafica(porFecha);
      mostrarLista(porFecha);
    } catch (error) {
      MiRitmo.alerta(document.getElementById("alerta"), error.mensaje);
    }
  }
  cargar();
})();
