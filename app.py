from flask import Flask, render_template, request
import sqlite3
import os
import requests
import re
import unicodedata


app = Flask(__name__)


BANCO = "banco/boletins.db"


URL_BANCO = (
    "https://github.com/brunopsfoz-cell/busca-boletins/"
    "raw/refs/heads/main/banco/boletins.db?download="
)



def baixar_banco():

    os.makedirs("banco", exist_ok=True)

    print("Baixando banco...")

    resposta = requests.get(
        URL_BANCO,
        timeout=300
    )

    resposta.raise_for_status()

    with open(BANCO, "wb") as arquivo:
        arquivo.write(resposta.content)

    print(
        "Banco baixado:",
        os.path.getsize(BANCO),
        "bytes"
    )





def verificar_banco():

    try:

        conn = sqlite3.connect(BANCO)

        conn.execute(
            "SELECT count(*) FROM paginas"
        )

        conn.execute(
            "SELECT count(*) FROM paginas_fts"
        )

        conn.execute(
            "SELECT count(*) FROM documentos"
        )

        conn.close()

        print("Banco OK")


    except Exception as erro:

        print("Banco inválido:", erro)

        if os.path.exists(BANCO):
            os.remove(BANCO)

        baixar_banco()





verificar_banco()





def conectar():

    conn = sqlite3.connect(BANCO)

    conn.row_factory = sqlite3.Row

    return conn







def limpar_busca(texto):

    texto = unicodedata.normalize(
        "NFKC",
        texto
    )


    texto = re.sub(
        r'[^\w\sáéíóúãõçÁÉÍÓÚÃÕÇ]',
        ' ',
        texto
    )


    texto = " ".join(
        texto.split()
    )


    return texto







def criar_trecho(texto, termo, tamanho=350):

    if not texto:
        return ""


    texto_lower = texto.lower()
    termo_lower = termo.lower()


    posicao = texto_lower.find(
        termo_lower
    )



    # Se não achar exatamente,
    # mostra início da página

    if posicao == -1:

        return texto[:tamanho] + "..."




    metade = tamanho // 2


    inicio = posicao - metade

    fim = posicao + len(termo) + metade




    if inicio < 0:
        inicio = 0



    if fim > len(texto):
        fim = len(texto)





    trecho = texto[inicio:fim]




    if inicio > 0:
        trecho = "..." + trecho



    if fim < len(texto):
        trecho = trecho + "..."





    trecho = trecho.replace(
        texto[posicao:posicao + len(termo)],
        "<mark>" +
        texto[posicao:posicao + len(termo)] +
        "</mark>"
    )



    return trecho











def executar_busca(cursor, consulta, termo, peso):

    cursor.execute(
        consulta,
        (termo,)
    )


    resultados = []



    for linha in cursor.fetchall():

        resultados.append(
            {
                "arquivo": linha["arquivo"],
                "pagina": linha["pagina"],

                "texto": criar_trecho(
                    linha["texto"],
                    termo
                ),

                "url": linha["url"],

                "numero_boletim": linha["numero_boletim"],

                "data_boletim": linha["data_boletim"],

                "peso": peso
            }
        )


    return resultados











def buscar_nome(cursor, termo):


    resultados = []

    palavras = termo.split()





    consulta_base = """

        SELECT

            paginas_fts.arquivo,

            paginas_fts.pagina,

            paginas_fts.texto,


            documentos.url,


            boletins_info.numero_boletim,


            boletins_info.data_boletim



        FROM paginas_fts



        LEFT JOIN documentos

        ON paginas_fts.arquivo = documentos.arquivo



        LEFT JOIN boletins_info

        ON paginas_fts.arquivo = boletins_info.arquivo



        WHERE paginas_fts MATCH ?

    """






    # 1 - Nome completo exato

    frase = '"' + termo + '"'


    resultados += executar_busca(
        cursor,
        consulta_base,
        frase,
        100
    )







    # 2 - Proximidade

    if len(palavras) > 1:


        proximidade = " NEAR ".join(
            palavras
        )


        resultados += executar_busca(
            cursor,
            consulta_base,
            proximidade,
            80
        )








    # 3 - Todas as palavras


    if len(palavras) > 1:


        todas = " AND ".join(
            palavras
        )


        resultados += executar_busca(
            cursor,
            consulta_base,
            todas,
            50
        )








    # 4 - Busca normal


    resultados += executar_busca(
        cursor,
        consulta_base,
        termo,
        20
    )








    # Remove duplicados


    vistos = set()

    final = []



    for r in resultados:


        chave = (
            r["arquivo"],
            r["pagina"]
        )


        if chave not in vistos:

            vistos.add(chave)

            final.append(r)






    final.sort(
        key=lambda x: x["peso"],
        reverse=True
    )



    return final[:500]









@app.route("/", methods=["GET", "POST"])
def index():


    resultados = []

    termo = ""




    if request.method == "POST":


        termo = limpar_busca(
            request.form.get(
                "busca",
                ""
            )
        )


    else:


        termo = limpar_busca(
            request.args.get(
                "busca",
                ""
            )
        )







    if termo:


        conn = conectar()

        cursor = conn.cursor()



        resultados = buscar_nome(
            cursor,
            termo
        )



        conn.close()



        print(
            "Busca:",
            termo,
            "Resultados:",
            len(resultados)
        )








    return render_template(

        "index.html",

        resultados=resultados,

        termo=termo,

        total=len(resultados),

        pagina=1,

        total_paginas=1

    )








if __name__ == "__main__":


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )