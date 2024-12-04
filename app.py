from flask import Flask, flash, render_template, request, redirect, session, send_from_directory, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from datetime import datetime
from functools import wraps #decorador
from decimal import Decimal
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
    def __init__(self, id_usuario, usuario, password, nombre, apellido, email, id_rol, id_estado, telefono, direccion):
        self.id_usuario = id_usuario
        self.usuario = usuario
        self.password = password
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.id_rol = id_rol  # Asegúrate de que 'id_rol' esté aquí
        self.id_estado = id_estado
        self.telefono = telefono
        self.direccion = direccion

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
            return User(id_usuario=usuario_data[0], usuario=usuario_data[1], password=usuario_data[2], nombre=usuario_data[3], apellido=usuario_data[4], email=usuario_data[5], id_rol=usuario_data[7], id_estado=usuario_data[8], telefono=usuario_data[11], direccion=usuario_data[12])
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
    cursor.execute("SELECT * FROM productos WHERE id_estado=1")
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
        WHERE productos.id_producto = %s
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

        # Verifica si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (_email,))
        email_existente = cursor.fetchone()
        
        if usuario_existente:
            conexion.close()
            return render_template('admin/registro.html', mensaje='El usuario ya existe.')
        
        if email_existente:
            conexion.close()
            return render_template('admin/registro.html', mensaje='El correo ya existe, favor contactar con un supevisor.')
        
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
        SELECT id_usuario, usuario, password, nombre, apellido, email, id_rol, id_estado, telefono, direccion
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
            id_estado=usuario[7],
            telefono=usuario[8],
            direccion=usuario[9]
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
    user_id = current_user.id_usuario  # ID del usuario actual
    conexion = dbconnection()
    cursor = conexion.cursor()
    
    # Excluir productos del usuario actual
    query = """
        SELECT * 
        FROM productos 
        WHERE id_estado = 1 AND id_usuario != %s
    """
    cursor.execute(query, (user_id,))
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
        WHERE productos.id_producto = %s
    """
    
    cursor.execute(query, (_id,))
    resultado = cursor.fetchall()
    print(resultado)
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
    _id_estado= 1
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql = "SELECT * FROM productos WHERE id_usuario = %s AND id_estado = %s"
    cursor.execute(sql, (_id_usuario, _id_estado))
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)

    #Llenar categorias
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql2 = "SELECT * FROM categorias"
    cursor.execute(sql2,)
    categoria=cursor.fetchall()

    insertCategoria=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in categoria:
        insertCategoria.append(dict(zip(columnaNames, record)))
    cursor.close()

    print(categoria)

    return render_template('admin/editar.html', producto=insertObjeto, categoria=insertCategoria)



@app.route('/admin/productos/guardar', methods=['GET','POST'])
@login_required
@role_required(3)  # 3 = Usuarios
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
        _id_categoria = request.form["txtCategoria"]
        
        print("categoria es: ", _id_categoria)
        # Tomar el id_usuario del usuario autenticado
        _id_usuario = current_user.id_usuario
        _id_usuario_actualiza = current_user.id_usuario
        fecha_registro = datetime.now()
        fecha_actualizacion = datetime.now()
        _id_estado = 1

        nuevoNombre1 = ""
        nuevoNombre2 = ""
        nuevoNombre3 = ""
        nuevoNombrevideo = ""

        tiempo= datetime.now()
        horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')

        # Agregar logs para verificar que los archivos están siendo recibidos
        print("Archivos recibidos:", request.files, request.form)

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

        print(_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio, _descripcion, _moneda, _id_usuario, fecha_registro, fecha_actualizacion, _id_usuario_actualiza, _id_categoria, _id_estado)
        
        sql = """INSERT INTO productos (nombre, imagen1, imagen2, imagen3, video, precio, descripcion, moneda, id_usuario, fecha_registro, fecha_actualizacion, id_usuario_actualiza, id_categoria, id_estado) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio, _descripcion, _moneda, _id_usuario, fecha_registro, fecha_actualizacion, _id_usuario_actualiza, _id_categoria, _id_estado))
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
    _id_producto = request.form['txtId']
    _nombre = request.form['txtNombre']
    _archivo1 = request.files['txtImagen1']
    _archivo2 = request.files['txtImagen2']
    _archivo3 = request.files['txtImagen3']
    _video = request.files['txtVideo']
    _moneda = request.form['txtMoneda']
    _precio = request.form['txtPrecio']
    _descripcion = request.form['txtDescripcion']
    _id_categoria = request.form["txtCategoria"]
        
    print("categoria es: ", _id_categoria)
    # Tomar el id_usuario del usuario autenticado
    _id_usuario_actualiza = current_user.id_usuario
    fecha_actualizacion = datetime.now()
    
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

            
    sql = "update productos set nombre=%s, imagen1=%s, imagen2=%s, imagen3=%s, video=%s, precio=%s, descripcion=%s, moneda=%s, fecha_actualizacion=%s, id_usuario_actualiza=%s, id_categoria=%s where id_producto=%s"
    cursor.execute(sql, (_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio,_descripcion,_moneda, fecha_actualizacion, _id_usuario_actualiza, _id_categoria, _id_producto))
    conexion.commit() 

    return redirect('/admin/editar')

@app.route('/admin/productos/borrar', methods=['POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def admin_productos_borrar():
    _id_producto = request.form['txtID']

    _id_usuario_actualiza = current_user.id_usuario
    fecha_actualizacion = datetime.now()
    
    
    conexion=dbconnection()
    cursor=conexion.cursor()
    sql = 'update productos set id_estado=2, fecha_actualizacion=%s, id_usuario_actualiza=%s where id_producto=%s'
    cursor.execute(sql, (fecha_actualizacion, _id_usuario_actualiza, _id_producto))
    conexion.commit()

    return redirect('/admin/editar')

@app.route('/admin/perfil')
@login_required
@role_required(3)  # 3 = Usuarios
def ver_perfil():
    _id_usuario= current_user.id_usuario
    conexion = dbconnection()
    cursor = conexion.cursor()
    sql = 'SELECT * FROM usuarios WHERE id_usuario =%s'
    cursor.execute(sql, _id_usuario)
    usuarios = cursor.fetchall()
    conexion.close()
    return render_template('admin/perfil.html', usuarios=usuarios)

@app.route('/admin/actualizar_perfil', methods=['POST'])
@login_required
@role_required(3)  # 3 = Usuarios
def editar_perfil_actualizar():
    try:
        # Datos del formulario
        _id_usuario = current_user.id_usuario
        _nombre = request.form["txtNombre"]
        _apellido = request.form["txtApellido"]
        _telefono = request.form["txtTelefono"]
        _direccion = request.form["txtDireccion"]
        _email = request.form["txtEmail"]
        _contrasena = request.form["txtContrasena"]

        # Conexión a la base de datos
        conexion = dbconnection()
        cursor = conexion.cursor()
        
        _id_usuario_actualiza = current_user.id_usuario
        fecha_actualizacion = datetime.now()

        # Construcción de la consulta
        if _contrasena.strip():  # Si la contraseña no está vacía
            hashed_password = generate_password_hash(_contrasena)  # Hasheamos la contraseña
            sql = '''
                UPDATE Usuarios 
                SET nombre=%s, apellido=%s, telefono=%s, direccion=%s, email=%s, password=%s, id_usuario_actualiza=%s, fecha_actualizacion=%s
                WHERE id_usuario=%s
            '''
            cursor.execute(sql, (_nombre, _apellido, _telefono, _direccion, _email, hashed_password, _id_usuario_actualiza, fecha_actualizacion, _id_usuario))
        else:
            sql = '''
                UPDATE Usuarios 
                SET nombre=%s, apellido=%s, telefono=%s, direccion=%s, email=%s, id_usuario_actualiza=%s, fecha_actualizacion=%s
                WHERE id_usuario=%s
            '''
            cursor.execute(sql, (_nombre, _apellido, _telefono, _direccion, _email, _id_usuario_actualiza, fecha_actualizacion, _id_usuario))

        # Confirmar cambios y cerrar conexión
        conexion.commit()
        cursor.close()
        conexion.close()

        return redirect('/admin/perfil')

    except pymysql.Error as e:
        print("Error de MySQL:", e)
    except Exception as e:
        print("Error general:", e)
    finally:
        try:
            conexion.close()
        except:
            pass

    return redirect('/admin/perfil')


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


@app.route('/admin/carrito')
@login_required
def mostrar_carrito():
    user_id = current_user.id_usuario  # Obtener el id del usuario actual
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Consultar los productos en el carrito del usuario
    cursor.execute(
    "SELECT p.id_producto, p.nombre, p.precio, p.moneda, p.imagen1, c.cantidad "
    "FROM carrito c "
    "JOIN productos p ON c.id_producto = p.id_producto "
    "WHERE c.id_usuario = %s",
    (user_id,)
)

    carrito = cursor.fetchall()

    # Calcular el total del carrito
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    cursor.close()
    conexion.close()

    return render_template('/admin/carrito.html', carrito=carrito, total=total)

@app.route('/admin/carrito/agregar/<int:id_producto>', methods=['POST'])
@login_required
def agregar_al_carrito(id_producto):
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    try:
        # Obtener los detalles del producto incluyendo su propietario (id_usuario)
        query_producto = """
            SELECT id_producto, nombre, moneda, imagen1, precio, id_usuario 
            FROM productos 
            WHERE id_producto = %s AND id_estado = 1
        """
        cursor.execute(query_producto, (id_producto,))
        producto = cursor.fetchone()

        if not producto:
            flash("El producto no existe o no está disponible.", "warning")
            return redirect(url_for('mostrar_productos'))  # Redirige si el producto no existe

        user_id = current_user.id_usuario  # Obtener el id del usuario actual

        # Verificar si el producto pertenece al usuario actual
        if producto["id_usuario"] == user_id:
            flash("No puedes agregar tu propio producto al carrito.", "danger")
            return redirect('/admin/editar')

        # Verificar si el producto ya está en el carrito del usuario
        query_carrito = "SELECT * FROM carrito WHERE id_usuario = %s AND id_producto = %s"
        cursor.execute(query_carrito, (user_id, id_producto))
        existing_product = cursor.fetchone()

        if existing_product:
            # Si el producto ya existe, se actualiza la cantidad
            query_update = "UPDATE carrito SET cantidad = cantidad + 1 WHERE id_usuario = %s AND id_producto = %s"
            cursor.execute(query_update, (user_id, id_producto))
        else:
            # Si el producto no está en el carrito, se inserta un nuevo registro
            query_insert = "INSERT INTO carrito (id_usuario, id_producto, cantidad) VALUES (%s, %s, %s)"
            cursor.execute(query_insert, (user_id, id_producto, 1))

        conexion.commit()
        flash("Producto agregado al carrito.", "success")
        return redirect(url_for('mostrar_carrito'))  # Redirige al carrito actualizado
    except Exception as e:
        conexion.rollback()
        flash(f"Error al agregar el producto al carrito: {str(e)}", "danger")
        return redirect(url_for('mostrar_productos'))
    finally:
        cursor.close()
        conexion.close()



@app.route('/admin/carrito/eliminar/<int:id_producto>', methods=['POST'])
@login_required
def eliminar_del_carrito(id_producto):
    user_id = current_user.id_usuario  # Obtener el id del usuario actual
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Eliminar el producto del carrito
    cursor.execute(
        "DELETE FROM carrito WHERE id_usuario = %s AND id_producto = %s",
        (user_id, id_producto)
    )

    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('mostrar_carrito'))  # Redirige al carrito actualizado


@app.route('/admin/carrito/vaciar', methods=['POST'])
@login_required
def vaciar_carrito():
    user_id = current_user.id_usuario  # Obtener el id del usuario actual
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Eliminar todos los productos del carrito del usuario
    cursor.execute(
        "DELETE FROM carrito WHERE id_usuario = %s",
        (user_id,)
    )

    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('mostrar_carrito'))  # Redirige al carrito vacío


@app.route('/admin/pago')
@login_required
def obtener_productos_carrito():
    id_usuario = current_user.id_usuario
    cart_items = obtener_productos_carrito(id_usuario)
    total_cordobas, total_dolares = calcular_total(cart_items)
    return render_template('admin/pago.html', cart_items=cart_items, total_cordobas=total_cordobas, total_dolares=total_dolares)

def obtener_productos_carrito(id_usuario):
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    query = """
        SELECT 
            p.id_producto, p.nombre, p.imagen1, p.imagen2, p.imagen3, p.video, 
            p.precio, p.descripcion, p.moneda, c.cantidad, 
            (p.precio * c.cantidad) AS subtotal
        FROM carrito c
        JOIN productos p ON c.id_producto = p.id_producto
        WHERE c.id_usuario = %s
    """
    cursor.execute(query, (id_usuario,))
    return cursor.fetchall()

def calcular_total(cart_items):
    tasa_cambio = 36.50  # Tasa de cambio fija
    total_cordobas = 0
    for item in cart_items:
        if item["moneda"] == "U$":
            total_cordobas += item["subtotal"] * tasa_cambio  # Convertir a córdobas
        else:
            total_cordobas += item["subtotal"]  # Sumar directamente en córdobas
    total_dolares = total_cordobas / tasa_cambio  # Convertir total a dólares
    return total_cordobas, total_dolares

@app.route('/admin/pedido/crear', methods=['POST'])
@login_required
def crear_pedido():
    id_usuario = current_user.id_usuario  # Obtener el ID del usuario actual
    moneda = request.form.get('moneda', 'C$')  # Obtener moneda del formulario (C$ por defecto)
    cart_items = obtener_productos_carrito(id_usuario)  # Obtener productos del carrito
    total_cordobas, total_dolares = calcular_total(cart_items)  # Calcular totales

    if not cart_items:
        flash("No hay productos en el carrito.", "warning")
        return redirect(url_for('mostrar_carrito'))

    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    try:
        # Verificar si todos los productos del carrito tienen id_estado = 1
        productos_vendidos = []
        for item in cart_items:
            cursor.execute(
                "SELECT id_estado FROM productos WHERE id_producto = %s", 
                (item["id_producto"],)
            )
            producto = cursor.fetchone()
            if not producto or producto["id_estado"] != 1:
                productos_vendidos.append(item["id_producto"])
        
        if productos_vendidos:
            # Quitar los productos vendidos del carrito
            for id_producto in productos_vendidos:
                cursor.execute(
                    "DELETE FROM carrito WHERE id_usuario = %s AND id_producto = %s", 
                    (id_usuario, id_producto)
                )
            conexion.commit()

            # Mensaje al usuario y redirigir al carrito
            flash("Algunos productos fueron vendidos y se han eliminado del carrito.", "danger")
            return redirect(url_for('mostrar_carrito'))

        # Insertar el pedido
        query_pedido = """
            INSERT INTO pedidos (id_usuario, fecha_pedido, moneda, total)
            VALUES (%s, NOW(), %s, %s)
        """
        total = total_cordobas if moneda == "C$" else total_dolares
        cursor.execute(query_pedido, (id_usuario, moneda, total))
        id_pedido = cursor.lastrowid  # Obtener el ID del pedido creado

        # Insertar los detalles del pedido
        query_detalle = """
            INSERT INTO detallepedidos (id_pedido, id_producto, moneda, precio, cantidad, subtotal)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        for item in cart_items:
            cursor.execute(query_detalle, (
                id_pedido,
                item["id_producto"],
                item["moneda"],
                item["precio"],
                item["cantidad"],
                item["subtotal"]
            ))
        
        # Actualizar el estado de cada producto a 4
        query_actualizar_estado = """
            UPDATE productos 
            SET id_estado = 4 
            WHERE id_producto = %s
        """
        for item in cart_items:
            cursor.execute(query_actualizar_estado, (item["id_producto"],))

        # Limpiar el carrito del usuario
        cursor.execute("DELETE FROM carrito WHERE id_usuario = %s", (id_usuario,))

        conexion.commit()
        flash("Pedido creado exitosamente.", "success")
        return redirect('/admin/mis_pedidos')  # Redirige a la lista de pedidos

    except Exception as e:
        conexion.rollback()
        flash("Error al crear el pedido: " + str(e), "danger")
        return redirect(url_for('mostrar_carrito'))
    finally:
        cursor.close()
        conexion.close()


@app.route('/admin/pedido/<int:id_pedido>')
@login_required
def mostrar_pedido(id_pedido):
    # Obtener el ID del usuario asociado al pedido
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Consultar el pedido y su usuario asociado
    query = """
        SELECT 
            p.id_pedido AS numero_factura, p.fecha_pedido, p.total, p.moneda, p.id_usuario
        FROM pedidos p
        WHERE p.id_pedido = %s
    """
    cursor.execute(query, (id_pedido,))
    pedido = cursor.fetchone()

    if not pedido:
        # Si no se encuentra el pedido, redirigir o mostrar un mensaje de error
        return redirect(url_for('mis_pedidos'))  # O mostrar una página de error

    # Obtener los detalles del pedido
    query_detalles = """
        SELECT 
            dp.id_producto, dp.cantidad, dp.moneda, dp.precio, dp.subtotal, p.nombre, u.usuario as vendedor
        FROM detallepedidos dp
        JOIN productos p ON dp.id_producto = p.id_producto
        JOIN usuarios u ON p.id_usuario = u.id_usuario
        WHERE dp.id_pedido = %s
    """
    cursor.execute(query_detalles, (id_pedido,))
    detalles = cursor.fetchall()

    # Consultar los datos del usuario con el id_usuario del pedido
    query_usuario = """
        SELECT nombre, apellido, telefono, direccion, email
        FROM usuarios
        WHERE id_usuario = %s
    """
    cursor.execute(query_usuario, (pedido['id_usuario'],))
    usuario = cursor.fetchone()

    # Calcular el total en córdobas y dólares
    total_cordobas, total_dolares = calcular_total_detalles(detalles, pedido['moneda'])

    conexion.close()

    # Pasar los datos del usuario junto con el pedido y los detalles a la plantilla
    return render_template('admin/mostrar_pedido.html', pedido=pedido, detalles=detalles, total_cordobas=total_cordobas, total_dolares=total_dolares, usuario=usuario)

def calcular_total_detalles(detalles, moneda_pedido):
    tasa_cambio = Decimal(36.50)  # Convertir la tasa de cambio a Decimal
    total_cordobas = Decimal(0)  # Asegurarse de que total_cordobas también sea Decimal

    # Calcular el total en córdobas
    for item in detalles:
        if moneda_pedido == "C$":
            total_cordobas += Decimal(item["subtotal"]) * tasa_cambio  # Convertir subtotal a Decimal si es necesario
        else:
            total_cordobas += Decimal(item["subtotal"])  # Sumar directamente en córdobas

    total_dolares = total_cordobas / tasa_cambio  # Convertir total a dólares

    return total_cordobas, total_dolares


@app.route('/admin/mis_pedidos')
@login_required
def mis_pedidos():
    user_id = current_user.id_usuario  # Obtener el ID del usuario actual
    conexion = dbconnection()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Consultar los pedidos del usuario activo
    query = """
        SELECT 
            p.id_pedido, p.fecha_pedido, p.total, p.moneda 
        FROM pedidos p
        WHERE p.id_usuario = %s
        ORDER BY p.fecha_pedido DESC
    """
    cursor.execute(query, (user_id,))
    pedidos = cursor.fetchall()

    conexion.close()

    return render_template('admin/mis_pedidos.html', pedidos=pedidos)


# Ejecuta la app
if __name__ == '__main__':
    app.run(debug=True)