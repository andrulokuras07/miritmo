// Pantalla Acceso: crear cuenta (RF-01) e iniciar sesión (RF-02).
(() => {
  if (MiRitmo.sesion()) {
    location.replace("dia.html");
    return;
  }

  const alerta = document.getElementById("alerta");
  const formEntrar = document.getElementById("form-entrar");
  const formCuenta = document.getElementById("form-cuenta");
  const tabEntrar = document.getElementById("tab-entrar");
  const tabCuenta = document.getElementById("tab-cuenta");

  function mostrarPestana(cuenta) {
    tabEntrar.setAttribute("aria-selected", String(!cuenta));
    tabCuenta.setAttribute("aria-selected", String(cuenta));
    formEntrar.hidden = cuenta;
    formCuenta.hidden = !cuenta;
    MiRitmo.alerta(alerta, "");
    (cuenta ? formCuenta : formEntrar).querySelector("input").focus();
  }
  tabEntrar.addEventListener("click", () => mostrarPestana(false));
  tabCuenta.addEventListener("click", () => mostrarPestana(true));

  async function enviar(form, ruta, datos) {
    const boton = form.querySelector("button[type=submit]");
    const textoBoton = boton.textContent;
    MiRitmo.limpiarErrores(form);
    MiRitmo.alerta(alerta, "");
    boton.disabled = true;
    boton.textContent = "Un momento…";
    try {
      const respuesta = await MiRitmo.api("POST", ruta, datos);
      MiRitmo.guardarSesion(respuesta);
      location.replace("dia.html");
    } catch (error) {
      MiRitmo.mostrarErrores(form, error.campos);
      MiRitmo.alerta(alerta, error.mensaje);
      boton.disabled = false;
      boton.textContent = textoBoton;
    }
  }

  formEntrar.addEventListener("submit", (e) => {
    e.preventDefault();
    enviar(formEntrar, "/sesiones", {
      correo: formEntrar.correo.value,
      contrasena: formEntrar.contrasena.value,
    });
  });

  formCuenta.addEventListener("submit", (e) => {
    e.preventDefault();
    // La API valida todos los campos y devuelve un mensaje por cada uno.
    enviar(formCuenta, "/cuentas", {
      nombre: formCuenta.nombre.value,
      correo: formCuenta.correo.value,
      contrasena: formCuenta.contrasena.value,
    });
  });
})();
