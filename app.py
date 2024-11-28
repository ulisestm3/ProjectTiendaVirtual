from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from datetime import datetime
from functools import wraps #decorador
from werkzeug.security import generate_password_hash, check_password_hash
import config
import pymysql
import os

app = Flask(__name__)
app.secret_key = config.HEX_SEC_KEY

# Función para establecer la conexión a la base de datos
def dbconnection():
    return pymysql.connect(
        host=config.MSQL_HOST,
        user=config.MSQL_USER,
        password=config.MSQL_PASSWORD,
        database=config.MSQL_DB
    )

# Configuración de Flask-Login
login_manager_app = LoginManager(app)
login_manager_app.login_view = 'admin_login'

#Funcion decorador de rutas
def role_required(role):
    """
    Decorador para restringir el acceso a rutas según el rol del usuario.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('admin_login'))  # Redirige al login si no está autenticado

            # Verifica si el rol del usuario es el adecuado
            print(f"Rol requerido: {role}, Rol actual del usuario: {current_user.id_rol}")  # Imprime los valores
            if current_user.id_rol != role:
                return redirect(url_for('admin_login'))  # Redirige si el rol no es el adecuado

            return func(*args, **kwargs)  # Permite el acceso si el rol es el adecuado

        return wrapper
    return decorator

# Clase de usuario para manejar la autenticación
class User(UserMixin):
    def __init__(self, id_usuario, usuario, password, nombre, apellido, email, id_rol, id_estado):
        self.id_usuario = id_usuario
        self.usuario = usuario
        self.password = password
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.id_rol = id_rol  # Asegúrate de que 'id_rol' esté aquí
        self.id_estado = id_estado

    def get_id(self):
        return str(self.id_usuario)

    @staticmethod
    def get(id_usuario):
        conexion = dbconnection()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario_data = cursor.fetchone()
        conexion.close()
        if usuario_data:
            return User(id_usuario=usuario_data[0], usuario=usuario_data[1], password=usuario_data[2], nombre=usuario_data[3], apellido=usuario_data[4], email=usuario_data[5], id_rol=usuario_data[7], id_estado=usuario_data[8])
        return None


@login_manager_app.user_loader
def load_user(user_id):
    return User.get(user_id)

# Control de sesion activa
@app.route('/admin/logout')
@login_required
def admin_logout():
    session.pop('logeado', None)
    logout_user()
    return redirect('/admin/login')

# Ruta para cargar imágenes y videos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)

@app.route('/video/<video>')
def videos(video):
    print(video)
    return send_from_directory(os.path.join('templates/sitio/video'),video)

# Rutas del sitio público
@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/productos')
def productos():
    conexion = dbconnection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conexion.close()
    return render_template('sitio/productos.html', productos=productos)

@app.route('/detalleproductos', methods=['POST'])
def detalleproductos():
    _id = request.form['txtID']
    conexion = dbconnection()
    cursor = conexion.cursor()
    
    # Consulta con INNER JOIN entre productos y usuarios a través de id_usuario
    query = """
        SELECT productos.*, usuarios.*
        FROM productos
        INNER JOIN usuarios ON productos.id_usuario = usuarios.id_usuario
        WHERE productos.id = %s
    """
    
    cursor.execute(query, (_id,))
    resultado = cursor.fetchall()
    
    # Cierra la conexión
    conexion.close()
    
    return render_template('sitio/detalleproductos.html', productos=resultado)

@app.route('/admin/')
def false_admin():
    return redirect(url_for('admin_login'))

@app.route('/admin/registro')
def admin_registro():
    return render_template('admin/registro.html')

@app.route('/admin/registro/usuario', methods=['POST'])
def admin_registro_usuario():
    try:
        _usuario = request.form['txtUsuario']
        _password = request.form['txtPassword']
        _nombre = request.form['txtNombre']
        _apellido = request.form['txtApellido']
        _email = request.form['txtEmail']
        
        # Obtiene la fecha y hora actual
        _fecha_registro = datetime.now()
        _rol = 3
        _estado = 1
        _fecha_actualizacion = datetime.now()
        _id_usuario_actualiza = 1
        
        conexion = dbconnection()
        cursor = conexion.cursor()
        
        # Verifica si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (_usuario,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            conexion.close()
            return render_template('admin/registro.html', mensaje='El usuario ya existe.')
        
        if not _password.strip():
            return render_template('admin/registro.html', mensaje="La contraseña no puede estar vacía.")


        # Genera un hash de la contraseña
        hashed_password = generate_password_hash(_password, method='pbkdf2:sha256')

        
        # Inserta el nuevo usuario con la contraseña hasheada
        cursor.execute("""
            INSERT INTO usuarios (usuario, password, nombre, apellido, email, fecha_registro, id_rol, id_estado, fecha_actualizacion, id_usuario_actualiza) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, 
            (_usuario, hashed_password, _nombre, _apellido, _email, _fecha_registro, _rol, _estado, _fecha_actualizacion, _id_usuario_actualiza)
        )
        
        conexion.commit()
        conexion.close()
        
        return render_template('admin/login.html', mensaje='Registro exitoso.')
    
    except pymysql.Error as e:
        print("Error de MySQL:", e)
    
    return render_template('admin/registro.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _usuario = request.form['txtUsuario']
    _password = request.form['txtPassword']
    
    conexion = dbconnection()
    cursor = conexion.cursor()
    
    cursor.execute("""
        SELECT id_usuario, usuario, password, nombre, apellido, email, id_rol, id_estado
        FROM usuarios 
        WHERE usuario = %s
    """, (_usuario,))
    usuario = cursor.fetchone()

    print(usuario)  # Agrega esto para depurar

    conexion.close()
    
    if not usuario:
        return render_template('admin/login.html', message="Usuario no encontrado")
    
    if check_password_hash(usuario[2], _password):
        id_rol = usuario[6]
        id_estado = usuario[7]
        print("Contraseña correcta")
        print(id_rol)
        print(id_estado)

        if id_estado == 2:
            return render_template('admin/login.html', message="Usuario inactivo")
        elif id_estado == 3:
            print("estado 3")
            return render_template('admin/login.html', message="Usuario bloqueado")
        
        session['logeado'] = True
        user = User(
            id_usuario=usuario[0], 
            usuario=usuario[1], 
            password=usuario[2], 
            nombre=usuario[3], 
            apellido=usuario[4], 
            email=usuario[5],
            id_rol=usuario[6],
            id_estado=usuario[7]
        )
        login_user(user)
        
        if id_rol == 1:
            return redirect('/supersu/indexadministrador')
        elif id_rol == 2:
            return redirect('/supersu/indexsupervisor')
        elif id_rol == 3:
            return redirect('/admin')
    else:
        print("Contraseña incorrecta")
        return render_template('admin/login.html', message="Credenciales incorrectas")

# Rutas para administración
@app.route('/admin')
@login_required
@role_required(3)  # 3 = Usuarios
def index_productos():
    conexion = dbconnection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conexion.close()
    return render_template('admin/index.html', productos=productos)

@app.route('/admin/detalleproductos', methods=['POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def detalleproductos_admin():
    _id = request.form['txtID']
    conexion = dbconnection()
    cursor = conexion.cursor()
    
    # Consulta con INNER JOIN entre productos y usuarios a través de id_usuario
    query = """
        SELECT productos.*, usuarios.*
        FROM productos
        INNER JOIN usuarios ON productos.id_usuario = usuarios.id_usuario
        WHERE productos.id = %s
    """
    
    cursor.execute(query, (_id,))
    resultado = cursor.fetchall()
    
    # Cierra la conexión
    conexion.close()
    
    return render_template('admin/detalleproductos.html', productos=resultado)

@app.route('/admin/nosotros')
@login_required
@role_required(3)  # 3 = Usuarios
def admin_nosotros():
    return render_template('admin/nosotros.html')

@app.route('/admin/productos')
@login_required
@role_required(3)  # 3 = Usuarios
def admin_productos_leer():
    conexion = dbconnection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conexion.close()
    return render_template('admin/productos.html', productos=productos)

@app.route('/admin/editar')
@login_required
@role_required(3)  # 3 = Usuarios
def admin_productos_editar():
    # Tomar el id_usuario del usuario autenticado
    _id_usuario = current_user.id_usuario
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql = "SELECT * FROM productos WHERE id_usuario = %s"
    cursor.execute(sql, (_id_usuario,))
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)
    return render_template('admin/editar.html', producto=insertObjeto)

# Rutas para CRUD de productos
@app.route('/admin/productos/guardar', methods=['GET','POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def admin_productos_guardar():
    for file in [request.files['txtImagen1'], request.files['txtVideo']]:
        if file and allowed_file(file.filename):
            if file.content_length > MAX_FILE_SIZE:
                return "Archivo demasiado grande", 400
            
    try:
        conexion = dbconnection()
        cursor = conexion.cursor()
        _nombre = request.form['txtNombre']
        _archivo1 = request.files['txtImagen1']
        _archivo2 = request.files['txtImagen2']
        _archivo3 = request.files['txtImagen3']
        _video = request.files['txtVideo']
        _moneda = request.form['txtMoneda']
        _precio = request.form['txtPrecio']
        _descripcion = request.form['txtDescripcion']
        
        # Tomar el id_usuario del usuario autenticado
        _id_usuario = current_user.id_usuario
        _id_usuario_actualiza = current_user.id_usuario
        fecha_registro = datetime.now()
        fecha_actualizacion = datetime.now()

        nuevoNombre1 = ""
        nuevoNombre2 = ""
        nuevoNombre3 = ""
        nuevoNombrevideo = ""

        tiempo= datetime.now()
        horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')

        # Agregar logs para verificar que los archivos están siendo recibidos
        print("Archivos recibidos:", request.files)

        if _archivo1.filename != "":
            nuevoNombre1 = horaActual + "_" + _archivo1.filename
            print("Guardando imagen 1 con nombre:", nuevoNombre1)
            _archivo1.save(os.path.join(app.root_path, "templates/sitio/img/", nuevoNombre1))

        if _archivo2.filename != "":
            nuevoNombre2 = horaActual + "_" + _archivo2.filename
            print("Guardando imagen 2 con nombre:", nuevoNombre2)
            _archivo2.save(os.path.join(app.root_path, "templates/sitio/img/", nuevoNombre2))

        if _archivo3.filename != "":
            nuevoNombre3 = horaActual + "_" + _archivo3.filename
            print("Guardando imagen 3 con nombre:", nuevoNombre3)
            _archivo3.save(os.path.join(app.root_path, "templates/sitio/img/", nuevoNombre3))

        if _video.filename != "":
            nuevoNombrevideo = horaActual + "_" + _video.filename
            print("Guardando video con nombre:", nuevoNombrevideo)
            _video.save(os.path.join(app.root_path, "templates/sitio/video/", nuevoNombrevideo))

        sql = """INSERT INTO productos (nombre, imagen1, imagen2, imagen3, video, precio, descripcion, moneda, id_usuario, fecha_registro, fecha_actualizacion, id_usuario_actualiza) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio, _descripcion, _moneda, _id_usuario, fecha_registro, fecha_actualizacion, _id_usuario_actualiza))
        conexion.commit()

    except pymysql.Error as e:
        print("Error de MySQL:", e)
    except Exception as e:
        print("Error general:", e)  # Captura otros posibles errores.
    finally:
        conexion.close()

    return redirect('/admin/editar')

@app.route('/admin/productos/actalizar', methods=['POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def admin_productos_actualizar():
    conexion = dbconnection()
    cursor = conexion.cursor()
    _id = request.form['txtId']
    _nombre = request.form['txtNombre']
    _archivo1 = request.files['txtImagen1']
    _archivo2 = request.files['txtImagen2']
    _archivo3 = request.files['txtImagen3']
    _video = request.files['txtVideo']
    _moneda = request.form['txtMoneda']
    _precio = request.form['txtPrecio']
    _descripcion = request.form['txtDescripcion']

    # Tomar el id_usuario del usuario autenticado
    _id_usuario = current_user.id_usuario

    nuevoNombre1 = ""
    nuevoNombre2 = ""
    nuevoNombre3 = ""
    nuevoNombrevideo = ""

    tiempo= datetime.now()
    horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')
    
    if _archivo1.filename!="":
        nuevoNombre1=horaActual+"_"+_archivo1.filename
        _archivo1.save(os.path.join(app.root_path,"templates/sitio/img/"+nuevoNombre1))
    else:
        nuevoNombre1= request.form['txtImagen11']


    if _archivo2.filename!="":
        nuevoNombre2=horaActual+"_"+_archivo2.filename
        _archivo2.save(os.path.join(app.root_path,"templates/sitio/img/"+nuevoNombre2))
    else:
        nuevoNombre2 = request.form['txtImagen21']


    if _archivo3.filename!="":
        nuevoNombre3=horaActual+"_"+_archivo3.filename
        _archivo3.save(os.path.join(app.root_path,"templates/sitio/img/"+nuevoNombre3))
    else:
        nuevoNombre3 = request.form['txtImagen31']


    if _video.filename!="":
        nuevoNombrevideo=horaActual+"_"+_video.filename
        _video.save(os.path.join(app.root_path,"templates/sitio/video/"+nuevoNombrevideo))
    else:
        nuevoNombrevideo = request.form['txtVideo1']

            
    sql = "update productos set nombre=%s, imagen1=%s, imagen2=%s, imagen3=%s, video=%s, precio=%s, descripcion=%s, moneda=%s where id=%s"
    cursor.execute(sql, (_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio,_descripcion,_moneda, _id))
    conexion.commit() 

    
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql = "select * from productos where id_usuario=%s"
    cursor.execute(sql, (_id_usuario))
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)
    return render_template('admin/editar.html', producto=insertObjeto)

@app.route('/admin/productos/borrar', methods=['POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def admin_productos_borrar():
    _id = request.form['txtID']
    print(_id) 
    
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql = 'delete from productos where id=%s'
    cursor.execute(sql, _id)
    conexion.commit()

    return redirect('/admin/editar')

@app.route('/admin/pago')
@login_required
@role_required(3)  # 3 = Usuarios
def pago_admin():
    return render_template('admin/pagoexitoso.html')

@app.route('/admin/pagoexitoso', methods=['POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def pago_exitoso():
    return render_template('admin/pagoexitoso.html')

@app.route('/supersu/indexadministrador')
@role_required(1)  # 1 = Administrador
def index_administrador():
    if not session.get('logeado'):
        return redirect('/admin/login')
    return render_template('supersu/indexadministrador.html')

@app.route('/supersu/indexsupervisor')
@role_required(2)  # 2 = Usuarios
def index_supervisor():
    if not session.get('logeado'):
        return redirect('/admin/login')
    return render_template('supersu/indexsupervisor.html')

# Ejecuta la app
if __name__ == '__main__':
    app.run(debug=True)