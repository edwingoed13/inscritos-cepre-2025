document.getElementById('sede').addEventListener('change', obtenerDatos);
document.getElementById('actualizar').addEventListener('click', obtenerDatos);
obtenerDatos();

function obtenerDatos() {
    const sede = document.getElementById('sede').value;
    const url = '/obtener_datos' + (sede ? `?sede=${sede}` : '');

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('resultados').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }

            const { total_inscritos, areas, turnos, fecha_actualizacion } = data;

            // Crear el contenido HTML
            let contentHTML = `<div class="card"><div class="card-body"><h2>Total de inscritos: ${total_inscritos}</h2></div></div>`;
            contentHTML += '<div class="chart-container">';
            contentHTML += '<div class="chart-item card"><div class="card-body"><canvas id="graficoAreas"></canvas></div></div>';
            contentHTML += '<div class="chart-item card"><div class="card-body"><canvas id="graficoBarras"></canvas></div></div>';
            contentHTML += '</div>';

            // Tabla de áreas
            let tableHTML = '<div class="card"><div class="card-body"><h3>Áreas</h3><table class="table table-bordered"><thead><tr><th>Área</th><th>Total</th></tr></thead><tbody>';

            const areaLabels = [];
            const areaCounts = [];

            for (const [area, total] of Object.entries(areas)) {
                areaLabels.push(area);
                areaCounts.push(total);
                tableHTML += `<tr><td>${area}</td><td>${total}</td></tr>`;
            }

            tableHTML += '</tbody></table></div></div>';

            // Tabla de turnos
            let turnosHTML = '<div class="card"><div class="card-body"><h3>Turnos</h3><table class="table table-bordered"><thead><tr><th>Área</th><th>Turno</th><th>Total</th></tr></thead><tbody>';

            for (const [area, turnosArea] of Object.entries(turnos)) {
                for (const [turno, total] of Object.entries(turnosArea)) {
                    turnosHTML += `<tr><td>${area}</td><td>${turno}</td><td>${total}</td></tr>`;
                }
            }

            turnosHTML += '</tbody></table></div></div>';

            // Insertar todo en el div de resultados
            document.getElementById('resultados').innerHTML = contentHTML + tableHTML + turnosHTML;

            // Crear los gráficos
            const pieCtx = document.getElementById('graficoAreas').getContext('2d');
            const barCtx = document.getElementById('graficoBarras').getContext('2d');

            new Chart(pieCtx, {
                type: 'pie',
                data: {
                    labels: areaLabels,
                    datasets: [{
                        label: 'Total de Inscritos por Área',
                        data: areaCounts,
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FFCD56', '#36A2EB'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });

            new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: areaLabels,
                    datasets: [{
                        label: 'Total de Inscritos por Área',
                        data: areaCounts,
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FFCD56', '#36A2EB'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error al obtener los datos:', error);
        });
}