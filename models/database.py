from flask_sqlalchemy import SQLAlchemy 

#Criando uma instância do SQLAlchemy
db = SQLAlchemy()

# Classe para imagens
class Imagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), unique=True, nullable=False)
    def __init__(self, filename):
        self.filename = filename


#Classe responsável por criar a entidade "Games" no banco com seus atributos
class Pokemon(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(150))
    tipo = db.Column(db.String(150))
    geracao = db.Column(db.Integer)
    
    #Método contrutor da Classe
    def __init__(self, nome, tipo, geracao):
        self.nome = nome
        self.tipo = tipo
        self.geracao = geracao