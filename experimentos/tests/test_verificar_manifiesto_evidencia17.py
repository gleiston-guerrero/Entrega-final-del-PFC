"""Prueba el generador/verificador de manifiesto sobre una copia temporal;
nunca opera sobre experimentos/evidencia-17 real."""

import tempfile
import unittest
from pathlib import Path

from experimentos.verificar_manifiesto_evidencia17 import generar, verificar


class ManifiestoEvidencia17Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paquete = Path(self.tmp.name) / "paquete-prueba"
        (self.paquete / "sub").mkdir(parents=True)
        (self.paquete / "a.json").write_text('{"x": 1}\n', encoding="utf-8")
        (self.paquete / "sub" / "b.txt").write_text("hola\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_generar_luego_verificar_es_valido(self):
        generar(self.paquete)
        self.assertTrue(verificar(self.paquete))

    def test_verificar_falla_si_no_existe_manifiesto(self):
        self.assertFalse(verificar(self.paquete))

    def test_verificar_falla_ante_un_byte_alterado(self):
        generar(self.paquete)
        objetivo = self.paquete / "sub" / "b.txt"
        objetivo.write_bytes(objetivo.read_bytes() + b"X")
        self.assertFalse(verificar(self.paquete))

    def test_manifiesto_no_se_incluye_a_si_mismo(self):
        generar(self.paquete)
        contenido = (self.paquete / "SHA256SUMS.txt").read_text(encoding="utf-8")
        self.assertNotIn("SHA256SUMS.txt", contenido)


if __name__ == "__main__":
    unittest.main()
