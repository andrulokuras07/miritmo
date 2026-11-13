// Pantalla Mi día: registrar (RF-03), ver la calificación (RF-04) y consultar o editar un día (RF-05).
(() => {
  const sesion = MiRitmo.sesion();
  if (!sesion) return;

  const form = document.getElementById("form-dia");
  const alerta = document.getElementById("alerta");
  const aviso = document.getElementById("aviso");
  const selectFecha = document.getElementById("fecha");
  const resultado = document.getElementById("resultado");
  const botonGuardar = form.querySelector("button[type=submit]");
  const CAMPOS = ["horas_trabajo", "tareas", "horas_sueno"];

  document.getElementById("saludo").textContent = `Hola, ${sesion.nombre}`;
  document.getElementById("salir").addEventListener("click", MiRitmo.cerrarSesion);

  // Fecha: hoy por defecto o uno de los 6 días anteriores, nunca futura.
  const hoy = MiRitmo.hoy();
  for (let i = 0; i <= 6; i++) {
    const iso = MiRitmo.sumarDias(hoy, -i);
    const texto = i < 2 ? `${MiRitmo.etiquetaFecha(iso)} · ${MiRitmo.formatoFecha(iso)}` : MiRitmo.formatoFecha(iso);
    selectFecha.add(new Option(texto, iso));
  }
  // "Mi semana" puede enviar aquí un día concreto: dia.html?fecha=AAAA-MM-DD
  const fechaPedida = new URLSearchParams(location.search).get("fecha");
  if ([...selectFecha.options].some((o) => o.value === fechaPedida)) selectFecha.value = fechaPedida;

  // Botones − y + para capturar rápido desde el celular.
  form.querySelectorAll(".paso").forEach((grupo) => {
    const entrada = grupo.querySelector("input");
    grupo.querySelectorAll("button").forEach((boton) => {
      boton.addEventListener("click", () => {
        const paso = Number(entrada.step);
        let valor = entrada.value === ""
          ? Number(entrada.dataset.inicio)
          : Number(entrada.value) + (boton.dataset.paso === "+" ? paso : -paso);
        valor = Math.min(Number(entrada.max), Math.max(Number(entrada.min), valor));
        entrada.value = valor;
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

  function mostrarResultado(registro, { desplazar = true } = {}) {
    document.getElementById("calificacion").textContent = registro.calificacion;
    document.getElementById("nivel").textContent = nivel(registro.calificacion);
    document.getElementById("detalle").textContent = `Calificación de ${MiRitmo.etiquetaFecha(registro.fecha).toLowerCase()} (${registro.fecha}).`;
    resultado.hidden = false;
    requestAnimationFrame(() => {
      document.getElementById("medidor").style.width = `${registro.calificacion}%`;
    });
    if (desplazar) resultado.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function llenarFormulario(registro) {
    CAMPOS.forEach((campo) => (form.elements[campo].value = registro ? registro[campo] : ""));
    form.querySelectorAll("input[name=energia]").forEach((r) => (r.checked = registro ? Number(r.value) === registro.energia : false));
    botonGuardar.textContent = registro ? "Guardar cambios" : "Guardar mi día";
    if (registro) {
      MiRitmo.alerta(aviso, "Ya registraste este día. Puedes cambiar los datos y guardar de nuevo.", "info");
      mostrarResultado(registro, { desplazar: false });
    } else {
      MiRitmo.alerta(aviso, "");
      resultado.hidden = true;
      document.getElementById("medidor").style.width = "0";
    }
  }

  // RF-05: al elegir una fecha registrada, el formulario muestra sus datos.
  async function cargarDia() {
    const fecha = selectFecha.value;
    MiRitmo.limpiarErrores(form);
    MiRitmo.alerta(alerta, "");
    form.setAttribute("aria-busy", "true");
    try {
      const { registros } = await MiRitmo.api("GET", `/registros?desde=${fecha}&hasta=${fecha}`);
      if (selectFecha.value === fecha) llenarFormulario(registros[0] || null);
    } catch (error) {
      MiRitmo.alerta(alerta, error.mensaje);
    } finally {
      form.removeAttribute("aria-busy");
    }
  }
  selectFecha.addEventListener("change", cargarDia);
  cargarDia();

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

    const textoBoton = botonGuardar.textContent;
    botonGuardar.disabled = true;
    botonGuardar.textContent = "Guardando…";
    try {
      const { registro } = await MiRitmo.api("PUT", `/registros/${selectFecha.value}`, datos);
      botonGuardar.textContent = "Guardar cambios";
      MiRitmo.alerta(aviso, "Guardado. Puedes editarlo cuando quieras.", "info");
      mostrarResultado(registro);
    } catch (error) {
      botonGuardar.textContent = textoBoton;
      MiRitmo.mostrarErrores(form, error.campos);
      MiRitmo.alerta(alerta, error.mensaje);
    } finally {
      botonGuardar.disabled = false;
    }
  });
})();
