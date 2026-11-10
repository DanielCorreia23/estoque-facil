
import sqlite3
import pytest
import app as modulo_app


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    banco = tmp_path / "teste.db"

    def conectar_teste():
        return sqlite3.connect(banco)

    monkeypatch.setattr("database.conectar", conectar_teste)
    monkeypatch.setattr(modulo_app, "conectar", conectar_teste)

    def renderizar(template, **context):
        if template == "validade.html":
            return " ".join(str(r[-1]) for r in context["registros"])
        return "OK"

    monkeypatch.setattr(modulo_app, "render_template", renderizar)

    modulo_app.criar_tabelas()
    modulo_app.app.config["TESTING"] = True

    with modulo_app.app.test_client() as client:
        yield client


def test_pagina_inicial(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200


def test_pagina_produtos(cliente):
    resposta = cliente.get("/produtos")
    assert resposta.status_code == 200


def test_cadastro_produto(cliente):
    resposta = cliente.post("/produtos", data={
        "nome": "Dipirona",
        "localizacao": "Prateleira A",
        "codigo": "123"
    })

    assert resposta.status_code == 302

    conexao = sqlite3.connect(cliente.application.config.get("TEST_DB", ":memory:")) if False else None
    from database import conectar
    conexao = conectar()
    produto = conexao.execute(
        "SELECT nome FROM produtos"
    ).fetchone()
    conexao.close()

    assert produto[0] == "Dipirona"


def test_produto_sem_nome(cliente):
    resposta = cliente.post("/produtos", data={
        "nome": "",
        "localizacao": "Prateleira A"
    })
    assert resposta.status_code == 302


def test_produto_sem_localizacao(cliente):
    resposta = cliente.post("/produtos", data={
        "nome": "Dipirona",
        "localizacao": ""
    })
    assert resposta.status_code == 302


def test_pagina_lotes(cliente):
    resposta = cliente.get("/lotes")
    assert resposta.status_code == 200


def test_cadastro_lote(cliente):
    from database import conectar

    cliente.post("/produtos", data={
        "nome": "Paracetamol",
        "localizacao": "Prateleira B",
        "codigo": "456"
    })

    conexao = conectar()
    produto = conexao.execute(
        "SELECT id FROM produtos"
    ).fetchone()
    conexao.close()

    resposta = cliente.post("/lotes", data={
        "produto_id": str(produto[0]),
        "data_validade": "2027-12-31",
        "quantidade": "20"
    })

    assert resposta.status_code == 302

    conexao = conectar()
    lote = conexao.execute(
        "SELECT data_validade FROM lotes"
    ).fetchone()
    conexao.close()

    assert lote[0] == "2027-12-31"


def test_pagina_validade(cliente):
    resposta = cliente.get("/validade")
    assert resposta.status_code == 200


def test_classificacao_produtos_vencidos(cliente):
    from database import conectar

    cliente.post("/produtos", data={
        "nome": "Produto Vencido",
        "localizacao": "A1"
    })

    conexao = conectar()
    produto = conexao.execute(
        "SELECT id FROM produtos"
    ).fetchone()

    conexao.execute(
        "INSERT INTO lotes (produto_id, data_validade, quantidade) VALUES (?, ?, ?)",
        (produto[0], "2020-01-01", 10)
    )
    conexao.commit()
    conexao.close()

    resposta = cliente.get("/validade")

    assert b"VENCIDO" in resposta.data

