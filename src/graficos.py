"""Estilo visual padrão dos gráficos do projeto."""
from pathlib import Path

import matplotlib.pyplot as plt

AZUL = "#2a78d6"
LARANJA = "#eb6834"
CINZA = "#b5b3ad"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
SUPERFICIE = "#fcfcfb"
RAMPA_AZUL = ["#86b6ef", "#5598e7", "#256abf", "#184f95"]

PASTA_IMAGENS = Path(__file__).resolve().parents[1] / "images"


def aplicar_estilo():
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "axes.edgecolor": CINZA,
        "axes.labelcolor": TEXTO_2,
        "axes.titlecolor": TEXTO,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#e6e5e1",
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "xtick.color": TEXTO_2,
        "ytick.color": TEXTO_2,
        "font.size": 10.5,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 130,
        "savefig.bbox": "tight",
    })


def salvar(fig, nome: str):
    PASTA_IMAGENS.mkdir(exist_ok=True)
    fig.savefig(PASTA_IMAGENS / f"{nome}.png", facecolor=SUPERFICIE)


def rotular_barras(ax, fmt="{:.1f}", horizontal=False):
    for p in ax.patches:
        if horizontal:
            v = p.get_width()
            ax.annotate(fmt.format(v), (v, p.get_y() + p.get_height() / 2),
                        xytext=(4, 0), textcoords="offset points", va="center", color=TEXTO, fontsize=9.5)
        else:
            v = p.get_height()
            ax.annotate(fmt.format(v), (p.get_x() + p.get_width() / 2, v),
                        xytext=(0, 3), textcoords="offset points", ha="center", color=TEXTO, fontsize=9.5)
