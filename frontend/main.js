// =================== FUNCIONES UTILITARIAS ===================
function formatearNumero(numero) {
    return Number(numero).toLocaleString("es-CL", { maximumFractionDigits: 0 });
}

// =================== CARGA DE FILTROS ===================
const filtros = {
    cliente: document.getElementById("filtro-cliente"),
    tecnico: document.getElementById("filtro-tecnico"),
    estado: document.getElementById("filtro-estado"),
    fecha: document.getElementById("filtro-fecha")
};

function deshabilitarFiltros() {
    Object.values(filtros).forEach(filtro => filtro.disabled = true);
}

function habilitarFiltros() {
    Object.values(filtros).forEach(filtro => filtro.disabled = false);
}

function cargarFiltrosDinamicos() {
    deshabilitarFiltros();
    const params = new URLSearchParams({
        cliente: filtros.cliente.value || "Todos",
        tecnico: filtros.tecnico.value || "Todos",
        estado: filtros.estado.value || "Todos",
        fecha: filtros.fecha.value || "Todos"
    });

    fetch("/filtros_dinamicos?" + params.toString())
        .then(resp => resp.json())
        .then(data => {
            actualizarOpciones(filtros.cliente, data.clientes);
            actualizarOpciones(filtros.tecnico, data.tecnicos);
            actualizarOpciones(filtros.estado, data.estados);
            actualizarOpciones(filtros.fecha, data.fechas);
        });
}

function actualizarOpciones(select, valores) {
    const valorSeleccionado = select.value;
    select.innerHTML = "";
    const opcionTodos = document.createElement("option");
    opcionTodos.value = "Todos";
    opcionTodos.textContent = "Todos";
    select.appendChild(opcionTodos);

    valores.forEach(valor => {
        const option = document.createElement("option");
        option.value = valor;
        option.textContent = valor;
        select.appendChild(option);
    });
    habilitarFiltros();

    if (valores.includes(valorSeleccionado)) {
        select.value = valorSeleccionado;
    }
}

function cargarDatosFiltrados() {
    deshabilitarFiltros();
    const params = new URLSearchParams({
        cliente: filtros.cliente.value || "Todos",
        tecnico: filtros.tecnico.value || "Todos",
        estado: filtros.estado.value || "Todos",
        fecha: filtros.fecha.value || "Todos"
    });

    fetch("/filtrado_combinado?" + params.toString())
        .then(resp => resp.json())
        .then(data => {
            cargarResumenTecnicosDesdeData(data.resumen_tecnicos);
            cargarResumenClientesDesdeData(data.resumen_clientes);
            cargarDetalleTecnicosDesdeData(data.detalle_tecnicos);
            cargarEstadoSolicitudDesdeData(data.estado_solicitud);
            actualizarMetricasDesdeData(data.metricas_generales);
            habilitarFiltros();
        });
}

function cargarResumenTecnicosDesdeData(data) {
    const tbody = document.getElementById("tabla-body");
    let rows = "";
    data.forEach(item => {
        rows += `
            <tr>
                <td>${item.tecnico}</td>
                <td>${item.solicitudes}</td>
                <td>${item.tiempo_total}</td>
            </tr>
        `;
    });
    tbody.innerHTML = rows;
}

function cargarResumenClientesDesdeData(data) {
    const tbody = document.getElementById("tabla-clientes-body");
    let rows = "";
    data.forEach(item => {
        rows += `
            <tr>
                <td>${item.cliente}</td>
                <td>${item.total_solicitudes}</td>
                <td>${formatearNumero(item.costo_total)}</td>
            </tr>
        `;
    });
    tbody.innerHTML = rows;
}

function cargarDetalleTecnicosDesdeData(data) {
    const tbody = document.querySelector("#segunda-tabla-wrapper table tbody");
    let rows = "";
    data.forEach(item => {
        const clienteLink = `<a href="#" onclick="cargarDetalleCliente('${item.tecnico}', '${item.cliente}')" style="color: #0000EE; text-decoration: underline;">${item.cliente}</a>`;
        rows += `
            <tr>
                <td>${item.tecnico}</td>
                <td>${item.comuna}</td>
                <td>${item.area_negocio}</td>
                <td>${clienteLink}</td>
                <td style="display:none">${item.mes_anio}</td>
                <td>${item.hora_atencion}</td>
                <td>${formatearNumero(item.monto_partner)}</td>
            </tr>
        `;
    });
    tbody.innerHTML = rows;
}

function actualizarMetricasDesdeData(data) {
    document.querySelectorAll('.info-box .valor')[0].textContent = '$' + Number(data.valor_total).toLocaleString('es-CL');
    document.querySelectorAll('.info-box .valor')[1].textContent = Number(data.total_solicitudes).toLocaleString('es-CL');
    document.querySelectorAll('.info-box .valor')[2].textContent = data.horas_totales;
}

function cargarEstadoSolicitudDesdeData(data) {
    const tbody = document.getElementById("tabla-estado-body");
    let rows = "";
    data.forEach(item => {
        rows += `
            <tr>
                <td>${item.estado}</td>
                <td>${item.total}</td>
            </tr>
        `;
    });
    tbody.innerHTML = rows;
}

function cargarDetalleCliente(tecnico, cliente) {
    const clienteFiltro = cliente || "Todos";
    const tecnicoFiltro = tecnico || "Todos";
    const estadoFiltro = filtros.estado && filtros.estado.value && filtros.estado.value.trim() !== "" ? filtros.estado.value : "Todos";
    const fechaFiltro = filtros.fecha && filtros.fecha.value && filtros.fecha.value.trim() !== "" ? filtros.fecha.value : "Todos";

    let params = [];

    if (tecnicoFiltro !== "Todos") params.push("tecnico=" + encodeURIComponent(tecnicoFiltro));
    if (clienteFiltro !== "Todos") params.push("cliente=" + encodeURIComponent(clienteFiltro));
    if (fechaFiltro !== "Todos") params.push("fecha=" + encodeURIComponent(fechaFiltro));

    const url = "/tickets_detalle?" + params.join("&");

    fetch(url)
        .then(resp => resp.json())
        .then(data => {
            const nuevaVentana = window.open("", "_blank");
            let contenidoHTML = `
                <html><head><title>Detalle de Tickets - ${clienteFiltro}</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; background-color: #f5f7fa; }
                    h3 { margin-top: 0; }
                    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                    th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
                    th { background-color: #006dcc; color: white; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                    button { margin-top: 20px; padding: 8px 16px; }
                </style></head><body>
                <h3>Detalle de Tickets - ${clienteFiltro}</h3>
                <table><thead>
                    <tr>
                        <th>Ticket</th><th>Fecha de Inicio</th><th>Fecha Finalización</th><th>Duración</th><th>Valor</th>
                    </tr></thead><tbody>`;
            data.forEach(item => {
                contenidoHTML += `
                    <tr>
                        <td>${(item.ticket_replika || "").toUpperCase()}</td>
                        <td>${item.fechahora_creacion || ""}</td>
                        <td>${item.fechahora_finalizacion || item.fechahora_cerrado || ""}</td>
                        <td>${item.duracion_real || ""}</td>
                        <td>${(Number(item.monto_partner) || 0).toLocaleString("es-CL")}</td>
                    </tr>`;
            });
            contenidoHTML += `</tbody></table><button onclick="window.close()">Cerrar</button></body></html>`;
            nuevaVentana.document.write(contenidoHTML);
            nuevaVentana.document.close();
        });
}

document.addEventListener("DOMContentLoaded", function () {
    cargarFiltrosDinamicos();
    cargarDatosFiltrados();
});

Object.values(filtros).forEach(filtro => {
    filtro.addEventListener("change", () => {
        cargarFiltrosDinamicos();
        cargarDatosFiltrados();
    });
});


