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





@app.route("/", methods=["GET", "POST"])
def index():

    resultados = []

    termo = ""

    pagina = int(
        request.args.get(
            "pagina",
            1
        )
    )


    por_pagina = 50

    total = 0

    total_paginas = 0



    if request.method == "POST":

        termo = request.form.get(
            "busca",
            ""
        ).strip()


        pagina = 1



    else:

        termo = request.args.get(
            "busca",
            ""
        ).strip()



    if termo:


        conn = conectar()

        cursor = conn.cursor()



        # conta todos os resultados
        cursor.execute(
            """
            SELECT count(*)
            FROM paginas_fts
            WHERE paginas_fts MATCH ?
            """,
            (termo,)
        )


        total = cursor.fetchone()[0]

        total_paginas = (
            (total + por_pagina - 1)
            // por_pagina
        )



        inicio = (
            pagina - 1
        ) * por_pagina



        cursor.execute(
            """
            SELECT
                arquivo,
                pagina,
                texto
            FROM paginas_fts
            WHERE paginas_fts MATCH ?
            LIMIT ? OFFSET ?
            """,
            (
                termo,
                por_pagina,
                inicio
            )
        )


        resultados = cursor.fetchall()


        conn.close()



        print(
            "Busca:",
            termo,
            "Total:",
            total,
            "Página:",
            pagina
        )




    return render_template(
        "index.html",
        resultados=resultados,
        termo=termo,
        pagina=pagina,
        total=total,
        total_paginas=total_paginas
    )





if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )