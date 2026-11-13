// Funciones compartidas: sesión, llamadas a la API, fechas y mensajes de error.
const MiRitmo = (() => {
  const CLAVE_SESION = "miritmo.sesion";
  const ZONA = "America/Mexico_City";

  // ------------------------------------------------------------------ sesión
  function leerToken(token) {
    const carga = token.split(".")[0].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(carga));
  }

  function sesion() {
    try {
      const datos = JSON.parse(localStorage.getItem(CLAVE_SESION));
      if (!datos || !datos.token) return null;
      if (leerToken(datos.token).exp * 1000 < Date.now()) {
        localStorage.removeItem(CLAVE_SESION);
        return null;
      }
      return datos;
    } catch {
      return null;
    }
  }

  function guardarSesion({ token, nombre, correo }) {
    localStorage.setItem(CLAVE_SESION, JSON.stringify({ token, nombre, correo }));
  }

  function cerrarSesion() {
    localStorage.removeItem(CLAVE_SESION);
    location.replace("index.html");
  }

  // Sin sesión no se puede abrir "Mi día" (RF-02).
  function exigirSesion() {
    const s = sesion();
    if (!s) location.replace("index.html");
    return s;
  }

  // --------------------------------------------------------------------- API
  async function api(metodo, ruta, cuerpo) {
    const base = window.MIRITMO_CONFIG.apiUrl.replace(/\/$/, "");
    const encabezados = { "Content-Type": "application/json" };
    const s = sesion();
    if (s) encabezados.Authorization = `Bearer ${s.token}`;

    let res;
    try {
      res = await fetch(base + ruta, {
        method: metodo,
        headers: encabezados,
        body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
      });
    } catch {
      throw { estado: 0, mensaje: "No se pudo conectar con el servidor. Revisa tu conexión.", campos: {} };
    }

    const datos = await res.json().catch(() => ({}));
    if (!res.ok) {
      // Token vencido o inválido en una ruta protegida: volver a Acceso.
      if (res.status === 401 && s && ruta !== "/sesiones") cerrarSesion();
      throw {
        estado: res.status,
        mensaje: datos.error || "Ocurrió un error. Intenta de nuevo.",
        campos: datos.campos || {},
      };
    }
    return datos;
  }

  // ------------------------------------------------------------------ fechas
  // Fecha de hoy en la hora del centro de México, formato AAAA-MM-DD.
  function hoy() {
    return new Intl.DateTimeFormat("en-CA", { timeZone: ZONA }).format(new Date());
  }

  function sumarDias(iso, dias) {
    const d = new Date(`${iso}T12:00:00Z`);
    d.setUTCDate(d.getUTCDate() + dias);
    return d.toISOString().slice(0, 10);
  }

  // "jueves, 12 de noviembre" (o "jue 12" en formato corto)
  function formatoFecha(iso, { corta = false } = {}) {
    const opciones = corta
      ? { weekday: "short", day: "numeric", timeZone: "UTC" }
      : { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" };
    const texto = new Intl.DateTimeFormat("es-MX", opciones).format(new Date(`${iso}T12:00:00Z`));
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  // "Hoy", "Ayer" o la fecha con formato.
  function etiquetaFecha(iso, opciones) {
    const base = hoy();
    if (iso === base) return "Hoy";
    if (iso === sumarDias(base, -1)) return "Ayer";
    return formatoFecha(iso, opciones);
  }

  // ------------------------------------------------------------- formularios
  function limpiarErrores(form) {
    form.querySelectorAll(".error-campo").forEach((el) => (el.textContent = ""));
    form.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  }

  function mostrarErrores(form, campos) {
    Object.entries(campos).forEach(([campo, mensaje]) => {
      const destino = form.querySelector(`[data-error="${campo}"]`);
      if (destino) destino.textContent = mensaje;
      const entrada = form.querySelector(`[name="${campo}"]`);
      if (entrada) entrada.setAttribute("aria-invalid", "true");
    });
  }

  function alerta(el, mensaje, tipo = "error") {
    el.className = `alerta ${tipo}`;
    el.textContent = mensaje;
    el.hidden = !mensaje;
  }

  return { sesion, guardarSesion, cerrarSesion, exigirSesion, api, hoy, sumarDias, formatoFecha, etiquetaFecha, limpiarErrores, mostrarErrores, alerta };
})();
