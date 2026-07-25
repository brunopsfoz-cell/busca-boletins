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





def buscar_nome(cursor, termo):

    palavras = termo.split()


    # 1 - Busca exata
    frase = '"' + termo + '"'


    cursor.execute(
        """
        SELECT
            arquivo,
            pagina,
            snippet(
                paginas_fts,
                2,
                '<mark>',
                '</mark>',
                '...',
                200
            ) AS texto
        FROM paginas_fts
        WHERE paginas_fts MATCH ?
        ORDER BY rank
        LIMIT 500
        """,
        (frase,)
    )


    resultados = cursor.fetchall()


    if resultados:
        return resultados



    # 2 - Busca por proximidade
    # Exemplo:
    # ROBERTO NEAR CESAR NEAR COELHO

    if len(palavras) > 1:

        proximidade = " NEAR ".join(
            palavras
        )


        cursor.execute(
            """
            SELECT
                arquivo,
                pagina,
                snippet(
                    paginas_fts,
                    2,
                    '<mark>',
                    '</mark>',
                    '...',
                    200
                ) AS texto
            FROM paginas_fts
            WHERE paginas_fts MATCH ?
            ORDER BY rank
            LIMIT 500
            """,
            (proximidade,)
        )


        resultados = cursor.fetchall()


        if resultados:
            return resultados



    # 3 - Busca normal

    cursor.execute(
        """
        SELECT
            arquivo,
            pagina,
            snippet(
                paginas_fts,
                2,
                '<mark>',
                '</mark>',
                '...',
                200
            ) AS texto
        FROM paginas_fts
        WHERE paginas_fts MATCH ?
        ORDER BY rank
        LIMIT 500
        """,
        (termo,)
    )


    return cursor.fetchall()





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