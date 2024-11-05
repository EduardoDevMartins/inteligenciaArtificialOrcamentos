import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'fotos_recebidas'

# Mapeamento entre categorias e abas do Excel
CATEGORIAS_ABAS = {
    "Vazamento_de_água_na_saída_da_pia": 'Sifao',
    "Vazamento_de_água_na_torneira": 'Torneiras',
    "entupimento_esgoto": 'Entupimentos',
    # Adicione outras categorias e suas respectivas abas aqui
}

# Perguntas por categoria
PERGUNTAS_CATEGORIAS = {
    "Vazamento_de_água_na_saída_da_pia": [
        {"id": "localizacao", "label": "Qual o tipo de sifão existente?", "placeholder": "Ex: Simples, duplo, copo, rígido, cano PVC"},
        {"id": "caracteristica", "label": "Qual o material do seu sifão", "placeholder": "Ex: plástico, metal, cromado, Cano PVC"},
        {"id": "tipo", "label": "Qual ambiente o problema ocorre", "placeholder": "Ex: Banheiro, cozinha, sacada, lavanderia"},
    ],
    "Vazamento_de_água_na_torneira": [
        {"id": "localizacao", "label": "Onde está a torneira?", "placeholder": "Ex: Cozinha, banheiro"},
        {"id": "tipo", "label": "Qual o tipo de torneira?", "placeholder": "Ex: Monocomando, misturador"}
    ],
    "entupimento_esgoto": [
        {"id": "localizacao", "label": "Onde está o entupimento?", "placeholder": "Ex: Ralo do banheiro"},
        {"id": "grau_entupimento", "label": "Qual o grau de entupimento?", "placeholder": "Ex: Total, parcial"}
    ],
    # Adicione outras categorias e perguntas conforme necessário
}

# Função para carregar dados da tabela com base na categoria
def carregar_dados_tabela(categoria):
    aba = CATEGORIAS_ABAS.get(categoria)
    if aba:
        tabela = pd.read_excel('tabela_precos.xlsx', sheet_name=aba)
        tabela.columns = tabela.columns.str.strip()
        tabela = tabela[tabela.iloc[:, 2].notna()]
        tabela['descricao_completa'] = (
            tabela.iloc[:, 2].astype(str) + ' ' +
            tabela.iloc[:, 3].astype(str) + ' ' +
            tabela.iloc[:, 4].astype(str) + ' ' +
            tabela.iloc[:, 5].astype(str)
        )
        return tabela
    return None

# Função para encontrar o serviço mais semelhante
def encontrar_servico_mais_semelhante(servico_solicitado, caracteristicas, tabela):
    vectorizer = TfidfVectorizer()
    if caracteristicas:
        servico_solicitado += ' ' + ' '.join(caracteristicas)

    tfidf_matrix = vectorizer.fit_transform(tabela['descricao_completa'])
    servico_solicitado_tfidf = vectorizer.transform([servico_solicitado])

    similaridade = cosine_similarity(servico_solicitado_tfidf, tfidf_matrix)
    indice_servico_mais_semelhante = similaridade.argmax()

    # Obter os dados do serviço mais semelhante
    preco_total = tabela.iloc[indice_servico_mais_semelhante, 12]
    preco_mao_de_obra = tabela.iloc[indice_servico_mais_semelhante, 10]
    preco_material = tabela.iloc[indice_servico_mais_semelhante, 11]
    diagnostico = tabela.iloc[indice_servico_mais_semelhante, 13]
    solucao = tabela.iloc[indice_servico_mais_semelhante, 14]

    # Verificação para valores NaN e preenchimento com texto padrão
    preco_total = preco_total if pd.notna(preco_total) else "Indisponível"
    preco_mao_de_obra = preco_mao_de_obra if pd.notna(preco_mao_de_obra) else "Indisponível"
    preco_material = preco_material if pd.notna(preco_material) else "Indisponível"
    diagnostico = diagnostico if pd.notna(diagnostico) else "Diagnóstico não encontrado"
    solucao = solucao if pd.notna(solucao) else "Solução não disponível"

    return preco_total, preco_mao_de_obra, preco_material, diagnostico, solucao

# Rota inicial - Seleção de Categoria
@app.route('/', methods=['GET', 'POST'])
def selecionar_categoria():
    if request.method == 'POST':
        categoria = request.form['categoria']
        return redirect(url_for('formulario_orcamento', categoria=categoria))
    return render_template('categoria.html', categorias=PERGUNTAS_CATEGORIAS.keys())

# Rota para o formulário de orçamento
@app.route('/orcamento/<categoria>', methods=['GET', 'POST'])
def formulario_orcamento(categoria):
    perguntas = PERGUNTAS_CATEGORIAS.get(categoria, [])
    tabela = carregar_dados_tabela(categoria)  # Carrega a tabela correspondente à categoria
    if request.method == 'POST':
        servico = request.form['servico']
        respostas_perguntas = {pergunta["id"]: request.form.get(pergunta["id"]) for pergunta in perguntas}
        preco_total, preco_mao_de_obra, preco_material, diagnostico, solucao = encontrar_servico_mais_semelhante(servico, respostas_perguntas.values(), tabela)
        return render_template('orcamento.html', 
                               preco_total=preco_total, 
                               preco_mao_de_obra=preco_mao_de_obra, 
                               preco_material=preco_material, 
                               diagnostico=diagnostico, 
                               solucao=solucao, 
                               perguntas=perguntas)
    return render_template('orcamento.html', preco_total=None, perguntas=perguntas)

if __name__ == '__main__':
    app.run(debug=True)
