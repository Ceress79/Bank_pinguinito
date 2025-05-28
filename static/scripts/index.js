document.addEventListener("DOMContentLoaded", function() {
  const togglePassword = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("password");

  togglePassword.addEventListener("click", function () {
    const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
    passwordInput.setAttribute("type", type);

    this.classList.toggle("fa-eye");
    this.classList.toggle("fa-eye-slash");
  });
});

function abrirModalCorreo() {
  document.getElementById('modalCorreo').style.display = 'block';
}

function cerrarModal(id) {
  document.getElementById(id).style.display = 'none';
}

function enviarCodigo() {
  const correo = document.getElementById('correoRecuperacion').value;

  fetch('/enviar_codigo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({correo: correo})
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
    } else {
      // cerrar modal correo
      cerrarModal('modalCorreo');
      // abrir modal código
      abrirModal('modalCodigo');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error enviando código');
  });
}


function verificarCodigo() {
  const inputs = document.querySelectorAll('.codigo');
  const codigo = Array.from(inputs).map(i => i.value).join('');
  if (codigo.length === 6) {
    // Aquí irá la lógica para verificar el código con el backend
    cerrarModal('modalCodigo');
    document.getElementById('modalNuevaClave').style.display = 'block';
  } else {
    alert("Código incompleto.");
  }
}

function guardarNuevaClave() {
  const clave = document.getElementById('nuevaClave').value;
  const confirmar = document.getElementById('confirmarClave').value;
  if (clave && confirmar && clave === confirmar) {
    // Aquí irá la lógica para guardar la nueva clave (con fetch/ajax al backend)
    cerrarModal('modalNuevaClave');
    alert("Contraseña actualizada correctamente.");
  } else {
    alert("Las contraseñas no coinciden o están vacías.");
  }
}

function mostrarAlerta(mensaje) {
  // Si ya existe una alerta, elimínala
  const existente = document.getElementById('flash-alert');
  if (existente) existente.remove();

  const alerta = document.createElement('div');
  alerta.className = 'alert show showAlert';
  alerta.id = 'flash-alert';
  alerta.innerHTML = `
    <span class="fas fa-exclamation-circle"></span>
    <span class="msg">${mensaje}</span>
    <div class="close-btn" onclick="closeAlert()">
      <span class="fas fa-times"></span>
    </div>
  `;

  document.body.appendChild(alerta);

  setTimeout(() => {
    alerta.classList.remove('show');
    alerta.classList.add('hide');
  }, 5000);
}

function closeAlert() {
  const alert = document.getElementById('flash-alert');
  if (alert) {
    alert.classList.remove('show');
    alert.classList.add('hide');
  }
}
