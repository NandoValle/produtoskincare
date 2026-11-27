"""Testes do diff de fórmula (INCI) do snapshot do catálogo.

    python3 -m unittest discover -s _scripts -p "test_snapshot_catalogo.py"
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot_catalogo import diff_inci, ingredientes, mudancas_de

BASE = {"nome": "Creme X", "preco": 50.0, "volume_ml": 50, "volume_g": None, "ativos": ["niacinamida"]}


def formula(antes, depois):
    velho = {"estado": {**BASE, "inci": antes, "inci_fonte": "embalagem"}}
    novo = {**BASE, "id": "creme-x", "inci": depois, "inci_fonte": "embalagem"}
    return [i for i in mudancas_de(velho, novo, "2026-12-01") if i["tipo"] == "formula"]


class DiffInci(unittest.TestCase):
    def test_separa_sem_partir_nome_com_virgula(self):
        self.assertEqual(ingredientes("AQUA, 1,2-HEXANEDIOL, Glycerin."), ["AQUA", "1,2-HEXANEDIOL", "Glycerin"])

    def test_primeiro_registro_nao_e_reformulacao(self):
        self.assertEqual(formula(None, "AQUA, GLYCERIN"), [])

    def test_maiusculas_e_espacos_nao_contam(self):
        self.assertEqual(formula("AQUA, GLYCERIN", "Aqua,  Glycerin."), [])

    def test_ingrediente_que_entra_e_que_sai(self):
        (item,) = formula("AQUA, GLYCERIN, NIACINAMIDE", "AQUA, NIACINAMIDE, PARFUM")
        self.assertEqual(item["entraram"], ["PARFUM"])
        self.assertEqual(item["sairam"], ["GLYCERIN"])
        self.assertFalse(item["reordenou"])
        self.assertIn("entraram: PARFUM", item["leitura"])

    def test_so_a_ordem(self):
        d = diff_inci("AQUA, GLYCERIN, NIACINAMIDE", "AQUA, NIACINAMIDE, GLYCERIN")
        self.assertEqual((d["mudou"], d["entraram"], d["sairam"], d["reordenou"]), (True, [], [], True))


if __name__ == "__main__":
    unittest.main()
