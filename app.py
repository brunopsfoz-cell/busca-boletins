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

        arquivo.write(
            resposta.content
        )


    tamanho = os.path.getsize(BANCO)

    print(
        "Banco baixado:",
        tamanho,
        "bytes"
    )




def verificar_banco():

    try:

        conn = sqlite3.connect(BANCO)


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

        print(
            "Banco inválido:",
            erro
        )


        if os.path.exists(BANCO):

            os.remove(BANCO)


        baixar_banco()



        # testa novamente depois do download
        conn = sqlite3.connect(BANCO)

        paginas = conn.execute(
            "SELECT count(*) FROM paginas"
        ).fetchone()


        fts = conn.execute(
            "SELECT count(*) FROM paginas_fts"
        ).fetchone()


        conn.close()


        print("Banco OK após download")
        print("Páginas:", paginas)
        print("FTS:", fts)




verificar_banco()




def conectar():

    conn = sqlite3.connect(
        BANCO
    )

    conn.row_factory = sqlite3.Row

    return conn





@app.route("/", methods=["GET", "POST"])
def index():

    resultados = []

    termo = ""


    if request.method == "POST":


        termo = request.form.get(
            "busca",
            ""
        ).strip()



        if termo:


            print(
                "Buscando:",
                termo
            )


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