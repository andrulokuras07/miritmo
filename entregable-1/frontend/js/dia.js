// Pantalla Mi día: registrar el día (RF-03) y ver la calificación (RF-04).
(() => {
  const sesion = MiRitmo.sesion();
  if (!sesion) return;

  const form = document.getElementById("form-dia");
  const alerta = document.getElementById("alerta");
  const selectFecha = document.getElementById("fecha");
  const resultado = document.getElementById("resultado");

  document.getElementById("saludo").textContent = `Hola, ${sesion.nombre}`;
  document.getElementById("salir").addEventListener("click", MiRitmo.cerrarSesion);

  // Fecha: hoy por defecto o uno de los 6 días anteriores, nunca futura.
  const hoy = MiRitmo.hoy();
  for (let i = 0; i <= 6; i++) {
    const iso = MiRitmo.sumarDias(hoy, -i);
    const texto = i < 2 ? `${MiRitmo.etiquetaFecha(iso)} · ${MiRitmo.formatoFecha(iso)}` : MiRitmo.formatoFecha(iso);
    selectFecha.add(new Option(texto, iso));
  }

  // Botones − y + para capturar rápido desde el celular.
  form.querySelectorAll(".paso").forEach((grupo) => {
    const entrada = grupo.querySelector("input");
    grupo.querySelectorAll("button").forEach((boton) => {
      boton.addEventListener("click", () => {
        const paso = Number(entrada.step);
        const min = Number(entrada.min);
        const max = Number(entrada.max);
        let valor;
        if (entrada.value === "") {
          valor = Number(entrada.dataset.inicio);
        } else {
          valor = Number(entrada.value) + (boton.dataset.paso === "+" ? paso : -paso);
        }
        entrada.value = Math.min(max, Math.max(min, valor));
        entrada.removeAttribute("aria-invalid");
      });
    });
  });

  function leerNumero(nombre) {
    const valor = form.elements[nombre].value;
    return valor === "" ? null : Number(valor);
  }

  function nivel(calificacion) {
    if (calificacion >= 85) return "¡Excelente día!";
    if (calificacion >= 70) return "Buen día";
    if (calificacion >= 50) return "Día regular";
    return "Día difícil · mañana es otra oportunidad";
  }

  function mostrarResultado(registro) {
    document.getElementById("calificacion").textContent = registro.calificacion;
    document.getElementById("nivel").textContent = nivel(registro.calificacion);
    document.getElementById("detalle").textContent = `Guardado para ${MiRitmo.etiquetaFecha(registro.fecha).toLowerCase()} (${registro.fecha}).`;
    resultado.hidden = false;
    requestAnimationFrame(() => {
      document.getElementById("medidor").style.width = `${registro.calificacion}%`;
    });
    resultado.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    MiRitmo.limpiarErrores(form);
    MiRitmo.alerta(alerta, "");

    const energia = form.querySelector("input[name=energia]:checked");
    const datos = {
      horas_trabajo: leerNumero("horas_trabajo"),
      tareas: leerNumero("tareas"),
      horas_sueno: leerNumero("horas_sueno"),
      energia: energia ? Number(energia.value) : null,
    };

    const boton = form.querySelector("button[type=submit]");
    boton.disabled = true;
    boton.textContent = "Guardando…";
    try {
      const { registro } = await MiRitmo.api("PUT", `/registros/${selectFecha.value}`, datos);
      mostrarResultado(registro);
    } catch (error) {
      MiRitmo.mostrarErrores(form, error.campos);
      MiRitmo.alerta(alerta, error.mensaje);
    } finally {
      boton.disabled = false;
      boton.textContent = "Guardar mi día";
    }
  });
})();
