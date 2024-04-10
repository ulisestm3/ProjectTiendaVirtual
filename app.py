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

    return redirect('/admin/productos')

@app.route('/admin/productos/borrar', methods=['POST'])
def admin_productos_borrar():
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
    _Id = request.form['txtId']
    _nombre = request.form['txtNombre']
    _archivo = request.files['txtImagen']
    _precio = request.form['txtPrecio']

    
    conexion=dbconnection()
    cursor=conexion.cursor()
    cursor.execute("select imagen from productos where id=%s", (_Id))
    producto=cursor.fetchall()
    conexion.commit()
    print(producto)

    if os.path.exists("templates/sitio/img/"+str(producto[0][0])):
        os.unlink("templates/sitio/img/"+str(producto[0][0]))

    tiempo= datetime.now()
    horaActual=tiempo.strftime('%Y-%m-%d_%H-%M-%S')

    if _archivo.filename!="":
        nuevoNombre=horaActual+"_"+_archivo.filename
        _archivo.save("templates/sitio/img/"+nuevoNombre)

    if _nombre and _archivo and _precio:
        conexion= dbconnection()
        cursor=conexion.cursor()
        sql = "update productos set nombre = %s, imagen = %s, precio = %s where id= %s"
        data = (_nombre, nuevoNombre, _precio,_Id)
        cursor.execute(sql,data)
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