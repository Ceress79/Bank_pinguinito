from flask import Flask

#Cada vez que el usuario entre en la ruta principal. lo lleva directamente a esta ruta

app = Flask( __name__)
@app.route('/')
def Index():
    return 'hello word'

#Ruta para agregar contacto
@app.route('/add_contact')
def add_contact():
    return 'add contact'

#Ruta editar datos
@app.route('/edit')
def edit_contact():
    return 'edit contact'

@app.route('/delete')
def delete_contact():
    return 'delete contact'

if __name__ == '__main__':
    app.run(port = 3000, debug= True)   