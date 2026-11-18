"""Gera os gráficos do artigo a partir de resultados/.

Nenhum número é digitado aqui: o script lê os resumo.txt, recursos.txt e
contexto.txt de cada medição e usa a mediana das execuções de cada rótulo.

Uso, na raiz do repositório:
    python3 artigo/img/gerar_graficos.py

Só usa a biblioteca padrão do Python. Gera arquivos .svg em artigo/img/.
"""

import math
import re
import statistics
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RESULTADOS = RAIZ / "resultados"
SAIDA = Path(__file__).resolve().parent

# Cores (paleta de referência, modo claro)
FUNDO = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
APAGADO = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
AZUL = "#2a78d6"
AZUL_CLARO = "#86b6ef"
LARANJA = "#eb6834"
FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

# Cada mudança: rótulo de quem é o "antes" (medido no mesmo dia, ou na mesma
# ronda) e rótulo do "depois", igual à tabela da seção 6 do artigo.
MUDANCAS = [
    ("01", "Índices", "00-linha-de-base", "01-indices", False),
    ("02", "JOIN", "01-indices", "02-join", False),
    ("03", "Pool (10)", "02-join", "03-pool", False),
    ("04", "Pool (20)", "03-pool", "04-pool-max20", True),
    ("05", "Índice /pedidos", "03-pool", "05-indice-pedidos", False),
    ("06", "Soma no SQL", "05-intercalado", "06-intercalado", False),
    ("07", "Índice na data", "06-intercalado", "07-indice-data", True),
    ("08", "Só o índice", "07-intercalado", "08-intercalado", False),
    ("09", "Visão top-produtos", "08-controle", "09-visao-materializada", False),
    ("10", "CPU redistribuída", "09-controle", "10-cpu-redistribuida", False),
    ("11", "Visão contagem", "10-controle", "11-contagem-materializada", False),
]


def pastas(rotulo):
    return sorted(p for p in RESULTADOS.iterdir() if p.name.endswith("-" + rotulo))


def vazao(pasta):
    texto = (pasta / "resumo.txt").read_text(encoding="utf-8")
    return float(re.search(r"Requisições/s:\s+([\d.]+)", texto).group(1))


def cpu_banco_pct_do_limite(pasta):
    recursos = (pasta / "recursos.txt").read_text(encoding="utf-8")
    cpu = float(re.search(r"banco-1\s+\d+\s+([\d.]+)%", recursos).group(1))
    contexto = (pasta / "contexto.txt").read_text(encoding="utf-8")
    limite = int(re.search(r"banco: cpus=(\d+)", contexto).group(1)) / 1e9
    return cpu / limite


def valores(rotulo, func):
    """Mediana das execuções; com 2 execuções, devolve as duas."""
    vals = [func(p) for p in pastas(rotulo)]
    if len(vals) == 2:
        return sorted(vals)
    return [statistics.median(vals)]


def fmt(v):
    return f"{v:.2f}".replace(".", ",")


def texto(x, y, conteudo, tam=13, cor=TINTA, ancora="start", peso="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam}" fill="{cor}" '
            f'text-anchor="{ancora}" font-weight="{peso}" font-family=\'{FONTE}\'>{conteudo}</text>')


def svg(larg, alt, corpo, titulo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{larg}" height="{alt}" '
            f'viewBox="0 0 {larg} {alt}" role="img" aria-label="{titulo}">\n'
            f'<rect width="{larg}" height="{alt}" fill="{FUNDO}"/>\n' + "\n".join(corpo) + "\n</svg>\n")


def eixo_log(x0, x1, vmin, vmax):
    a, b = math.log10(vmin), math.log10(vmax)
    return lambda v: x0 + (math.log10(v) - a) / (b - a) * (x1 - x0)


def grafico_vazao():
    larg, alt = 760, 570
    esq, dir_, topo = 210, 700, 88
    linha = 36
    escala = eixo_log(esq, dir_, 1, 200)
    corpo = [
        texto(24, 34, "Vazão antes e depois de cada mudança", 18, TINTA, peso="600"),
        texto(24, 56, "Requisições por segundo, mediana de 3 execuções. Cada par foi medido no mesmo dia.", 13, TINTA_2),
    ]
    base = topo + linha * len(MUDANCAS)
    for marca in [1, 2, 5, 10, 20, 50, 100, 200]:
        x = escala(marca)
        corpo.append(f'<line x1="{x:.1f}" y1="{topo - 14}" x2="{x:.1f}" y2="{base - 10}" stroke="{GRADE}" stroke-width="1"/>')
        corpo.append(texto(x, base + 8, str(marca), 12, APAGADO, "middle"))
    corpo.append(texto((esq + dir_) / 2, base + 30, "req/s (escala logarítmica)", 12, APAGADO, "middle"))

    for i, (num, nome, antes, depois, sem_ganho) in enumerate(MUDANCAS):
        y = topo + i * linha
        va = valores(antes, vazao)
        vd = valores(depois, vazao)[0]
        corpo.append(texto(24, y + 4, num, 13, TINTA_2))
        corpo.append(texto(52, y + 4, nome, 13, TINTA))
        xs = [escala(v) for v in va]
        xd = escala(vd)
        x_ini = min(xs + [xd])
        x_fim = max(xs + [xd])
        corpo.append(f'<line x1="{x_ini:.1f}" y1="{y:.1f}" x2="{x_fim:.1f}" y2="{y:.1f}" stroke="{EIXO}" stroke-width="2"/>')
        for x in xs:
            corpo.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{AZUL_CLARO}" stroke="{FUNDO}" stroke-width="2"/>')
        corpo.append(f'<circle cx="{xd:.1f}" cy="{y:.1f}" r="6" fill="{AZUL}" stroke="{FUNDO}" stroke-width="2"/>')
        lado = 1 if vd >= max(va) else -1
        rotulo = fmt(vd)
        if sem_ganho:
            x_txt = max(xs + [xd]) + 12
            corpo.append(texto(x_txt, y + 4, rotulo, 12, TINTA_2))
            corpo.append(texto(x_txt + 40, y + 4, "sem ganho", 11, LARANJA, peso="600"))
        else:
            corpo.append(texto(xd + 12 * lado, y + 4, rotulo, 12, TINTA_2, "start" if lado > 0 else "end"))

    ly = alt - 30
    corpo.append(f'<circle cx="30" cy="{ly - 4}" r="6" fill="{AZUL_CLARO}"/>')
    corpo.append(texto(42, ly, "antes (versão anterior, mesmo dia; nas mudanças 09 e 10, 2 execuções)", 12, TINTA_2))
    corpo.append(f'<circle cx="30" cy="{ly + 16}" r="6" fill="{AZUL}"/>')
    corpo.append(texto(42, ly + 20, "depois", 12, TINTA_2))
    (SAIDA / "vazao-por-mudanca.svg").write_text(
        svg(larg, alt + 10, corpo, "Vazão antes e depois de cada mudança"), encoding="utf-8")


def grafico_cpu_e_vazao():
    rotulos = [("00", "00-linha-de-base")] + [(m[0], m[3]) for m in MUDANCAS]
    vaz = [valores(r, vazao)[0] for _, r in rotulos]
    cpu = [valores(r, cpu_banco_pct_do_limite)[0] for _, r in rotulos]
    larg, alt = 760, 520
    esq, dir_ = 70, 720
    passo = (dir_ - esq) / (len(rotulos) - 1)
    xs = [esq + i * passo for i in range(len(rotulos))]
    corpo = [
        texto(24, 34, "A vazão subiu, a CPU do banco ficou no limite", 18, TINTA, peso="600"),
        texto(24, 56, "Valores de cada mudança (depois), medidos em dias diferentes. Mediana de 3 execuções.", 13, TINTA_2),
    ]

    # Painel de cima: vazão (log)
    t1, b1 = 100, 250
    corpo.append(texto(24, t1 - 14, "Vazão (req/s, escala logarítmica)", 13, TINTA, peso="600"))
    a, b = math.log10(1), math.log10(200)
    y_v = lambda v: b1 - (math.log10(v) - a) / (b - a) * (b1 - t1)
    for marca in [1, 10, 100]:
        y = y_v(marca)
        corpo.append(f'<line x1="{esq}" y1="{y:.1f}" x2="{dir_}" y2="{y:.1f}" stroke="{GRADE}" stroke-width="1"/>')
        corpo.append(texto(esq - 10, y + 4, str(marca), 12, APAGADO, "end"))
    pts = " ".join(f"{x:.1f},{y_v(v):.1f}" for x, v in zip(xs, vaz))
    corpo.append(f'<polyline points="{pts}" fill="none" stroke="{AZUL}" stroke-width="2"/>')
    for x, v in zip(xs, vaz):
        corpo.append(f'<circle cx="{x:.1f}" cy="{y_v(v):.1f}" r="4" fill="{AZUL}" stroke="{FUNDO}" stroke-width="2"/>')
    corpo.append(texto(xs[0] + 8, y_v(vaz[0]) - 10, fmt(vaz[0]), 12, TINTA_2))
    corpo.append(texto(xs[-1] - 8, y_v(vaz[-1]) - 10, fmt(vaz[-1]), 12, TINTA_2, "end"))

    # Painel de baixo: CPU do banco em % do limite
    t2, b2 = 320, 450
    corpo.append(texto(24, t2 - 20, "CPU do banco (% do limite do container)", 13, TINTA, peso="600"))
    y_c = lambda v: b2 - v / 100 * (b2 - t2)
    for marca in [0, 50, 100]:
        y = y_c(marca)
        corpo.append(f'<line x1="{esq}" y1="{y:.1f}" x2="{dir_}" y2="{y:.1f}" stroke="{GRADE if marca else EIXO}" stroke-width="1"/>')
        corpo.append(texto(esq - 10, y + 4, f"{marca}%", 12, APAGADO, "end"))
    pts = " ".join(f"{x:.1f},{y_c(min(v, 100)):.1f}" for x, v in zip(xs, cpu))
    corpo.append(f'<polyline points="{pts}" fill="none" stroke="{AZUL}" stroke-width="2"/>')
    for x, v in zip(xs, cpu):
        corpo.append(f'<circle cx="{x:.1f}" cy="{y_c(min(v, 100)):.1f}" r="4" fill="{AZUL}" stroke="{FUNDO}" stroke-width="2"/>')
    faixa = f"{fmt(min(cpu)).split(',')[0]}% e {fmt(max(cpu)).split(',')[0]}%"
    corpo.append(texto(dir_, t2 - 20, f"entre {faixa} em todas as mudanças", 12, TINTA_2, "end"))

    for x, (num, _) in zip(xs, rotulos):
        corpo.append(texto(x, b2 + 22, num, 12, APAGADO, "middle"))
    corpo.append(texto((esq + dir_) / 2, b2 + 44, "mudança (00 = aplicação original)", 12, APAGADO, "middle"))
    (SAIDA / "cpu-e-vazao.svg").write_text(
        svg(larg, alt, corpo, "Vazão e CPU do banco ao longo das mudanças"), encoding="utf-8")
    return cpu


def seta(x1, x2, y, cor=TINTA_2, tracejada=False):
    traco = ' stroke-dasharray="5 4"' if tracejada else ""
    ponta = x2 - 8 if x2 > x1 else x2 + 8
    return (f'<line x1="{x1}" y1="{y}" x2="{ponta}" y2="{y}" stroke="{cor}" stroke-width="2"{traco}/>'
            f'<polygon points="{x2},{y} {ponta},{y - 5} {ponta},{y + 5}" fill="{cor}"/>')


def diagrama_n_mais_um():
    larg, alt = 760, 420
    corpo = [
        texto(24, 34, "Rota /clientes/:id/pedidos: antes e depois da mudança 02", 18, TINTA, peso="600"),
        texto(24, 56, "Cada seta cheia é uma consulta da API ao banco; a tracejada é a resposta.", 13, TINTA_2),
    ]
    for x0, titulo, linhas, total in [
        (24, "Antes: uma consulta por pedido e por item", [
            "1. o cliente",
            "2. os pedidos do cliente",
            "3. os itens do pedido 1",
            "4. o produto do item 1",
            "5. o produto do item 2",
            "6. os itens do pedido 2",
            "…",
        ], "Total: 2 + 1 por pedido + 1 por item"),
        (400, "Depois: JOIN", [
            "1. o cliente",
            "2. pedidos + itens + produtos (JOIN)",
        ], "Total: sempre 2 consultas"),
    ]:
        api_x, banco_x = x0 + 30, x0 + 300
        corpo.append(texto(x0, 92, titulo, 14, TINTA, peso="600"))
        corpo.append(texto(api_x, 120, "API", 13, TINTA_2, "middle", "600"))
        corpo.append(texto(banco_x, 120, "Banco", 13, TINTA_2, "middle", "600"))
        corpo.append(f'<line x1="{api_x}" y1="128" x2="{api_x}" y2="370" stroke="{EIXO}" stroke-width="1"/>')
        corpo.append(f'<line x1="{banco_x}" y1="128" x2="{banco_x}" y2="370" stroke="{EIXO}" stroke-width="1"/>')
        y = 150
        for rotulo in linhas:
            if rotulo == "…":
                corpo.append(texto((api_x + banco_x) / 2, y + 4, "… e assim por diante", 12, APAGADO, "middle"))
                y += 30
                continue
            corpo.append(seta(api_x, banco_x, y, AZUL))
            corpo.append(texto((api_x + banco_x) / 2, y - 6, rotulo, 12, TINTA, "middle"))
            corpo.append(seta(banco_x, api_x, y + 12, APAGADO, tracejada=True))
            y += 32
        corpo.append(texto(x0, 396, total, 13, TINTA, peso="600"))
    (SAIDA / "n-mais-um.svg").write_text(
        svg(larg, alt, corpo, "Consultas da rota de pedidos do cliente antes e depois do JOIN"), encoding="utf-8")


if __name__ == "__main__":
    grafico_vazao()
    cpu = grafico_cpu_e_vazao()
    diagrama_n_mais_um()
    for num, nome, antes, depois, _ in MUDANCAS:
        print(num, nome, "antes", [fmt(v) for v in valores(antes, vazao)],
              "depois", [fmt(v) for v in valores(depois, vazao)])
    print("CPU do banco (% do limite):", [fmt(v) for v in cpu])
