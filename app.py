from flask import Flask, render_template, request
import sqlite3
import os
import requests


app = Flask(__name__)


BANCO = "banco/boletins.db"

URL_BANCO = "https://drive.google.com/uc?export=download&id=1DIdZcUa3DyXuA7kAPG83w0yNxnMNCOoo"


def baixar_banco():

    os.makedirs("banco", exist_ok=True)

    print("Baixando banco...")

    resposta = requests.get(URL_BANCO)

    resposta.raise_for_status()

    with open(BANCO, "wb") as arquivo:
        arquivo.write(resposta.content)

    print("Banco baixado!")


def verificar_banco():

    try:

        conn = sqlite3.connect(BANCO)

        conn.execute("SELECT count(*) FROM paginas")

        paginas = conn.execute(
            "SELECT count(*) FROM paginas"
        ).fetchone()

        fts = conn.execute(
            "SELECT count(*) FROM paginas_fts"
        ).fetchone()

        conn.close()

        print("Banco OK")
        print("Páginas:", paginas)
        print("FTS:", fts)


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


    if request.method == "POST":

        termo = request.form.get("busca", "").strip()


        if termo:

            print("Buscando:", termo)

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
                    (f'"{termo}"',)
                )

                resultados = cursor.fetchall()

                print(
                    "Resultados encontrados:",
                    len(resultados)
                )


            except Exception as erro:

                print(
                    "Erro na busca:",
                    erro
                )


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