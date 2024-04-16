from flask import Flask, render_template, request, redirect,session, send_from_directory
from datetime import datetime
import config
import pymysql
import os


app = Flask(__name__)

app.secret_key = config.HEX_SEC_KEY

# Función para establecer la conexión a la base de datos
def dbconnection():
    return pymysql.connect(host= config.MSQL_HOST, user= config.MSQL_USER, password= config.MSQL_PASSWORD, database= config.MSQL_DB)


#Rutas para cargar imagenes
@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)

@app.route('/video/<video>')
def videos(video):
    print(video)
    return send_from_directory(os.path.join('templates/sitio/video'),video)

# Rutas para sitio
@app.route('/')
def inicio():
    return render_template('sitio/index.html')


@app.route('/productos')
def productos():
    conexion = dbconnection()
    cursor=conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    productos=cursor.fetchall()
    conexion.commit()    
    
    return render_template('sitio/productos.html', productos=productos)

@app.route('/detalleproductos', methods=['POST'])
def detalleproductos():
    _id = request.form['txtID']
    conexion = dbconnection()
    cursor=conexion.cursor()
    sql = 'SELECT * FROM productos WHERE id= %s'
    cursor.execute(sql, _id)
    productos=cursor.fetchall()
    conexion.commit()

    return render_template('sitio/detalleproductos.html', productos=productos)

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/pago')
def pago():
    return render_template('sitio/pago.html')

@app.route('/pagoexitoso', methods=['POST'])
def pago_exitoso():
    return render_template('sitio/pagoexitoso.html')

# Rutas para admin
@app.route('/admin')
def admin_index():
    return render_template('admin/index.html')


@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')


@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _usuario=request.form['txtUsuario']
    _password=request.form['txtPassword']
    print(_usuario)
    print(_password)
    
    conexion = dbconnection()
    cursor=conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND password = %s", (_usuario, _password))
    usuario=cursor.fetchone()
    print(usuario)
        
    
    if usuario:
        session['logeado'] = True
        session['id'] = usuario[0]
        return render_template('/admin/index.html')
    
    else:
        return render_template('/admin/login.html', message = " Credenciales no son correctas " )

@app.route('/admin/registro')
def admin_registro():
    return render_template('admin/registro.html')

@app.route('/admin/registro/usuario', methods=['POST'])
def admin_registro_usuario():
    conexion = None
    
    try:
        _usuario = request.form['txtUsuario']
        _password = request.form['txtPassword']
        _nombre = request.form['txtNombre']
        _apellido = request.form['txtApellido']
        _email = request.form['txtEmail']

        conexion = dbconnection()
        cursor = conexion.cursor()

        # Verificar si el usuario o el correo electrónico ya existen
        sql_select = "SELECT * FROM usuarios WHERE usuario = %s"
        cursor.execute(sql_select, (_usuario,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            # Si el usuario o el correo electrónico ya existen, mostrar un mensaje en el formulario de registro
            return render_template('admin/registro.html', mensaje='El usuario o el correo electrónico ya existen.')

        # Si el usuario y el correo electrónico no existen, insertar los datos en la base de datos
        sql_insert = "INSERT INTO usuarios (usuario, password, nombre, apellido, email) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_insert, (_usuario, _password, _nombre, _apellido, _email))
        conexion.commit()

        # Redireccionar a la página de inicio de sesión después del registro exitoso
        return render_template('admin/login.html')

    except pymysql.Error as e:
        print("Error de MySQL:", e)
    finally:
        if conexion is not None:
            conexion.close()

    return render_template('admin/login.html')




@app.route('/admin/productos')
def admin_productos_leer():
    
    try:
        conexion = dbconnection()
        cursor=conexion.cursor()
        cursor.execute("SELECT * FROM productos")
        productos=cursor.fetchall()
        conexion.commit()
        print(productos)
        conexion.close()
    except pymysql.Error as e:
        print("Error de MySQL:", e)
    return render_template('admin/productos.html', productos=productos)

@app.route('/admin/editar', methods=['POST'])
def admin_productos_editar():
    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("select * from productos")
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)
    return render_template('admin/editar.html', producto=insertObjeto)


@app.route('/admin/productos/guardaradv', methods=['POST'])
def admin_productos_guardaradv():
    try:
        conexion = dbconnection()
        cursor = conexion.cursor()
        _nombre = request.form['txtNombre']
        _archivo = request.files['txtImagen']
        _precio = request.form['txtPrecio']

        tiempo= datetime.now()
        horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')

        if _archivo.filename!="":
            nuevoNombre=horaActual+"_"+_archivo.filename
            _archivo.save("templates/sitio/img/"+nuevoNombre)
                
        sql = "INSERT INTO productos (nombre, imagen, precio) VALUES (%s, %s, %s)"
        cursor.execute(sql, (_nombre, nuevoNombre, _precio))
        conexion.commit()

        print(_nombre)
        print(_archivo)
        print(_precio)

    except pymysql.Error as e:
        print("Error de MySQL:", e)
    finally:
        conexion.close()

    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("select * from productos")
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)
    return render_template('admin/editar.html', producto=insertObjeto)


@app.route('/admin/productos/guardar', methods=['POST'])
def admin_productos_guardar():
    try:
        conexion = dbconnection()
        cursor = conexion.cursor()
        _nombre = request.form['txtNombre']
        _archivo1 = request.files['txtImagen1']
        _archivo2 = request.files['txtImagen2']
        _archivo3 = request.files['txtImagen3']
        _video = request.files['txtVideo']
        _precio = request.form['txtPrecio']
        _descripcion = request.form['txtDescripcion']

        nuevoNombre1 = None
        nuevoNombre2 = None
        nuevoNombre3 = None
        nuevoNombrevideo = None

        tiempo= datetime.now()
        horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')
        
        if _archivo1.filename!="":
            nuevoNombre1=horaActual+"_"+_archivo1.filename
            _archivo1.save("templates/sitio/img/"+nuevoNombre1)

        if _archivo2.filename!="":
            nuevoNombre2=horaActual+"_"+_archivo2.filename
            _archivo2.save("templates/sitio/img/"+nuevoNombre2)

        if _archivo3.filename!="":
            nuevoNombre3=horaActual+"_"+_archivo3.filename
            _archivo3.save("templates/sitio/img/"+nuevoNombre3)

        if _video.filename!="":
            nuevoNombrevideo=horaActual+"_"+_video.filename
            _video.save("templates/sitio/video/"+nuevoNombrevideo)
                
        sql = "INSERT INTO productos (nombre, imagen1, imagen2, imagen3, video, precio, descripcion) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio,_descripcion))
        conexion.commit() 

    except pymysql.Error as e:
        print("Error de MySQL:", e)
    finally:
        conexion.close()

    return redirect('/admin/productos')

@app.route('/admin/productos/borrar', methods=['POST'])
def admin_productos_borrar():
    _id = request.form['txtID']
    print(_id) 
    
    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("delete from productos where id=%s", (_id))
    conexion.commit()

    return redirect('/admin/productos')

@app.route('/admin/productos/borraradv', methods=['POST'])
def admin_productos_borraradv():
    _id = request.form['txtID']
    print(_id)
    
    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("select imagen from productos where id=%s", (_id))
    producto=cursor.fetchall()
    conexion.commit()
    print(producto)

    if os.path.exists("templates/sitio/img/"+str(producto[0][0])):
        os.unlink("templates/sitio/img/"+str(producto[0][0]))

    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("delete from productos where id=%s", (_id))
    conexion.commit()

    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("select * from productos")
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)
    return render_template('admin/editar.html', producto=insertObjeto)


@app.route('/admin/productos/actalizar', methods=['POST'])
def admin_productos_actualizar():
    conexion = dbconnection()
    cursor = conexion.cursor()
    _id = request.form['txtId']
    _nombre = request.form['txtNombre']
    _archivo1 = request.files['txtImagen1']
    _archivo2 = request.files['txtImagen2']
    _archivo3 = request.files['txtImagen3']
    _video = request.files['txtVideo']
    _precio = request.form['txtPrecio']
    _descripcion = request.form['txtDescripcion']

    nuevoNombre1 = None
    nuevoNombre2 = None
    nuevoNombre3 = None
    nuevoNombrevideo = None

    tiempo= datetime.now()
    horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')
    
    if _archivo1.filename!="":
        nuevoNombre1=horaActual+"_"+_archivo1.filename
        _archivo1.save("templates/sitio/img/"+nuevoNombre1)
    else:
        nuevoNombre1= request.form['txtImagen11']


    if _archivo2.filename!="":
        nuevoNombre2=horaActual+"_"+_archivo2.filename
        _archivo2.save("templates/sitio/img/"+nuevoNombre2)
    else:
        nuevoNombre2 = request.form['txtImagen21']


    if _archivo3.filename!="":
        nuevoNombre3=horaActual+"_"+_archivo3.filename
        _archivo3.save("templates/sitio/img/"+nuevoNombre3)
    else:
        nuevoNombre3 = request.form['txtImagen31']


    if _video.filename!="":
        nuevoNombrevideo=horaActual+"_"+_video.filename
        _video.save("templates/sitio/video/"+nuevoNombrevideo)
    else:
        nuevoNombrevideo = request.form['txtVideo1']

            
    sql = "update productos set nombre=%s, imagen1=%s, imagen2=%s, imagen3=%s, video=%s, precio=%s, descripcion=%s where id=%s"
    cursor.execute(sql, (_nombre, nuevoNombre1, nuevoNombre2, nuevoNombre3, nuevoNombrevideo, _precio,_descripcion, _id))
    conexion.commit() 

    
    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("select * from productos")
    producto=cursor.fetchall()

    insertObjeto=[]
    columnaNames=[column[0] for column in cursor.description]

    for record in producto:
        insertObjeto.append(dict(zip(columnaNames, record)))
    cursor.close()
        
    print(producto)
    return render_template('admin/editar.html', producto=insertObjeto)
    

#Ejecuta la app
if __name__ =='__main__':
    app.run(debug=True)