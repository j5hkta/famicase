// GlobalDental - JavaScript principal

// Inicializar DataTables con configuración en español
const dtEspanol = {
    language: {
        url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json'
    },
    pageLength: 25,
    responsive: true
};

// Función para inicializar DataTable en una tabla
function initDataTable(selector, opciones) {
    if ($(selector).length) {
        $(selector).DataTable({ ...dtEspanol, ...opciones });
    }
}

// Auto-cerrar alertas después de 5 segundos
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert.fade.show');
        alerts.forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Confirmación antes de eliminar
function confirmarEliminacion(mensaje) {
    return confirm(mensaje || '¿Estás seguro de que deseas eliminar este registro?');
}
