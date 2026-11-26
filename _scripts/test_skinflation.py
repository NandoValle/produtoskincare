"""Testes da conta do Índice Skinflation. Uso: python3 -m unittest _scripts/test_skinflation.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_skinflation import ipca_acumulado, leituras_mensais, serie


def obs(pid, data, reais, promo=False):
    return {"product_id": pid, "checked_at": data, "price_cents": round(reais * 100), "promo": promo}


TAM = {f"p{i}": {"size_ml": 100, "size_g": None} for i in range(12)}


def indice(observacoes, snapshots=None, campo="unitario"):
    return serie(leituras_mensais(observacoes, snapshots or {}, TAM), campo=campo)


class Skinflation(unittest.TestCase):
    def test_um_mes_so_e_a_base(self):
        s = indice([obs(f"p{i}", "2026-11-02", 50) for i in range(12)])
        self.assertEqual([(l["indice"], l["variacao"]) for l in s], [(100.0, None)])

    def test_todos_sobem_dez_por_cento(self):
        s = indice([obs(f"p{i}", "2026-11-02", 50) for i in range(12)] + [obs(f"p{i}", "2026-12-03", 55) for i in range(12)])
        self.assertAlmostEqual(s[1]["indice"], 110.0)
        self.assertAlmostEqual(s[1]["variacao"], 10.0)
        self.assertEqual(s[1]["pares"], 12)

    def test_frasco_encolhe_e_o_preco_fica(self):
        # p0 vai de 100 ml para 80 ml em dezembro; os outros 11 não mudam.
        snaps = {"p0": [{"em": "2026-11-01", "volume_ml": 100}, {"em": "2026-12-01", "volume_ml": 80}]}
        o = [obs(f"p{i}", "2026-11-02", 50) for i in range(12)] + [obs(f"p{i}", "2026-12-03", 50) for i in range(12)]
        por_ml = indice(o, snaps)[1]["indice"]
        etiqueta = indice(o, snaps, campo="preco")[1]["indice"]
        self.assertAlmostEqual(etiqueta, 100.0)                      # o preço do frasco não mudou
        self.assertAlmostEqual(por_ml, 100 * 1.25 ** (1 / 12))       # o preço por ml de um produto subiu 25%
        self.assertGreater(por_ml, etiqueta)

    def test_promocao_nao_entra(self):
        o = [obs(f"p{i}", "2026-11-02", 50) for i in range(12)] + [obs(f"p{i}", "2026-12-03", 50) for i in range(12)]
        o.append(obs("p0", "2026-12-20", 20, promo=True))
        self.assertAlmostEqual(indice(o)[1]["indice"], 100.0)

    def test_produto_novo_nao_mexe_no_indice(self):
        o = [obs(f"p{i}", "2026-11-02", 50) for i in range(11)] + [obs(f"p{i}", "2026-12-03", 50) for i in range(11)]
        o.append(obs("p11", "2026-12-03", 500))
        s = indice(o)
        self.assertAlmostEqual(s[1]["indice"], 100.0)
        self.assertEqual(s[1]["pares"], 11)

    def test_mes_com_poucos_pares_nao_e_publicado_e_o_seguinte_compara_com_o_ultimo_publicado(self):
        o = [obs(f"p{i}", "2026-11-02", 50) for i in range(12)]
        o += [obs(f"p{i}", "2026-12-03", 60) for i in range(3)]          # só 3 produtos em dezembro
        o += [obs(f"p{i}", "2027-01-05", 55) for i in range(12)]
        s = indice(o)
        self.assertIsNone(s[1]["indice"])
        self.assertAlmostEqual(s[2]["indice"], 110.0)                     # janeiro contra novembro

    def test_sem_volume_fica_fora(self):
        o = [obs(f"p{i}", "2026-11-02", 50) for i in range(12)] + [obs("sem-volume", "2026-11-02", 50)]
        self.assertEqual(indice(o)[0]["produtos"], 12)

    def test_ipca_acumulado_e_incompleto(self):
        meses = ["2026-11", "2026-12", "2027-02"]
        a = ipca_acumulado({"2026-12": 1.0, "2027-01": 1.0, "2027-02": 1.0}, meses)
        self.assertEqual(a["2026-11"], 0.0)
        self.assertAlmostEqual(a["2026-12"], 1.0)
        self.assertAlmostEqual(a["2027-02"], (1.01 ** 3 - 1) * 100)
        self.assertIsNone(ipca_acumulado({"2026-12": 1.0}, meses)["2027-02"])


if __name__ == "__main__":
    unittest.main()
