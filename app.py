from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from datetime import datetime
import config
import pymysql
import os

app = Flask(__name__)
app.secret_key = config.HEX_SEC_KEY

# Configuración de Flask-Login
login_manager_app = LoginManager(app)
login_manager_app.login_view = 'admin_login'

# Clase de usuario para manejar la autenticación
class User(UserMixin):
    def __init__(self, id_usuario, usuario, password, nombre, apellido, email):
        self.id_usuario = id_usuario
        self.usuario = usuario
        self.password = password
        self.nombre = nombre
        self.apellido = apellido
        self.email = email

    # Implementación de get_id para que Flask-Login pueda obtener el identificador del usuario
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
            return User(id_usuario=usuario_data[0], usuario=usuario_data[1], password=usuario_data[2], nombre=usuario_data[3], apellido=usuario_data[4], email=usuario_data[5])
        return None

# Función para establecer la conexión a la base de datos
def dbconnection():
    return pymysql.connect(
        host=config.MSQL_HOST,
        user=config.MSQL_USER,
        password=config.MSQL_PASSWORD,
        database=config.MSQL_DB
    )

@login_manager_app.user_loader
def load_user(user_id):
    return User.get(user_id)

# Ruta para cargar imágenes y videos
@app.route('/img/<imagen>')
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

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/pago')
def pago():
    return render_template('sitio/pago.html')

@app.route('/pagoexitoso', methods=['POST'])
def pago_exitoso():
    return render_template('sitio/pagoexitoso.html')

# Rutas para administración
@app.route('/admin')
@login_required
def index_productos():
    conexion = dbconnection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conexion.close()
    return render_template('admin/index.html', productos=productos)

@app.route('/admin/')
def false_admin():
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def logout_admin():
    logout_user()
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/nosotros')
@login_required
def admin_nosotros():
    return render_template('admin/nosotros.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _usuario = request.form['txtUsuario']
    _password = request.form['txtPassword']
    conexion = dbconnection()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, usuario, password, nombre, apellido, email FROM usuarios WHERE usuario = %s AND password = %s", (_usuario, _password))
    usuario = cursor.fetchone()
    conexion.close()

    if usuario:
        session['logeado'] = True
        user = User(id_usuario=usuario[0], usuario=usuario[1], password=usuario[2], nombre=usuario[3], apellido=usuario[4], email=usuario[5])
        login_user(user)
        return redirect('/admin')
    else:
        return render_template('admin/login.html', message="Credenciales incorrectas")

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
        fecha_registro = datetime.now()
        
        conexion = dbconnection()
        cursor = conexion.cursor()
        
        # Verifica si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (_usuario,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            return render_template('admin/registro.html', mensaje='El usuario ya existe.')
        
        # Inserta el nuevo usuario con la fecha de registro
        cursor.execute("""
            INSERT INTO usuarios (usuario, password, nombre, apellido, email, fecha_registro) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """, 
            (_usuario, _password, _nombre, _apellido, _email, fecha_registro)
        )
        
        conexion.commit()
        conexion.close()
        
        return render_template('admin/login.html')
    
    except pymysql.Error as e:
        print("Error de MySQL:", e)
    
    return render_template('admin/registro.html')


@app.route('/admin/productos')
@login_required
def admin_productos_leer():
    conexion = dbconnection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conexion.close()
    return render_template('admin/productos.html', productos=productos)

@app.route('/admin/editar')
@login_required
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
def admin_productos_guardar():
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
def admin_productos_borrar():
    _id = request.form['txtID']
    print(_id) 
    
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql = 'delete from productos where id=%s'
    cursor.execute(sql, _id)
    conexion.commit()

    return redirect('/admin/editar')

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.pop('logeado', None)
    logout_user()
    return redirect('/admin/login')

# Ejecuta la app
if __name__ == '__main__':
    app.run(debug=True)
