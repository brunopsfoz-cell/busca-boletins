from flask import Flask, render_template, request
import sqlite3
import os
import requests


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
                "texto": linha["texto"],
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


            snippet(
                paginas_fts,
                2,
                '<mark>',
                '</mark>',
                '...',
                300
            ) AS texto,


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




    # ==================================================
    # 1 - NOME COMPLETO EXATO
    # ==================================================

    frase = '"' + termo + '"'


    resultados += executar_busca(
        cursor,
        consulta_base,
        frase,
        100
    )





    # ==================================================
    # 2 - PROXIMIDADE
    # ==================================================

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






    # ==================================================
    # 3 - TODAS AS PALAVRAS
    # ==================================================

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







    # ==================================================
    # 4 - PALAVRAS SOLTAS
    # ==================================================

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





    # Mais relevantes primeiro

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

        termo = request.form.get(
            "busca",
            ""
        ).strip()



    else:

        termo = request.args.get(
            "busca",
            ""
        ).strip()





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