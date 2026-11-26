"""Testes do que o snapshot do catálogo chama de mudança. Uso: python -m unittest _scripts/test_snapshot_catalogo.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot_catalogo import diferenca_inci, mudancas_de

BASE = {"id": "x", "nome": "Produto X", "preco": 50.0, "volume_ml": 100, "volume_g": None,
        "ativos": ["niacinamida"], "inci": None, "inci_fonte": None, "inci_em": None}
LISTA = "AQUA, GLYCERIN, NIACINAMIDE, 1,2-HEXANEDIOL, PHENOXYETHANOL"


def tipos(velho, novo):
    return [i["tipo"] for i in mudancas_de({"estado": velho}, novo, "2026-11-26")]


class MudancasTests(unittest.TestCase):
    def test_primeira_lista_inci_nao_e_mudanca(self):
        self.assertEqual(tipos(BASE, {**BASE, "inci": LISTA, "inci_fonte": "embalagem", "inci_em": "2026-11-26"}), [])

    def test_mesma_lista_escrita_de_outro_jeito_nao_e_mudanca(self):
        velho = {**BASE, "inci": LISTA}
        self.assertEqual(tipos(velho, {**BASE, "inci": "Aqua,  Glycerin, Niacinamide, 1,2-Hexanediol, Phenoxyethanol."}), [])

    def test_ingrediente_que_entra_e_sai_vira_formula_com_os_nomes(self):
        velho = {**BASE, "inci": LISTA}
        itens = mudancas_de({"estado": velho}, {**BASE, "inci": "AQUA, GLYCERIN, NIACINAMIDE, 1,2-HEXANEDIOL, PARFUM"}, "2026-11-26")
        self.assertEqual([i["tipo"] for i in itens], ["formula"])
        self.assertEqual(itens[0]["saiu"], ["PHENOXYETHANOL"])
        self.assertEqual(itens[0]["entrou"], ["PARFUM"])
        self.assertNotIn("reformula", itens[0]["leitura"])

    def test_mudar_ativos_do_catalogo_nao_e_formula(self):
        self.assertEqual(tipos(BASE, {**BASE, "ativos": ["niacinamida", "zinco"]}), ["catalogo"])

    def test_virgula_dentro_do_nome(self):
        self.assertEqual(diferenca_inci(LISTA, LISTA.replace("1,2-HEXANEDIOL", "PENTYLENE GLYCOL")),
                         (["1,2-HEXANEDIOL"], ["PENTYLENE GLYCOL"]))

    def test_volume_menor_com_mesmo_preco(self):
        itens = mudancas_de({"estado": BASE}, {**BASE, "volume_ml": 80}, "2026-11-26")
        self.assertEqual([i["tipo"] for i in itens], ["volume"])
        self.assertIn("shrinkflation", itens[0]["leitura"])


if __name__ == "__main__":
    unittest.main()
