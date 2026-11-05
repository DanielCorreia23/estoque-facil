from flask import Flask, render_template, request, redirect, url_for, flash
from database import conectar, criar_tabelas
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "estoque-facil-chave-local"

criar_tabelas()


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        localizacao = request.form.get("localizacao", "").strip()
        codigo = request.form.get("codigo", "").strip()

        if not nome or not localizacao:
            flash("Preencha o nome e a localização.")
            return redirect(url_for("produtos"))

        conexao = conectar()
        conexao.execute(
            """INSERT INTO produtos
            (nome, localizacao_prateleira, codigo)
            VALUES (?, ?, ?)""",
            (nome, localizacao, codigo)
        )
        conexao.commit()
        conexao.close()

        flash("Produto cadastrado com sucesso!")
        return redirect(url_for("produtos"))

    return render_template("produtos.html")


@app.route("/lotes", methods=["GET", "POST"])
def lotes():
    conexao = conectar()

    if request.method == "POST":
        produto_id = request.form.get("produto_id")
        validade = request.form.get("data_validade")
        quantidade = request.form.get("quantidade")

        if not produto_id or not validade:
            flash("Selecione um produto e informe a validade.")
        else:
            conexao.execute(
                """INSERT INTO lotes
                (produto_id, data_validade, quantidade)
                VALUES (?, ?, ?)""",
                (produto_id, validade, quantidade or None)
            )
            conexao.commit()
            flash("Lote cadastrado com sucesso!")

        conexao.close()
        return redirect(url_for("lotes"))

    lista = conexao.execute(
        "SELECT id, nome FROM produtos ORDER BY nome"
    ).fetchall()

    conexao.close()
    return render_template("lotes.html", produtos=lista)


@app.route("/validade")
def validade():
    conexao = conectar()

    registros = conexao.execute("""
        SELECT produtos.nome,
               produtos.localizacao_prateleira,
               lotes.data_validade,
               lotes.quantidade
        FROM lotes
        JOIN produtos ON produtos.id = lotes.produto_id
        ORDER BY lotes.data_validade
    """).fetchall()

    conexao.close()

    hoje = date.today()
    limite = hoje + timedelta(days=30)
    resultados = []

    for registro in registros:
        data = date.fromisoformat(registro[2])

        if data < hoje:
            status = "VENCIDO"
        elif data <= limite:
            status = "VENCE EM ATÉ 30 DIAS"
        else:
            status = "OK"

        resultados.append((*registro, status))

    return render_template("validade.html", registros=resultados)


if __name__ == "__main__":
    app.run(debug=True)
