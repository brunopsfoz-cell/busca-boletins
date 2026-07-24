from flask import Flask, render_template, request
import sqlite3
import os
import re

app = Flask(__name__)

BANCO = "banco/boletins.db"


def conectar():
    conn = sqlite3.connect(BANCO)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def index():

    resultados = []
    termo = ""

    if request.method == "POST":

        termo = request.form["busca"].strip()

        if termo:

            conn = conectar()
            cursor = conn.cursor()

            consulta = """
            SELECT 
                arquivo,
                pagina,
                texto
            FROM paginas_fts
            WHERE paginas_fts MATCH ?
            LIMIT 100
            """

            try:
                cursor.execute(
                    consulta,
                    (termo,)
                )

                resultados = cursor.fetchall()

            except Exception as erro:
                print(erro)

            conn.close()


    return render_template(
        "index.html",
        resultados=resultados,
        termo=termo
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )