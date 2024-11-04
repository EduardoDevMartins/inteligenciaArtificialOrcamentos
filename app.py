import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Inicializar o Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'fotos_recebidas'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Função para verificar extensões de arquivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Carregar os dados
tabela = pd.read_excel('tabela_precos.xlsx', sheet_name='Hidráulica')
tabela.columns = tabela.columns.str.strip()  # Remove espaços em branco dos nomes das colunas

# Remover linhas com valores NaN na coluna de serviços (C)
tabela = tabela[tabela.iloc[:, 2].notna()]

# Concatenar as colunas C, D, E e F para criar uma representação completa de cada serviço
tabela['descricao_completa'] = tabela.iloc[:, 2].astype(str) + ' ' + tabela.iloc[:, 3].astype(str) + ' ' + tabela.iloc[:, 4].astype(str) + ' ' + tabela.iloc[:, 5].astype(str)

# Função para encontrar o serviço mais semelhante
def encontrar_servico_mais_semelhante(servico_solicitado, caracteristicas):
    vectorizer = TfidfVectorizer()
    if caracteristicas:
        servico_solicitado = f"{servico_solicitado} {' '.join(caracteristicas)}"
    
    tfidf_matrix = vectorizer.fit_transform(tabela['descricao_completa'])
    servico_solicitado_tfidf = vectorizer.transform([servico_solicitado])
    
    similaridade = cosine_similarity(servico_solicitado_tfidf, tfidf_matrix)
    indice_servico_mais_semelhante = similaridade.argmax()
    
    preco_total = tabela.iloc[indice_servico_mais_semelhante, 12]  # Coluna M
    preco_mao_de_obra = tabela.iloc[indice_servico_mais_semelhante, 10]  # Coluna K
    preco_material = tabela.iloc[indice_servico_mais_semelhante, 11]  # Coluna L
    diagnostico = tabela.iloc[indice_servico_mais_semelhante, 13]  # Coluna N
    solucao = tabela.iloc[indice_servico_mais_semelhante, 14]  # Coluna O
    
    return preco_total, preco_mao_de_obra, preco_material, diagnostico, solucao

# Rota inicial - Seleção de Categoria
@app.route('/', methods=['GET', 'POST'])
def selecionar_categoria():
    if request.method == 'POST':
        categoria = request.form['categoria']
        return redirect(url_for('formulario_orcamento', categoria=categoria))
    return render_template('categoria.html')

# Rota para o formulário de orçamento
@app.route('/orcamento/<categoria>', methods=['GET', 'POST'])
def formulario_orcamento(categoria):
    if request.method == 'POST':
        servico = request.form['servico']
        caracteristicas = [
            request.form.get('caracteristica1', ''),
            request.form.get('caracteristica2', ''),
            request.form.get('caracteristica3', '')
        ]
        preco_total, preco_mao_de_obra, preco_material, diagnostico, solucao = encontrar_servico_mais_semelhante(servico, caracteristicas)
        return render_template('orcamento.html', preco_total=preco_total, preco_mao_de_obra=preco_mao_de_obra, preco_material=preco_material, diagnostico=diagnostico, solucao=solucao)
    return render_template('orcamento.html', preco_total=None)

# Rota para dados pessoais e upload de fotos
@app.route('/dados_pessoais', methods=['POST'])
def dados_pessoais():
    nome = request.form['nome']
    telefone = request.form['telefone']
    email = request.form['email']
    endereco = request.form['endereco']
    imobiliaria = request.form['imobiliaria']
    tipo_usuario = request.form['tipo_usuario']

    # Lidar com o upload de fotos
    if 'foto' not in request.files:
        return "Nenhuma foto foi enviada", 400
    file = request.files['foto']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

    # Salvar os dados em uma planilha Excel
    dados = pd.DataFrame({
        'Nome': [nome],
        'Telefone': [telefone],
        'Email': [email],
        'Endereço': [endereco],
        'Imobiliária': [imobiliaria],
        'Tipo de Usuário': [tipo_usuario],
        'Foto': [filename]
    })
    if not os.path.exists('recebidos.xlsx'):
        dados.to_excel('recebidos.xlsx', index=False)
    else:
        dados_existentes = pd.read_excel('recebidos.xlsx')
        dados_completos = pd.concat([dados_existentes, dados], ignore_index=True)
        dados_completos.to_excel('recebidos.xlsx', index=False)

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
