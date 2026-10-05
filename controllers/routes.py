from flask import Flask, render_template, request, redirect, url_for, flash
import urllib.request
import os
import uuid
import json
from models.database import db, Pokemon
from urllib.error import HTTPError, URLError
from models.database import db, Pokemon, Imagem

app = Flask(__name__)


# Lista para armazenar Pokémon
pokemon_list = []

# Dicionário para armazenar Pokémon
pokemon_dict = {}

def init_app(app):
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/pokedex', methods=['GET', 'POST'])
    def pokedex():
        pokemon = None
        error = None

        if request.method == 'POST':
            pokemon_name = request.form.get('pokemon_name', '').strip().lower()

            if pokemon_name:
                try:
                    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}'

                    req = urllib.request.Request(
                        url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )

                    with urllib.request.urlopen(req) as response:
                        data = json.loads(response.read())

                    pokemon = {
                        'id': data['id'],
                        'name': data['name'],
                        'image': data['sprites']['other']['official-artwork']['front_default'],
                        'types': [
                            type_data['type']['name']
                            for type_data in data['types']
                        ],
                        'height': data['height'] / 10,
                        'weight': data['weight'] / 10,
                        'base_experience': data['base_experience'],
                        'abilities': [
                            ability['ability']['name']
                            for ability in data['abilities']
                        ],
                        'stats': [
                            {
                                'name': stat['stat']['name'],
                                'value': stat['base_stat']
                            }
                            for stat in data['stats']
                        ]
                    }

                except HTTPError:
                    error = "Pokémon não encontrado. Verifique o nome ou número informado."

                except URLError:
                    error = "Não foi possível acessar a PokéAPI."

                except Exception as e:
                    print(f"Erro: {e}")
                    error = "Ocorreu um erro ao buscar o Pokémon."

        return render_template(
            'pokedex.html',
            pokemon=pokemon,
            error=error
        )
    
    # UPLOAD DE IMAGENS
    @app.route('/galeria', methods=['GET', 'POST'])
    def galeria():
        # Seleciona os nomes dos arquivos de imagens no banco
        imagens = Imagem.query.all()

        if request.method == 'POST':
            # Captura o arquivo vindo do formulário
            file = request.files['file']
            # Verifica se a extensão do arquivo é permitida
            if not arquivos_permitidos(file.filename):
                flash("Utilize os tipos de arquivos referentes a imagem.", 'danger')
                return redirect(request.url)
            # Define um nome aleatório para o arquivo
            filename = str(uuid.uuid4())
            
            # Gravando o nome do arquivo no banco
            img = Imagem(filename)
            db.session.add(img)
            db.session.commit()

            # Salva o arquivo na pasta de uploads
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("Imagem enviada com sucesso!", 'success')
        return render_template('galeria.html', imagens=imagens)

        
    #Rota com CRUD de jogos
    @app.route('/pokemon', methods=['GET', 'POST'])
    @app.route('/pokemon/delete/<int:id>')
    def pokemon(id=None):
        if id:
            # Deletar Pokémon
            pokemon = Pokemon.query.get(id)
            if pokemon:
                db.session.delete(pokemon)
                db.session.commit()
            return redirect(url_for('pokemon'))

        if request.method == 'POST':
            nome = request.form.get('nome')
            tipo = request.form.get('tipo')
            geracao = request.form.get('geracao')

            if nome and tipo and geracao:
                novo_pokemon = Pokemon(nome, tipo, int(geracao))
                db.session.add(novo_pokemon)
                db.session.commit()

            return redirect(url_for('pokemon'))

        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = 5
        pokemon_page = Pokemon.query.paginate(page=page, per_page=per_page)

        # Passando a variável corretamente para o template
        return render_template('pokemon_table.html', pokemon_page=pokemon_page)


                
            
        # Método do SQLAlchemy que faz um select no banco na tabela Games
       # gamesestoque = Game.query.all()
       # return render_template('estoque.html', gamesestoque=gamesestoque)
       
    @app.route('/editar_pokemon/<int:id>', methods=['GET', 'POST'])
    def editar_pokemon(id):
        pokemon = Pokemon.query.get(id)
        if not pokemon:
            return "Pokémon não encontrado", 404

        if request.method == 'POST':
            pokemon.nome = request.form['nome']
            pokemon.tipo = request.form['tipo']
            pokemon.geracao = request.form['geracao']
            
            db.session.commit()
            return redirect(url_for('pokemon'))

        return render_template('editar_pokemon.html', pokemon=pokemon)
                                
    @app.route('/pokemon_table', methods=['GET', 'POST'])
    def pokemon_table():
        if request.method == 'POST':
            pokemon_name = request.form.get('pokemon_name')
            pokemon_type = request.form.get('pokemon_type')
            if pokemon_name and pokemon_type:
                pokemon_dict[pokemon_name] = pokemon_type
                return redirect(url_for('pokemon_table'))
        
        return render_template('pokemon_table.html', pokemon_dict=pokemon_dict)

    @app.route('/api_pokemon', methods=['GET'])
    def api_pokemon():
        try:
            # Parâmetros de paginação
            limit = 12  # Número de Pokémon por página
            offset = int(request.args.get('offset', 0))  # Offset inicial (0 por padrão)

            # URL da PokeAPI com paginação
            url = f'https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}'

            # Criar uma requisição com cabeçalhos
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            # Abrir a URL e ler os dados
            res = urllib.request.urlopen(req)
            data = res.read()
            pokemon_data = json.loads(data)

            # Extrair os detalhes de cada Pokémon
            pokemons = []
            for pokemon in pokemon_data['results']:
                pokemon_url = pokemon['url']
                try:
                    # Criar uma requisição com cabeçalhos para os detalhes do Pokémon
                    pokemon_req = urllib.request.Request(pokemon_url, headers={'User-Agent': 'Mozilla/5.0'})
                    pokemon_res = urllib.request.urlopen(pokemon_req)
                    pokemon_info = json.loads(pokemon_res.read())
                    
                    # Extrair dados extras
                    types = [t['type']['name'] for t in pokemon_info['types']]  # Tipos do Pokémon
                    height = pokemon_info['height'] / 10  # Altura em metros
                    weight = pokemon_info['weight'] / 10  # Peso em quilogramas
                  
                    pokemons.append({
                    'name': pokemon_info['name'],
                    'image': pokemon_info['sprites']['front_default'],
                    'types': types,
                    'height': height,
                    'weight': weight,
                    })
                except (HTTPError, URLError) as e:
                    print(f"Erro ao buscar detalhes do Pokémon {pokemon['name']}: {e}")
                    continue  # Ignora esse Pokémon e continua para o próximo

            # Verificar se há mais páginas
            next_offset = offset + limit if pokemon_data['next'] else None
            prev_offset = offset - limit if offset > 0 else None

            return render_template('api_pokemon.html', pokemons=pokemons, next_offset=next_offset, prev_offset=prev_offset)
        
        except (HTTPError, URLError) as e:
            return f"Erro ao acessar a PokeAPI: {e}", 500
        except json.JSONDecodeError as e:
            return f"Erro ao decodificar JSON: {e}", 500
        except Exception as e:
            return f"Erro inesperado: {e}", 500

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=4000, debug=True)